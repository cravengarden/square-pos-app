
class ErrorCase:

    def get_description(self):
        return self._description

    def get_exception_type(self):
        return self._exception_type

    def __init__(
            self
    ):
        self._description = None
        self._exception_type = None

    def description(self, description):
        self._description = description
        return self

    def exception_type(self, exception_type):
        self._exception_type = exception_type
        return self
