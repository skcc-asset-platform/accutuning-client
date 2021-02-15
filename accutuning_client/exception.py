class StatusError(Exception):
    """지정한 상태값이 아닐 때 내보내는 예외

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class HttpStatusError(Exception):
    """HTTP 상태코드가 HTTP.OK이 아닐경우 내보내는 예외"""

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


class PreviousJobNotDoneError(Exception):
    """선행 작업이 끝나지 않았을 경우 내보내는 예외"""

    def __init__(self, message):
        self.message = message
