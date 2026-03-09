"""
Kubeflow-compatible pipeline: wrap local steps as KFP components.
Build local pipeline first; then add KFP when needed.
"""
# Optional: use kfp to define components that call the same logic as local_pipeline.
# Example:
# from kfp import dsl
# @dsl.component(...)
# def scrape_op(): ...
# @dsl.pipeline(...)
# def smart_ecommerce_pipeline(): ...
# For now, placeholder so the module exists and can be extended.
def run():
    print("Kubeflow pipeline: use local_pipeline for now. Add kfp components when ready.")
