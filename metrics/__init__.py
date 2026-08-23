"""
Four-layer engineering-metrics pipeline.

    Layer 1  collect     deterministic, no model
    Layer 2  compute     deterministic, no model
    Layer 3  interpret   the only place a model runs
    gate     guardrails  deterministic, no model
    Layer 4  distribute  policy

Layers 1, 2 and the gate are code. Layer 3 is the model. Layer 4 is policy.
"""

__all__ = ["SCHEMA_VERSION"]

# 1: the ranked-leaderboard schema this pipeline replaced.
# 2: per-PR classification, team/individual profiles, no rank anywhere.
SCHEMA_VERSION = 2
