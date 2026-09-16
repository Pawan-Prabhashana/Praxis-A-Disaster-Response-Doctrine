"""Praxis data CLI.

Run with: ``uv run python -m app.cli <command>``.

Commands:
  ingest admin | osm | flood | weather | hazard-flood | desinventar | landslide | gdacs
  ingest scenario        (re)create the seed scenario (requires admin loaded)
  seed-scenario          run the full seed pipeline end to end
  data-report            print row counts per table with source + real/synthetic
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from app.db.sync_session import sync_session
from app.ingest import (
    admin,
    closures,
    desinventar,
    flood,
    gdacs,
    hazard_flood,
    landslide,
    osm,
    report,
    seed,
    weather,
)
from app.ingest.scenario import ensure_scenario

app = typer.Typer(help="Praxis geospatial data ingestion CLI.", no_args_is_help=True)
ingest_app = typer.Typer(help="Individual ingestion pipelines.", no_args_is_help=True)
app.add_typer(ingest_app, name="ingest")
console = Console()


def _emit(title: str, result: dict[str, int]) -> None:
    console.print(f"[bold green]✓[/] {title}")
    for key, value in result.items():
        console.print(f"    {key}: [cyan]{value}[/]")


@ingest_app.command("admin")
def cmd_admin(force: bool = typer.Option(False, help="Re-download source files.")) -> None:
    """Ingest COD-AB admin boundaries + COD-PS population."""
    _emit("admin", admin.run_admin(force=force))


@ingest_app.command("scenario")
def cmd_scenario() -> None:
    """Create/refresh the seed scenario (requires admin regions loaded)."""
    with sync_session() as session:
        scenario = ensure_scenario(session)
    _emit("scenario", {"scenario": 1, "slug_len": len(scenario.slug)})


@ingest_app.command("hazard-flood")
def cmd_hazard_flood(force: bool = typer.Option(False, help="Re-download source files.")) -> None:
    """Ingest the 2017 flood extent as a hazard layer."""
    _emit("hazard-flood", hazard_flood.run_hazard_flood(force=force))


@ingest_app.command("osm")
def cmd_osm(force: bool = typer.Option(False, help="Bypass the Overpass cache.")) -> None:
    """Ingest OSM candidate shelters and roads."""
    _emit("osm", osm.run_osm(force=force))


@ingest_app.command("flood")
def cmd_flood() -> None:
    """Ingest GloFAS ensemble river discharge for the event window."""
    _emit("flood", flood.run_discharge())


@ingest_app.command("weather")
def cmd_weather() -> None:
    """Ingest daily weather for the event window."""
    _emit("weather", weather.run_weather())


@ingest_app.command("desinventar")
def cmd_desinventar(force: bool = typer.Option(False, help="Re-download the export.")) -> None:
    """Ingest historical flood/landslide incidents (DesInventar)."""
    _emit("desinventar", desinventar.run_desinventar(force=force))


@ingest_app.command("landslide")
def cmd_landslide() -> None:
    """Ingest NBRO landslide zonation (real if provided, else flagged synthetic)."""
    _emit("landslide", landslide.run_landslide())


@ingest_app.command("gdacs")
def cmd_gdacs() -> None:
    """Ingest current GDACS alerts as reference incidents."""
    _emit("gdacs", gdacs.run_gdacs())


@ingest_app.command("closures")
def cmd_closures() -> None:
    """Derive scenario road closures from the flood extent (flagged synthetic)."""
    _emit("closures", closures.run_closures())


@app.command("seed-scenario")
def cmd_seed(force: bool = typer.Option(False, help="Re-download source files.")) -> None:
    """Run the full seed-scenario data load end to end."""
    result = seed.seed_scenario(force=force)
    _emit("seed-scenario complete", result)


@app.command("data-report")
def cmd_report() -> None:
    """Print row counts per table with source and real/synthetic status."""
    rows = report.build_report()
    table = Table(title="Praxis data ledger", header_style="bold")
    table.add_column("Table")
    table.add_column("Source")
    table.add_column("Kind")
    table.add_column("Rows", justify="right")

    total_real = 0
    total_synth = 0
    for r in rows:
        kind = "[yellow]SYNTHETIC[/]" if r.is_synthetic else "[green]real[/]"
        table.add_row(r.table, r.source, kind, f"{r.rows:,}")
        if r.is_synthetic:
            total_synth += r.rows
        else:
            total_real += r.rows

    console.print(table)
    console.print(
        f"Total real rows: [green]{total_real:,}[/]  |  "
        f"Total synthetic rows: [yellow]{total_synth:,}[/]"
    )


if __name__ == "__main__":
    app()
