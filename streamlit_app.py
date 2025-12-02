import logging
import sys
import textwrap
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Literal

import pandas as pd
import pyperclip
import requests
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

LOGO: str = st.secrets.get("logo") or "https://avatars.githubusercontent.com/u/8287084"
HOMEPAGE: str = st.secrets.get("homepage") or False
IP_API_URL: str = st.secrets.get("ip_api_url") or "http://ip-api.com/json/{ip}"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


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
        summary: str = "Failed to retrieve IP details from API. Please try again.",
        details: str | None = None,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        """
        super().__init__(
            summary,
            details,
        )


class InvalidAPIResponseError(MyIPError):
    """
    Exception raised for invalid responses from the IP API.
    """

    def __init__(
        self,
        summary: str = "Invalid response received from the API. Please try again.",
        details: str | None = None,
    ):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        """
        super().__init__(
            summary,
            details,
            logging.WARNING,
        )


class InvalidIPError(MyIPError):
    """
    Exception raised for invalid IP addresses.
    """

    def __init__(self, summary: str | None = None, details: str | None = None):
        """
        :param summary: A brief summary of the error.
        :param details: Detailed information about the error that should not be shown to the user.
        """
        super().__init__(
            summary or "Invalid IP address. Please enter a valid IPv4 or IPv6 address.",
            details,
            logging.INFO,
        )


class NonGlobalIPError(Exception):
    def __init__(
        self,
        message: str = "The IP address is not a global address.",
        ip: IPv4Address | IPv6Address | None = None,
    ):
        super().__init__(message)
        self.ip: IPv4Address | IPv6Address | None = ip


class LinkLocalIPError(NonGlobalIPError):
    def __init__(
        self,
        message: str = "The IP address is a link-local address.",
        ip: IPv4Address | IPv6Address | None = None,
    ):
        super().__init__(message, ip)


class PrivateIPError(NonGlobalIPError):
    def __init__(
        self,
        message: str = "The IP address is a private address.",
        ip: IPv4Address | IPv6Address | None = None,
    ):
        super().__init__(message, ip)


class LoopbackIPError(NonGlobalIPError):
    def __init__(
        self,
        message: str = "The IP address is a loopback (localhost) address.",
        ip: IPv4Address | IPv6Address | None = None,
    ):
        super().__init__(message, ip)


def render_and_log_error(
    exception: Exception | None = None,
    err_msg: str | None = None,
    widget: Literal["error", "toast"] = "error",
) -> None:
    """
    Render an error message using `st.error()`, log the error, and stop execution using
    `st.stop()`.

    :param exception: Exception instance to determine the error type and message.
    :param err_msg: Optional custom error message to display instead of the exception message.
    :param widget: The type of Streamlit widget to use for displaying the error message.
    :return: None
    """

    details: str = ""

    # Determine error message, details, and log level based on exception type
    if exception is None:
        log_level = logging.NOTSET
    elif isinstance(exception, MyIPError):
        if not err_msg and exception.summary:
            err_msg = exception.summary
        if exception.details:
            details = " Details: " + exception.details
        log_level = exception.log_level
    elif isinstance(exception, NonGlobalIPError):
        err_msg = str(exception)
        if str(exception.ip):
            details = " IP: " + str(exception.ip) if exception.ip else ""
        log_level = logging.INFO
    else:
        if str(exception):
            details = " Details: " + str(exception)
        log_level = logging.NOTSET

    # Fallback error message and details if none provided
    err_msg = err_msg or "An error occurred. Please try again."

    # Log the error
    logger.log(log_level or logging.ERROR, err_msg + details)

    # Render the error message
    if widget == "toast":
        st.toast(err_msg, icon=":material/error:")
    else:
        st.error(err_msg, icon=":material/error:")

    st.stop()


def render_ip_address_copy_button(
    ip: IPv4Address | IPv6Address, disabled: bool = False
) -> None:
    """
    Render a button to copy the IP address to clipboard.
    :param ip: IP address to copy
    :param disabled: Whether the button should be disabled
    :return: None
    """

    if st.button(
        "Copy", icon=":material/content_copy:", disabled=disabled, width="stretch"
    ):
        try:
            pyperclip.copy(str(ip))
            st.toast("IP address copied to clipboard!", icon=":material/check_circle:")
        except pyperclip.PyperclipException as e:
            render_and_log_error(
                e,
                err_msg=textwrap.dedent(
                    """
                    Failed to copy IP address to clipboard. 
                    Please copy it manually.
                    """
                ),
                widget="toast",
            )


