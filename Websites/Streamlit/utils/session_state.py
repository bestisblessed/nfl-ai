"""
Shared helpers for consistent Streamlit session-state handling.

Each page should build widget keys with `widget_key("<page>", "<widget>")`
and call `ensure_option_state` (for select-type widgets) or
`ensure_value_state` before rendering the widget. This guarantees that
the stored value is valid and prevents accidental cross-page collisions.
"""

import streamlit as st
from typing import Iterable, List, Optional, Sequence, TypeVar

T = TypeVar("T")


def widget_key(page: str, widget: str) -> str:
    """
    Build a unique widget key using the page slug and widget name.
    """
    return f"{page}_{widget}"


def _resolved_default(options: Iterable[T], default: Optional[T]) -> Optional[T]:
    options_list = list(options)
    if not options_list:
        return None
    if default in options_list:
        return default
    return options_list[0]


def ensure_option_state(key: str, options: Iterable[T], default: Optional[T] = None) -> Optional[T]:
    """
    Ensure session_state[key] exists and is part of the provided options.
    Returns the validated value (or None when options are empty).
    """
    options_list = list(options)
    if not options_list:
        st.session_state.pop(key, None)
        return None

    desired_default = _resolved_default(options_list, default)
    if key not in st.session_state or st.session_state[key] not in options_list:
        st.session_state[key] = desired_default

    return st.session_state[key]


def ensure_value_state(key: str, default: T) -> T:
    """
    Ensure session_state[key] exists; assign default if missing.
    """
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def ensure_multi_option_state(
    key: str,
    options: Iterable[T],
    default: Optional[Sequence[T]] = None,
) -> List[T]:
    """
    Ensure a multiselect-style session_state list only contains allowed options.
    """
    options_list = list(options)
    if not options_list:
        st.session_state[key] = []
        return []

    current_values = st.session_state.get(key, [])
    if not isinstance(current_values, list):
        current_values = [current_values]

    filtered_values = [value for value in current_values if value in options_list]

    if not filtered_values and default:
        filtered_values = [value for value in default if value in options_list]

    st.session_state[key] = filtered_values
    return filtered_values


def _resolve_container(container):
    return container if container is not None else st


def persistent_selectbox(
    label: str,
    options: Iterable[T],
    *,
    page: str,
    widget: str,
    default: Optional[T] = None,
    container=None,
    format_func=None,
    **kwargs,
) -> Optional[T]:
    """
    Render a selectbox whose value persists even when navigating across pages.
    """
    select_container = _resolve_container(container)
    options_list = list(options)
    key = widget_key(page, widget)
    ensure_option_state(key, options_list, default)

    if not options_list:
        placeholder_options = ["No options available"]
        select_container.selectbox(label, placeholder_options, index=0, disabled=True, **kwargs)
        return None

    try:
        selected_index = options_list.index(st.session_state[key])
    except ValueError:
        selected_index = 0
        st.session_state[key] = options_list[0]

    selectbox_kwargs = dict(kwargs)
    if format_func is not None:
        selectbox_kwargs["format_func"] = format_func

    selected_value = select_container.selectbox(
        label,
        options_list,
        index=selected_index,
        **selectbox_kwargs,
    )
    st.session_state[key] = selected_value
    return selected_value


def persistent_multiselect(
    label: str,
    options: Iterable[T],
    *,
    page: str,
    widget: str,
    default: Optional[Sequence[T]] = None,
    container=None,
    **kwargs,
) -> List[T]:
    """
    Render a multiselect with manually managed persistent state.
    """
    select_container = _resolve_container(container)
    options_list = list(options)
    key = widget_key(page, widget)
    ensure_multi_option_state(key, options_list, default=default or [])

    selected_values = select_container.multiselect(
        label,
        options_list,
        default=st.session_state[key],
        **kwargs,
    )
    st.session_state[key] = selected_values
    return selected_values


def persistent_slider(
    label: str,
    *,
    page: str,
    widget: str,
    default: T,
    container=None,
    **kwargs,
) -> T:
    """
    Render a slider (including range sliders) with persistent value.
    """
    select_container = _resolve_container(container)
    key = widget_key(page, widget)
    ensure_value_state(key, default)

    slider_value = select_container.slider(
        label,
        value=st.session_state[key],
        **kwargs,
    )
    st.session_state[key] = slider_value
    return slider_value


