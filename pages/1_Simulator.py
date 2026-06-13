"""Main simulator page — interactive dashboard with all parameters and live plots."""

import streamlit as st
import numpy as np

from src.controls import render_parameter_controls, render_preset_buttons, render_timeline_control, validate_active_preset
from src.defaults import ALL_PARAMS
from src.engine import (
    apply_market_curves,
    compute_gpu_hourly_cost,
    compute_concurrency,
    compute_gpus_from_deployment,
    compute_paid_users_from_adoption,
    compute_profitability,
    compute_industry_annual,
)
from src.tps_models import compute_tps, TPS_MODELS
from src.plots import cost_breakdown_pie, cost_vs_concurrency_curve, revenue_vs_cost_bar, margin_over_time
from src.utils import (
    fmt_currency,
    fmt_compact,
    color_for_profit,
    compute_cost_breakdown,
)

st.title("AI Profitability Simulator")
st.caption(
    "Based on the model by [u/ksjdragon](https://www.reddit.com/r/BetterOffline/comments/1tzwnhi/ai_profitability_is_mathematically_impossible/). "
    "Adjust any parameter to explore how it affects profitability."
)
timeline_value = render_timeline_control("")

with st.sidebar:
    render_preset_buttons("")

    st.divider()
    st.header("Parameters")
    tps_model = st.selectbox("TPS Model", list(TPS_MODELS.keys()), index=0)
    vals = render_parameter_controls("", include_timeline=False, validate_preset=False)

vals["adoption_years_since_launch"] = timeline_value
validate_active_preset("", vals)

config = apply_market_curves({p.key: vals[p.key] for p in ALL_PARAMS})
t = config.get("adoption_years_since_launch")
tam = config.get("adoption_tam_millions", 1000.0)
k_adopt = config.get("adoption_growth_rate", 2.5)
mp_adopt = config.get("adoption_midpoint_years", 4.48)
saturation = config.get("gpu_saturation_millions", 25.0)
k_gpu = config.get("gpu_deployment_growth_rate", 2.0)
mp_gpu = config.get("gpu_deployment_midpoint", 4.265)

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

total_concurrent, paid_concurrent = compute_concurrency(
    config["total_gpus_millions"],
    config["paid_users_millions"],
    config["free_paid_ratio"],
    config["usage_hours_per_day"],
)

computed_params = config["total_parameters_b"] * (config["moe_active_ratio"] / 100.0)
effective_concurrent = total_concurrent * (config.get("concurrency_efficiency_pct", 100.0) / 100.0)

tps = compute_tps(total_concurrent, computed_params, tps_model, config)

results = compute_profitability(
    gpu_hourly_cost,
    tps,
    total_concurrent,
    paid_concurrent,
    config["blended_price_per_mt"],
)

industry = compute_industry_annual(
    results["profit_per_gpu_hour"],
    config["total_gpus_millions"],
    config["corporate_tax_rate"],
)

gpu_breakdown, dc_breakdown, elec_breakdown = compute_cost_breakdown(gpu_hourly_cost, config)

if t is not None:
    st.subheader("Margin Over Time (Both S-Curves Advancing)")

    t_range = np.linspace(1.0, 7.0, 50)
    margins = []
    concs = []
    users = []
    gpus = []
    for ti in t_range:
        p = compute_paid_users_from_adoption(ti, tam, k_adopt, mp_adopt)
        gp = compute_gpus_from_deployment(ti, saturation, k_gpu, mp_gpu)
        tc2, pc2 = compute_concurrency(gp, p, config["free_paid_ratio"], config["usage_hours_per_day"])
        tt2 = compute_tps(tc2, computed_params, tps_model, config)
        r2 = compute_profitability(gpu_hourly_cost, tt2, tc2, pc2, config["blended_price_per_mt"])
        margins.append(r2["profit_margin_pct"])
        concs.append(tc2)
        users.append(p)
        gpus.append(gp)

    margin_fig = margin_over_time(t_range, np.array(margins), np.array(concs),
                                   np.array(users), np.array(gpus), t,
                                   results["profit_margin_pct"])
    st.plotly_chart(margin_fig, width="stretch")

