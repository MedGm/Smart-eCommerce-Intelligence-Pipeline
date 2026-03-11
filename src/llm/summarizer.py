"""
LLM summarizer: consumes aggregated metrics only (top products, cluster summaries, etc.).
Logs prompt inputs and data source for responsible design.

Phase 5 expects a Gemini (or Gemini-compatible) client:
- we read a generic LLM_API_KEY or GEMINI_API_KEY from the environment
- the actual HTTP call remains a TODO so that the pipeline runs without secrets.
"""

import json
import os

from dotenv import load_dotenv

from src.config import analytics_dir, get_logger

# Charge les variables depuis .env (GEMINI_API_KEY, etc.) si présent
load_dotenv()

logger = get_logger(__name__)


def _log_usage(source: str, prompt_preview: str, response_preview: str) -> None:
    """Record prompt and response for MCP-inspired accountability."""
    log_dir = analytics_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "source": source,
        "prompt_preview": prompt_preview[:200],
        "response_preview": (response_preview or "")[:200],
    }
    log_path = log_dir / "llm_usage_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.debug("LLM usage logged: source=%s", source)


def generate_summary(structured_data: dict) -> str:
    """
    Call Gemini-compatible API (or local LLM) with structured_data only.

    structured_data should contain: top_categories, best_shop, cluster_summary, etc.
    Returns generated text; logs usage.
    """
    from src.llm.prompts import EXECUTIVE_SUMMARY_PROMPT

    prompt = EXECUTIVE_SUMMARY_PROMPT.format(data=json.dumps(structured_data, indent=2))
    # No key → ne pas casser le dashboard, juste expliquer comment activer
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        out = (
            "(LLM summary disabled: set GEMINI_API_KEY in your environment to enable "
            "Gemini 3 Flash.)"
        )
        _log_usage("none", prompt[:200], out)
        return out

    # Appel réel à l'API Gemini via google-genai
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        # Use a currently supported text model; good default for summaries.
        # See: https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        out = getattr(response, "text", "") or str(response)
        _log_usage("gemini", prompt[:200], out)
        return out
    except Exception as exc:  # pragma: no cover - garde le dashboard robuste
        out = f"(LLM error: {exc})"
        _log_usage("gemini_error", prompt[:200], out)
        return out


def run():
    """Load analytics outputs and generate summary."""
    a_dir = analytics_dir()
    if not (a_dir / "topk_products.csv").exists():
        return "(Run pipeline first to generate analytics.)"
    import pandas as pd

    topk = pd.read_csv(a_dir / "topk_products.csv")
    top_categories = (
        topk["category"].value_counts().head(5).index.tolist() if "category" in topk.columns else []
    )
    best_shop = ""
    if "shop_name" in topk.columns and not topk.empty:
        best_shop = topk.groupby("shop_name")["score"].mean().idxmax()
    data = {
        "top_categories": top_categories,
        "best_shop": best_shop,
        "n_top_products": len(topk),
    }
    if (a_dir / "clusters.csv").exists():
        clusters = pd.read_csv(a_dir / "clusters.csv")
        data["cluster_summary"] = clusters.groupby("cluster").size().to_dict()
    return generate_summary(data)


if __name__ == "__main__":
    print(run())
