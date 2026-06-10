"""Parameter defaults, rationales, and citations for the AI Profitability Simulator.

Each parameter is a dataclass with name, default value, range, step, unit,
a ~50-word rationale, and a list of (label, url) citation tuples.

Model derived from u/ksjdragon's Reddit post:
"AI profitability is mathematically impossible under all technological advancements"
https://www.reddit.com/r/BetterOffline/comments/1tzwnhi/
"""

from dataclasses import dataclass, field


@dataclass
class Parameter:
    key: str
    label: str
    default: float
    min_val: float
    max_val: float
    step: float
    unit: str
    rationale: str
    citations: list[tuple[str, str]] = field(default_factory=list)


GPU_PARAMS: list[Parameter] = [
    Parameter(
        key="gpu_price_per_unit",
        label="GPU Unit Price",
        default=38889,
        min_val=10000,
        max_val=100000,
        step=1000,
        unit="$",
        rationale=(
            "An NVL72 rack containing 72 B200 GPUs costs approximately $2.8M to $3.4M. "
            "The default uses the lowest reported figure: $2.8M / 72 = $38,889 per GPU. "
            "OP treats this as generously low."
        ),
        citations=[
            ("NVIDIA GTC 2024 Keynote — Blackwell Platform",
             "https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing"),
        ],
    ),
    Parameter(
        key="gpu_amortization_years",
        label="GPU Amortization",
        default=3,
        min_val=1,
        max_val=10,
        step=1,
        unit="years",
        rationale=(
            "NVIDIA's datacenter GPU release cadence is roughly 2 years (Hopper 2022, "
            "Blackwell 2024, Vera Rubin 2026). OP adds 1 year of leniency, assuming "
            "Blackwell GPUs remain economically useful into the Rubin era."
        ),
        citations=[
            ("NVIDIA GTC 2026 — Vera Rubin Announcement",
             "https://nvidianews.nvidia.com/news/nvidia-vera-rubin"),
            ("AnandTech — NVIDIA Blackwell Architecture",
             "https://www.anandtech.com/show/21310/nvidia-blackwell-architecture-and-b200b100-accelerators-announced"),
        ],
    ),
    Parameter(
        key="gpu_power_draw_kw",
        label="GPU Power Draw",
        default=1.35,
        min_val=0.5,
        max_val=3.0,
        step=0.05,
        unit="kW",
        rationale=(
            "Each B200 draws ~1,200W. The GB200 'superchip' pairs 2 B200s with 1 Grace CPU "
            "(300W total), so OP attributes 150W of CPU power per GPU. Actual NVL72 rack is "
            "rated at 132kW = 1.83kW per GPU normalized, making this value generous."
        ),
        citations=[
            ("NVIDIA GB200 NVL72 Product Page",
             "https://www.nvidia.com/en-us/data-center/gb200-nvl72/"),
        ],
    ),
    Parameter(
        key="pue",
        label="Power Usage Effectiveness (PUE)",
        default=1.4,
        min_val=1.0,
        max_val=2.5,
        step=0.05,
        unit="ratio",
        rationale=(
            "PUE measures total facility power ÷ IT equipment power. The Uptime Institute "
            "2024 survey reports a global average of 1.58. Hyperscalers claim 1.1-1.2. "
            "OP omitted cooling costs entirely, so PUE=1.4 is a realistic middle ground."
        ),
        citations=[
            ("Uptime Institute — 2024 Global Data Center Survey",
             "https://uptimeinstitute.com/resources/research-and-reports/annual-global-data-center-survey"),
        ],
    ),
    Parameter(
        key="dc_capex_per_mw",
        label="Data Center CapEx per MW",
        default=9_000_000,
        min_val=3_000_000,
        max_val=25_000_000,
        step=500_000,
        unit="$/MW",
        rationale=(
            "Hyperscale data center construction costs range from $9M to $15M per MW of IT "
            "load (McKinsey 2024). Includes land, electrical infrastructure, networking, "
            "cooling hardware, and installation. OP uses the lowest figure."
        ),
        citations=[
            ("McKinsey — Investing in the rising data center economy",
             "https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/investing-in-the-rising-data-center-economy"),
            ("CBRE — Global Data Center Trends 2024",
             "https://www.cbre.com/insights/reports/global-data-center-trends-2024"),
        ],
    ),
    Parameter(
        key="dc_amortization_years",
        label="DC Amortization",
        default=5,
        min_val=3,
        max_val=20,
        step=1,
        unit="years",
        rationale=(
            "OP assumes creditors allow 5 years before any interest payment — an arrangement "
            "no commercial lender offers. GAAP guidance: 15-20 years for buildings, 5-7 for "
            "electrical equipment. Default is OP's generous value."
        ),
        citations=[
            ("FASB ASC 360 — Property, Plant, and Equipment",
             "https://fasb.org/page/PageContent?pageId=/standards/accounting-standards-update-360.html"),
        ],
    ),
    Parameter(
        key="electricity_rate",
        label="Electricity Rate",
        default=0.0685,
        min_val=0.02,
        max_val=0.35,
        step=0.001,
        unit="$/kWh",
        rationale=(
            "US Energy Information Administration (EIA) Electric Power Monthly, March 2026: "
            "Washington State industrial rate = 6.85 cents/kWh, the lowest in the contiguous US. "
            "US industrial average: 8.58 cents/kWh. OP used an 11.78 cent projection."
        ),
        citations=[
            ("EIA — Electric Power Monthly, Table 5.6.A (March 2026)",
             "https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_5_06_a"),
        ],
    ),
]

