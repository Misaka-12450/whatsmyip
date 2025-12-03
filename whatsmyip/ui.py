"""
Streamlit UI rendering functions.
"""

import logging
import textwrap
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Literal

import pandas as pd
import pyperclip
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from whatsmyip.api import fetch_ip_details, process_ip_details
from whatsmyip.exceptions import (
    InvalidAPIResponseError,
    InvalidIPError,
    LinkLocalIPError,
    LoopbackIPError,
    MyIPError,
    NonGlobalIPError,
    PrivateIPError,
)

logger = logging.getLogger(__name__)


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


def render_search_bar(
    default_ip: IPv4Address | IPv6Address | str | None = None,
    wtf_mode: bool = False,
) -> None:
    """
    Render a search bar for IP address lookup.

    :param default_ip: The IP address to pre-fill in the search bar.
    :param wtf_mode: Whether to use WTF mode messaging.
    :return: None
    """
    with st.form("ip_search_form", border=False):
        search_cols: list[DeltaGenerator] = st.columns(
            [5, 1], vertical_alignment="bottom"
        )
        with search_cols[0]:
            ip_input: str = st.text_input(
                f"Look up a{' fucking' if wtf_mode else 'n'} IP address",
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
            # try:
            #     ip_input: IPv4Address | IPv6Address = ip_address(ip_input.strip())
            # except ValueError as e:
            #     render_and_log_error(InvalidIPError(details=str(e), wtf_mode=wtf_mode))

            st.query_params["ip"] = str(ip_input)
            st.rerun()


def render_ip_details(
    ip: IPv4Address | IPv6Address,
    api_url: str,
    wtf_mode: bool = False,
) -> None:
    """
    Render IP details fetched from the external API.

    :param ip: IP address to look up
    :param api_url: The API URL template with {ip} placeholder
    :param wtf_mode: Whether to use WTF mode messaging.
    :return: None
    """
    # Fetch IP details
    logger.info(f"Fetching details for {ip}")
    data: dict = {}
    try:
        data = fetch_ip_details(ip, api_url, wtf_mode)
        logger.info(f"Fetched details for {ip}: {data}")
    except MyIPError as e:
        render_and_log_error(e)

    # Validate API response
    if data.get("status") != "success":
        msg: str = data.get("message")
        render_and_log_error(InvalidAPIResponseError(details=msg, wtf_mode=wtf_mode))

    st.subheader(f"{'Fucking d' if wtf_mode else 'D'}etails for {ip}")

    data = process_ip_details(data)
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
