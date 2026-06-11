"""Breakeven solver — find conditions required for profitability."""

import streamlit as st
import numpy as np

from src.defaults import ALL_PARAMS, PARAM_GROUPS
from src.engine import (
    apply_market_curves,
    compute_gpu_hourly_cost,
    compute_concurrency,
    compute_profitability,
    solve_breakeven_price,
    solve_breakeven_users,
)
from src.tps_models import compute_tps, TPS_MODELS
from src.utils import fmt_currency, fmt_compact, slider_value_format

st.title("Breakeven Solver")
st.caption("Find the conditions required for AI inference to be profitable.")

with st.sidebar:
    st.header("Parameters")
    tps_model = st.selectbox("TPS Model", list(TPS_MODELS.keys()), index=0)
    vals = {}
    for group_name, group_params in PARAM_GROUPS.items():
        with st.expander(group_name, expanded=(group_name == "GPU Hardware & Power")):
            for p in group_params:
                if isinstance(p.step, int) and isinstance(p.min_val, int) and isinstance(p.max_val, int):
                    min_v, max_v, step_v, def_v = int(p.min_val), int(p.max_val), int(p.step), int(p.default)
                else:
                    min_v, max_v, step_v, def_v = float(p.min_val), float(p.max_val), float(p.step), float(p.default)
                vals[p.key] = st.slider(
                    p.label,
                    min_value=min_v,
                    max_value=max_v,
                    value=def_v,
                    step=step_v,
                    help=p.rationale,
                    key=f"be_{p.key}",
                    format=slider_value_format(p.unit),
                )
    if st.button("Restore Baseline Defaults", width="stretch"):
        for p in ALL_PARAMS:
            st.session_state.pop(f"be_{p.key}", None)
        st.rerun()

config = apply_market_curves({p.key: vals[p.key] for p in ALL_PARAMS})

gpu_hourly_cost = compute_gpu_hourly_cost(
    config["gpu_price_per_unit"],
    config["gpu_amortization_years"],
    config["dc_capex_per_mw"],
    config["dc_amortization_years"],
    config["gpu_power_draw_kw"],
    config["pue"],
    config["electricity_rate"],
    discount_rate_pct=config.get("discount_rate_pct", 0.0),
    bonus_depreciation_pct=config.get("bonus_depreciation_pct", 0.0),
    corporate_tax_rate=config.get("corporate_tax_rate", 21.0),
    dc_building_share_pct=config.get("dc_building_share_pct"),
)

computed_params = config["total_parameters_b"] * (config["moe_active_ratio"] / 100.0)

total_concurrent, paid_concurrent = compute_concurrency(
    config["total_gpus_millions"],
    config["paid_users_millions"],
    config["free_paid_ratio"],
    config["usage_hours_per_day"],
)

tps = compute_tps(total_concurrent, computed_params, tps_model, config)

results = compute_profitability(
    gpu_hourly_cost, tps, total_concurrent, paid_concurrent, config["blended_price_per_mt"],
)

paid_ratio = paid_concurrent / total_concurrent if total_concurrent > 0 else 0

st.subheader("Current State")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Cost per MT", f"${results['cost_per_mt']:,.2f}")
with c2:
    st.metric("Blended Price/MT", f"${config['blended_price_per_mt']:,.2f}")
with c3:
    st.metric("Profit/GPU-hr", f"${results['profit_per_gpu_hour']:,.2f}")

st.divider()

st.subheader("Solve for Breakeven")

solve_mode = st.radio(
    "What do you want to solve for?",
    [
        "Required price per MT at current concurrency",
        "Required paid users at current price",
        "Required GPU price reduction",
        "Required electricity rate",
    ],
)

if solve_mode == "Required price per MT at current concurrency":
    needed_price = solve_breakeven_price(gpu_hourly_cost, tps, paid_ratio)
    current_price = config["blended_price_per_mt"]
    multiplier = needed_price / current_price if current_price > 0 else float("inf")

    st.metric("Required Blended Price per MT", f"${needed_price:,.2f}")
    if multiplier < float("inf"):
        st.metric("Multiple of Current Price", f"{multiplier:.1f}×")
        if multiplier > 3:
            st.warning(f"Would require {multiplier:.1f}× current pricing — likely demand-destructive per the OP's argument.")
        elif multiplier <= 1:
            st.success("Already profitable at current pricing!")
        else:
            st.info(f"Modest {multiplier:.1f}× increase needed — potentially achievable.")

