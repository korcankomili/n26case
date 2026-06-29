import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from src.cleaning import clean_data
from src.charts import STAGES, LABELS, build_funnel_figure, compute_conversion_table, format_conversion_table


@st.cache_data
def load_data(dataset: str) -> pd.DataFrame:
    return clean_data(dataset)


st.set_page_config(page_title="N26 Funnel", layout="wide")
st.title("N26 Acquisition Funnel")

df = load_data("part_a")

# ── sidebar filters ──
st.sidebar.header("Filters")

min_date, max_date = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

countries = sorted(df["country"].unique())
selected_countries = st.sidebar.multiselect("Country", countries, default=countries)

channels = sorted(df["marketing_channel"].unique())
selected_channels = st.sidebar.multiselect("Channel", channels, default=channels)

breakdown = st.sidebar.radio("Break down by", ["None", "Channel", "Country"])

# ── filter ──
mask = (
    (df["date"].dt.date >= date_range[0])
    & (df["date"].dt.date <= date_range[1])
    & (df["country"].isin(selected_countries))
    & (df["marketing_channel"].isin(selected_channels))
)
filtered = df[mask]

st.caption(f"{len(filtered):,} rows selected out of {len(df):,}")

# ── funnel chart ──
fig = build_funnel_figure(filtered, breakdown)
fig.update_layout(
    title=dict(text="Acquisition Funnel", x=0.5),
    font=dict(size=13),
    height=750,
    margin=dict(l=100, r=30, t=60, b=40),
)
st.plotly_chart(fig, use_container_width=True)

# ── metrics row ──
totals = [int(filtered[s].sum()) for s in STAGES]
cols = st.columns(5)
for col, label, val in zip(cols, LABELS, totals):
    col.metric(label, f"{val:,}")

# ── step conversion table ──
_BREAKDOWN_COLS = {
    "Channel": ["marketing_channel"],
    "Country": ["country"],
    "Country + Channel": ["country", "marketing_channel"],
}

with st.expander("Step conversion detail"):
    group_cols = _BREAKDOWN_COLS.get(breakdown)
    st.dataframe(
        format_conversion_table(compute_conversion_table(filtered, group_cols=group_cols)),
        hide_index=True,
        use_container_width=True,
    )

# ── funnel performance over time ──
st.subheader("Funnel Performance Over Time")

_FREQ = {
    "Daily": "D",
    "Weekly": "W",
    "Monthly": "ME",
    "Quarterly": "QE",
    "Yearly": "YE",
}

ctrl_cols = st.columns([2, 2, 3])
with ctrl_cols[0]:
    step_from_label = st.selectbox("Step From", LABELS, index=0)
with ctrl_cols[1]:
    from_idx = LABELS.index(step_from_label)
    step_to_label = st.selectbox("Step To", LABELS[from_idx + 1:], index=len(LABELS[from_idx + 1:]) - 1)
with ctrl_cols[2]:
    agg_level = st.radio("Aggregation", list(_FREQ.keys()), horizontal=True)

step_from_col = STAGES[LABELS.index(step_from_label)]
step_to_col = STAGES[LABELS.index(step_to_label)]
conv_label = f"{step_to_label} % of {step_from_label}"

_DIM_COLS = {
    "None": [],
    "Channel": ["marketing_channel"],
    "Country": ["country"],
    "Country + Channel": ["country", "marketing_channel"],
}
dim_cols = _DIM_COLS[breakdown]

agg_cols = list({step_from_col, step_to_col})
if dim_cols:
    trend = (
        filtered
        .groupby([pd.Grouper(key="date", freq=_FREQ[agg_level])] + dim_cols)[agg_cols]
        .sum()
        .reset_index()
    )
else:
    trend = (
        filtered
        .set_index("date")
        .resample(_FREQ[agg_level])[agg_cols]
        .sum()
        .reset_index()
    )

trend = trend[trend[step_from_col] > 0].copy()
trend[conv_label] = trend[step_to_col] / trend[step_from_col]

fig_trend = go.Figure()

if dim_cols:
    dim_values = trend[dim_cols].drop_duplicates().sort_values(dim_cols)
    palette = [
        "#36b37e", "#00b8d9", "#6554c0", "#ff8b00", "#ff5630",
        "#0052cc", "#00875a", "#de350b", "#6b778c", "#8777d9",
    ]
    for idx, row_vals in enumerate(dim_values.itertuples(index=False)):
        mask_dim = pd.Series([True] * len(trend), index=trend.index)
        for col, val in zip(dim_cols, row_vals):
            mask_dim &= trend[col] == val
        segment = trend[mask_dim]
        seg_label = " / ".join(str(v) for v in row_vals)
        fig_trend.add_trace(go.Scatter(
            x=segment["date"],
            y=segment[conv_label],
            mode="lines+markers",
            name=seg_label,
            line=dict(color=palette[idx % len(palette)], width=2),
            marker=dict(size=4),
            hovertemplate=f"{seg_label}<br>%{{x|%Y-%m-%d}}<br>%{{y:.1%}}<extra></extra>",
        ))
else:
    fig_trend.add_trace(go.Scatter(
        x=trend["date"],
        y=trend[conv_label],
        mode="lines+markers",
        name=conv_label,
        line=dict(color="#36b37e", width=2),
        marker=dict(size=5),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1%}<extra></extra>",
    ))

fig_trend.update_layout(
    yaxis=dict(tickformat=".0%", title=conv_label),
    xaxis=dict(title=None),
    height=400,
    margin=dict(l=60, r=30, t=40, b=40),
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)
