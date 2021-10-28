import requests
from reserveInfo import ReserveInfo, TicketInfo
from config import ConfigInfo
from util import IsLINEException


class AlertReserveStatus:
    def __init__(self, configInfo: ConfigInfo, reserveInfoList: list) -> None:
        self.lineActor = LineActor(configInfo.lineInfo.url, configInfo.lineInfo.token)
        self.reserveInfoList = reserveInfoList
        self.lastMessageDict = {}
        for reserveInfo in reserveInfoList:
            self.lastMessageDict[reserveInfo] = ""

    def alert_hotelInfo_to_LINE(self, reserveInfo: ReserveInfo, message: str):
        if self.lastMessageDict[reserveInfo] != message:
            self.lastMessageDict[reserveInfo] = message
            message_w_date = f"\n【{reserveInfo.dateInfo.year}/{reserveInfo.dateInfo.month}/{reserveInfo.dateInfo.day}の"\
                f"{reserveInfo.hotelInfo.roomNum}部屋の空室情報】\n"
            if message != '':
                message_w_date = message_w_date + message
            else:
                message_w_date = message_w_date + "空室は存在しません"
            self.lineActor.line_ntfy(message_w_date)

    def alert_ticketInfo_to_LINE(self, ticketInfo: TicketInfo, message: str):
        parkNameDict = {1: "ランド", 2: "シー"}
        parkName = parkNameDict[ticketInfo.parkIndex]
        message_w_date = f"\n{message}の試行で{ticketInfo.useDate}に{parkName}の"\
                         f"チケットが大人{ticketInfo.numOfAdult}名、中人{ticketInfo.numOfJunior}名、小人{ticketInfo.numOfChild}名"\
                         f"分のチケットを購入することができました。"
        self.lineActor.line_ntfy(message_w_date)


class LineActor:

    def __init__(self, url, token):
        self.url = url
        self.token = token

    # ラインへ通知を送る関数
    def line_ntfy(self, mess):
        headers = {"Authorization": "Bearer " + self.token}
        payload = {"message": str(mess)}
        try:
            requests.post(self.url, headers=headers, params=payload)
        except BaseException as e:
            print(e)
            # raise IsLINEException("Error On Line post") from e

    def line_ntfy_kakuninn(self, num):
        headers = {"Authorization": "Bearer " + self.token}
        payload = {"message": '調査回数  ' + str(num)}
        requests.post(self.url, headers=headers, params=payload)
