class StatusError(Exception):
    """지정한 상태값이 아닐 때 내보내는 예외

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
