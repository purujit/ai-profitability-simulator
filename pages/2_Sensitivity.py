"""Sensitivity analysis — tornado chart, scenario comparison."""

import streamlit as st
import numpy as np
import copy

from src.defaults import ALL_PARAMS, PARAM_GROUPS, get_defaults
from src.engine import (
    compute_gpu_hourly_cost,
    compute_concurrency,
    compute_profitability,
)
from src.tps_models import compute_tps, TPS_MODELS
from src.plots import sensitivity_tornado, scenario_comparison_table
from src.utils import fmt_currency

st.title("Sensitivity Analysis")
st.caption("Understand which parameters have the greatest impact on profitability.")

with st.sidebar:
    st.header("Current Baseline")
    tps_model = st.selectbox("TPS Model", list(TPS_MODELS.keys()), index=0)
    delta_pct = st.slider("Perturbation", 5, 50, 20, 5, help="±% change applied to each parameter")
    base_vals = {}
    for group_name, group_params in PARAM_GROUPS.items():
        with st.expander(group_name, expanded=False):
            for p in group_params:
                base_vals[p.key] = st.number_input(
                    f"{p.label} ({p.unit})",
                    min_value=float(p.min_val),
                    max_value=float(p.max_val),
                    value=float(p.default),
                    step=float(p.step),
                    key=f"sens_{p.key}",
                )
    if st.button("Restore OP's Defaults", use_container_width=True):
        st.rerun()

config = dict(base_vals)
gpu_hourly_cost = compute_gpu_hourly_cost(
    config["gpu_price_per_unit"],
    config["gpu_amortization_years"],
    config["dc_capex_per_mw"],
    config["dc_amortization_years"],
    config["gpu_power_draw_kw"],
    config["pue"],
    config["electricity_rate"],
)

computed_params = config["total_parameters_b"] * (config["moe_active_ratio"] / 100.0)

total_concurrent, paid_concurrent = compute_concurrency(
    config["total_gpus_millions"],
    config["paid_users_millions"],
    config["free_paid_ratio"],
    config["usage_hours_per_day"],
)

tps = compute_tps(total_concurrent, computed_params, tps_model, config)

base_results = compute_profitability(
    gpu_hourly_cost, tps, total_concurrent, paid_concurrent, config["blended_price_per_mt"],
)
base_profit = base_results["profit_per_gpu_hour"]

st.subheader(f"Baseline Profit per GPU-Hour: ${base_profit:,.2f}")

perturbable_keys = [
    "gpu_price_per_unit",
    "gpu_amortization_years",
    "gpu_power_draw_kw",
    "pue",
    "dc_capex_per_mw",
    "dc_amortization_years",
    "electricity_rate",
    "total_parameters_b",
    "moe_active_ratio",
    "paid_users_millions",
    "free_paid_ratio",
    "usage_hours_per_day",
    "blended_price_per_mt",
    "total_gpus_millions",
]

perturbable_labels = {p.key: p.label for p in ALL_PARAMS if p.key in perturbable_keys}

def run_scenario(vals_overrides):
    c = dict(config)
    c.update(vals_overrides)
    ghc = compute_gpu_hourly_cost(
        c["gpu_price_per_unit"], c["gpu_amortization_years"],
        c["dc_capex_per_mw"], c["dc_amortization_years"],
        c["gpu_power_draw_kw"], c["pue"], c["electricity_rate"],
    )
    comp_p = c["total_parameters_b"] * (c["moe_active_ratio"] / 100.0)
    tc, pc = compute_concurrency(
        c["total_gpus_millions"], c["paid_users_millions"],
        c["free_paid_ratio"], c["usage_hours_per_day"],
    )
    t = compute_tps(tc, comp_p, tps_model, c)
    return compute_profitability(ghc, t, tc, pc, c["blended_price_per_mt"])

param_deltas = []
for key in perturbable_keys:
    c_lo = dict(config)
    factor = 1 - delta_pct / 100
    if key in ("blended_price_per_mt", "paid_users_millions", "usage_hours_per_day",
               "gpu_amortization_years", "dc_amortization_years", "moe_active_ratio"):
        factor = 1 + delta_pct / 100
    c_lo[key] *= (1 - delta_pct / 100)
    profit_lo = run_scenario(c_lo)["profit_per_gpu_hour"]

    c_hi = dict(config)
    c_hi[key] *= (1 + delta_pct / 100)
    profit_hi = run_scenario(c_hi)["profit_per_gpu_hour"]

    param_deltas.append((perturbable_labels[key], profit_lo, profit_hi))

st.subheader("Tornado Chart")
tornado_fig = sensitivity_tornado(base_profit, param_deltas)
st.plotly_chart(tornado_fig, use_container_width=True)

st.divider()

st.subheader("Scenario Comparison")

scenario_defs = {
    "OP's Lenient": {
        "label": "OP's original generous assumptions",
        "overrides": {},
    },
    "Realistic": {
        "label": "Realistic amortization, cooling, user counts",
        "overrides": {
            "gpu_amortization_years": 2,
            "dc_amortization_years": 3,
            "pue": 1.58,
            "paid_users_millions": 50,
            "free_paid_ratio": 5.0,
            "electricity_rate": 0.0858,
        },
    },
    "Optimistic": {
        "label": "Everything goes right for AI",
        "overrides": {
            "paid_users_millions": 200,
            "free_paid_ratio": 1.0,
            "blended_price_per_mt": 8.0,
            "gpu_amortization_years": 5,
            "gpu_price_per_unit": 25000,
        },
    },
    "Doomsday": {
        "label": "Worst case: low demand, high costs",
        "overrides": {
            "gpu_amortization_years": 1.5,
            "dc_amortization_years": 2,
            "pue": 2.0,
            "electricity_rate": 0.20,
            "paid_users_millions": 30,
            "free_paid_ratio": 10.0,
            "blended_price_per_mt": 2.0,
            "gpu_price_per_unit": 55000,
        },
    },
}

scenario_results = {}
for name, sd in scenario_defs.items():
    c = dict(config)
    c.update(sd["overrides"])
    scenario_results[name] = run_scenario(c)

table_fig = scenario_comparison_table(scenario_results)
st.plotly_chart(table_fig, use_container_width=True)

for name, sd in scenario_defs.items():
    st.caption(f"**{name}**: {sd['label']}  —  {'; '.join(f'{k}={v}' for k,v in sd['overrides'].items())}")
