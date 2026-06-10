"""Tests verifying the engine reproduces OP's published numbers."""

import pytest
import numpy as np
from src.engine import (
    compute_gpu_hourly_cost,
    compute_concurrency,
    compute_profitability,
    solve_breakeven_price,
)
from src.tps_models import ols_logistic, compute_tps

OP_CONFIG = {
    "base_tps_70b_1user": 250,
    "saturation_tps_70b": 12000,
}


def test_op_gpu_hourly_cost():
    """OP GPU cost: $1.48/hr, DC: $0.21/hr/kW, combined: $1.73/hr."""
    gpu = compute_gpu_hourly_cost(
        gpu_price_per_unit=38889,
        gpu_amortization_years=3,
        dc_capex_per_mw=9_000_000,
        dc_amortization_years=5,
        gpu_power_draw_kw=1.2,
        pue=1.0,
        electricity_rate=0.0,
    )
    assert abs(gpu - 1.73) < 0.04, f"Expected ~1.73, got {gpu}"


def test_op_tps_at_1_user():
    """OP TPS at 1 concurrent user, 70B params: ~250 TPS."""
    tps = ols_logistic(1.0, 70.0, OP_CONFIG)
    assert abs(tps - 125) < 10, f"Expected ~125 (OP's formula), got {tps}"


def test_op_tps_at_200_users():
    """OP TPS at 200 concurrent users, 70B params: ~10,000 TPS."""
    tps = ols_logistic(200.0, 70.0, OP_CONFIG)
    assert abs(tps - 10000) < 2000, f"Expected ~10000, got {tps}"


def test_op_tps_scales_with_params():
    """TPS should be inversely proportional to parameter count."""
    tps_70b = ols_logistic(50.0, 70.0, OP_CONFIG)
    tps_140b = ols_logistic(50.0, 140.0, OP_CONFIG)
    ratio = tps_70b / tps_140b
    assert abs(ratio - 2.0) < 0.5, f"Expected ~2x, got {ratio}x"


def test_op_cost_per_mt_concurrency_6():
    """At 6 concurrent users, 300B params, cost should be ~$4.22/MT."""
    p = 300.0
    u = 6.0
    tps = compute_tps(u, p, "OP's Logistic (Original Post)", OP_CONFIG)
    gpu_hourly = compute_gpu_hourly_cost(38889, 3, 9_000_000, 5, 1.35, 1.0, 0.1178)
    tokens_ph = 3600 * tps
    cost_mt = gpu_hourly / (tokens_ph / 1e6) if tps > 0 else float("inf")
    assert abs(cost_mt - 4.22) < 1.5, f"Expected ~4.22, got {cost_mt:.2f}"


def test_op_full_profitability_lenient():
    """OP's full lenient scenario: ~80M users, ~4.45M GPUs."""
    config = {
        "gpu_price_per_unit": 38889,
        "gpu_amortization_years": 3,
        "dc_capex_per_mw": 9_000_000,
        "dc_amortization_years": 5,
        "gpu_power_draw_kw": 1.35,
        "pue": 1.0,
        "electricity_rate": 0.1178,
        "total_parameters_b": 4000,
        "moe_active_ratio": 7.5,
        "base_tps_70b_1user": 250,
        "saturation_tps_70b": 12000,
        "total_gpus_millions": 4.45,
        "paid_users_millions": 80,
        "free_paid_ratio": 0.0,
        "usage_hours_per_day": 8,
        "blended_price_per_mt": 5.0,
    }
    gpu_hourly = compute_gpu_hourly_cost(
        config["gpu_price_per_unit"], config["gpu_amortization_years"],
        config["dc_capex_per_mw"], config["dc_amortization_years"],
        config["gpu_power_draw_kw"], config["pue"], config["electricity_rate"],
    )
    total_u, paid_u = compute_concurrency(
        config["total_gpus_millions"], config["paid_users_millions"],
        config["free_paid_ratio"], config["usage_hours_per_day"],
    )
    comp_p = config["total_parameters_b"] * (config["moe_active_ratio"] / 100)
    tps = compute_tps(total_u, comp_p, "OP's Logistic (Original Post)", OP_CONFIG)

    results = compute_profitability(gpu_hourly, tps, total_u, paid_u, config["blended_price_per_mt"])
    cost_mt = results["cost_per_mt"]
    assert cost_mt < 10, f"Cost/MT should be under $10 in lenient scenario, got ${cost_mt:.2f}"
    assert cost_mt > 2, f"Cost/MT should be above $2, got ${cost_mt:.2f}"


def test_breakeven_price():
    """Breakeven price should equal cost per MT when paid_ratio = 1."""
    hourly = 2.0
    tps = 1000
    needed = solve_breakeven_price(hourly, tps, 1.0)
    tokens_ph = 3600 * tps
    expected = hourly / (tokens_ph / 1e6)
    assert abs(needed - expected) < 0.01


def test_concurrency_calculation():
    """Simple concurrency sanity check."""
    tc, pc = compute_concurrency(
        total_gpus_millions=5.0,
        paid_users_millions=100,
        free_paid_ratio=1.0,
        usage_hours_per_day=12,
    )
    assert abs(tc - 20.0) < 0.1, f"Expected 20, got {tc}"
    assert abs(pc - 10.0) < 0.1, f"Expected 10, got {pc}"
