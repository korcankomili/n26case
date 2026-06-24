import pandas as pd
from plotly import graph_objects as go

STAGES = ["signups", "kyc_init", "kyc_complete", "card_activation", "first_transaction"]
LABELS = ["Signup", "KYC Initiated", "KYC Completed", "Card Activated", "First Transaction"]
COLORS = ["#36b37e", "#00b8d9", "#6554c0", "#ff8b00", "#ff5630"]


def make_funnel(data: pd.DataFrame, name: str = None) -> go.Funnel:
    totals = [int(data[s].sum()) for s in STAGES]
    return go.Funnel(
        y=LABELS,
        x=totals,
        name=name or "All",
        textinfo="value+percent initial+percent previous",
        textposition="auto",
        marker=dict(color=COLORS) if name is None else None,
        connector=dict(line=dict(color="#e0e0e0", width=1)),
    )


def _conversion_rows(data: pd.DataFrame, group_name: str = None) -> list[dict]:
    vals = [int(data[s].sum()) for s in STAGES]
    rows = []
    for i, (label, val) in enumerate(zip(LABELS, vals)):
        row = {}
        if group_name is not None:
            row["Group"] = group_name
        row["Stage"] = label
        row["Volume"] = val
        row["% of Signup"] = val / vals[0] if vals[0] else None
        row["% of Previous"] = (
            val / vals[i - 1] if i > 0 and vals[i - 1] else 100.0
        )
        row["Drop-off"] = vals[i - 1] - val if i > 0 else None
        row["Drop-off % of Previous"] = (
            (vals[i - 1] - val) / vals[i - 1] if i > 0 and vals[i - 1] else None
        )
        row["Drop-off % of Signup"] = (
            (vals[0] - val) / vals[0] if i > 0 and vals[0] else None
        )
        rows.append(row)
    return rows


def format_conversion_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["% of Signup", "% of Previous", "Drop-off % of Previous", "Drop-off % of Signup"]:
        if col in out.columns:
            out[col] = out[col].apply(lambda v: f"{v * 100:.1f}%" if v is not None and pd.notna(v) else "-")
    if "Drop-off" in out.columns:
        out["Drop-off"] = out["Drop-off"].apply(lambda v: f"{int(v):,}" if v is not None and pd.notna(v) else "-")
    return out


def compute_conversion_table(
    data: pd.DataFrame,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Return a tidy conversion DataFrame. Usable standalone for EDA.

    Args:
        data: filtered funnel DataFrame.
        group_cols: e.g. ["country"], ["marketing_channel"], or both.
                    None → aggregate over all rows.
    """
    if not group_cols:
        return pd.DataFrame(_conversion_rows(data))

    all_rows = []
    for keys, group in data.groupby(group_cols, sort=True):
        if isinstance(keys, str):
            keys = (keys,)
        group_name = " / ".join(str(k) for k in keys)
        all_rows.extend(_conversion_rows(group, group_name=group_name))
    return pd.DataFrame(all_rows)


def build_funnel_figure(filtered: pd.DataFrame, breakdown: str) -> go.Figure:
    if breakdown == "None":
        return go.Figure(make_funnel(filtered))

    if breakdown == "Country + Channel":
        fig = go.Figure()
        for (country, channel), group in filtered.groupby(
            ["country", "marketing_channel"], sort=True
        ):
            fig.add_trace(make_funnel(group, name=f"{country} / {channel}"))
        return fig

    col = "marketing_channel" if breakdown == "Channel" else "country"
    fig = go.Figure()
    for g in sorted(filtered[col].unique()):
        fig.add_trace(make_funnel(filtered[filtered[col] == g], name=g))
    return fig
