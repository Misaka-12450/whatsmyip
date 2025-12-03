"""
Custom exception classes for the whatsmyip application.
"""

import logging
from ipaddress import IPv4Address, IPv6Address


class MyIPError(Exception):
    """
    Base exception class for MyIP-related errors.
    """

    def __init__(
        self,
        summary: str | None = None,
        details: str | None = None,
        log_level: int = logging.ERROR,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        :param log_level: The logging level for this error.
        """
        super().__init__(summary)
        self.summary: str = summary or ""
        self.details: str = details or ""
        self.log_level: int = log_level

    def __str__(self):
        return self.summary


class IPAPIConnectionError(MyIPError):
    """
    Exception raised for connection errors to the IP API.
    """

    def __init__(
        self,
        summary: str = "",
        details: str | None = None,
        wtf_mode: bool = False,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        :param wtf_mode: Whether to use WTF mode messaging.
        """
        super().__init__(
            (
                summary or "Can't connect to the fucking API right now!"
                if wtf_mode
                else summary or "Failed to connect to the IP API. Please try again."
            ),
            details,
        )


class InvalidAPIResponseError(MyIPError):
    """
    Exception raised for invalid responses from the IP API.
    """

    def __init__(
        self,
        summary: str = "",
        details: str | None = None,
        wtf_mode: bool = False,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        :param wtf_mode: Whether to use WTF mode messaging.
        """
        super().__init__(
            (
                summary or "The fucking API returned an invalid response!"
                if wtf_mode
                else summary
                or "Invalid response received from the API. Please try again."
            ),
            details,
            logging.WARNING,
        )


class InvalidIPError(MyIPError):
    """
    Exception raised for invalid IP addresses.
    """

    def __init__(
        self,
        summary: str | None = None,
        details: str | None = None,
        wtf_mode: bool = False,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        :param wtf_mode: Whether to use WTF mode messaging.
        """
        super().__init__(
            (
                summary or "That's not a valid fucking IP address!"
                if wtf_mode
                else summary
                or "Invalid IP address. Please enter a valid IPv4 or IPv6 address."
            ),
            details,
            logging.INFO,
        )


class NonGlobalIPError(Exception):
    """
    Exception raised when an IP address is not a global address.
    """

    def __init__(
        self,
        message: str = "",
        ip: IPv4Address | IPv6Address | None = None,
        wtf_mode: bool = False,
    ):
        super().__init__(
            message or "That's not a global fucking address!"
            if wtf_mode
            else message or "The IP address is not a global address."
        )
        self.ip: IPv4Address | IPv6Address | None = ip


class LinkLocalIPError(NonGlobalIPError):
    """
    Exception raised when an IP address is a link-local address.
    """

    def __init__(
        self,
        message: str = "",
        ip: IPv4Address | IPv6Address | None = None,
        wtf_mode: bool = False,
    ):
        super().__init__(
            (
                message or "That's a fucking link-local address!"
                if wtf_mode
                else message or "The IP address is a link-local address."
            ),
            ip,
        )


class PrivateIPError(NonGlobalIPError):
    """
    Exception raised when an IP address is a private address.
    """

    def __init__(
        self,
        message: str = "",
        ip: IPv4Address | IPv6Address | None = None,
        wtf_mode: bool = False,
    ):
        super().__init__(
            (
                message or "That's a fucking private address!"
                if wtf_mode
                else message or "The IP address is a private address."
            ),
            ip,
        )


class LoopbackIPError(NonGlobalIPError):
    """
    Exception raised when an IP address is a loopback address.
    """

    def __init__(
        self,
        message: str = "",
        ip: IPv4Address | IPv6Address | None = None,
        wtf_mode: bool = False,
    ):
        super().__init__(
            (
                message or "That's a fucking loopback address!"
                if wtf_mode
                else message or "The IP address is a loopback (localhost) address."
            ),
            ip,
        )
