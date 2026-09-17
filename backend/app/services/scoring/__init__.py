"""Deterministic playbook scoring.

The core (`core.score`) is pure: plain ``ScoringInputs`` in, ``ScoreResult`` out —
no DB, no HTTP, no randomness. The DB-backed provider (`gather`) builds the inputs
via PostGIS. Phase 5 will perturb the inputs and re-run the same core.
"""
