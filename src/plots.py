"""Plotly visualization functions for the AI profitability simulator."""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd


def cost_breakdown_pie(gpu_hourly: float, dc_hourly: float, elec_hourly: float) -> go.Figure:
    """Donut chart showing GPU-hourly cost breakdown."""
    labels = ["GPU Amortization", "Data Center CapEx", "Electricity (incl. PUE)"]
    values = [gpu_hourly, dc_hourly, elec_hourly]
    colors = ["#e74c3c", "#f39c12", "#2ecc71"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#1a1c23", width=2)),
                textinfo="label+percent",
                textposition="outside",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=12),
        showlegend=False,
    )
    return fig


def cost_vs_concurrency_curve(
    p_billion: float,
    tps_func,
    config: dict,
    model_name: str,
    current_u: float,
    current_cost: float,
) -> go.Figure:
    """Cost per MT as a function of concurrent users, with current operating point."""
    u_range = np.logspace(-1, 3, 200)

    costs = []
    for u in u_range:
        tps = tps_func(u, p_billion, model_name, config)
        hourly = config.get("_gpu_hourly_cost", 1.89)
        tokens_ph = 3600 * tps
        cost_mt = hourly / (tokens_ph / 1e6) if tps > 0 else float("inf")
        costs.append(cost_mt)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=u_range,
            y=costs,
            mode="lines",
            name="Cost/MT",
            line=dict(color="#3498db", width=2.5),
            hovertemplate="Concurrency: %{x:.1f} users<br>Cost: $%{y:.2f}/MT<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[current_u],
            y=[current_cost],
            mode="markers",
            name="Current Operating Point",
            marker=dict(color="#e74c3c", size=14, symbol="x-thin", line=dict(width=2)),
            hovertemplate="Current: %{x:.1f} users<br>Cost: $%{y:.2f}/MT<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Concurrent Users per GPU",
        yaxis_title="Cost per Million Tokens ($/MT)",
        xaxis=dict(type="log", gridcolor="#333"),
        yaxis=dict(type="log", gridcolor="#333"),
        margin=dict(t=10, b=50, l=50, r=10),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


def revenue_vs_cost_bar(
    cost_per_mt: float,
    blended_price_per_mt: float,
    effective_revenue_per_mt: float,
    gpu_hourly_cost: float,
    revenue_per_gpu_hour: float,
) -> go.Figure:
    """Side-by-side bar chart comparing costs and revenue."""
    fig = go.Figure()

    categories = ["Per\nGPU-Hour", "Per\nMillion Tokens"]
    revenue_vals = [revenue_per_gpu_hour, effective_revenue_per_mt]
    cost_vals = [gpu_hourly_cost, cost_per_mt]

    fig.add_trace(
        go.Bar(
            name="Revenue",
            x=categories,
            y=revenue_vals,
            marker_color="#2ecc71",
            hovertemplate="Revenue: $%{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Cost",
            x=categories,
            y=cost_vals,
            marker_color="#e74c3c",
            hovertemplate="Cost: $%{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="group",
        margin=dict(t=10, b=30, l=10, r=10),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        yaxis=dict(gridcolor="#333", title="$"),
    )
    return fig


def sensitivity_tornado(
    base_profit: float,
    param_deltas: list[tuple[str, float, float]],
) -> go.Figure:
    """Tornado chart showing profit sensitivity to ±20% changes in each parameter."""
    param_deltas.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    param_deltas = param_deltas[:12]

    low_values = [p[1] for p in param_deltas][::-1]
    high_values = [p[2] for p in param_deltas][::-1]
    labels = [p[0] for p in param_deltas][::-1]
    low_deltas = [p - base_profit for p in low_values]
    high_deltas = [p - base_profit for p in high_values]

    fig = go.Figure()

    segment_x = []
    segment_y = []
    for label, low, high in zip(labels, low_deltas, high_deltas):
        segment_x.extend([low, high, None])
        segment_y.extend([label, label, None])
    fig.add_trace(
        go.Scatter(
            y=segment_y,
            x=segment_x,
            mode="lines",
            name="Sensitivity range",
            line=dict(color="#777", width=4),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            y=labels,
            x=low_deltas,
            mode="markers",
            name="Lower value",
            marker=dict(color="#3498db", size=10, symbol="circle"),
            customdata=low_values,
            hovertemplate="%{y}<br>Profit: $%{customdata:.2f}/GPU-hr<br>Change: $%{x:+.2f}/GPU-hr<extra>Lower value</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            y=labels,
            x=high_deltas,
            mode="markers",
            name="Higher value",
            marker=dict(color="#f39c12", size=10, symbol="diamond"),
            customdata=high_values,
            hovertemplate="%{y}<br>Profit: $%{customdata:.2f}/GPU-hr<br>Change: $%{x:+.2f}/GPU-hr<extra>Higher value</extra>",
        )
    )

    fig.add_vline(x=0, line_dash="dash", line_color="#888", line_width=1)

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(
            title="Change in Profit per GPU-Hour vs Baseline ($)",
            gridcolor="#333",
            tickformat="+.2f",
            hoverformat="+.2f",
        ),
    )
    return fig


