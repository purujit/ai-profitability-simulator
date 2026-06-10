"""Utility helpers for the AI profitability simulator."""


def fmt_currency(val: float) -> str:
    """Format a number as currency with appropriate scale."""
    if abs(val) >= 1e12:
        return f"${val/1e12:,.2f}T"
    elif abs(val) >= 1e9:
        return f"${val/1e9:,.2f}B"
    elif abs(val) >= 1e6:
        return f"${val/1e6:,.2f}M"
    elif abs(val) >= 1e3:
        return f"${val/1e3:,.2f}K"
    else:
        return f"${val:,.2f}"


def fmt_compact(val: float, decimals: int = 2) -> str:
    """Format a number compactly."""
    if abs(val) >= 1e12:
        return f"{val/1e12:,.{decimals}f}T"
    elif abs(val) >= 1e9:
        return f"{val/1e9:,.{decimals}f}B"
    elif abs(val) >= 1e6:
        return f"{val/1e6:,.{decimals}f}M"
    elif abs(val) >= 1e3:
        return f"{val/1e3:,.{decimals}f}K"
    return f"{val:,.{decimals}f}"


def color_for_profit(profit: float) -> str:
    """Return green for profit, red for loss."""
    return "#2ecc71" if profit >= 0 else "#e74c3c"


def compute_cost_breakdown(gpu_hourly_cost: float, config: dict) -> tuple[float, float, float]:
    """Decompose total hourly cost into GPU, DC, and electricity components."""
    p = config
    gpu_price = p["gpu_price_per_unit"]
    amort_y = p["gpu_amortization_years"]
    dc_capex = p["dc_capex_per_mw"]
    dc_amort = p["dc_amortization_years"]
    power = p["gpu_power_draw_kw"]
    pue = p["pue"]
    elec_rate = p["electricity_rate"]

    hours_year = 365.25 * 24
    gpu_hourly = gpu_price / (amort_y * hours_year)
    dc_hourly = (dc_capex / 1000.0) / (dc_amort * hours_year) * power
    elec_hourly = power * elec_rate * pue

    return gpu_hourly, dc_hourly, elec_hourly
