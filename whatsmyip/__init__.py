"""
whatsmyip - A Streamlit app for IP address lookup.
"""

from whatsmyip.api import fetch_ip_details, process_ip_details
from whatsmyip.exceptions import (
    IPAPIConnectionError,
    InvalidAPIResponseError,
    InvalidIPError,
    LinkLocalIPError,
    LoopbackIPError,
    MyIPError,
    NonGlobalIPError,
    PrivateIPError,
)
from whatsmyip.ui import (
    render_and_log_error,
    render_ip_address_copy_button,
    render_ip_details,
    render_search_bar,
)

__all__ = [
    # Exceptions
    "MyIPError",
    "IPAPIConnectionError",
    "InvalidAPIResponseError",
    "InvalidIPError",
    "NonGlobalIPError",
    "LinkLocalIPError",
    "PrivateIPError",
    "LoopbackIPError",
    # API functions
    "fetch_ip_details",
    "process_ip_details",
    # UI functions
    "render_and_log_error",
    "render_ip_address_copy_button",
    "render_search_bar",
    "render_ip_details",
]