st.divider()

col1, col2, col3, col4, col5, col6 = st.columns(6)

profit_color = color_for_profit(results["profit_per_gpu_hour"])

with col1:
    st.metric("Cost per MT", f"${results['cost_per_mt']:,.2f}")
with col2:
    st.metric("Revenue/GPU-hr", f"${results['revenue_per_gpu_hour']:,.2f}")
with col3:
    st.metric(
        "Profit/GPU-hr",
        f"${results['profit_per_gpu_hour']:,.2f}",
        delta=f"{results['profit_margin_pct']:+.1f}%" if results['profit_margin_pct'] > float('-inf') else None,
    )
with col4:
    st.metric("Gross Margin/MT", f"${results['gross_margin_per_mt']:,.2f}")
with col5:
    annual_val = fmt_currency(industry["annual_pretax_profit"])
    st.metric("Annual Pre-Tax", annual_val)
with col6:
    st.metric("Concurrent Users/GPU", f"{total_concurrent:,.1f}")

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Cost Breakdown per GPU-Hour")
    pie_fig = cost_breakdown_pie(gpu_breakdown, dc_breakdown, elec_breakdown)
    st.plotly_chart(pie_fig, width="stretch")

    st.caption(
        f"GPU: ${gpu_breakdown:.2f}/hr ({gpu_breakdown/gpu_hourly_cost*100:.1f}%)  |  "
        f"DC: ${dc_breakdown:.2f}/hr ({dc_breakdown/gpu_hourly_cost*100:.1f}%)  |  "
        f"Electricity: ${elec_breakdown:.2f}/hr ({elec_breakdown/gpu_hourly_cost*100:.1f}%)"
    )

    st.metric("Total GPU-Hourly Cost", f"${gpu_hourly_cost:,.2f}")

with col_right:
    st.subheader("Cost vs Concurrency Curve")

    hourly_for_curve = gpu_hourly_cost
    curve_config = dict(config)
    curve_config["_gpu_hourly_cost"] = hourly_for_curve

    cost_curve = cost_vs_concurrency_curve(
        computed_params,
        compute_tps,
        curve_config,
        tps_model,
        total_concurrent,
        results["cost_per_mt"],
    )
    st.plotly_chart(cost_curve, width="stretch")

st.divider()

col_bar, col_detail = st.columns([1, 1])

with col_bar:
    st.subheader("Revenue vs Cost")
    bar_fig = revenue_vs_cost_bar(
        results["cost_per_mt"],
        config["blended_price_per_mt"],
        config["blended_price_per_mt"] * results["paid_ratio"],
        gpu_hourly_cost,
        results["revenue_per_gpu_hour"],
    )
    st.plotly_chart(bar_fig, width="stretch")

with col_detail:
    st.subheader("Detailed Metrics")
    detail_data = {
        "Active Parameters": f"{computed_params:,.0f}B",
        "TPS (total)": f"{tps:,.1f}",
        "Tokens/GPU-hr": f"{results['tokens_per_hour']:,.0f}",
        "Paid User Ratio": f"{results['paid_ratio']:.4f}",
        "Total Concurrent/GPU": f"{total_concurrent:,.1f}",
        "Effective Concurrent/GPU": f"{effective_concurrent:,.1f}",
        "Paid Concurrent/GPU": f"{paid_concurrent:,.3f}",
        "Total GPUs": f"{config['total_gpus_millions']:.2f}M",
        "Annual Pre-Tax Profit": fmt_currency(industry["annual_pretax_profit"]),
        "Annual After-Tax Profit": fmt_currency(industry["annual_aftertax_profit"]),
    }
    for label, val in detail_data.items():
        st.text(f"{label}:  {val}")

st.divider()
st.caption(
    "Model based on [u/ksjdragon's Reddit post](https://www.reddit.com/r/BetterOffline/comments/1tzwnhi/ai_profitability_is_mathematically_impossible/). "
    "14 points of leniency were applied in the original analysis. Adjust parameters to explore real-world scenarios."
)
