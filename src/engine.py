"""Core profitability computation engine.

Pure functions — no side effects, no global state.
"""

import numpy as np

HOURS_PER_YEAR = 365.25 * 24


def compute_gpu_hourly_cost(
    gpu_price_per_unit: float,
    gpu_amortization_years: float,
    dc_capex_per_mw: float,
    dc_amortization_years: float,
    gpu_power_draw_kw: float,
    pue: float,
    electricity_rate: float,
    total_power_draw_kw: float | None = None,
) -> float:
    """Compute total cost per GPU per hour.

    gpu_power_draw_kw is used for DC CapEx amortization (IT load).
    total_power_draw_kw is used for electricity (GPU + CPU share).
    Defaults to gpu_power_draw_kw + 0.15 if not specified (Grace CPU overhead).

    Returns:
        float: $/GPU-hour combining GPU amortization, DC CapEx amortization,
               and electricity (including PUE overhead).
    """
    if total_power_draw_kw is None:
        total_power_draw_kw = gpu_power_draw_kw + 0.15

    gpu_hourly = gpu_price_per_unit / (gpu_amortization_years * HOURS_PER_YEAR)

    dc_cost_per_kw_hour = (dc_capex_per_mw / 1000.0) / (dc_amortization_years * HOURS_PER_YEAR)
    dc_hourly = dc_cost_per_kw_hour * gpu_power_draw_kw

    elec_hourly = total_power_draw_kw * electricity_rate * pue

    return gpu_hourly + dc_hourly + elec_hourly


def compute_concurrency(
    total_gpus_millions: float,
    paid_users_millions: float,
    free_paid_ratio: float,
    usage_hours_per_day: float,
) -> tuple[float, float]:
    """Compute concurrent users per GPU.

    Returns:
        (total_concurrent_per_gpu, paid_concurrent_per_gpu)
    """
    total_gpus = total_gpus_millions * 1e6
    paid_users = paid_users_millions * 1e6
    total_users = paid_users * (1.0 + free_paid_ratio)

    utilization = usage_hours_per_day / 24.0

    total_concurrent_per_gpu = total_users * utilization / total_gpus
    paid_concurrent_per_gpu = paid_users * utilization / total_gpus

    return total_concurrent_per_gpu, paid_concurrent_per_gpu


def compute_profitability(
    gpu_hourly_cost: float,
    tps: float,
    total_concurrent_per_gpu: float,
    paid_concurrent_per_gpu: float,
    blended_price_per_mt: float,
) -> dict:
    """Compute profitability metrics per GPU-hour.

    Returns dict with:
      - tokens_per_hour
      - cost_per_mt
      - revenue_per_gpu_hour
      - profit_per_gpu_hour
      - profit_margin_pct
      - gross_margin_per_mt
    """
    tokens_per_hour = 3600.0 * tps

    cost_per_mt = gpu_hourly_cost / (tokens_per_hour / 1e6) if tps > 0 else float("inf")

    paid_ratio = paid_concurrent_per_gpu / total_concurrent_per_gpu if total_concurrent_per_gpu > 0 else 0

    revenue_per_gpu_hour = paid_ratio * tokens_per_hour * blended_price_per_mt / 1e6

    profit_per_gpu_hour = revenue_per_gpu_hour - gpu_hourly_cost
    profit_margin_pct = (profit_per_gpu_hour / revenue_per_gpu_hour * 100) if revenue_per_gpu_hour > 0 else float("-inf")

    gross_margin_per_mt = blended_price_per_mt - cost_per_mt

    return {
        "tokens_per_hour": tokens_per_hour,
        "cost_per_mt": cost_per_mt,
        "revenue_per_gpu_hour": revenue_per_gpu_hour,
        "profit_per_gpu_hour": profit_per_gpu_hour,
        "profit_margin_pct": profit_margin_pct,
        "gross_margin_per_mt": gross_margin_per_mt,
        "paid_ratio": paid_ratio,
    }


def compute_industry_annual(
    profit_per_gpu_hour: float,
    total_gpus_millions: float,
    corporate_tax_rate: float,
) -> dict:
    """Scale per-GPU-hour results to industry-wide annual figures."""
    total_gpus = total_gpus_millions * 1e6
    annual_profit = profit_per_gpu_hour * total_gpus * HOURS_PER_YEAR
    after_tax = annual_profit * (1 - corporate_tax_rate / 100)
    return {
        "annual_pretax_profit": annual_profit,
        "annual_aftertax_profit": after_tax,
        "total_gpus": total_gpus,
    }


def solve_breakeven_price(
    gpu_hourly_cost: float,
    tps: float,
    paid_ratio: float,
) -> float:
    """Compute the price per MT required to break even."""
    if tps <= 0 or paid_ratio <= 0:
        return float("inf")
    tokens_per_hour = 3600.0 * tps
    needed_revenue_per_hour = gpu_hourly_cost
    return needed_revenue_per_hour / (paid_ratio * tokens_per_hour / 1e6)


def solve_breakeven_users(
    gpu_hourly_cost: float,
    tps: float,
    blended_price_per_mt: float,
    total_concurrent_per_gpu: float,
) -> float:
    """Compute the number of paid concurrent users per GPU required to break even."""
    if blended_price_per_mt <= 0 or tps <= 0:
        return float("inf")
    tokens_per_hour = 3600.0 * tps
    needed_paid_ratio = gpu_hourly_cost / (tokens_per_hour * blended_price_per_mt / 1e6)
    return needed_paid_ratio * total_concurrent_per_gpu
