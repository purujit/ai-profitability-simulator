"""Three TPS (tokens per second) model implementations.

Models predict total GPU throughput as a function of:
  - u: concurrent user requests on a GPU
  - p: active parameter count in billions (total × MoE active ratio)
"""

import numpy as np
from scipy.optimize import fsolve


def ols_logistic(u: float, p_billion: float, config: dict) -> float:
    """OP's logistic model from the Reddit post.

    Fits a logistic curve through two NVIDIA benchmark data points:
      - mid point: base_tps at 1 concurrent user (250 TPS at 70B params)
      - saturates at 1.2× the 200-user benchmark (12,000 TPS at 70B params)

    TPS_70(u) = L/(1 + exp(-k·u)) - offset
    Scaled linearly by 70/p for parameter count.

    Parameters are read from config:
      - base_tps_70b_1user: TPS at 1 user for 70B params
      - saturation_tps_70b: asymptotic TPS for 70B params
    """
    b = config["base_tps_70b_1user"]
    s = config["saturation_tps_70b"]

    L = s * 2 - b * 2
    k_base = 0.0119
    offset = L - s

    k = k_base * (70.0 / p_billion)

    tps_70b = L / (1.0 + np.exp(-k_base * u)) - offset
    return tps_70b * (70.0 / p_billion)


def roofline(u: float, p_billion: float, config: dict) -> float:
    """Roofline model based on memory bandwidth and compute limits.

    TPS = min(bw_cap, compute_cap) × concurrency_factor

    Memory-bound: TPS ≈ bandwidth / (2 × active_params × bytes_per_weight)
    Compute-bound: TPS ≈ FLOPs / (2 × active_params × flops_per_token)

    For B200: ~8 TB/s memory bandwidth, ~4.5 PFLOPS FP8.
    For FP8 inference: 2 × p_billion × 1 byte = 2p GB per token.

    Concurrency scaling: TPS increases as more users batch,
    approaching the hardware limit asymptotically.
    """
    bw_bytes_sec = config.get("memory_bandwidth_tb_s", 8.0) * 1e12
    compute_flops = config.get("compute_petaflops", 4.5) * 1e15

    bytes_per_token = 2 * p_billion * 1e9 * 1
    flops_per_token = 2 * p_billion * 1e9

    bw_bound_tps = bw_bytes_sec / bytes_per_token
    compute_bound_tps = compute_flops / flops_per_token

    hardware_limit = min(bw_bound_tps, compute_bound_tps)

    concurrency_factor = 1.0 - np.exp(-u / config.get("roofline_scale", 20.0))
    effective_tps = hardware_limit * concurrency_factor

    efficiency = config.get("roofline_efficiency", 0.30)
    return max(effective_tps * efficiency, config.get("min_tps", 10.0))


def simple_linear(u: float, p_billion: float, config: dict) -> float:
    """Simple linear TPS model with saturation.

    TPS = base_tps + (sat_tps - base_tps) * min(u / sat_users, 1.0)

    Scaled inversely by parameter count.
    """
    b = config["base_tps_70b_1user"]
    s = config["saturation_tps_70b"]
    sat_users = config.get("saturation_users", 200)

    tps_70b = b + (s - b) * min(u / sat_users, 1.0)
    return tps_70b * (70.0 / p_billion)


TPS_MODELS = {
    "OP's Logistic (Original Post)": ols_logistic,
    "Roofline (Memory/Compute Bound)": roofline,
    "Simple Linear (User-Defined)": simple_linear,
}


def compute_tps(u: float, p_billion: float, model_name: str, config: dict) -> float:
    """Compute TPS for a given concurrency and parameter count using the selected model."""
    u = max(u, 0.01)
    p_billion = max(p_billion, 0.1)
    func = TPS_MODELS.get(model_name, ols_logistic)
    return func(u, p_billion, config)
