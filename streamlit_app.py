import logging
import sys

import streamlit as st

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger.info("Starting whatsmyip")

LOGO: str = st.secrets.get("logo") or "https://avatars.githubusercontent.com/u/8287084"
HOMEPAGE: str = st.secrets.get("homepage") or False

st.logo(LOGO, size="large", link=HOMEPAGE)
st.title("What's my IP?", anchor=False)

if st.query_params("ip"):
    # IP defined, show IP details
    pass
else:
    # No IP defined, show search bar
    pass
