def get_personInfoList(personInfoDict: dict):
    personInfoList = []
    for personKey in personInfoDict:
        personDict = personInfoDict[personKey]
        personInfo = PersonInfo(age=personDict["age"],
                                isNeedBed=personDict["isNeedBed"],
                                roomNum=personDict["roomNum"],
                                name=personDict["name"])
        personInfoList.append(personInfo)

    return personInfoList


def get_dateInfo(dateInfoDict: dict):
    dateInfo = DateInfo(dateInfoDict["year"], dateInfoDict["month"], dateInfoDict["day"])
    return dateInfo


def get_hotelInfo(hotelInfoDict: dict):
    hotelInfo = HotelInfo(hotelInfoDict["roomNum"], hotelInfoDict["hotelName"], hotelInfoDict["roomType"])
    return hotelInfo


def get_nStayInfo(hotelInfoDict: dict):
    nStayInfo = NStayInfo(hotelInfoDict["nStay"])
    return nStayInfo


def get_reserveInfo(dateInfoDict, personInfoDict, hotelInfoDict):
    personInfoList = get_personInfoList(personInfoDict)
    peopleInfo = PeopleInfo(personInfoList)
    dateInfo = get_dateInfo(dateInfoDict)
    hotelInfo = get_hotelInfo(hotelInfoDict)
    nStayInfo = get_nStayInfo(hotelInfoDict)

    reserveInfo = ReserveInfo(dateInfo, nStayInfo, peopleInfo, hotelInfo)
    return reserveInfo


def get_peopleInfoForTicket(peopleInfoForTicketDict: dict):
    numOfAdult = peopleInfoForTicketDict["numOfAdult"]
    numOfJunior = peopleInfoForTicketDict["numOfJunior"]
    numOfChild = peopleInfoForTicketDict["numOfChild"]
    peopleInfoForTicket = PeopleInfoForTicket(numOfAdult, numOfJunior, numOfChild)
    return peopleInfoForTicket


def get_ticketInfo(dateInfoDict: dict, peopleInfoForTicketDict: dict, parkName: str):
    dateInfo = get_dateInfo(dateInfoDict)
    peopleInfoForTicket = get_peopleInfoForTicket(peopleInfoForTicketDict)
    ticketInfo = TicketInfo(dateInfo, peopleInfoForTicket, parkName)
    return ticketInfo


class DateInfo:
    def __init__(self, year, month, day) -> None:
        self.year = year
        self.month = month
        self.day = day


class HotelInfo:
    def __init__(self, roomNum, hotelName=None, roomType=None):
        self.roomNum = roomNum
        self.roomType = roomType
        self.hotelName = hotelName


class NStayInfo:
    def __init__(self, nStay) -> None:
        self.nStay = nStay


class PersonInfo:
    def __init__(self, age: str, isNeedBed: bool, roomNum: int, name=None) -> None:
        self.age_numeric = self._get_age_for_reserve(age)
        self.isAdult = True if self.age_numeric >= 19 else False
        self.age = age
        self.isNeedBed = isNeedBed
        self.roomNum = roomNum
        self.name = name

    def _get_age_for_reserve(self, age: str):
        ageDictForReserveDropdown = {"0???": 0,
                                     "1???": 1,
                                     "2???": 2,
                                     "3???": 3,
                                     "4???": 4,
                                     "5???": 5,
                                     "6??????????????????": 6,
                                     "6??????????????????": 6,
                                     "7???": 7,
                                     "8???": 8,
                                     "9???": 9,
                                     "10???": 10,
                                     "11???": 11,
                                     "12??????????????????": 12,
                                     "12??????????????????": 12,
                                     "13???18??????????????????": 13,
                                     "19?????????": 19}

        return ageDictForReserveDropdown[age]


class PeopleInfo:
    def __init__(self, personInfoList=[]) -> None:
        for personInfo in personInfoList:
            if not isinstance(personInfo, PersonInfo):
                raise ValueError("it is not PersonInfo")
        self._personInfoList = personInfoList

        self._get_peopleInfoForReserve()

    def add(self, personInfo: PersonInfo):
        if not isinstance(personInfo, PersonInfo):
            raise ValueError("it is not PersonInfo class")

        self._personInfoList.append(personInfo)
        self._get_peopleInfoForReserve()

    def _get_peopleInfoForReserve(self):
        self.adultInfoList = []
        self.childInfoList = []
        for personInfo in self._personInfoList:
            if personInfo.isAdult:
                self.adultInfoList.append(personInfo)
            else:
                self.childInfoList.append(personInfo)

        self.adultNum = len(self.adultInfoList)
        self.childNum = len(self.childInfoList)


class ReserveInfo:
    def __init__(self, dateInfo: DateInfo, nStayInfo: NStayInfo, peopleInfo: PeopleInfo, hotelInfo: HotelInfo) -> None:
        self.dateInfo = dateInfo
        self.nStay = nStayInfo.nStay
        self.peopleInfo = peopleInfo
        self.hotelInfo = hotelInfo


class PeopleInfoForTicket:
    def __init__(self, numOfAdult: int, numOfJunior: int, numOfChild: int):
        self.numOfAdult = numOfAdult
        self.numOfJunior = numOfJunior
        self.numOfChild = numOfChild


class TicketInfo:
    def __init__(self, dateInfo: DateInfo, peopleInfoForTicket: PeopleInfoForTicket, parkName: str):
        self.useDate = f"{dateInfo.year:04}{dateInfo.month:02}{dateInfo.day:02}"
        self.numOfAdult = peopleInfoForTicket.numOfAdult
        self.numOfJunior = peopleInfoForTicket.numOfJunior
        self.numOfChild = peopleInfoForTicket.numOfChild
        parkIdxDict = {"land": 1, "sea": 2}
        self.parkIndex = parkIdxDict[parkName.lower()]

        self.parkTicketGroupCd = 20
        self.ticketSales = 1
