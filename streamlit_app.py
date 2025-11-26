from ipaddress import IPv4Address, IPv6Address, ip_address
import logging
import sys
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


def render_error(
    type: Literal["invalid_ip", "api_failure"] | None = None, message: str | None = None
):
    """
    Render an error message using st.error and provide appropriate actions.

    :param type: Error type, will provide default messages and actions
    :type type: Literal["invalid_ip", "api_failure"] | None
    :param message: Error message, will override default messages for types
    :type message: str | None
    :param title: Optional title for the page displaying the error message
    :type title: str | None
    """
    if not message:
        if type == "invalid_ip":
            message = "Invalid IP address. Please enter a valid IPv4 or IPv6 address."
        elif type == "api_failure":
            message = "Failed to retrieve IP details. Please try again."
        else:
            message = "An error occurred. Please try again."

    st.error(message, icon=":material/error:")

    # if type == "api_failure":
    #     if st.button("Refresh", icon=":material/refresh:"):
    #         st.rerun()
    # elif type == "invalid_ip":
    #     render_search_bar()

    st.stop()


def render_ip_address_copy_button(ip: str):
    if st.button("Copy", icon=":material/content_copy:", width="stretch"):
        pyperclip.copy(ip)
        st.toast("IP address copied to clipboard!", icon=":material/check_circle:")


def render_search_bar(default_ip: str = "", label: str = ""):
    search_cols = st.columns([5, 1], vertical_alignment="bottom")
    with search_cols[0]:
        ip_input = st.text_input(
            label or "Look up an IP address",
            # label_visibility="collapsed" if not label else "visible",
            value=default_ip,
        )
    # with search_cols[1]:
    # render_ip_address_copy_button(ip_input)
    with search_cols[1]:
        _search = st.button(
            "Search", icon=":material/search:", type="primary", width="stretch"
        )

    if _search:
        try:
            ip_address(ip_input)
            st.query_params.from_dict({"ip": ip_input})
            st.rerun()
        except ValueError:
            render_error(type="invalid_ip")


def render_search_page(user_ip: str = ""):
    render_search_bar(user_ip)


def render_ip_details(ip: str):
    # render_search_bar(ip)

    # Validate IP address
    try:
        ip_address(ip)
    except ValueError:
        render_error(type="invalid_ip")

    # TODO: Handle localhost and private IP

    # Fetch IP details from external API
    response = requests.get(IP_API_URL.format(ip=ip))
    if response.status_code != requests.codes.ok:
        render_error(type="api_failure")

    # Parse response JSON
    try:
        ip_data = response.json()
    except requests.exceptions.JSONDecodeError:
        render_error(type="api_failure")

    if ip_data.get("status") != "success":
        # API returned an error
        render_error(type="api_failure")


def main():
    # if not st.session_state.get("last_query_params"):
    #     st.session_state["last_query_params"] = st.query_params.to_dict()
    # if st.session_state["last_query_params"] != st.query_params.to_dict():
    #     st.session_state["last_query_params"] = st.query_params.to_dict()
    #     st.rerun()

    user_ip: str = st.context.ip_address or "127.0.0.1"

    logger.info("whatsmyip accessed by %s", user_ip)

    st.logo(LOGO, size="large", link=HOMEPAGE)
    st.title("What's my IP?", anchor=False)

    ip_cols = st.columns([1, 5], vertical_alignment="center")
    with ip_cols[0]:
        render_ip_address_copy_button(user_ip)
    with ip_cols[1]:
        st.markdown(f"Your IP address is `{user_ip}`")

    # render_search_bar(user_ip)

    if query_ip := st.query_params.get("ip"):
        # IP defined, show IP details
        render_search_bar(query_ip)
        render_ip_details(query_ip)
    else:
        # No IP defined, show search bar
        render_search_bar(user_ip)


if __name__ == "__main__":
    main()
