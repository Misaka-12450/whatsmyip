from ipaddress import IPv4Address, IPv6Address, ip_address
import logging
import sys
import textwrap
from typing import Literal
import requests
import pyperclip

import streamlit as st

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


class IPFetchError(Exception):
    pass


def render_error(
    type: Literal["invalid_ip", "api_failure"] | None = None,
    message: str | None = None,
    replace_message: bool = False,
):
    """
    Render an error message using st.error and provide appropriate actions.

    :param type: Error type, will provide default messages and actions
    :type type: Literal["invalid_ip", "api_failure"] | None
    :param message: Error message, will append default messages
    :type message: str | None
    """
    if not (replace_message and message):
        message_suffix = (
            textwrap.dedent(
                f"""
                
                ```
                {message}
                ```
                """
            )
            if message
            else ""
        )
        if type == "invalid_ip":
            message = "Invalid IP address. Please enter a valid IPv4 or IPv6 address."
        elif type == "api_failure":
            message = "Failed to retrieve IP details. Please try again."
        else:
            message = "An error occurred. Please try again."
        message += message_suffix

    st.error(message, icon=":material/error:")
    st.stop()


def render_ip_address_copy_button(ip: str):
    if st.button("Copy", icon=":material/content_copy:", width="stretch"):
        pyperclip.copy(ip)
        st.toast("IP address copied to clipboard!", icon=":material/check_circle:")


@st.cache_data(show_spinner="Fetching IP details...")
def fetch_ip_details(ip: str) -> dict:
    """
    Docstring for fetch_ip_details

    :param ip: IP address to look up
    :type ip: str
    :return: IP details as a dictionary
    :rtype: dict
    """
    response = requests.get(IP_API_URL.format(ip=ip))
    if response.status_code != requests.codes.ok:
        logger.error(f"Failed to fetch IP details for {ip}: {response.status_code}")
        raise IPFetchError("api_failure")

    try:
        data = response.json()
    except ValueError:
        logger.error(f"Failed to parse JSON response for {ip}")
        raise IPFetchError("api_failure")

    return data


def render_search_bar(default_ip: str = "", label: str = ""):
    search_cols = st.columns([5, 1], vertical_alignment="bottom")
    with search_cols[0]:
        ip_input = st.text_input(
            label or "Look up an IP address",
            value=default_ip,
        )
    with search_cols[1]:
        search = st.button(
            "Search", icon=":material/search:", type="primary", width="stretch"
        )

    if search:
        try:
            ip_address(ip_input)
            st.query_params.from_dict({"ip": ip_input})
            st.rerun()
        except ValueError:
            render_error(type="invalid_ip")


def render_ip_details(ip: str):
    try:
        ip_address(ip)
    except ValueError:
        render_error(type="invalid_ip")

    try:
        logger.info(f"Fetching details for {ip}")
        data: dict = fetch_ip_details(ip)
    except IPFetchError as e:
        render_error(type=str(e))

    logger.info(f"Fetched details for {ip}: {data}")

    if data.get("status") != "success":
        messsage: str = data.get("message")
        logger.info(f"API returned unsuccessful status for {ip}: {messsage}")
        render_error(type="api_failure", message=messsage)
    st.write(data)


def main():
    user_ip: str = st.context.ip_address or "127.0.0.1"

    logger.info("whatsmyip accessed by %s", user_ip)

    st.logo(LOGO, size="large", link=HOMEPAGE)
    st.title("What's my IP?", anchor=False)

    ip_cols = st.columns([1, 5], vertical_alignment="center")
    with ip_cols[0]:
        render_ip_address_copy_button(user_ip)
    with ip_cols[1]:
        st.markdown(f"Your IP address is `{user_ip}`")

    if query_ip := st.query_params.get("ip"):
        # IP defined, show IP details
        render_search_bar(query_ip)
        render_ip_details(query_ip)
    else:
        # No IP defined
        render_search_bar(user_ip)


if __name__ == "__main__":
    main()
