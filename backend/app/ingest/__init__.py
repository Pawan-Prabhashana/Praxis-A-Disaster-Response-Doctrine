"""Ingestion pipelines.

Each module exposes a ``run_*`` function that downloads a real public source,
transforms it to EPSG:4326, and upserts it into PostGIS with provenance. The
Typer CLI (``app.cli``) wires these into subcommands.
"""
