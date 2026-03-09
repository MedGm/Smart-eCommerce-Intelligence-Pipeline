"""
Prompt templates for LLM. Input must be structured (top_categories, best_shop, cluster_summary, etc.).
LLM never receives raw product rows as source of truth.
"""

EXECUTIVE_SUMMARY_PROMPT = """You are an eCommerce analyst. Based on the following structured analytics summary, write a short executive summary (3–5 sentences) for a decision-maker. Be precise and only use the facts provided. Do not invent numbers or categories.

Data:
{data}
"""

CATEGORY_TRENDS_PROMPT = """Based on these category-level insights, write 2–3 sentences on category trends. Use only the provided data.

{data}
"""

# Example input structure (to be passed as JSON/dict):
# {
#   "top_categories": ["Electronics", "Fashion", "Home"],
#   "best_shop": "Shop A",
#   "best_shop_avg_score": 0.82,
#   "cluster_summary": {"cluster_0": "Affordable highly rated", "cluster_1": "Premium low-review"}
# }