MODEL_PARAMS: list[Parameter] = [
    Parameter(
        key="total_parameters_b",
        label="Total Parameters",
        default=4000,
        min_val=10,
        max_val=20000,
        step=10,
        unit="B",
        rationale=(
            "Frontier models like GPT-5.5 and Claude Opus 4.7 are estimated at ~4 trillion "
            "total parameters using Mixture-of-Experts architecture. Range spans from Llama 3.1 "
            "70B up to speculated future 10T+ models."
        ),
        citations=[
            ("Semianalysis — AI Model Architecture Database",
             "https://www.semianalysis.com/"),
        ],
    ),
    Parameter(
        key="moe_active_ratio",
        label="MoE Active Parameter Ratio",
        default=7.5,
        min_val=1.0,
        max_val=100.0,
        step=0.5,
        unit="%",
        rationale=(
            "Mixture-of-Experts models only activate a subset of parameters per token. "
            "DeepSeek-V2 uses ~5-10% of total parameters. Mixtral 8x7B activates ~12.5%. "
            "OP assumes 7.5% for frontier models. 100% = dense model (no MoE)."
        ),
        citations=[
            ("DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model (arXiv:2405.04434)",
             "https://arxiv.org/abs/2405.04434"),
            ("Mixtral of Experts (arXiv:2401.04088)",
             "https://arxiv.org/abs/2401.04088"),
        ],
    ),
    Parameter(
        key="base_tps_70b_1user",
        label="Base TPS (70B, 1 user)",
        default=250,
        min_val=10,
        max_val=2000,
        step=10,
        unit="tokens/sec",
        rationale=(
            "Derived from NVIDIA's Llama 4 Maverick benchmark: 8×B200 GPUs achieve 1,000 "
            "TPS/user on a 400B MoE model (~30B effective per user). Normalized to 1 GPU "
            "and 70B parameters: (30/70) × 250 = 107 TPS/GPU. OP rounds to 250 TPS."
        ),
        citations=[
            ("NVIDIA — Blackwell Inference Performance Benchmarks",
             "https://developer.nvidia.com/blog/nvidia-blackwell-inference-performance-leap/"),
        ],
    ),
    Parameter(
        key="saturation_tps_70b",
        label="Saturation TPS (70B, ∞ users)",
        default=12000,
        min_val=2000,
        max_val=50000,
        step=500,
        unit="tokens/sec",
        rationale=(
            "Extrapolated from NVIDIA's Llama 3.3 70B benchmark with 200 concurrent users "
            "achieving 10,000 TPS/GPU. OP adds 20% headroom for saturation asymptote at "
            "12,000 TPS/GPU as the theoretical limit with perfect batching."
        ),
        citations=[
            ("NVIDIA — Blackwell Inference Performance Benchmarks",
             "https://developer.nvidia.com/blog/nvidia-blackwell-inference-performance-leap/"),
        ],
    ),
    Parameter(
        key="output_input_token_ratio",
        label="Output:Input Token Ratio",
        default=4.0,
        min_val=0.5,
        max_val=20.0,
        step=0.5,
        unit=":1",
        rationale=(
            "Frontier models using chain-of-thought reasoning can generate 3-5× the number "
            "of input tokens as hidden reasoning tokens before producing output. Higher ratios "
            "favor the model provider since output tokens typically cost more."
        ),
        citations=[
            ("OpenAI — GPT-5.5 System Card",
             "https://openai.com/index/gpt-5-5-system-card/"),
            ("Anthropic — Claude Opus 4.7 Model Card",
             "https://www.anthropic.com/research/claude-opus-model-card"),
        ],
    ),
]

