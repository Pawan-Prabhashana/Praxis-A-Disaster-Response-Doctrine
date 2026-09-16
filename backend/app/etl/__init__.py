"""ETL / geospatial ingestion layer.

Downloads real public data into a git-ignored cache, transforms it with
GeoPandas/Shapely (reprojecting everything to EPSG:4326), and upserts it into
PostGIS with provenance. Uses the SYNC engine (``app.db.sync_session``).
"""
