"""Utility helpers for the AI profitability simulator."""

from src.engine import compute_gpu_hourly_cost_breakdown


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


def fmt_param_value(val: float, unit: str) -> str:
    """Format a parameter value for compact display in sidebar controls."""
    if unit == "$":
        return fmt_currency(val)
    if unit == "$/MW":
        return f"{fmt_currency(val)}/MW"
    if unit == "$/kWh":
        return f"${val:.3f}/kWh"
    if unit == "$/MT":
        return f"${val:.2f}/MT"
    if unit == "%":
        return f"{val:.1f}%"
    if unit == "kW":
        return f"{val:.2f} kW"
    if unit == "years":
        return f"{val:g} yr"
    if unit == "tokens/sec":
        return f"{val:,.0f} tok/s"
    if unit == "B":
        return f"{val:,.0f}B"
    if unit == "M GPUs":
        return f"{val:g}M GPUs"
    if unit == "M paid users":
        return f"{val:,.0f}M paid"
    if unit == "hrs/day":
        return f"{val:g} hr/day"
    if unit == "×":
        return f"{val:.2f}x"
    if unit == ":1":
        return f"{val:g}:1"
    if unit == "k":
        return f"{val:g}"
    if unit == "years since ChatGPT":
        return f"{val:g} yr since launch"
    if unit == "ratio":
        return f"{val:g}"
    return f"{val:g} {unit}".strip()


def slider_value_format(unit: str) -> str | None:
    """Return a Streamlit slider printf format string for a parameter unit."""
    formats = {
        "$": "$%d",
        "$/MW": "$%d/MW",
        "$/kWh": "$%.3f/kWh",
        "$/MT": "$%.2f/MT",
        "%": "%.1f%%",
        "kW": "%.2f kW",
        "years": "%g yr",
        "tokens/sec": "%d tok/s",
        "B": "%dB",
        "M GPUs": "%.1fM",
        "M paid users": "%.0fM",
        "hrs/day": "%.2f h/day",
        "×": "%.2fx",
        ":1": "%.2f:1",
        "k": "%.1f",
        "years since ChatGPT": "%.2f yr",
        "ratio": "%.2f",
    }
    return formats.get(unit)


def color_for_profit(profit: float) -> str:
    """Return green for profit, red for loss."""
    return "#2ecc71" if profit >= 0 else "#e74c3c"


def compute_cost_breakdown(gpu_hourly_cost: float, config: dict) -> tuple[float, float, float]:
    """Decompose total hourly cost into GPU, DC, and electricity components."""
    p = config
    return compute_gpu_hourly_cost_breakdown(
        p["gpu_price_per_unit"],
        p["gpu_amortization_years"],
        p["dc_capex_per_mw"],
        p["dc_amortization_years"],
        p["gpu_power_draw_kw"],
        p["pue"],
        p["electricity_rate"],
        discount_rate_pct=p.get("discount_rate_pct", 0.0),
        bonus_depreciation_pct=p.get("bonus_depreciation_pct", 0.0),
        corporate_tax_rate=p.get("corporate_tax_rate", 21.0),
        dc_building_share_pct=p.get("dc_building_share_pct"),
    )
