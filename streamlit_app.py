"""
What's My IP? - A Streamlit application for IP address lookup.
"""

from ipaddress import ip_address
import logging
import sys

import streamlit as st

from whatsmyip import (
    InvalidIPError,
    LinkLocalIPError,
    LoopbackIPError,
    NonGlobalIPError,
    PrivateIPError,
    render_and_log_error,
    render_ip_address_copy_button,
    render_ip_details,
    render_search_bar,
)

# Configuration
LOGO: str = st.secrets.get("logo") or "https://avatars.githubusercontent.com/u/8287084"
HOMEPAGE: str = st.secrets.get("homepage") or False
IP_API_URL: str = st.secrets.get("ip_api_url") or "http://ip-api.com/json/{ip}"

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def main():
    wtf_mode = st.session_state.get("wtf_mode", bool(st.query_params.get("wtf_mode")))

    user_ip = ip_address(st.context.ip_address or "127.0.0.1")
    if not user_ip.is_global:
        user_ip = None

    logger.info("whatsmyip accessed by %s", user_ip)

    st.logo(LOGO, size="large", link=HOMEPAGE)
    title_suffix = " the fuck is " if wtf_mode else "'s "
    st.title(
        f"What{title_suffix}my IP?",
        anchor=False,
    )

    wtf_mode = st.toggle(
        "WTF Mode", value=wtf_mode, key="wtf_mode", help="WTF is this?"
    )
    if wtf_mode:
        st.query_params["wtf_mode"] = True
    else:
        if st.query_params.get("wtf_mode"):
            st.query_params.pop("wtf_mode")

    ip_cols = st.columns([1, 5], vertical_alignment="center")
    with ip_cols[0]:
        render_ip_address_copy_button(user_ip, disabled=not user_ip)
    with ip_cols[1]:
        if user_ip:
            st.markdown(
                f"Your{' fucking ' if wtf_mode else ' '}IP address is `{user_ip}`"
            )
        else:
            st.markdown(
                "🖕 Nobody knows your fucking IP address"
                if wtf_mode
                else "⚠️ Unable to determine your global IP address"
            )

    if query_ip := st.query_params.get("ip", ""):
        # IP defined, show IP details

        # Strip whitespace from the IP address
        query_ip_stripped = query_ip.strip()
        if query_ip_stripped != query_ip:
            st.query_params["ip"] = query_ip_stripped
            st.rerun()

        render_search_bar(query_ip, wtf_mode=wtf_mode)
        try:
            query_ip = ip_address(query_ip)
        except ValueError as e:
            render_and_log_error(InvalidIPError(details=str(e), wtf_mode=wtf_mode))

        # Check if the IP is global
        if not query_ip.is_global:
            if query_ip.is_link_local:
                render_and_log_error(LinkLocalIPError(wtf_mode=wtf_mode))
            elif query_ip.is_loopback:
                render_and_log_error(LoopbackIPError(wtf_mode=wtf_mode))
            elif query_ip.is_private:
                render_and_log_error(PrivateIPError(wtf_mode=wtf_mode))
            else:
                render_and_log_error(NonGlobalIPError(wtf_mode=wtf_mode))

        # IP is global, render details
        render_ip_details(query_ip, IP_API_URL, wtf_mode=wtf_mode)
    else:
        # No IP defined
        render_search_bar(user_ip, wtf_mode=wtf_mode)


if __name__ == "__main__":
    main()