@st.cache_data(show_spinner="Fetching IP details...")
def fetch_ip_details(ip: str | IPv4Address | IPv6Address) -> dict:
    """
    Fetch IP details from the external API.
    :param ip: IP address to look up
    :type ip: str
    :return: IP details as a dictionary
    :rtype: dict
    :raises IPAPIConnectionError: If there is a connection error to the API.
    :raises InvalidAPIResponseError: If the API response is invalid.
    """

    response = requests.get(IP_API_URL.format(ip=ip))
    if response.status_code != requests.codes.ok:
        raise IPAPIConnectionError(details=f"Status code: {response.status_code}")

    try:
        data = response.json()
    except ValueError as e:
        raise InvalidAPIResponseError(details=str(e))

    return data


def render_search_bar(
    default_ip: IPv4Address | IPv6Address | str | None = None, label: str | None = None
) -> None:
    """
    Render a search bar for IP address lookup.
    :param default_ip: The IP address to pre-fill in the search bar.
    :param label: The label for the search bar.
    :return: None
    """

    with st.form("ip_search_form", border=False):
        search_cols: list[DeltaGenerator] = st.columns(
            [5, 1], vertical_alignment="bottom"
        )
        with search_cols[0]:
            ip_input: str = st.text_input(
                f"Look up a{" fucking" if st.session_state.get("wtf_mode") else "n"} IP address",
                value=str(default_ip) if default_ip is not None else "",
            )
        with search_cols[1]:
            submit: bool = st.form_submit_button(
                "Search",
                icon=":material/search:",
                type="primary",
                width="stretch",
            )
        if submit:
            try:
                ip_input: IPv4Address | IPv6Address = ip_address(ip_input)

            except ValueError as e:
                render_and_log_error(InvalidIPError(details=str(e)))

            st.query_params["ip"] = str(ip_input)
            st.rerun()


def render_ip_details(ip: IPv4Address | IPv6Address) -> None:
    """
    Render IP details fetched from the external API.
    :param ip: IP address to look up
    :return: None
    """

    # Fetch IP details
    logger.info(f"Fetching details for {ip}")
    data: dict = {}
    try:
        data = fetch_ip_details(ip)
        logger.info(f"Fetched details for {ip}: {data}")
    except Exception as e:
        render_and_log_error(e)

    # Validate API response
    if data.get("status") != "success":
        msg: str = data.get("message")
        render_and_log_error(InvalidAPIResponseError(details=msg))

    latitude = data.get("latitude") or data.get("lat")
    longitude = data.get("longitude") or data.get("lon") or data.get("long")
    if latitude and longitude:
        # Render map and details side by side
        left, right = st.columns(2)
        df = pd.DataFrame({"latitude": [latitude], "longitude": [longitude]})
        with left:
            map_container = st.empty()
            with map_container:
                st.map(df, size=100)
        with right:
            st.write(data)
    else:
        # No coordinates, render IP details only
        st.write(data)


def main():
    user_ip: IPv4Address | IPv6Address | None = ip_address(
        st.context.ip_address or "127.0.0.1"
    )
    if not user_ip.is_global:
        user_ip = None

    logger.info("whatsmyip accessed by %s", user_ip)

    st.logo(LOGO, size="large", link=HOMEPAGE)
    st.title(
        f"What's my{" fucking " if st.session_state.get("wtf_mode")else " "}IP?",
        anchor=False,
    )

    wtf_mode: bool = st.toggle("WTF Mode", key="wtf_mode", help="WTF is this?")

    ip_cols = st.columns([1, 5], vertical_alignment="center")
    with ip_cols[0]:
        render_ip_address_copy_button(user_ip, disabled=not user_ip)
    with ip_cols[1]:
        if user_ip:
            st.markdown(
                f"Your{" fucking " if wtf_mode else " "}IP address is `{user_ip}`"
            )
        else:
            st.markdown(
                "🖕 Nobody knows your fucking IP address"
                if wtf_mode
                else "⚠️ Unable to determine your global IP address"
            )

    if query_ip := st.query_params.get("ip"):
        # IP defined, show IP details
        render_search_bar(query_ip)
        try:
            query_ip: IPv4Address | IPv6Address = ip_address(query_ip)
        except ValueError as e:
            render_and_log_error(InvalidIPError(details=str(e)))

        # Check if the IP is global
        if not query_ip.is_global:
            if query_ip.is_link_local:
                render_and_log_error(LinkLocalIPError())
            elif query_ip.is_loopback:
                render_and_log_error(LoopbackIPError())
            elif query_ip.is_private:
                render_and_log_error(PrivateIPError())
            else:
                render_and_log_error(NonGlobalIPError())

        # IP is global, render details
        render_ip_details(query_ip)
    else:
        # No IP defined

        render_search_bar(user_ip)


if __name__ == "__main__":
    main()
