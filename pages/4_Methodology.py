"""Methodology page — equations, references, and attributions."""

import streamlit as st
from src.defaults import ALL_PARAMS

st.title("Methodology & References")
st.caption("How the model works, where the numbers come from, and what assumptions are made.")

st.header("Attribution")
st.markdown(
    """
This simulation is based on the model described by **u/ksjdragon** in their Reddit post:

> [**AI profitability is mathematically impossible under all technological advancements**](https://www.reddit.com/r/BetterOffline/comments/1tzwnhi/ai_profitability_is_mathematically_impossible/)

The original analysis applies 14 points of deliberate leniency toward AI companies
and still concludes that inference cannot be profitable. This simulator lets you
adjust those leniency assumptions and explore the parameter space yourself.
"""
)

st.header("Core Equations")

st.subheader("1. GPU-Hourly Cost")
st.latex(r"""
\text{Cost}_\text{GPU/hr} =
\frac{\text{Annualize}(P_\text{GPU} \cdot (1 - D_\text{bonus} \cdot T), r, Y_\text{GPU})}{8766}
+ \left[
\frac{C_\text{DC}/1000 \cdot s_\text{building}}{20 \cdot 8766}
+ \frac{C_\text{DC}/1000 \cdot (1-s_\text{building})}{Y_\text{GPU} \cdot 8766}
\right] \cdot W_\text{GPU}
+ W_\text{total} \cdot R \cdot \text{PUE}
""")
st.markdown(
    """
Where:
- $P_\\text{GPU}$ = GPU unit price ($)
- $D_\\text{bonus}$ = first-year bonus depreciation share
- $T$ = corporate tax rate used for the depreciation tax shield
- $r$ = discount rate / cost of capital
- $Y_\\text{GPU}$ = GPU amortization period (years)
- $C_\\text{DC}$ = Data center CapEx ($/MW)
- $s_\\text{building}$ = share of DC CapEx treated as long-lived building shell
- $W_\\text{GPU}$ = GPU power draw used for IT load allocation
- $W_\\text{total}$ = GPU power draw plus CPU overhead used for electricity
- $R$ = Electricity rate ($/kWh)
- $\\text{PUE}$ = Power usage effectiveness (cooling overhead)

When the building share is 100%, the model uses the OP-compatible single DC amortization period instead of the split above.
"""
)

st.subheader("2. Concurrency")
st.latex(r"""
u_\text{total} = \frac{U_\text{paid} \cdot (1 + r_\text{free}) \cdot h/24}{N_\text{GPU}}
""")
st.markdown(
    """
Where:
- $u_\\text{total}$ = total concurrent users per GPU
- $U_\\text{paid}$ = number of paid users
- $r_\\text{free}$ = free-to-paid user ratio
- $h$ = usage hours per day
- $N_\\text{GPU}$ = total GPUs deployed
"""
)

st.subheader("3. Tokens Per Second (3 Models)")
st.markdown(
    """
**OP's Logistic Model:** Fits a logistic curve through two NVIDIA benchmark data points,
scaling linearly with parameter count: $\\text{TPS}(u, p) = \\text{TPS}_{70}(u) \\cdot 70/p$

**Roofline Model:** Based on hardware limits — memory bandwidth and compute throughput.
$\\text{TPS} = \\min(\\text{TPS}_\\text{mem}, \\text{TPS}_\\text{compute}) \\cdot \\eta$

**Simple Linear:** Linear scaling from base TPS to saturation TPS at a user-defined concurrency.
"""
)

st.subheader("4. Cost per Million Tokens")
st.latex(r"""
\text{Cost}_\text{/MT} = \frac{\text{Cost}_\text{GPU/hr}}{\text{TPS} \cdot 3600 / 10^6}
= 277.78 \cdot \frac{\text{Cost}_\text{GPU/hr}}{\text{TPS}}
""")

st.subheader("5. Profitability")
st.latex(r"""
\text{Revenue}_\text{GPU/hr} = \frac{u_\text{paid}}{u_\text{total}} \cdot \frac{\text{TPS} \cdot 3600}{10^6} \cdot P_\text{MT}
""")
st.latex(r"""
\text{Profit}_\text{GPU/hr} = \text{Revenue}_\text{GPU/hr} - \text{Cost}_\text{GPU/hr}
""")

st.divider()

st.header("Reference Table")

ref_data = []
for p in ALL_PARAMS:
    refs = "; ".join([f"[{label}]({url})" for label, url in p.citations]) if p.citations else "—"
    ref_data.append({
        "Parameter": p.label,
        "Default": f"{p.default} {p.unit}" if p.unit and p.unit not in ("ratio", ":1") else f"{p.default}",
        "Rationale": p.rationale[:120] + "...",
        "Sources": refs,
    })

st.dataframe(ref_data, width="stretch", hide_index=True)

st.divider()

st.header("Key Sources")

st.markdown(
    """
1. **NVIDIA GTC 2024 Keynote** — Blackwell architecture announcement, pricing, performance claims.
   [nvidianews.nvidia.com](https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing)

2. **EIA Electric Power Monthly** — US industrial electricity rates by state (March 2026).
   [eia.gov](https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_5_06_a)

3. **Uptime Institute** — Annual Global Data Center Survey (PUE benchmarks).
   [uptimeinstitute.com](https://uptimeinstitute.com/resources/research-and-reports/annual-global-data-center-survey)

4. **McKinsey & Company** — "Investing in the rising data center economy" (2024).
   [mckinsey.com](https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/investing-in-the-rising-data-center-economy)

5. **Artificial Analysis** — Independent AI model benchmarks (speed, price, quality).
   [artificialanalysis.ai](https://artificialanalysis.ai/)

6. **NVIDIA Developer Blog** — Blackwell inference performance benchmarks.
   [developer.nvidia.com](https://developer.nvidia.com/blog/nvidia-blackwell-inference-performance-leap/)

7. **OpenAI / Anthropic API Pricing** — Current market pricing for frontier model inference.
   [openai.com](https://openai.com/api/pricing/)  ·  [anthropic.com](https://www.anthropic.com/pricing)

8. **FASB ASC 360** — GAAP guidance on property, plant, and equipment amortization.
   [fasb.org](https://fasb.org/)

9. **Wikipedia — Blackwell (microarchitecture)** — Technical specifications for B200/B100.
   [wikipedia.org](https://en.wikipedia.org/wiki/Blackwell_(microarchitecture))

Source quality varies by parameter. Hardware specifications, PUE, electricity rates, and tax references are anchored to operator or government sources where available. Model sizes, market pricing blends, GPU fleet counts, and some future-looking data center build assumptions are industry estimates or third-party analyses, not audited primary data.
"""
)

st.divider()

st.header("Limitations & Disclaimers")

st.markdown(
    """
- **Model size estimates**: Total parameter counts for frontier models are not publicly confirmed.
  Values used are community estimates.
- **TPS benchmarks**: Published NVIDIA benchmarks are conducted under idealized conditions.
  Real-world performance is typically lower due to network latency, batching inefficiencies, and
  variable prompt lengths.
- **Market data**: Paid user figures are based on company announcements and press reports,
  which may be incomplete or outdated.
- **Cost figures**: GPU pricing and data center CapEx are industry estimates that vary by region,
  contract size, and vendor relationship.
- **Training costs**: This model focuses exclusively on inference profitability. Training costs
  (estimated at $1B-$10B+ per frontier model) are treated as sunk costs per the OP's analysis.
- **Not investment advice**: This simulation is for educational and analytical purposes only.
"""
)
