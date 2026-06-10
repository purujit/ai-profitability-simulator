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
        default=41700,
        min_val=10000,
        max_val=100000,
        step=1000,
        unit="$",
        rationale=(
            "GB200 NVL72 rack contains 72 B200 GPUs. Midpoint of reported pricing: "
            "SemiAnalysis (Aug 2025): $2.6M–$3.1M/rack; ModulEdge (Jun 2026): $3.0M–$3.4M; "
            "Introl (Apr 2026): ~$3M; IO Fund (Feb 2025): ~$3M. Consensus ~$3M ÷ 72 = $41,667. "
            "Jensen Huang confirmed 3.6M Blackwell GPUs sold (Mar 2025)."
        ),
        citations=[
            ("SemiAnalysis — H100 vs GB200 NVL72 Training Benchmarks (Aug 2025)",
             "https://newsletter.semianalysis.com/p/h100-vs-gb200-nvl72-training-benchmarks"),
            ("ModulEdge — NVIDIA Blackwell Explained (Jun 2026)",
             "https://www.moduledge.com/blog/nvidia-blackwell"),
            ("Introl — B200 vs GB200 Deployment Guide (Apr 2026)",
             "https://introl.com/blog/nvidia-b200-vs-gb200-deployment-guide"),
        ],
    ),
    Parameter(
        key="gpu_amortization_years",
        label="GPU Amortization",
        default=6,
        min_val=1,
        max_val=10,
        step=1,
        unit="years",
        rationale=(
            "CoreWeave's average take-or-pay contract term is 4 years (Glenn Lockwood, Apr 2026). "
            "Meta's expanded CoreWeave deal runs through 2032 (6-7yr). Hyperscalers use 5-6 years "
            "per SEC filings; Amazon recently cut from 6 to 5. Default uses 6 years, matching "
            "the high end of market contract terms and hyperscaler depreciation schedules."
        ),
        citations=[
            ("CoreWeave GPU Cluster Contracts — Glenn K. Lockwood (Apr 2026)",
             "https://www.glennklockwood.com/garden/entities/coreweave"),
            ("Amazon SEC Filing — Server Useful Life Reduction (Feb 2025)",
             "https://www.cnbc.com/2025/11/14/ai-gpu-depreciation-coreweave-nvidia-michael-burry.html"),
            ("CoreWeave & Meta — $21B AI Infrastructure Agreement Through 2032",
             "https://www.coreweave.com/news/coreweave-and-meta-announce-21-billion-expanded-ai-infrastructure-agreement"),
        ],
    ),
    Parameter(
        key="discount_rate_pct",
        label="Discount Rate (Cost of Capital)",
        default=7.0,
        min_val=0.0,
        max_val=20.0,
        step=0.5,
        unit="%",
        rationale=(
            "Opportunity cost of capital — the return an investor could earn on alternative "
            "investments of similar risk. 0% = OP's assumption (flat amortization, no PV). "
            "Typical WACC for data center operators is 6-10%. Default 7% reflects a neutral "
            "estimate. Used to convert upfront GPU purchase into an annualized cost via annuity formula."
        ),
        citations=[
            ("Damodaran — Cost of Capital by Industry Sector (2026)",
             "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.htm"),
        ],
    ),
    Parameter(
        key="bonus_depreciation_pct",
        label="Bonus Depreciation (Year 1 Write-Off)",
        default=100.0,
        min_val=0.0,
        max_val=100.0,
        step=5.0,
        unit="%",
        rationale=(
            "The OBBB Act (One Big Beautiful Bill, signed mid-2025) permanently restored "
            "100% first-year bonus depreciation for qualifying equipment including AI GPUs "
            "placed in service after Jan 19, 2025. Each $1 of GPU spend generates an immediate "
            "tax shield at the corporate tax rate. 0% = OP's assumption (ignores this entirely)."
        ),
        citations=[
            ("KBKG — 100% Bonus Depreciation Now Permanent Under OBBB Tax Bill (Jul 2025)",
             "https://www.kbkg.com/feature/obbb-tax-bill-makes-100-bonus-depreciation-permanent-what-you-need-to-know"),
            ("SemiAnalysis — Meta Superintelligence: OBBB Boosts Hyperscaler CapEx (Jul 2025)",
             "https://newsletter.semianalysis.com/p/meta-superintelligence-leadership-compute-talent-and-data"),
        ],
    ),
    Parameter(
        key="gpu_power_draw_kw",
        label="GPU Power Draw",
        default=0.6,
        min_val=0.3,
        max_val=3.0,
        step=0.05,
        unit="kW",
        rationale=(
            "GB200 NVL72 superchip (2 B200 GPUs + 1 Grace CPU) draws 1,200W combined "
            "(Introl Apr 2026). Per-GPU: ~600W. OP used 1.2kW, which is the full superchip "
            "figure misapplied as per-GPU power — a 2× overestimate. Standalone HGX B200 is "
            "1,000W but this model uses NVL72 rack-scale deployment numbers. "
            "Simulation adds +0.15kW CPU share to this slider value for electricity."
        ),
        citations=[
            ("NVIDIA GB200 NVL72 Product Page",
             "https://www.nvidia.com/en-us/data-center/gb200-nvl72/"),
            ("Introl — B200 vs GB200 Deployment Guide (Apr 2026)",
             "https://introl.com/blog/nvidia-b200-vs-gb200-deployment-guide"),
        ],
    ),
    Parameter(
        key="pue",
        label="Power Usage Effectiveness (PUE)",
        default=1.1,
        min_val=1.0,
        max_val=2.5,
        step=0.05,
        unit="ratio",
        rationale=(
            "Google's fleet-wide trailing twelve-month PUE is 1.09 (Q1 2026), published quarterly "
            "for every data center they operate. Individual campuses range from 1.04 to 1.15. "
            "Google is the only hyperscaler that publicly reports per-campus PUE data. "
            "OP used 1.0 (zero cooling costs), which is impossible for any real facility. "
            "We use 1.1 as a rounded operator-reported figure."
        ),
        citations=[
            ("Google Data Centers — Power Usage Effectiveness (Q1 2026)",
             "https://www.google.com/about/datacenters/efficiency/"),
        ],
    ),
    Parameter(
        key="dc_capex_per_mw",
        label="Data Center CapEx per MW",
        default=12_000_000,
        min_val=3_000_000,
        max_val=30_000_000,
        step=500_000,
        unit="$/MW",
        rationale=(
            "Core Scientific (operator, May 2026): DC build costs rose from ~$8M/MW to "
            "$11.5M–$12M/MW. Includes shell, core, electrical, plumbing, and cooling "
            "infrastructure. Excludes land acquisition and AI hardware (GPUs, networking, "
            "racks priced separately). JLL 2025 global average shell & core: $10.7M/MW. "
            "OP used $9M/MW (lowest of outdated $9M–$15M range)."
        ),
        citations=[
            ("Core Scientific — AI Data Center Build Costs (May 2026)",
             "https://www.theglobeandmail.com/investing/markets/stocks/CORZ/pressreleases/2213089/core-scientific-targets-ai-data-center-deals-as-build-costs-climb/"),
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
            "Electrical/cooling infrastructure (70% of DC CapEx, per slider below) amortizes "
            "over the GPU amortization period (6 years). Building shell (30%) amortizes over "
            "20 years (GAAP standard). The DC amortization slider is retained for the OP model "
            "compatibility but overridden in 'My Assumptions' by this split approach."
        ),
        citations=[
            ("FASB ASC 360 — Property, Plant, and Equipment",
             "https://fasb.org/page/PageContent?pageId=/standards/accounting-standards-update-360.html"),
        ],
    ),
    Parameter(
        key="dc_building_share_pct",
        label="Building Share of DC CapEx",
        default=30.0,
        min_val=10.0,
        max_val=80.0,
        step=5.0,
        unit="%",
        rationale=(
            "Share of DC CapEx allocated to building shell (amortized over 20 years per GAAP). "
            "Remainder is electrical/cooling/mechanical, amortized over GPU amortization period. "
            "AI data centers with liquid cooling and high-density power have a lower building share. "
            "30% is typical for liquid-cooled NVL72-class facilities."
        ),
        citations=[],
    ),
    Parameter(
        key="electricity_rate",
        label="Electricity Rate",
        default=0.0826,
        min_val=0.02,
        max_val=0.35,
        step=0.001,
        unit="$/kWh",
        rationale=(
            "Blended industrial rate of top 2 US data center states by capacity (EIA Electric "
            "Power Monthly, March 2026): Virginia $0.1025, Texas $0.0626. Simple average = "
            "$0.0826/kWh. Virginia hosts ~5,000 MW operating; Texas 6,500 MW under construction "
            "(Belfer Center, Apr 2026). California excluded — #3 by facility count, not AI GPU capacity."
        ),
        citations=[
            ("EIA — Electric Power Monthly, Table 5.6.A (March 2026)",
             "https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_5_06_a"),
            ("Belfer Center — Data Centers and Electric Growth: Virginia & Texas (Apr 2026)",
             "https://www.belfercenter.org/research-analysis/data-centers-texas-virginia-comparison"),
        ],
    ),
]

