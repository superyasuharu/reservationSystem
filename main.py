import pytz
import datetime
import time
import yaml
import argparse
from pathlib import Path
import datetime

from disneyScrayper import DisneyScraper
from reserveInfo import get_reserveInfo, get_ticketInfo
from alertSystem import AlertReserveStatus
from config import ConfigInfo


def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--yamlDir', type=str, default='yamls')
    parser.add_argument('--driverPath', type=str, default='driver/chromedriver_95')
    parser.add_argument('--hotelReserveYamlBaseName', type=str, default='hotelReserveInfo')
    parser.add_argument('--ticketYamlBaseName', type=str, default='ticketInfo')
    parser.add_argument('--configYamlName', type=str, default='config')

    args = parser.parse_args()

    args.yamlDir = Path(args.yamlDir)
    args.driverPath = Path(args.driverPath)

    return args


def get_ticketInfos(yamlDir: Path, ticketYamlBaseName: str):

    ticketInfos = []
    ticketInfoYamls = yamlDir.glob(f"{ticketYamlBaseName}*.yaml")
    for ticketInfoYaml in ticketInfoYamls:
        with open(ticketInfoYaml, mode='r', encoding='utf-8') as yml:
            ticketInfoDict = yaml.safe_load(yml)
        peopleInfoForTicketDict = ticketInfoDict["peopleInfoForTicket"]
        dateInfoDict = ticketInfoDict["dateInfo"]
        parkName = ticketInfoDict["parkName"]

        ticketInfo = get_ticketInfo(dateInfoDict, peopleInfoForTicketDict, parkName)

        ticketInfos.append(ticketInfo)

    return ticketInfos


def get_hotelReserveInfos(yamlDir: Path, hotelReserveYamlBaseName: str):

    hotelReserveInfos = []
    hotelReserveYamls = yamlDir.glob(f"{hotelReserveYamlBaseName}*.yaml")
    for hotelReserveYaml in hotelReserveYamls:
        with open(hotelReserveYaml, mode='r', encoding='utf-8') as yml:
            hotelReserveInfoDict = yaml.safe_load(yml)
        personInfoDict = hotelReserveInfoDict["peopleInfo"]
        dateInfoDict = hotelReserveInfoDict["dateInfo"]
        hotelInfoDict = hotelReserveInfoDict["hotelInfo"]

        hotelReserveInfo = get_reserveInfo(dateInfoDict, personInfoDict, hotelInfoDict)

        hotelReserveInfos.append(hotelReserveInfo)

    return hotelReserveInfos


def load_configInfo(yamlDir: Path, configYamlName: str):
    configInfoYamlPath = yamlDir / f"{configYamlName}.yaml"
    with open(configInfoYamlPath, mode='r', encoding='utf-8') as yml:
        configInfoDict = yaml.safe_load(yml)
    configInfo = ConfigInfo(configInfoDict)
    return configInfo


def scrape_reseveInfoList(
        alertReserveHotelStatus: AlertReserveStatus,
        alertReserveVPStatus: AlertReserveStatus,
        reserveInfoList: list,
        configInfo: ConfigInfo,
        driverPath: Path):

    for reserveInfo in reserveInfoList:
        disneyScraper = DisneyScraper(configInfo, driverPath)
        message = disneyScraper._get_hotel_info_directly(reserveInfo)
        if message is not None:
            alertReserveHotelStatus.alert_hotelInfo_to_LINE(reserveInfo, message)

        message = disneyScraper._get_vacationPackage_info_directly(reserveInfo)
        if message is not None:
            alertReserveVPStatus.alert_vpInfo_to_LINE(reserveInfo, message)

        del disneyScraper


def scrape_ticketInfoList(alertReserveStatus: AlertReserveStatus, ticketInfoList: list, configInfo: ConfigInfo, driverPath: Path):

    for ticketInfo in ticketInfoList:
        disneyScraper = DisneyScraper(configInfo, driverPath)

        message = disneyScraper.get_ticket_info_directly(ticketInfo)
        if message is not None:
            alertReserveStatus.alert_ticketInfo_to_LINE(ticketInfo, message)

        del disneyScraper


def main():
    args = get_argument()
    yamlDir = args.yamlDir
    hotelReserveYamlBaseName = args.hotelReserveYamlBaseName
    ticketYamlBaseName = args.ticketYamlBaseName
    reserveInfo_List = get_hotelReserveInfos(yamlDir, hotelReserveYamlBaseName)
    ticketInfo_List = get_ticketInfos(yamlDir, ticketYamlBaseName)

    configYamlName = args.configYamlName
    configInfo = load_configInfo(yamlDir, configYamlName)

    iterN = 0
    alertReserveHotelStatus = AlertReserveStatus(configInfo, reserveInfo_List)
    alertReserveVPStatus = AlertReserveStatus(configInfo, reserveInfo_List)
    while True:
        dt_now = datetime.datetime.now()
        hour = dt_now.hour
        if hour >= 14:
            iterN += 1
            now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
            print(f"{iterN}回目の調査開始: {now}")
            scrape_ticketInfoList(alertReserveHotelStatus, ticketInfo_List, configInfo, args.driverPath)
            scrape_reseveInfoList(alertReserveHotelStatus, alertReserveVPStatus, reserveInfo_List, configInfo, args.driverPath)

        min01 = 60 * 1
        time.sleep(min01)


if __name__ == "__main__":
    main()
