"""
LLM summarizer: consumes aggregated metrics only (top products, cluster summaries, etc.).
Logs prompt inputs and data source for responsible design.
"""
import json
import os
from pathlib import Path


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


def _log_usage(source: str, prompt_preview: str, response_preview: str) -> None:
    """Record prompt and response for MCP-inspired accountability."""
    log_dir = _data_dir() / "analytics"
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {"source": source, "prompt_preview": prompt_preview[:200], "response_preview": (response_preview or "")[:200]}
    log_path = log_dir / "llm_usage_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def generate_summary(structured_data: dict) -> str:
    """
    Call OpenAI-compatible API (or local LLM) with structured_data only.
    structured_data should contain: top_categories, best_shop, cluster_summary, etc.
    Returns generated text; logs usage.
    """
    from src.llm.prompts import EXECUTIVE_SUMMARY_PROMPT
    prompt = EXECUTIVE_SUMMARY_PROMPT.format(data=json.dumps(structured_data, indent=2))
    # Placeholder: no API key by default; return static message so pipeline/dashboard don't break
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        out = "(LLM summary disabled: no API key. Set OPENAI_API_KEY or LLM_API_KEY and use your client here.)"
        _log_usage("none", prompt[:200], out)
        return out
    # TODO(Ismail): add actual API call (openai or httpx to OpenAI-compatible endpoint)
    # response = client.chat.completions.create(...)
    # out = response.choices[0].message.content
    # _log_usage("openai", prompt[:200], out[:200])
    out = "(LLM integration placeholder.)"
    _log_usage("placeholder", prompt[:200], out)
    return out


def run():
    """Load analytics outputs and generate summary."""
    root = _data_dir()
    analytics_dir = root / "analytics"
    if not (analytics_dir / "topk_products.csv").exists():
        return "(Run pipeline first to generate analytics.)"
    import pandas as pd
    topk = pd.read_csv(analytics_dir / "topk_products.csv")
    top_categories = topk["category"].value_counts().head(5).index.tolist() if "category" in topk.columns else []
    best_shop = ""
    if "shop_name" in topk.columns and not topk.empty:
        best_shop = topk.groupby("shop_name")["score"].mean().idxmax()
    data = {"top_categories": top_categories, "best_shop": best_shop, "n_top_products": len(topk)}
    if (analytics_dir / "clusters.csv").exists():
        clusters = pd.read_csv(analytics_dir / "clusters.csv")
        data["cluster_summary"] = clusters.groupby("cluster").size().to_dict()
    return generate_summary(data)


if __name__ == "__main__":
    print(run())