elif solve_mode == "Required paid users at current price":
    needed_paid_per_gpu = solve_breakeven_users(
        gpu_hourly_cost, tps, config["blended_price_per_mt"], total_concurrent,
    )
    needed_ratio = needed_paid_per_gpu / total_concurrent if total_concurrent > 0 else float("inf")
    needed_users_m = needed_ratio * config["total_gpus_millions"] * 1e6 / (config["usage_hours_per_day"] / 24) / 1e6

    st.metric("Required Paid Users", f"{needed_users_m:,.1f}M")
    st.metric("Current Paid Users", f"{config['paid_users_millions']:,.1f}M")
    st.metric("Required Paid User Ratio", f"{needed_ratio:.1%}")

    if needed_ratio > 1:
        st.warning("Requires >100% paid user ratio — impossible with any free users.")
    elif needed_users_m > config["paid_users_millions"] * 2:
        st.warning(f"Requires {needed_users_m/config['paid_users_millions']:.1f}× current paid user base.")
    elif needed_users_m <= config["paid_users_millions"]:
        st.success("Already profitable at current user count!")

elif solve_mode == "Required GPU price reduction":
    low, high = 1000, config["gpu_price_per_unit"]
    target = 0.001
    found = None
    for _ in range(50):
        mid = (low + high) / 2
        test_config = dict(config)
        test_config["gpu_price_per_unit"] = mid
        test_ghc = compute_gpu_hourly_cost(
            mid, config["gpu_amortization_years"], config["dc_capex_per_mw"],
            config["dc_amortization_years"], config["gpu_power_draw_kw"],
            config["pue"], config["electricity_rate"],
            discount_rate_pct=config.get("discount_rate_pct", 0.0),
            bonus_depreciation_pct=config.get("bonus_depreciation_pct", 0.0),
            corporate_tax_rate=config.get("corporate_tax_rate", 21.0),
            dc_building_share_pct=config.get("dc_building_share_pct"),
        )
        test_tps = compute_tps(total_concurrent, computed_params, tps_model, test_config)
        test_paid = paid_concurrent
        test_r = compute_profitability(test_ghc, test_tps, total_concurrent, test_paid, config["blended_price_per_mt"])
        if test_r["profit_per_gpu_hour"] >= 0:
            found = mid
            high = mid
        else:
            low = mid
    if found:
        discount = (1 - found / config["gpu_price_per_unit"]) * 100
        st.metric("Break-Even GPU Price", f"${found:,.0f}")
        st.metric("Required Discount", f"{discount:.0f}%")
        if discount > 90:
            st.error(f"GPU price would need to drop {discount:.0f}% — effectively impossible.")
        else:
            st.info(f"Needs {discount:.0f}% price reduction from current ~${config['gpu_price_per_unit']:,.0f}.")
    else:
        st.error("Cannot break even at any positive GPU price — try adjusting other parameters.")

elif solve_mode == "Required electricity rate":
    bracketed = False
    for rate in np.linspace(0, config["electricity_rate"], 1000):
        test_config = dict(config)
        test_config["electricity_rate"] = rate
        test_ghc = compute_gpu_hourly_cost(
            config["gpu_price_per_unit"], config["gpu_amortization_years"],
            config["dc_capex_per_mw"], config["dc_amortization_years"],
            config["gpu_power_draw_kw"], config["pue"], rate,
            discount_rate_pct=config.get("discount_rate_pct", 0.0),
            bonus_depreciation_pct=config.get("bonus_depreciation_pct", 0.0),
            corporate_tax_rate=config.get("corporate_tax_rate", 21.0),
            dc_building_share_pct=config.get("dc_building_share_pct"),
        )
        test_tps = compute_tps(total_concurrent, computed_params, tps_model, test_config)
        test_r = compute_profitability(test_ghc, test_tps, total_concurrent, paid_concurrent, config["blended_price_per_mt"])
        if test_r["profit_per_gpu_hour"] >= 0:
            st.metric("Break-Even Electricity Rate", f"${rate*100:.2f}/kWh")
            st.metric("Current Rate", f"${config['electricity_rate']*100:.2f}/kWh")
            reduction = (1 - rate / config["electricity_rate"]) * 100
            st.info(f"Electricity would need to be ${rate*100:.2f}/kWh ({reduction:.0f}% reduction).")
            bracketed = True
            break
    if not bracketed:
        st.error("Cannot break even at any positive electricity rate. Costs are dominated by GPU amortization and data center CapEx — not electricity.")
        st.caption("This confirms the OP's key insight: the bulk of inference cost comes from capital investment, not from electricity. Free electricity alone cannot make AI profitable.")
