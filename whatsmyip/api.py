"""
API-related functions for fetching and processing IP data.
"""

from ipaddress import IPv4Address, IPv6Address

import requests
import streamlit as st

from whatsmyip.exceptions import IPAPIConnectionError, InvalidAPIResponseError


@st.cache_data(show_spinner="Fetching IP details...")
def fetch_ip_details(
    ip: str | IPv4Address | IPv6Address,
    api_url: str,
    wtf_mode: bool = False,
) -> dict:
    """
    Fetch IP details from the external API.

    :param ip: IP address to look up
    :param api_url: The API URL template with {ip} placeholder
    :param wtf_mode: Whether to use WTF mode messaging in errors
    :return: IP details as a dictionary
    :raises IPAPIConnectionError: If there is a connection error to the API.
    :raises InvalidAPIResponseError: If the API response is invalid.
    """
    response = requests.get(api_url.format(ip=ip))
    if response.status_code != requests.codes.ok:
        raise IPAPIConnectionError(
            details=f"Status code: {response.status_code}",
            wtf_mode=wtf_mode,
        )

    try:
        data = response.json()
    except ValueError as e:
        raise InvalidAPIResponseError(details=str(e), wtf_mode=wtf_mode)

    return data


def process_ip_details(data: dict) -> dict:
    """
    Removes the 'status' and 'ip' fields from the API response dictionary,
    as these are not needed for display or further processing.

    :param data: Raw IP details from the API response
    :return: Processed IP details with 'status' and 'ip' fields removed
    """
    return {k: v for k, v in data.items() if k not in ["status", "ip"]}
