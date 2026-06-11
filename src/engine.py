"""Core profitability computation engine.

Pure functions — no side effects, no global state.
"""

import numpy as np

HOURS_PER_YEAR = 365.25 * 24
BUILDING_AMORT_YEARS = 20.0

ADOPTION_TAM = 1000.0  # million paid users at saturation (1B global knowledge workers)
ADOPTION_K = 2.5        # logistic growth rate (5x smartphone)
ADOPTION_MIDPOINT = 4.48  # years since ChatGPT launch, calibrated to 80M at t=3.5


def compute_paid_users_from_adoption(years_since_launch: float, tam: float = ADOPTION_TAM,
                                      k: float = ADOPTION_K, midpoint: float = ADOPTION_MIDPOINT) -> float:
    """Logistic S-curve for paid AI user adoption."""
    return tam / (1.0 + np.exp(-k * (years_since_launch - midpoint)))


GPU_SATURATION_M = 25.0  # million GPUs at full DC buildout
GPU_K = 2.0               # deployment growth rate (slightly slower than adoption, physical constraints)
GPU_MIDPOINT = 4.13       # calibrated to hit 5.5M at t=3.5 (Jensen Huang Oct 2025 disclosure)


def compute_gpus_from_deployment(years_since_launch: float, saturation: float = GPU_SATURATION_M,
                                   k: float = GPU_K, midpoint: float = GPU_MIDPOINT) -> float:
    """Logistic S-curve for GPU deployment (DC buildout)."""
    return saturation / (1.0 + np.exp(-k * (years_since_launch - midpoint)))


def compute_gpu_hourly_cost(
    gpu_price_per_unit: float,
    gpu_amortization_years: float,
    dc_capex_per_mw: float,
    dc_amortization_years: float,
    gpu_power_draw_kw: float,
    pue: float,
    electricity_rate: float,
    total_power_draw_kw: float | None = None,
    discount_rate_pct: float = 0.0,
    bonus_depreciation_pct: float = 0.0,
    corporate_tax_rate: float = 21.0,
    dc_building_share_pct: float | None = None,
) -> float:
    """Compute total cost per GPU per hour.

    gpu_power_draw_kw is used for DC CapEx amortization (IT load).
    total_power_draw_kw is used for electricity (GPU + CPU share).
    Defaults to gpu_power_draw_kw + 0.15 if not specified (Grace CPU overhead).

    discount_rate_pct: cost of capital for PV-based annualization. 0 = flat (OP).
    bonus_depreciation_pct: % of GPU cost deductible year 1 per OBBB. 0 = ignored (OP).
    corporate_tax_rate: used to compute tax shield from bonus depreciation.
    dc_building_share_pct: % of DC CapEx in building shell (20yr). Remainder = electrical (GPU amort).
                          None/100 = OP model (single amortization period for all DC).

    The effective GPU purchase price is reduced by the bonus depreciation tax shield:
      effective_price = gpu_price * (1 - bonus% * tax_rate)

    Then annualized using the annuity formula with the discount rate:
      A = P * r * (1+r)^n / ((1+r)^n - 1)
    If r = 0 (OP's assumption): A = P / n (straight-line).

    Returns:
        float: $/GPU-hour.
    """
    if total_power_draw_kw is None:
        total_power_draw_kw = gpu_power_draw_kw + 0.15

    bonus_rec = bonus_depreciation_pct / 100.0
    tax_rec = corporate_tax_rate / 100.0
    effective_price = gpu_price_per_unit * (1.0 - bonus_rec * tax_rec)

    r = discount_rate_pct / 100.0
    n = gpu_amortization_years

    if r == 0.0:
        annual_cost = effective_price / n
    else:
        factor = (1.0 + r) ** n
        annual_cost = effective_price * r * factor / (factor - 1.0)

    gpu_hourly = annual_cost / HOURS_PER_YEAR

    building_share = dc_building_share_pct / 100.0 if dc_building_share_pct is not None else 1.0
    electrical_share = 1.0 - building_share

    if building_share < 1.0 and building_share > 0.0:
        building_hourly = (dc_capex_per_mw / 1000.0) * building_share / (BUILDING_AMORT_YEARS * HOURS_PER_YEAR)
        electrical_hourly = (dc_capex_per_mw / 1000.0) * electrical_share / (gpu_amortization_years * HOURS_PER_YEAR)
        dc_cost_per_kw_hour = building_hourly + electrical_hourly
    else:
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
