from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from pathlib import Path
import time
import traceback
from reserveInfo import DateInfo, NStayInfo, PersonInfo, PeopleInfo, HotelInfo, ReserveInfo, TicketInfo
from config import ConfigInfo
from util import IsBusyException, IsErrorException


class DisneyScraper:
    def __init__(self, configInfo: ConfigInfo, driver_path: Path):
        mobile_emulation = {"deviceName": "iPad"}
        options = webdriver.ChromeOptions()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument('--incognito')
        options.add_argument('--enable-quic')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # options.headless = True

        self.driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
        self.driver.set_page_load_timeout(30)
        self.action = ActionInWebWithWait(self.driver)
        self.inputReserveInformation = InputReserveInformation(self.driver, self.action)
        self.max_tab_num = 10

        self.login_mailAddress = configInfo.loginInfo.mailAdress
        self.login_password = configInfo.loginInfo.password
        self.code = configInfo.loginInfo.code

        self.xml_noResult = '[@class="noResultView"]'
        self.xml_hotelResult = '[@class="cards"]'
        self.closed_window = set()

    def __del__(self):
        try:
            window_num = self.driver.window_handles
            for window in window_num:
                self.driver.switch_to.window(window)
                self.driver.close()
            # self.driver.quit()

        except BaseException:
            pass

    def login(self):
        self.driver.implicitly_wait(10)
        self.action.get(self.reserve_url)
        xml_sideMenu = '[@class="btnDrower"]'
        self.action.click_by_xpath(xml_sideMenu)
        xml_loginIcon = '[@class="login"]'
        self.action.click_by_xpath(xml_loginIcon)

        # ログイン
        xml_userId = '[@id="_userId"]'
        self.action.send_key_by_xpath(xml_userId, self.login_mailAddress)
        xml_password = '[@id="_password"]'
        self.action.send_key_by_xpath(xml_password, self.login_passward)
        xml_confirmButton = '[@class="list_button"]'
        self.action.click_by_xpath(xml_confirmButton)

        # self._confirm_log_in()

    def get_ticket_info_directly(self, ticketInfo):
        try:
            message = self._get_ticket_info_directly(ticketInfo)
        except BaseException as e:
            print(e)
            message = ""

        return message

    def _get_ticket_info_directly(self, ticketInfo: TicketInfo):

        ticketSales = ticketInfo.ticketSales
        useDate = ticketInfo.useDate
        parkIndex = ticketInfo.parkIndex
        numOfAdult = ticketInfo.numOfAdult
        numOfJunior = ticketInfo.numOfJunior
        numOfChild = ticketInfo.numOfChild
        parkTicketGroupCd = ticketInfo.parkTicketGroupCd

        url = f"https://reserve.tokyodisneyresort.jp/ticket/search/?"\
              f"useDateFrom={useDate}&selectParkDay1={parkIndex:02}&parkTicketSalesForm={ticketSales}&"\
              f"numOfAdult={numOfAdult}&numOfJunior={numOfJunior}&numOfChild={numOfChild}&"\
              f"parkTicketGroupCd={parkTicketGroupCd:03}&useDays=1&route=2&"

        message = self._retry_action_when_busy(url, self._get_ticketSearchResult, self._is_loadingTicketResult_page)
        if message is not None:
            message = f"{self._retry_cnt}回"
        return message

    def _is_loadingTicketResult_page(self):
        return True

    def _get_ticketSearchResult(self):

        xml_buy = '[@class="list_button button-vertical"]'
        element = self.action.click_by_xpath(xml_buy)

        # xml_confirm = '[@class="list-purchae-view"]'
        # xml_confirm = '[@class="list_button"]'
        xml_confirm = '[@class="js-mm-next button next"]'
        element = self.action.click_by_xpath(xml_confirm)

        logInUrl = self.driver.current_url

        if "errorCd=" in logInUrl:
            xml_error = '[@class="messages"]'
            element = self.action.get_element_by_xpath(xml_error)

            if element is not None:
                if "売り切れ" in element.text:
                    return

        message = "チケット取得画面通過"

        # ログイン
        xml_userId = '[@name="userId"]'
        self.action.send_key_by_xpath(xml_userId, self.login_mailAddress)
        xml_password = '[@name="password"]'
        self.action.send_key_by_xpath(xml_password, self.login_password)
        xml_confirmButton = '[@class="list_button"]'
        self.action.click_by_xpath(xml_confirmButton)

        xml_cardInfo = '[@name="defaultCardSecurityCode"]'
        self.action.send_key_by_xpath(xml_cardInfo, self.code)

        xml_confirm_to_by = '[@class="next executeSubmit ui-link"]'
        # xml_confirm_to_by = '[@name="execute"]'
        self.action.click_by_xpath(xml_confirm_to_by)

        xml_check_box = '[@for="accept"]'
        self.action.click_by_xpath(xml_check_box)
        xml_final_confirm = '[@name="next"]'

        message += "/最後まで通過"

        return message

    def _get_hotel_info_directly(self, reserveInfo: ReserveInfo):
        roomsNum = reserveInfo.hotelInfo.roomNum
        adultNum = reserveInfo.peopleInfo.adultNum
        childNum = reserveInfo.peopleInfo.childNum
        stayingDays = reserveInfo.nStay
        useDate = f"{reserveInfo.dateInfo.year:02}{reserveInfo.dateInfo.month:02}{reserveInfo.dateInfo.day:02}"
        if childNum == 0:
            childAgeBedInform = ""
        else:
            childAgeBedInform = "03_3%7C00_3%7C"

        url = f"https://reserve.tokyodisneyresort.jp/sp/hotel/list/?showWay="\
              f"&roomsNum={roomsNum}&adultNum={adultNum}&childNum={childNum}&"\
              f"stayingDays={stayingDays}&useDate={useDate}&cpListStr=&childAgeBedInform={childAgeBedInform}&"\
              f"searchHotelCD=&searchHotelDiv=&hotelName=&searchHotelName=&searchLayer=&searchRoomName=&"\
              f"hotelSearchDetail=true&detailOpenFlg=0&checkPointStr=&hotelChangeFlg=false&removeSessionFlg=true&"\
              f"returnFlg=false&hotelShowFlg=&displayType=data-hotel&reservationStatus=1"

        message = self._retry_action_when_busy(url, self._get_hotelSearchResult, self._is_loadingHotelResult_page)
        return message

    def _retry_action_when_busy(self, url, get_result_function, is_loading_function):

        self._retry_cnt = 0

        message = None
        is_busy = False
        try:
            self.action.get(url)
            message = get_result_function()
            if message is not None:
                return message

        except IsBusyException:
            is_busy = True
            # return
        except BaseException as e:
            print(e)
            return

        self.src_window_handle = self.driver.current_window_handle

        if is_busy or message is None:
            is_sucess = False
            while not is_sucess:
                try:
                    # タブ数がmaxになるまでタブ起動
                    try:
                        c_tab_num = len(self.driver.window_handles)
                    except BaseException:
                        c_tab_num = 0
                    new_tab_num = self.max_tab_num - c_tab_num
                    for idx in range(new_tab_num):
                        self._retry_cnt += 1
                        self.driver.execute_script("window.open()")
                        nextWindow = self.driver.window_handles[-1]

                        self.driver.switch_to.window(nextWindow)
                        self.action.get(url)
                        if not self.action._busy_check():
                            break
                        time.sleep(0.5)

                except IsBusyException as e:
                    # ビジーだった結果のタブは閉じる
                    # print(e)
                    self._close_currentWindow()

                except BaseException as e:
                    print(e)

                try:
                    # タブの中身を順次確認
                    window_handles = self.driver.window_handles
                    for window in window_handles:
                        self.driver.switch_to.window(window)
                        if is_loading_function():
                            try:
                                message = get_result_function()
                                is_sucess = True
                            except IsBusyException as e:
                                self._close_currentWindow()
                            if is_sucess:
                                break
                except IsBusyException as e:
                    # ビジーだった結果のタブは閉じる
                    # print(e)
                    self._close_currentWindow()
                except BaseException as e:
                    print(e)
        return message

    def _close_currentWindow(self):
        current_window_handle = self.driver.current_window_handle
        if self.src_window_handle != current_window_handle:
            self.closed_window.add(current_window_handle)
            self.driver.close()
            window_handles = self.driver.window_handles
            self.driver.switch_to.window(window_handles[0])
            time.sleep(0.5)

    def _is_loadingHotelResult_page(self):
        noResultElement = self.action.get_element_by_xpath(self.xml_noResult)
        hotelResultElement = self.action.get_element_by_xpath(self.xml_hotelResult)

        noResultText = noResultElement.text
        hotelResultText = hotelResultElement.text
        if (noResultText == '') & ("0円" not in hotelResultText):
            return True
        else:
            return False

    def _get_hotelSearchResult(self, trialLimit=300):

        noResultElement = self.action.get_element_by_xpath(self.xml_noResult)
        hotelResultElement = self.action.get_element_by_xpath(self.xml_hotelResult)

        isLoadedPage = False
        errorCnt = 0
        while not isLoadedPage:
            if errorCnt >= trialLimit:
                print("タイムアウトが発生しました")
                # self.driver.quit()
                return None

            noResultText = noResultElement.text
            hotelResultText = hotelResultElement.text
            if (noResultText == '') & ("0円" not in hotelResultText):
                time.sleep(1)
                errorCnt += 1
            else:
                isLoadedPage = True

        message = ''
        if noResultText == '':
            xpath_h1 = 'h1'
            elements = self.driver.find_elements_by_xpath(f'//{xpath_h1}')
            for idx, element in enumerate(elements):
                if element.text != "":
                    if "ホテル" in element.text:
                        message += f"\n{element.text}\n"
                    else:
                        message += f"・{element.text}\n"
                    print(f"{element.text}")

        # self.driver.quit()
        return message

    def get_hotel_info(self, reserveInfo: ReserveInfo):
        self.driver.implicitly_wait(10)
        self.action.get(self.reserve_url)

        xml_hotelIcon = '[@class="iconHotel"]'
        self.action.click_by_xpath(xml_hotelIcon)
        cur_url = self.driver.current_url
        if "dialog" in cur_url:
            xml_confirmlIcon = '/html/body/div[10]/div/div[2]/ul'
            # クリックボタンが定期的にdiableになってクリックできなくなるので、ページが遷移しているまでくり返す
            is_still_dialog = True
            while is_still_dialog:
                self.action.click_by_xpath(xml_confirmlIcon, isFullXpath=True)
                cur_url = self.driver.current_url
                if "dialog" not in cur_url:
                    is_still_dialog = False

        xml_dateIcon = '[@class="iconDateBl"]'
        self.action.click_by_xpath(xml_dateIcon)

        self.inputReserveInformation(reserveInfo)

        message = self._get_hotelSearchResult()
        return message

    def _confirm_log_in(self):
        xml_sideMenu = '[@class="btnDrower"]'
        self.action.click_by_xpath(xml_sideMenu)
        xml_mypageIcon = '[@class="mypage"]'
        self.action.get_element_by_xpath(xml_mypageIcon)
        xml_logoutIcon = '[@class="logout"]'
        self.action.click_by_xpath(xml_logoutIcon)


