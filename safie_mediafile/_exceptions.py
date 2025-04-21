from typing import Any, Union


class SafieError(Exception):
    """Base exception class for Safie API"""


class SafieAPIError(SafieError):
    """Error during API call"""

    def __init__(self, message: str, status_code: int, response: Union[Any, str]):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class SafieMediaFileError(Exception):
    """Base exception class for Safie Media File operations"""


class SafieMediaFileTimeoutError(SafieMediaFileError):
    """Exception when media file generation times out"""
