"""Cached direct-data helpers for Streamlit pages."""

from __future__ import annotations

from typing import Callable

import streamlit as st
from pydantic import BaseModel

from src.api.services.page_data import (
    get_financial_markets_page,
    get_global_flows_page,
    get_home_page,
    get_housing_credit_page,
    get_macro_pulse_page,
    get_monetary_policy_page,
)
from src.database.database_manager import ensure_database_available


@st.cache_resource(show_spinner=False)
def get_dashboard_database_path() -> str:
    """Resolve/download the warehouse once per Streamlit process."""
    return str(ensure_database_available().resolve())


def _load(builder: Callable[..., BaseModel]) -> dict:
    response = builder(database_path=get_dashboard_database_path())
    return response.model_dump(mode="json")


@st.cache_data(ttl=300, show_spinner=False)
def load_home_data() -> dict:
    return _load(get_home_page)


@st.cache_data(ttl=300, show_spinner=False)
def load_macro_pulse_data() -> dict:
    return _load(get_macro_pulse_page)


@st.cache_data(ttl=300, show_spinner=False)
def load_monetary_policy_data() -> dict:
    return _load(get_monetary_policy_page)


@st.cache_data(ttl=300, show_spinner=False)
def load_housing_credit_data() -> dict:
    return _load(get_housing_credit_page)


@st.cache_data(ttl=300, show_spinner=False)
def load_financial_markets_data() -> dict:
    return _load(get_financial_markets_page)


@st.cache_data(ttl=300, show_spinner=False)
def load_global_flows_data() -> dict:
    return _load(get_global_flows_page)