class InputInfo:
    def __init__(self, driver, actionInWebWithWait):
        self.driver = driver
        self.action = actionInWebWithWait

    def __call__(self):
        pass


class InputReserveInformation(InputInfo):
    def __init__(self, driver, actionInWebWithWait):
        super().__init__(driver, actionInWebWithWait)
        self._inputReserveDate = InputReserveDate(driver, actionInWebWithWait)
        self._inputNstay = InputNstay(driver, actionInWebWithWait)
        self._inputNperson = InputNperson(driver, actionInWebWithWait)
        self._inputNroom = InputNroom(driver, actionInWebWithWait)
        self._inputHotel = InputHotel(driver, actionInWebWithWait)

    def __call__(self, reserveInfo: ReserveInfo):

        self._inputReserveDate(reserveInfo.dateInfo)
        self._inputNstay(reserveInfo.nStay)
        self._inputNperson(reserveInfo.peopleInfo)
        self._inputNroom(reserveInfo.hotelInfo.roomNum)
        self._inputHotel(reserveInfo.hotelInfo.hotelName)

        xpath_searchBtn = '[@class="sectionBtnModal"]'
        self.action.click_by_xpath(xpath_searchBtn)


class InputNstay(InputInfo):
    def __call__(self, nstays):
        xpath_inputStayDays = '[@id="stayDays"]'
        self.action.select_element_from_visibleText_by_xpath(xpath_inputStayDays, nstays)


