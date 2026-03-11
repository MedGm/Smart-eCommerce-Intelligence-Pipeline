"""
Streamlit dashboard: Overview, Top-K, Shop comparison, Product segmentation, LLM Insights.
Consumes only pipeline outputs from data/analytics and data/processed.
"""

import os
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


def load_topk():
    p = _data_dir() / "analytics" / "topk_products.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_topk_per_shop():
    p = _data_dir() / "analytics" / "topk_per_shop.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_clusters():
    p = _data_dir() / "analytics" / "clusters.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_pca_viz():
    p = _data_dir() / "analytics" / "pca_viz.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_features():
    p = _data_dir() / "processed" / "features.parquet"
    if p.exists():
        return pd.read_parquet(p)
    return pd.DataFrame()


st.set_page_config(page_title="Smart eCommerce Intelligence", layout="wide")
st.title("Smart eCommerce Intelligence Pipeline")

# --- Overview ---
st.header("1. Overview")
df_f = load_features()
if not df_f.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Products", len(df_f))
    col2.metric(
        "Shops", df_f["shop_name"].nunique() if "shop_name" in df_f.columns else 0
    )
    col3.metric(
        "Avg price", f"{df_f['price'].mean():.2f}" if "price" in df_f.columns else "—"
    )
    col4.metric(
        "Avg rating",
        f"{df_f['rating'].mean():.2f}" if "rating" in df_f.columns else "—",
    )
else:
    st.info("Run the pipeline to see overview metrics.")

# --- Top-K ---
st.header("2. Top-K products")
topk = load_topk()
if not topk.empty:
    st.dataframe(topk.head(50), use_container_width=True)
else:
    st.info("No Top-K data. Run scoring step.")

# --- Shop comparison ---
st.header("3. Shop comparison")
topk_shop = load_topk_per_shop()
if not topk_shop.empty:
    # Expect columns like: shop_name, score, product_count (see scoring script)
    # Rename for nicer display if needed
    display_df = topk_shop.rename(
        columns={
            "shop_name": "Shop",
            "score": "Avg score",
            "product_count": "Product count",
        }
    )
    st.dataframe(
        display_df.sort_values("Avg score", ascending=False),
        use_container_width=True,
    )
else:
    st.info("Run pipeline with features and scoring for shop comparison (topk_per_shop.csv).")

# --- Product segmentation (PCA) ---
st.header("4. Product segmentation")
pca = load_pca_viz()
if not pca.empty and "cluster" in pca.columns:
    fig = px.scatter(
        pca, x="pc1", y="pc2", color="cluster", title="PCA 2D projection by cluster"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Run clustering step for PCA visualization.")

# --- LLM Insights ---
st.header("5. Insights / LLM summary")
try:
    from src.llm.summarizer import run as llm_run

    summary = llm_run()
    st.write(summary)
except Exception as e:
    st.warning(f"LLM summary unavailable: {e}")
