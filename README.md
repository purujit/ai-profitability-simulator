# AI Profitability Simulator

An interactive Streamlit app that lets you explore whether AI inference can be profitable by adjusting the key variables in the cost model.

**Based on [u/ksjdragon's Reddit post](https://www.reddit.com/r/BetterOffline/comments/1tzwnhi/ai_profitability_is_mathematically_impossible/):** *"AI profitability is mathematically impossible under all technological advancements"*

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" → select your repo → set main file to `app.py`
4. Deploy

## What This Simulates

The model breaks down the cost of AI inference into three components:

| Component | Typical Share |
|---|---|
| GPU Amortization | ~65% |
| Data Center CapEx | ~25% |
| Electricity (with cooling) | ~10% |

The key insight: **costs are dominated by capital investment, not electricity.** Even free power cannot make AI profitable if GPUs and data centers remain expensive and underutilized.

## Pages

- **Simulator** — Live dashboard with adjustable assumptions, cost breakdown pie, cost-vs-concurrency curve, revenue-vs-cost bars
- **Sensitivity** — Tornado chart showing which parameters move profit most, plus 4 scenario presets
- **Breakeven Solver** — Solve for the price, user count, GPU price, or electricity rate needed to break even
- **Methodology** — Full equation derivations, reference table with citations, attribution to the original post

## TPS Models

Three selectable models for GPU token throughput:

1. **OP's Logistic** — The original post's logistic curve fit from NVIDIA benchmarks
2. **Roofline** — Memory bandwidth and compute-bound hardware limits
3. **Simple Linear** — Linear scaling with user-defined saturation point

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Project Structure

```
ai_profitability/
├── app.py                    # Streamlit entry point
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── pages/
│   ├── 1_Simulator.py        # Main interactive dashboard
│   ├── 2_Sensitivity.py      # Tornado + scenarios
│   ├── 3_Breakeven.py        # Solver mode
│   └── 4_Methodology.py      # References & equations
├── src/
│   ├── engine.py             # Core computation functions
│   ├── tps_models.py         # 3 TPS curve implementations
│   ├── defaults.py           # Parameters with rationales & citations
│   ├── plots.py              # Plotly figure builders
│   └── utils.py              # Formatting helpers
└── tests/
    └── test_engine.py        # Verifies OP's numbers
```