class InputNroom(InputInfo):
    def __call__(self, nRoom):
        xpath_inputRoomsNum = '[@id="roomsNum"]'
        self.action.select_element_from_visibleText_by_xpath(xpath_inputRoomsNum, nRoom)


class InputHotel(InputInfo):
    def __call__(self, hotel):
        if hotel is None:
            return
        xpath_inputHotel = '[@id="hotelCdSelecter"]'
        self.action.select_element_from_visibleText_by_xpath(xpath_inputHotel, hotel)


class InputNperson(InputInfo):
    def __call__(self, peopleInfo: PeopleInfo):
        self._input_nadult(peopleInfo.adultNum)
        self._input_nchild(peopleInfo.childInfoList)

    def _input_nadult(self, adultNum: int):
        xpath_inputAdultNum = '[@id="adultNum"]'
        self.action.select_element_from_visibleText_by_xpath(xpath_inputAdultNum, adultNum)

    def _input_nchild(self, childInfoList: list):
        xpath_inputChildNum = '[@id="childNum"]'
        childrenNum = len(childInfoList)
        self.action.select_element_from_visibleText_by_xpath(xpath_inputChildNum, childrenNum)
        for childIdx, childInfo in enumerate(childInfoList):
            xpath_inputChildAge = f'[@class="childNumSelect hotelChildAge_{childIdx+1}"]'
            childAge = childInfo.age
            self.action.select_element_from_visibleText_by_xpath(xpath_inputChildAge, childAge)
            if childInfo.age_numeric == 0:
                continue
            if childInfo.isNeedBed:
                xpath_inputChildBed = f'[@for="hotel_bed_{childIdx+1}"]'
            else:
                xpath_inputChildBed = f'[@for="hotel_lyingbed_{childIdx+1}"]'
            self.action.click_by_xpath(xpath_inputChildBed)