def scenario_comparison_table(scenarios: dict[str, dict]) -> go.Figure:
    """Table showing key metrics across scenarios."""
    headers = ["Metric"] + list(scenarios.keys())
    metrics = [
        "cost_per_mt",
        "revenue_per_gpu_hour",
        "profit_per_gpu_hour",
        "profit_margin_pct",
        "paid_ratio",
    ]
    metric_labels = {
        "cost_per_mt": "Cost per MT ($)",
        "revenue_per_gpu_hour": "Revenue/GPU-hr ($)",
        "profit_per_gpu_hour": "Profit/GPU-hr ($)",
        "profit_margin_pct": "Profit Margin (%)",
        "paid_ratio": "Paid User Ratio",
    }

    cells = [[metric_labels[m] for m in metrics]]
    for name, results in scenarios.items():
        row = []
        for m in metrics:
            val = results.get(m, 0)
            if "pct" in m or "ratio" in m:
                row.append(f"{val:.1f}")
            else:
                row.append(f"${val:,.2f}")
        cells.append(row)

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=headers,
                    fill_color="#1a1c23",
                    align="center",
                    font=dict(color="#e0e0e0", size=13),
                    line_color="#333",
                    height=36,
                ),
                cells=dict(
                    values=cells,
                    fill_color=["#222", "#2a2a2a", "#222", "#2a2a2a", "#222"],
                    align="center",
                    font=dict(color="#e0e0e0", size=12),
                    line_color="#333",
                    height=32,
                ),
            )
        ]
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def margin_over_time(
    t_range: np.ndarray,
    margins: np.ndarray,
    concurrents: np.ndarray,
    paid_users: np.ndarray,
    gpu_counts: np.ndarray,
    current_t: float,
    current_margin: float,
) -> go.Figure:
    """Profit margin over time as both S-curves advance."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=t_range,
            y=margins,
            mode="lines",
            name="Profit Margin",
            line=dict(color="#2ecc71", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(46,204,113,0.1)",
            hovertemplate="t=%{x:.1f}yr<br>Margin: %{y:+.1f}%<extra></extra>",
        )
    )

    fig.add_hline(y=0, line_dash="dash", line_color="#e74c3c", line_width=1, opacity=0.7)

    fig.add_trace(
        go.Scatter(
            x=[current_t],
            y=[current_margin],
            mode="markers",
            name="Current",
            marker=dict(color="#f39c12", size=14, symbol="diamond"),
            hovertemplate="t=%{x:.1f}yr<br>Margin: %{y:+.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Years Since ChatGPT Launch (Nov 2022)",
        yaxis_title="Profit Margin (%)",
        xaxis=dict(gridcolor="#333"),
        yaxis=dict(gridcolor="#333", zerolinecolor="#e74c3c", zerolinewidth=1, zeroline=True),
        margin=dict(t=10, b=50, l=50, r=10),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig
