"""
Smart eCommerce Intelligence Pipeline — BI Dashboard
Multi-page Streamlit app with enforced dark theme, interactive Plotly charts,
and MCP-based data access (responsible architecture).

Dossier tools: Streamlit, Plotly, Altair, Seaborn.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.mcp.architecture import MCPClient

try:
    import altair as alt

    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# ── Design Tokens ─────────────────────────────────────────────
C = {
    "primary": "#7C6EF6",
    "secondary": "#E05B7A",
    "accent": "#1DB9D8",
    "success": "#2DCC8E",
    "warning": "#F0A150",
    "surface": "#161B22",
    "card": "#1C2129",
    "border": "rgba(255,255,255,0.06)",
    "text": "#E6EDF3",
    "muted": "#7D8590",
    "palette": [
        "#7C6EF6",
        "#1DB9D8",
        "#2DCC8E",
        "#F0A150",
        "#E05B7A",
        "#A371F7",
        "#3FB950",
        "#D29922",
        "#F778BA",
        "#79C0FF",
    ],
}


# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Smart eCommerce Intelligence",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Force dark background everywhere */
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #161B22 100%);
    border-right: 1px solid rgba(255,255,255,0.04);
}
section[data-testid="stSidebar"] .stRadio > div {
    gap: 2px;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 14px;
    padding: 10px 16px;
    border-radius: 8px;
    transition: all 0.15s ease;
    margin: 0;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(124, 110, 246, 0.08);
}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
section[data-testid="stSidebar"] input[type="radio"]:checked + div {
    background: rgba(124, 110, 246, 0.12);
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #1C2129;
    border-radius: 10px;
    padding: 18px 22px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(124, 110, 246, 0.25);
}
div[data-testid="stMetric"] label {
    color: #7D8590 !important;
    font-size: 11.5px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-weight: 700 !important;
    font-size: 26px !important;
    color: #E6EDF3 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 20px;
    border-radius: 6px 6px 0 0;
    font-size: 13px;
    font-weight: 500;
    color: #7D8590;
}
.stTabs [aria-selected="true"] {
    background: rgba(124, 110, 246, 0.1) !important;
    color: #E6EDF3 !important;
    border-bottom: 2px solid #7C6EF6 !important;
}

/* Headers */
.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #E6EDF3;
    margin-bottom: 4px;
    letter-spacing: -0.3px;
}
.page-subtitle {
    font-size: 14px;
    color: #7D8590;
    margin-bottom: 24px;
}
.section-header {
    font-size: 15px;
    font-weight: 600;
    color: #C9D1D9;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 24px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

/* Dataframes */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* Buttons */
.stButton > button {
    background: #7C6EF6 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 24px !important;
    letter-spacing: 0.3px;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #6959E0 !important;
    box-shadow: 0 4px 16px rgba(124, 110, 246, 0.3) !important;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }

/* Expander */
.streamlit-expanderHeader {
    font-size: 13px;
    font-weight: 500;
}

/* Select / Slider */
.stSelectbox label, .stSlider label {
    font-size: 12px !important;
    color: #7D8590 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── MCP Client ────────────────────────────────────────────────
mcp = MCPClient()


@st.cache_data(ttl=60)
def load_csv(name: str) -> pd.DataFrame:
    content = mcp.get_analytics(name)
    if content is None:
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(content))


@st.cache_data(ttl=60)
def load_json(name: str) -> dict:
    content = mcp.get_analytics(name)
    if content is None:
        return {}
    return json.loads(content)


@st.cache_data(ttl=60)
def load_features() -> pd.DataFrame:
    from src.config import processed_dir

    p = processed_dir() / "features.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


@st.cache_data(ttl=300)
def get_llm_summary() -> str:
    try:
        from src.llm.summarizer import run as llm_run

        return llm_run()
    except Exception as e:
        return f"LLM summary unavailable: {e}"


def apply_theme(fig, title="", height=400):
    """Apply consistent dark styling to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=C["text"], family="Inter")),
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], family="Inter, sans-serif", size=12),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(font=dict(size=11)),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
    <div style="padding: 24px 0 16px; text-align: center;">
        <div style="font-size: 13px; font-weight: 700; letter-spacing: 2px;
             text-transform: uppercase; color: #7C6EF6;">Smart eCommerce</div>
        <div style="font-size: 11px; color: #7D8590; margin-top: 2px;">
            Intelligence Pipeline</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Product Rankings",
            "Shop Analysis",
            "ML Models",
            "Segmentation",
            "Association Rules",
            "LLM Insights",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        f"""<div style="text-align:center; padding: 8px 0;">
        <div style="font-size: 10px; color: #484F58; text-transform: uppercase;
             letter-spacing: 1px; margin-bottom: 6px;">Architecture</div>
        <div style="font-size: 11px; color: #7D8590;">MCP Host / Client / Server</div>
        <div style="font-size: 11px; color: #484F58; margin-top: 2px;">
            {len(mcp.list_analytics())} analytics files loaded</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown('<div class="page-title">Dashboard Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Real-time analytics from 8 stores across 6 product niches</div>',
        unsafe_allow_html=True,
    )

    df = load_features()
    if df.empty:
        st.warning("No data available. Run the pipeline first.")
        st.stop()

    # KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Products", f"{len(df):,}")
    k2.metric("Shops", df["shop_name"].nunique() if "shop_name" in df.columns else 0)
    k3.metric("Avg Price", f"${df['price'].dropna().mean():.2f}" if "price" in df.columns else "—")
    k4.metric(
        "Avg Rating", f"{df['rating'].dropna().mean():.1f}" if "rating" in df.columns else "—"
    )
    k5.metric("Categories", df["category"].nunique() if "category" in df.columns else 0)

    st.markdown("")

    # Row 1: Platform + Shop
    r1a, r1b = st.columns(2)
    with r1a:
        if "source_platform" in df.columns:
            pf = df["source_platform"].value_counts().reset_index()
            pf.columns = ["Platform", "Products"]
            fig = px.pie(
                pf,
                values="Products",
                names="Platform",
                hole=0.6,
                color_discrete_sequence=[C["primary"], C["accent"]],
            )
            fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=12)
            fig = apply_theme(fig, "Platform Distribution", 340)
            st.plotly_chart(fig, width="stretch")

    with r1b:
        if "shop_name" in df.columns:
            sc = df["shop_name"].value_counts().reset_index()
            sc.columns = ["Shop", "Count"]
            fig = px.bar(
                sc,
                x="Count",
                y="Shop",
                orientation="h",
                color="Count",
                color_continuous_scale=[[0, C["primary"]], [1, C["accent"]]],
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            fig = apply_theme(fig, "Products per Shop", 340)
            st.plotly_chart(fig, width="stretch")

    # Row 2: Categories + Price
    r2a, r2b = st.columns(2)
    with r2a:
        if "category" in df.columns:
            cc = df["category"].value_counts().head(12).reset_index()
            cc.columns = ["Category", "Count"]
            if HAS_ALTAIR:
                chart = (
                    alt.Chart(cc)
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("Count:Q", title="Products"),
                        y=alt.Y("Category:N", sort="-x", title=None),
                        color=alt.Color(
                            "Count:Q",
                            scale=alt.Scale(range=[C["primary"], C["accent"]]),
                            legend=None,
                        ),
                    )
                    .properties(title="Top Categories", height=340)
                    .configure_view(strokeWidth=0)
                    .configure_axis(
                        gridColor="rgba(255,255,255,0.04)",
                        labelColor=C["muted"],
                        titleColor=C["muted"],
                    )
                    .configure_title(color=C["text"], fontSize=14)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                fig = px.bar(
                    cc,
                    x="Count",
                    y="Category",
                    orientation="h",
                    color="Count",
                    color_continuous_scale=[[0, C["primary"]], [1, C["success"]]],
                )
                fig.update_layout(coloraxis_showscale=False)
                fig = apply_theme(fig, "Top Categories", 340)
                st.plotly_chart(fig, width="stretch")

    with r2b:
        if "price" in df.columns:
            prices = df["price"].dropna()
            if not prices.empty:
                fig = go.Figure()
                fig.add_trace(
                    go.Histogram(
                        x=prices,
                        nbinsx=30,
                        marker=dict(color=C["primary"], line=dict(width=0.5, color="#0E1117")),
                        opacity=0.9,
                        name="Count",
                    )
                )
                fig = apply_theme(fig, "Price Distribution", 340)
                fig.update_layout(xaxis_title="Price ($)", yaxis_title="Products", bargap=0.05)
                st.plotly_chart(fig, width="stretch")

    # Row 3: Rating + Discount
    r3a, r3b = st.columns(2)
    with r3a:
        if "rating" in df.columns:
            rated = df["rating"].dropna()
            rated = rated[rated > 0]
            if not rated.empty:
                fig = go.Figure()
                fig.add_trace(
                    go.Histogram(
                        x=rated,
                        nbinsx=20,
                        marker=dict(color=C["warning"], line=dict(width=0.5, color="#0E1117")),
                    )
                )
                fig = apply_theme(fig, f"Rating Distribution ({len(rated)} rated)", 300)
                fig.update_layout(xaxis_title="Rating", yaxis_title="Products")
                st.plotly_chart(fig, width="stretch")

    with r3b:
        if "discount_pct" in df.columns:
            disc = df["discount_pct"].dropna()
            disc = disc[disc > 0]
            if not disc.empty:
                fig = go.Figure()
                fig.add_trace(
                    go.Histogram(
                        x=disc,
                        nbinsx=20,
                        marker=dict(color=C["secondary"], line=dict(width=0.5, color="#0E1117")),
                    )
                )
                fig = apply_theme(fig, f"Discount Distribution ({len(disc)} discounted)", 300)
                fig.update_layout(xaxis_title="Discount %", yaxis_title="Products")
                st.plotly_chart(fig, width="stretch")

    # Correlation heatmap
    if HAS_SEABORN:
        with st.expander("Feature Correlation Matrix"):
            num = df.select_dtypes(include=[np.number]).columns.tolist()
            keep = [c for c in num if c not in ["shop_product_count", "category_frequency"]][:12]
            if len(keep) > 3:
                corr = df[keep].corr()
                fig_s, ax = plt.subplots(figsize=(10, 5.5))
                sns.heatmap(
                    corr,
                    annot=True,
                    fmt=".2f",
                    cmap="RdBu_r",
                    ax=ax,
                    square=True,
                    linewidths=0.5,
                    cbar_kws={"shrink": 0.75},
                    annot_kws={"size": 9},
                )
                ax.set_title("Feature Correlation Matrix", fontsize=13, pad=12, color="#E6EDF3")
                ax.tick_params(colors="#7D8590", labelsize=9)
                fig_s.patch.set_facecolor("#0E1117")
                ax.set_facecolor("#0E1117")
                plt.tight_layout()
                st.pyplot(fig_s)
                plt.close(fig_s)


# ══════════════════════════════════════════════════════════════
# PRODUCT RANKINGS
# ══════════════════════════════════════════════════════════════
elif page == "Product Rankings":
    st.markdown('<div class="page-title">Product Rankings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Top-K products by composite score (weighted: rating, reviews, availability, discount)</div>',
        unsafe_allow_html=True,
    )

    topk = load_csv("topk_products.csv")
    if topk.empty:
        st.warning("No ranking data available. Run the scoring step.")
        st.stop()

    # Filters
    st.markdown('<div class="section-header">Filters</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        cats = ["All"] + (
            sorted(topk["category"].dropna().unique().tolist())
            if "category" in topk.columns
            else []
        )
        sel_cat = st.selectbox("Category", cats)
    with fc2:
        shops = ["All"] + (
            sorted(topk["shop_name"].dropna().unique().tolist())
            if "shop_name" in topk.columns
            else []
        )
        sel_shop = st.selectbox("Shop", shops)
    with fc3:
        if "price" in topk.columns and topk["price"].notna().any():
            pmin, pmax = float(topk["price"].min()), float(topk["price"].max())
            price_range = st.slider("Price range ($)", pmin, pmax, (pmin, pmax))
        else:
            price_range = None
    with fc4:
        k = st.slider("Show top", 5, 100, 25)

    fd = topk.copy()
    if sel_cat != "All" and "category" in fd.columns:
        fd = fd[fd["category"] == sel_cat]
    if sel_shop != "All" and "shop_name" in fd.columns:
        fd = fd[fd["shop_name"] == sel_shop]
    if price_range and "price" in fd.columns:
        fd = fd[(fd["price"] >= price_range[0]) & (fd["price"] <= price_range[1])]
    fd = fd.head(k)

    st.caption(f"Showing {len(fd)} of {len(topk)} products")

    if "score" in fd.columns and len(fd) > 0:
        chart_col, table_col = st.columns([1.2, 1])

        with chart_col:
            display_df = fd.head(20).copy()
            if "title" in display_df.columns:
                display_df["label"] = display_df["title"].str[:45]
            else:
                display_df["label"] = display_df.index.astype(str)
            fig = px.bar(
                display_df,
                x="score",
                y="label",
                orientation="h",
                color="score",
                color_continuous_scale=[
                    [0, C["secondary"]],
                    [0.5, C["warning"]],
                    [1, C["success"]],
                ],
                hover_data=[
                    c for c in ["shop_name", "price", "category"] if c in display_df.columns
                ],
            )
            fig.update_layout(
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"},
                yaxis_title=None,
            )
            fig = apply_theme(fig, f"Top {min(20, len(fd))} by Score", 500)
            st.plotly_chart(fig, width="stretch")

        with table_col:
            cols = [
                c for c in ["title", "shop_name", "category", "price", "score"] if c in fd.columns
            ]
            st.dataframe(fd[cols].head(20) if cols else fd.head(20), height=480)

    # Per-category analysis
    topk_cat = load_csv("topk_per_category.csv")
    if not topk_cat.empty and "category" in topk_cat.columns and "score" in topk_cat.columns:
        with st.expander("Category Score Breakdown"):
            cat_avg = (
                topk_cat.groupby("category")["score"]
                .mean()
                .sort_values(ascending=False)
                .head(15)
                .reset_index()
            )
            cat_avg.columns = ["Category", "Avg Score"]
            fig = px.bar(
                cat_avg,
                x="Avg Score",
                y="Category",
                orientation="h",
                color="Avg Score",
                color_continuous_scale=[[0, C["primary"]], [1, C["success"]]],
            )
            fig.update_layout(coloraxis_showscale=False)
            fig = apply_theme(fig, "Average Score by Category", 380)
            st.plotly_chart(fig, width="stretch")


# ══════════════════════════════════════════════════════════════
# SHOP ANALYSIS
# ══════════════════════════════════════════════════════════════
elif page == "Shop Analysis":
    st.markdown('<div class="page-title">Shop Performance</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Comparative analysis across all scraped stores</div>',
        unsafe_allow_html=True,
    )

    df = load_features()
    topk_shop = load_csv("topk_per_shop.csv")

    if df.empty:
        st.warning("No data available.")
        st.stop()

    if "shop_name" in df.columns:
        stats = (
            df.groupby("shop_name")
            .agg(
                products=("product_id", "count"),
                avg_price=("price", "mean"),
                avg_rating=("rating", "mean"),
                avg_discount=("discount_pct", "mean"),
            )
            .reset_index()
            .sort_values("products", ascending=False)
        )

        st.dataframe(
            stats.style.format(
                {"avg_price": "${:.2f}", "avg_rating": "{:.2f}", "avg_discount": "{:.1%}"}
            ),
            height=280,
        )

        tab1, tab2, tab3 = st.tabs(["Radar Comparison", "Price Distribution", "Score Ranking"])

        with tab1:
            metrics = ["avg_price", "avg_rating", "avg_discount", "products"]
            rd = stats.copy()
            for m in metrics:
                mn, mx = rd[m].min(), rd[m].max()
                rd[f"{m}_n"] = (rd[m] - mn) / (mx - mn) if mx > mn else 0.5

            fig = go.Figure()
            for i, (_, row) in enumerate(rd.iterrows()):
                vals = [row[f"{m}_n"] for m in metrics] + [row[f"{metrics[0]}_n"]]
                theta = ["Price", "Rating", "Discount", "Products", "Price"]
                fig.add_trace(
                    go.Scatterpolar(
                        r=vals,
                        theta=theta,
                        fill="toself",
                        name=row["shop_name"],
                        opacity=0.55,
                        line=dict(color=C["palette"][i % len(C["palette"])]),
                    )
                )
            fig = apply_theme(fig, "Shop Comparison", 450)
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(gridcolor="rgba(255,255,255,0.06)", showticklabels=False),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                )
            )
            st.plotly_chart(fig, width="stretch")

        with tab2:
            fig = px.box(
                df.dropna(subset=["price"]),
                x="shop_name",
                y="price",
                color="shop_name",
                color_discrete_sequence=C["palette"],
            )
            fig = apply_theme(fig, "Price Distribution by Shop", 400)
            fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Price ($)")
            st.plotly_chart(fig, width="stretch")

        with tab3:
            if (
                not topk_shop.empty
                and "score" in topk_shop.columns
                and "shop_name" in topk_shop.columns
            ):
                ss = (
                    topk_shop.groupby("shop_name")["score"]
                    .mean()
                    .sort_values(ascending=True)
                    .reset_index()
                )
                ss.columns = ["Shop", "Avg Score"]
                fig = px.bar(
                    ss,
                    x="Avg Score",
                    y="Shop",
                    orientation="h",
                    color="Avg Score",
                    color_continuous_scale=[
                        [0, C["secondary"]],
                        [0.5, C["warning"]],
                        [1, C["success"]],
                    ],
                )
                fig.update_layout(coloraxis_showscale=False)
                fig = apply_theme(fig, "Shop Score Ranking", 380)
                st.plotly_chart(fig, width="stretch")


# ══════════════════════════════════════════════════════════════
# ML MODELS
# ══════════════════════════════════════════════════════════════
elif page == "ML Models":
    st.markdown('<div class="page-title">Machine Learning Models</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Classification and evaluation metrics for high-potential product prediction</div>',
        unsafe_allow_html=True,
    )

    rf = load_json("model_metrics.json")
    xgb = load_json("model_metrics_xgboost.json")

    if not rf and not xgb:
        st.warning("No model metrics. Run training steps.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Performance", "Feature Importance", "Confusion Matrix"])

    with tab1:
        models = []
        if rf:
            models.append(
                {
                    "Model": "RandomForest",
                    **{k: rf.get(k) for k in ["accuracy", "precision", "recall", "f1"]},
                }
            )
        if xgb:
            models.append(
                {
                    "Model": "XGBoost",
                    **{k: xgb.get(k) for k in ["accuracy", "precision", "recall", "f1"]},
                }
            )

        if models:
            st.dataframe(
                pd.DataFrame(models).style.format(
                    {k: "{:.3f}" for k in ["accuracy", "precision", "recall", "f1"]}
                ),
                height=120,
            )

            met = ["accuracy", "precision", "recall", "f1"]
            fig = go.Figure()
            colors = [C["primary"], C["accent"]]
            for i, m in enumerate(models):
                fig.add_trace(
                    go.Bar(
                        name=m["Model"],
                        x=met,
                        y=[m.get(k, 0) for k in met],
                        marker_color=colors[i % 2],
                        text=[f"{m.get(k, 0):.3f}" for k in met],
                        textposition="outside",
                        textfont_size=11,
                    )
                )
            fig.update_layout(barmode="group", yaxis_range=[0, 1.12])
            fig = apply_theme(fig, "Model Comparison", 400)
            st.plotly_chart(fig, width="stretch")

    with tab2:
        if rf.get("feature_importance"):
            fi = pd.DataFrame(rf["feature_importance"]).sort_values("importance")
            fig = px.bar(
                fi,
                x="importance",
                y="feature",
                orientation="h",
                color="importance",
                color_continuous_scale=[[0, C["primary"]], [1, C["success"]]],
            )
            fig.update_layout(coloraxis_showscale=False, yaxis_title=None)
            fig = apply_theme(fig, "RandomForest — Feature Importance", 380)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Feature importance data not available. Re-run training.")

    with tab3:
        for name, metrics in [("RandomForest", rf), ("XGBoost", xgb)]:
            if metrics.get("confusion_matrix"):
                cm = np.array(metrics["confusion_matrix"])
                labels = ["Negative", "Positive"]
                fig = px.imshow(
                    cm,
                    text_auto=True,
                    x=labels,
                    y=labels,
                    color_continuous_scale=[[0, "#0E1117"], [1, C["primary"]]],
                    labels=dict(x="Predicted", y="Actual", color="Count"),
                )
                fig = apply_theme(fig, f"{name} — Confusion Matrix", 320)
                st.plotly_chart(fig, width="stretch")


# ══════════════════════════════════════════════════════════════
# SEGMENTATION
# ══════════════════════════════════════════════════════════════
elif page == "Segmentation":
    st.markdown('<div class="page-title">Product Segmentation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Unsupervised clustering for catalog structure analysis</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["KMeans Clustering", "DBSCAN Anomalies"])

    with tab1:
        pca = load_csv("pca_viz.csv")
        clusters = load_csv("clusters.csv")

        if not pca.empty and "cluster" in pca.columns:
            pca["cluster"] = pca["cluster"].astype(str)
            fig = px.scatter(
                pca,
                x="pc1",
                y="pc2",
                color="cluster",
                color_discrete_sequence=C["palette"],
                opacity=0.7,
            )
            fig.update_traces(marker=dict(size=7, line=dict(width=0.5, color="rgba(0,0,0,0.3)")))
            fig = apply_theme(fig, "PCA Projection — KMeans Clusters", 480)
            fig.update_layout(xaxis_title="PC 1", yaxis_title="PC 2")
            st.plotly_chart(fig, width="stretch")

            if not clusters.empty:
                ca, cb = st.columns(2)
                with ca:
                    sizes = clusters["cluster"].value_counts().reset_index()
                    sizes.columns = ["Cluster", "Size"]
                    sizes["Cluster"] = sizes["Cluster"].astype(str)
                    fig = px.pie(
                        sizes,
                        values="Size",
                        names="Cluster",
                        hole=0.55,
                        color_discrete_sequence=C["palette"],
                    )
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    fig = apply_theme(fig, "Cluster Distribution", 320)
                    st.plotly_chart(fig, width="stretch")
                with cb:
                    if "score" in clusters.columns:
                        cs = (
                            clusters.groupby("cluster")
                            .agg(count=("cluster", "size"), avg_score=("score", "mean"))
                            .reset_index()
                        )
                        cs.columns = ["Cluster", "Products", "Avg Score"]
                        st.dataframe(cs.style.format({"Avg Score": "{:.3f}"}), height=260)
        else:
            st.info("Run clustering step for PCA visualization.")

    with tab2:
        dbscan = load_csv("dbscan_clusters.csv")
        if not dbscan.empty and "dbscan_cluster" in dbscan.columns:
            n_out = int((dbscan["dbscan_cluster"] == -1).sum())
            n_cl = dbscan["dbscan_cluster"].nunique() - (
                1 if -1 in dbscan["dbscan_cluster"].values else 0
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Clusters", n_cl)
            c2.metric("Outliers", n_out)
            c3.metric("Total", len(dbscan))

            ds = dbscan["dbscan_cluster"].value_counts().reset_index()
            ds.columns = ["Cluster", "Count"]
            ds["Cluster"] = ds["Cluster"].astype(str)
            ds["Type"] = ds["Cluster"].apply(lambda x: "Outlier" if x == "-1" else "Cluster")
            fig = px.bar(
                ds,
                x="Cluster",
                y="Count",
                color="Type",
                color_discrete_map={"Outlier": C["secondary"], "Cluster": C["primary"]},
            )
            fig = apply_theme(fig, "DBSCAN Cluster Distribution", 340)
            st.plotly_chart(fig, width="stretch")

            with st.expander(f"View {n_out} Outlier Products"):
                outs = dbscan[dbscan["dbscan_cluster"] == -1]
                cols = [c for c in ["title", "shop_name", "category"] if c in outs.columns]
                st.dataframe(outs[cols] if cols else outs)
        else:
            st.info("Run DBSCAN step for anomaly detection.")


# ══════════════════════════════════════════════════════════════
# ASSOCIATION RULES
# ══════════════════════════════════════════════════════════════
elif page == "Association Rules":
    st.markdown('<div class="page-title">Association Rules</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Apriori-mined patterns across categories, platforms, and price buckets</div>',
        unsafe_allow_html=True,
    )

    rules = load_csv("association_rules.csv")
    if rules.empty:
        st.warning("No rules generated. Run the association rules step.")
        st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rules", f"{len(rules):,}")
    c2.metric(
        "Avg Confidence",
        f"{rules['confidence'].mean():.2f}" if "confidence" in rules.columns else "—",
    )
    c3.metric("Avg Lift", f"{rules['lift'].mean():.2f}" if "lift" in rules.columns else "—")

    tab1, tab2 = st.tabs(["Scatter Plot", "Rules Table"])

    with tab1:
        if all(c in rules.columns for c in ["support", "confidence", "lift"]):
            fig = px.scatter(
                rules.head(300),
                x="support",
                y="confidence",
                size="lift",
                color="lift",
                color_continuous_scale=[[0, C["primary"]], [0.5, C["accent"]], [1, C["success"]]],
                hover_data=[c for c in ["antecedents", "consequents"] if c in rules.columns],
                opacity=0.7,
            )
            fig.update_traces(marker=dict(line=dict(width=0.3, color="rgba(0,0,0,0.3)")))
            fig = apply_theme(fig, "Support vs Confidence (size = lift)", 480)
            st.plotly_chart(fig, width="stretch")

    with tab2:
        cols = [
            c
            for c in ["antecedents", "consequents", "support", "confidence", "lift"]
            if c in rules.columns
        ]
        sorted_r = rules.sort_values("lift", ascending=False) if "lift" in rules.columns else rules
        st.dataframe(
            sorted_r[cols]
            .head(50)
            .style.format({"support": "{:.3f}", "confidence": "{:.3f}", "lift": "{:.2f}"})
            if cols
            else sorted_r.head(50),
            height=500,
        )


# ══════════════════════════════════════════════════════════════
# LLM INSIGHTS
# ══════════════════════════════════════════════════════════════
elif page == "LLM Insights":
    st.markdown('<div class="page-title">Advanced LLM Capabilities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">AI-generated BI strategies, product profiling, and interactive chat via secure MCP architecture</div>',
        unsafe_allow_html=True,
    )

    tab_report, tab_chat, tab_mcp = st.tabs(
        ["Strategic Reports", "BI Assistant (Chat)", "MCP Architecture"]
    )

    with tab_report:
        st.markdown(
            """<div style="background: #1C2129; border-radius: 8px; padding: 16px 20px;
            border-left: 3px solid #7C6EF6; font-size: 13px; color: #7D8590; margin-bottom: 20px;">
            The LLM receives <strong style="color:#E6EDF3">only aggregated pipelines outputs and top-K rows</strong>
            — never the entire raw database.</div>""",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        if c1.button("Executive Summary", use_container_width=True):
            with st.spinner("Calling Gemini API..."):
                st.markdown("### Executive Summary")
                st.info(get_llm_summary())

        if c2.button("Strategic Recommendations", use_container_width=True):
            with st.spinner("Generating Chain-of-Thought Strategy..."):
                from src.llm.summarizer import generate_strategy_report

                topk = load_csv("topk_products.csv")
                data = {}
                if not topk.empty:
                    data = {
                        "top_categories": topk["category"].value_counts().head(5).index.tolist()
                        if "category" in topk.columns
                        else [],
                        "best_shop": topk.groupby("shop_name")["score"].mean().idxmax()
                        if "shop_name" in topk.columns
                        else "",
                    }

                st.markdown("### Marketing Strategy & Trends")
                st.success(generate_strategy_report(data))

        if c3.button("Competitive Profiling", use_container_width=True):
            with st.spinner("Profiling Top Products..."):
                from src.llm.summarizer import generate_product_profile

                st.markdown("### Customer & Product Profile")
                st.warning(generate_product_profile(mcp.get_top_products(5)))

    with tab_chat:
        st.markdown("Ask the AI Assistant questions about your eCommerce data.")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your eCommerce AI Assistant. How can I help you analyze the data today?",
                }
            ]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ex: What are the 5 emerging products this week?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    from src.llm.summarizer import chat_with_data

                    # Build live context
                    topk = load_csv("topk_products.csv")
                    ctx = {"top_products": mcp.get_top_products(5) if mcp else []}
                    if not topk.empty and "category" in topk.columns:
                        ctx["top_categories"] = topk["category"].value_counts().head(5).to_dict()

                    response = chat_with_data(prompt, ctx, st.session_state.messages)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_mcp:
        st.markdown("### MCP Implementation details")
        st.markdown("""
| Concept | Implementation |
|---------|---------------|
| **Host** | This Streamlit dashboard |
| **Client** | `MCPClient` routes requests to servers |
| **AnalyticsReader** | Read-only access to whitelisted CSV/JSON files, plus secure `get_top_products()` |
| **SummaryGenerator** | LLM calls with structured input only |
| **Permissions** | No raw data, no code execution, no score modification |
| **Audit Logs** | `llm_usage_log.jsonl`, `mcp_access_log.jsonl` |
        """)

        with st.expander("LLM Usage Log", expanded=False):
            import json

            from src.config import analytics_dir as _adir

            lp = _adir() / "llm_usage_log.jsonl"
            if lp.exists():
                for line in lp.read_text().strip().split("\\n")[-5:]:
                    line = line.strip()
                    if line:
                        try:
                            st.json(json.loads(line))
                        except json.JSONDecodeError:
                            st.text(line)
            else:
                st.info("No LLM usage log yet.")