class InputReserveDate(InputInfo):
    def __init__(self, driver, actionInWebWithWait) -> None:
        super().__init__(driver, actionInWebWithWait)
        self.xml_calenderYear = '[@class="ui-datepicker-year"]'
        self.xml_calenderMonth = '[@class="ui-datepicker-month"]'
        self.xml_calenderDay = '[@data-handler="selectDay"]'
        self.xpath_nextMonth = '[@class="ui-icon ui-icon-circle-triangle-e"]'

    def __call__(self, dateInfo: DateInfo):
        # show calender
        xml_dateIcon = '[@id="useDateParam"]'
        self.action.click_by_xpath(xml_dateIcon)

        year = dateInfo.year
        month = dateInfo.month
        day = dateInfo.day

        self._move_to_correct_year_or_month(year)
        self._move_to_correct_year_or_month(month, is_year=False)
        self._click_correct_day(day)

    def _move_to_correct_year_or_month(self, date: int, is_year=True):
        """[summary]

        Args:
            date (int): year or month

        Raises:
            ValueError: [description]
        """
        is_correct_date = False
        while not is_correct_date:
            if is_year:
                xml_calendarDate = self.xml_calenderYear
            else:
                xml_calendarDate = self.xml_calenderMonth
            element = self.action.get_element_by_xpath(xml_calendarDate)

            if is_year:
                splitText = "年"
            else:
                splitText = "月"

            cdate = int(element.text.split(splitText)[0])

            if cdate > date:
                raise ValueError("you input past date")
            elif cdate < date:
                self.action.click_by_xpath(self.xpath_nextMonth)
            else:
                is_correct_date = True

    def _click_correct_day(self, day: int):
        elements = self.action.get_elements_by_xpath(self.xml_calenderDay)
        for element in elements:
            eday = int(element.text)
            if eday == day:
                element.click()
                return

        raise ValueError("you input past date")


