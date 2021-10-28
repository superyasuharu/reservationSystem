
class ConfigInfo:
    def __init__(self, configDict):
        self.loginInfo = LoginInfo(configDict["login"])
        self.lineInfo = LineInfo(configDict["line"])


class LoginInfo:
    def __init__(self, loginDict):
        self.mailAdress = loginDict["mailAdress"]
        self.password = loginDict["password"]
        self.code = loginDict["code"]


class LineInfo:
    def __init__(self, lineDict):
        self.url = lineDict["url"]
        self.token = lineDict["token"]