MODEL_PARAMS: list[Parameter] = [
    Parameter(
        key="total_parameters_b",
        label="Total Parameters",
        default=1600,
        min_val=10,
        max_val=20000,
        step=10,
        unit="B",
        rationale=(
            "DeepSeek V4 Pro: 1.6T total parameters, 49B active (3.1% MoE) — model card "
            "(Future AGI, May 2026). Claude Fable 5 is estimated at ~10T (AI Magicx, Mar 2026) "
            "but DeepSeek V4 represents the widely deployed inference economics. "
            "OP used 4T for pre-Fable generation models."
        ),
        citations=[
            ("Future AGI — Best LLMs in May 2026: DeepSeek V4 Pro Specs",
             "https://futureagi.substack.com/p/best-llms-in-may-2026-what-actually"),
        ],
    ),
    Parameter(
        key="moe_active_ratio",
        label="MoE Active Parameter Ratio",
        default=3.1,
        min_val=1.0,
        max_val=100.0,
        step=0.5,
        unit="%",
        rationale=(
            "DeepSeek V4 Pro uses 3.1% active ratio (49B active from 1.6T total) per model "
            "card (Future AGI, May 2026). OP assumed 7.5% based on earlier Mixtral/DeepSeek-V2 "
            "architectures. Lower MoE ratio = more experts, cheaper inference per active parameter. "
            "100% = dense model (no MoE)."
        ),
        citations=[
            ("Future AGI — Best LLMs in May 2026: DeepSeek V4 Pro Specs",
             "https://futureagi.substack.com/p/best-llms-in-may-2026-what-actually"),
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
        key="tps_calibration_multiplier",
        label="TPS Calibration",
        default=1.44,
        min_val=0.5,
        max_val=3.0,
        step=0.01,
        unit="×",
        rationale=(
            "NVIDIA Dev Blog (Apr 2026): GB200 NVL72 achieves 150+ tok/sec/user on DeepSeek "
            "V4 Pro (1.6T params, 49B active). At 20 concurrent that's 3,000 TPS total — "
            "1.44× the OP logistic prediction. The OP's curve was fitted to dense Llama models; "
            "DeepSeek V4's hybrid attention (CSA/DSA/HCA) reduces per-token FLOPs 73% vs V3.2, "
            "making it substantially faster per active parameter. 1.0 = OP's original calibration."
        ),
        citations=[
            ("NVIDIA Dev Blog — Build with DeepSeek V4 on Blackwell (Apr 2026)",
             "https://developer.nvidia.com/blog/build-with-deepseek-v4-using-nvidia-blackwell-and-gpu-accelerated-endpoints/"),
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
        default=10.0,
        min_val=0.1,
        max_val=50.0,
        step=0.05,
        unit="M",
        rationale=(
            "NVIDIA shipped ~5.2M Blackwell GPUs in 2025 + 1.8M in 2026 = ~7M cumulative. "
            "Top 4 CSPs ordered 3.6M units; AWS 1M; Meta ordered millions (CNBC Feb 2026). "
            "Adding Hopper (still deployed) and early Rubin, total AI GPU base is ~10M+. "
            "FY2026 revenue $215.9B, Q4 alone $68.1B (NVIDIA Feb 2026). $119B supply commitments "
            "from OpenAI, Anthropic, Meta (24/7 Wall St, Jun 2026). OP used 4.45M based on 2024 data."
        ),
        citations=[
            ("NVIDIA Q4 FY2026 Earnings — Record $68.1B Quarter (Feb 2026)",
             "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/default.aspx"),
            ("CNBC — Meta Expands NVIDIA Deal for Millions of AI Chips (Feb 2026)",
             "https://www.cnbc.com/2026/02/17/meta-nvidia-deal-ai-data-center-chips.html"),
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
            "OpenAI: 50M paid subscribers (Panto AI, May 2026), 900M+ WAU, $2B/month revenue "
            "(Reuters, 2026). Anthropic: paid subs doubled in H1 2026 (TechCrunch, Mar 2026), "
            "estimated ~25-30M. Combined ~75-80M. OP's 80M estimate was accurate."
        ),
        citations=[
            ("Panto AI — OpenAI Statistics 2026 (May 2026)",
             "https://www.getpanto.ai/blog/openai-statistics"),
            ("TechCrunch — Anthropic Claude Paid Subscriptions Doubled (Mar 2026)",
             "https://techcrunch.com/2026/03/28/anthropics-claude-popularity-with-paying-consumers-is-skyrocketing/"),
        ],
    ),
    Parameter(
        key="free_paid_ratio",
        label="Free:Paid User Ratio",
        default=18.0,
        min_val=0.0,
        max_val=50.0,
        step=0.1,
        unit=":1",
        rationale=(
            "ChatGPT: 900M WAU (Panto AI, May 2026) with only 50M paying (~5%) = ~17-18:1 "
            "free-to-paid ratio (LinkedIn analysis, Feb 2026). OpenAI generates ~$2B/month "
            "revenue from subscriptions but free users consume compute without direct revenue. "
            "OP used 0:1 (lenient baseline with no free users)."
        ),
        citations=[
            ("Panto AI — OpenAI Statistics: 900M+ WAU, 50M+ Subscribers (May 2026)",
             "https://www.getpanto.ai/blog/openai-statistics"),
            ("NPR — What You Get When You Pay for AI (Jun 2026)",
             "https://www.npr.org/2026/06/04/nx-s1-5791661/chatgpt-gemini-claude-subscription-revenue-openai"),
        ],
    ),
    Parameter(
        key="adoption_years_since_launch",
        label="Adoption Timeline",
        default=3.5,
        min_val=0.5,
        max_val=7.0,
        step=0.25,
        unit="years since ChatGPT",
        rationale=(
            "Logistic S-curve for paid AI user adoption, calibrated to smartphone adoption "
            "compressed 5×. TAM = 500M paid users (global knowledge workers). k = 2.5, "
            "midpoint at 4.2 years. Current (t=3.5, mid-2026): ~80M paid. Projects to 200M by "
            "end of 2026, 450M by 2027, plateau at 500M by 2028. GPU deployment scales "
            "proportionally with paid user count (not all 10M GPUs deployed upfront)."
        ),
        citations=[],
    ),
    Parameter(
        key="usage_hours_per_day",
        label="Usage Hours per Day",
        default=8.0,
        min_val=0.5,
        max_val=24.0,
        step=0.25,
        unit="hrs/day",
        rationale=(
            "OP's assumption: users generate tokens continuously for 8 hrs/day, 365 days/year "
            "including weekends. Represents maximal plausible per-user usage and is a useful "
            "gaming assumption — if the model can't be profitable at 8 hrs/day, it can't work at all. "
            "OP used this uniformly across all users with no free tier."
        ),
        citations=[],
    ),
    Parameter(
        key="blended_price_per_mt",
        label="Blended Price per MT",
        default=0.20,
        min_val=0.05,
        max_val=50.0,
        step=0.05,
        unit="$/MT",
        rationale=(
            "DeepSeek V4 Pro (Max): $0.435/MT input, $0.87/MT output, $0.004/MT cached input "
            "(-99%). Artificial Analysis blended price: $0.20/MT incorporating typical caching "
            "(artificialanalysis.ai, Jun 2026). Other models: Claude Fable 5 = $8.20/MT, "
            "GPT-5.5 = $4.30/MT, MiMo-V2.5 = $0.20/MT. OP used $5.00 for GPT-5.5 era pricing."
        ),
        citations=[
            ("Artificial Analysis — DeepSeek V4 Pro (Max) Pricing",
             "https://artificialanalysis.ai/models/deepseek-v4-pro"),
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