class ActionInWebWithWait:
    def __init__(self, driver, waitTime=180, is_debug=False):
        self.driver = driver
        self.wait = WebDriverWait(driver, waitTime)
        self.ac = ActionChains(driver)
        self.is_debug = is_debug

    def get_element_by_xpath(self, xpath, isFullXpath=False):
        element = None

        self._busy_check()

        try:
            if isFullXpath:
                element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            else:
                element = self.wait.until(EC.presence_of_element_located((By.XPATH, f'//*{xpath}')))
        except BaseException as e:
            print(e)
            print(traceback.format_exc())
            # self.driver.quit()

        self._noName_check()

        if element is None:
            raise Exception(f"couldnt get correct element.{self.driver.current_url}--{xpath}")

        return element

    def get_elements_by_xpath(self, xpath, isFullXpath=False):

        self._busy_check()

        elements = None
        try:
            if isFullXpath:
                self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elements = self.driver.find_elements_by_xpath(xpath)
            else:
                self.wait.until(EC.presence_of_element_located((By.XPATH, f'//*{xpath}')))
                elements = self.driver.find_elements_by_xpath(f'//*{xpath}')
        except BaseException as e:
            print(e)
            print(traceback.format_exc())
            # self.driver.quit()
        self._noName_check()
        if elements is None:
            raise Exception(f"couldnt get correct element.{self.driver.current_url}--{xpath}")

        return elements

    def click_by_xpath(self, xpath, isFullXpath=False):
        erroCnt = 0
        endLoop = False
        while not endLoop:
            try:
                element = self.get_element_by_xpath(xpath, isFullXpath=isFullXpath)
                element.click()
                endLoop = True
            except IsBusyException as e:
                raise IsBusyException from e

            except BaseException as e:
                print(e)
                erroCnt += 1
                time.sleep(1)
                if erroCnt > 300:
                    element = None
                    endLoop = True
                    print(traceback.format_exc())
                    # self.driver.quit()

        self._error_check()
        self._noName_check()

        return element

    def send_key_by_xpath(self, xpath, inputKey, isFullXpath=False):
        erroCnt = 0
        endLoop = False
        while not endLoop:
            try:
                element = self.get_element_by_xpath(xpath, isFullXpath=isFullXpath)
                endLoop = True
            except IsBusyException as e:
                raise IsBusyException from e

            except BaseException as e:
                print(e)
                erroCnt += 1
                time.sleep(1)
                if erroCnt > 300:
                    element = None
                    endLoop = True
                    print(traceback.format_exc())
                    # self.driver.quit()

        self._error_check()
        self._noName_check()
        element.send_keys(inputKey)
        return element

    def select_element_from_visibleText_by_xpath(self, xpath, dropdownText):
        dropdown = self.get_element_by_xpath(xpath)
        select = Select(dropdown)
        select.select_by_visible_text(str(dropdownText))

    def _busy_check(self):
        busyMessage = self.driver.find_elements_by_class_name("textalign")
        if len(busyMessage) > 0 and busyMessage[0].text.find('アクセスが集中') != -1:
            raise IsBusyException(f"couldnt open correct page because the website is busy.")

        return False

    def _error_check(self):
        cUrl = self.driver.current_url

        if "errorCd=" in cUrl:
            urlUnits = cUrl.split("&")
            errorCode = ""
            for urlUnit in urlUnits:
                if "errorCd=" in urlUnit:
                    errorCode = urlUnit
            raise IsErrorException(f"error Code '{errorCode}'")
        return False

    def _noName_check(self):
        title = self.driver.title
        if title == "無題":
            raise IsBusyException(f"couldnt open correct page.")

    def get(self, url):
        self.driver.get(url)
        self._busy_check()
        self._error_check()
        self._noName_check()
