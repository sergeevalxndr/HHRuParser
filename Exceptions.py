class ErrorAuthDataMissing(Exception):
    def __init__(self):
        super().__init__("Authorisation data is missing! Check the configuration file.")


class ErrorAuthDataWrong(Exception):
    def __init__(self):
        super().__init__("Authorisation data is wrong! Check the configuration file.")


class ErrorAuthLimit(Exception):
    def __init__(self):
        super().__init__("Reached authorisation limit!")
