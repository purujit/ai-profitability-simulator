"""Shared Streamlit controls for parameter presets and input panels."""

import math

import streamlit as st

from src.defaults import ALL_PARAMS, PARAM_GROUPS, PARAMS_BY_KEY, PRESETS, get_defaults
from src.utils import display_scale_for_unit, scaled_slider_value_format, slider_value_format


def preset_values(preset_name: str) -> dict[str, float]:
    """Return a complete parameter dict for a preset."""
    vals = get_defaults()
    vals.update(PRESETS[preset_name])
    return vals


def _state_key(prefix: str, key: str) -> str:
    return f"{prefix}_{key}" if prefix else key


def _display_key(prefix: str, key: str) -> str:
    return f"{prefix}_{key}_display" if prefix else f"{key}_display"


def _active_preset_key(prefix: str) -> str:
    return f"{prefix}_active_preset" if prefix else "_active_preset"


def _set_param_state(prefix: str, key: str, value: float) -> None:
    param = PARAMS_BY_KEY[key]
    st.session_state[_state_key(prefix, key)] = value
    scale, _ = display_scale_for_unit(param.unit)
    if scale != 1.0:
        st.session_state[_display_key(prefix, key)] = value / scale


def _clear_param_state(prefix: str, key: str) -> None:
    st.session_state.pop(_state_key(prefix, key), None)
    st.session_state.pop(_display_key(prefix, key), None)


def render_preset_buttons(prefix: str, *, show_header: bool = True) -> None:
    """Render two preset buttons and apply selected values to this page's widgets."""
    if show_header:
        st.header("Presets")

    active_key = _active_preset_key(prefix)
    active_preset = st.session_state.get(active_key)
    selected_preset = None

    pcol1, pcol2 = st.columns(2)
    if pcol1.button(
        "OP's Assumptions",
        width="stretch",
        type="primary" if active_preset == "OP's Lenient Assumptions" else "secondary",
        help="u/ksjdragon's original lenient baseline",
        key=f"{prefix}_op_preset_button",
    ):
        selected_preset = "OP's Lenient Assumptions"
    if pcol2.button(
        "My Assumptions",
        width="stretch",
        type="primary" if active_preset == "My Assumptions" else "secondary",
        help="Updated baseline with current hardware, cost, pricing, and adoption assumptions",
        key=f"{prefix}_my_preset_button",
    ):
        selected_preset = "My Assumptions"

    if active_preset:
        st.caption(f"Selected: {active_preset}")

    if selected_preset:
        for key, value in preset_values(selected_preset).items():
            _set_param_state(prefix, key, value)
        st.session_state[active_key] = selected_preset
        st.rerun()


def render_parameter_controls(prefix: str, *, expanded_group: str = "GPU Hardware & Power") -> dict[str, float]:
    """Render parameter controls using the same formatting across pages."""
    vals = {}
    for group_name, group_params in PARAM_GROUPS.items():
        with st.expander(group_name, expanded=(group_name == expanded_group)):
            for p in group_params:
                if isinstance(p.step, int) and isinstance(p.min_val, int) and isinstance(p.max_val, int):
                    min_v, max_v, step_v = int(p.min_val), int(p.max_val), int(p.step)
                    current_val = int(st.session_state.get(_state_key(prefix, p.key), p.default))
                else:
                    min_v, max_v, step_v = float(p.min_val), float(p.max_val), float(p.step)
                    current_val = float(st.session_state.get(_state_key(prefix, p.key), p.default))

                scale, display_unit = display_scale_for_unit(p.unit)
                if scale != 1.0:
                    display_val = current_val / scale
                    display_selected = st.slider(
                        p.label,
                        min_value=min_v / scale,
                        max_value=max_v / scale,
                        value=display_val,
                        step=step_v / scale,
                        key=_display_key(prefix, p.key),
                        help=p.rationale,
                        format=scaled_slider_value_format(display_unit),
                    )
                    vals[p.key] = display_selected * scale
                    st.session_state[_state_key(prefix, p.key)] = vals[p.key]
                else:
                    vals[p.key] = st.slider(
                        p.label,
                        min_value=min_v,
                        max_value=max_v,
                        value=current_val,
                        step=step_v,
                        key=_state_key(prefix, p.key),
                        help=p.rationale,
                        format=slider_value_format(p.unit),
                    )

    active_preset = st.session_state.get(_active_preset_key(prefix))
    if active_preset:
        expected = preset_values(active_preset)
        if any(not math.isclose(float(vals[k]), float(expected[k]), rel_tol=0.0, abs_tol=1e-9) for k in vals):
            st.session_state[_active_preset_key(prefix)] = None
            st.rerun()

    return vals


def clear_parameter_controls(prefix: str) -> None:
    """Clear all page-local parameter widget state."""
    for p in ALL_PARAMS:
        _clear_param_state(prefix, p.key)
    st.session_state.pop(_active_preset_key(prefix), None)