MARKET_PARAMS: list[Parameter] = [
    Parameter(
        key="total_gpus_millions",
        label="Total GPUs Deployed",
        default=4.45,
        min_val=0.1,
        max_val=50.0,
        step=0.05,
        unit="M",
        rationale=(
            "OP's derivation: NVIDIA sold ~$210B in datacenter GPUs in 2024. At ~$2.8M per "
            "NVL72 rack with 72 GPUs, that yields ~75K racks and ~5.4M GPUs. Discounted for "
            "pre-Blackwell generations, arriving at ~4.45M B200-equivalent GPUs."),
        citations=[
            ("NVIDIA FY2024 Annual Report (10-K)",
             "https://investor.nvidia.com/financial-info/sec-filings/"),
        ],
    ),
    Parameter(
        key="paid_users_millions",
        label="Paid Users",
        default=80,
        min_val=1,
        max_val=1000,
        step=1,
        unit="M",
        rationale=(
            "OpenAI claims ~50M paying subscribers across ChatGPT Plus/Pro/Team/Enterprise. "
            "Anthropic reported 18-30M. OP uses the combined optimistic maximum of 80M. "
            "Excludes free-tier users entirely from this count."
        ),
        citations=[
            ("OpenAI — ChatGPT Reaches 50 Million Paid Subscribers (Reuters, 2025)",
             "https://www.reuters.com/technology/artificial-intelligence/"),
            ("Anthropic — Annual Report 2024",
             "https://www.anthropic.com/news"),
        ],
    ),
    Parameter(
        key="free_paid_ratio",
        label="Free:Paid User Ratio",
        default=3.0,
        min_val=0.0,
        max_val=20.0,
        step=0.1,
        unit=":1",
        rationale=(
            "Most AI platforms report 3-5× more free-tier users than paying subscribers. "
            "ChatGPT has ~200M+ weekly active users versus ~50M paid, suggesting a ~3:1 ratio. "
            "Free users consume tokens that must be subsidized by paid users."
        ),
        citations=[
            ("The Information — ChatGPT User Metrics",
             "https://www.theinformation.com/"),
        ],
    ),
    Parameter(
        key="usage_hours_per_day",
        label="Usage Hours per Day",
        default=8.0,
        min_val=0.5,
        max_val=24.0,
        step=0.5,
        unit="hrs/day",
        rationale=(
            "The average white-collar workday is 8 hours. OP assumes users are effectively "
            "generating tokens continuously for their entire 8-hour workday, 365 days/year "
            "(including weekends), representing maximal plausible usage."
        ),
        citations=[
            ("Bureau of Labor Statistics — American Time Use Survey",
             "https://www.bls.gov/tus/"),
        ],
    ),
    Parameter(
        key="blended_price_per_mt",
        label="Blended Price per MT",
        default=5.00,
        min_val=0.10,
        max_val=50.0,
        step=0.10,
        unit="$/MT",
        rationale=(
            "GPT-5.5 charges $5/MT input, $15/MT output. Claude Opus 4.7 charges $5/MT "
            "input, $20/MT (output). With a 4:1 output:input ratio, the blended effective "
            "price is approximately $5/MT after weighting. DeepSeek charges as low as $0.27/MT."
        ),
        citations=[
            ("OpenAI API Pricing",
             "https://openai.com/api/pricing/"),
            ("Anthropic API Pricing",
             "https://www.anthropic.com/pricing"),
            ("Artificial Analysis — Model Price Comparison",
             "https://artificialanalysis.ai/"),
        ],
    ),
    Parameter(
        key="corporate_tax_rate",
        label="Corporate Tax Rate",
        default=21,
        min_val=0,
        max_val=50,
        step=1,
        unit="%",
        rationale=(
            "US federal statutory corporate income tax rate is 21% (Tax Cuts and Jobs Act "
            "of 2017). State taxes typically add 2-5% on top. OP applies this to determine "
            "after-tax profitability."
        ),
        citations=[
            ("IRS — Publication 542, Corporations",
             "https://www.irs.gov/publications/p542"),
        ],
    ),
]

ALL_PARAMS = GPU_PARAMS + MODEL_PARAMS + MARKET_PARAMS

PARAM_GROUPS = {
    "GPU Hardware & Power": GPU_PARAMS,
    "Model Architecture": MODEL_PARAMS,
    "Market & Usage": MARKET_PARAMS,
}

def get_defaults() -> dict[str, float]:
    return {p.key: p.default for p in ALL_PARAMS}
