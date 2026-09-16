"""Resolve download URLs for HDX (Humanitarian Data Exchange) datasets.

HDX is a CKAN instance; ``package_show`` returns a dataset's resources. We look
up the actual resource download URL by name/format at runtime rather than
hard-coding volatile CDN URLs.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.etl.http import FetchError, fetch_json

HDX_API = "https://data.humdata.org/api/3/action/package_show"


@dataclass(frozen=True)
class HdxResource:
    """A single downloadable resource within an HDX dataset."""

    name: str
    format: str
    url: str


@dataclass(frozen=True)
class HdxDataset:
    """An HDX dataset: its licence plus resources."""

    dataset_id: str
    title: str
    license: str
    resources: list[HdxResource]

    def find(self, *, name_contains: str | None = None, fmt: str | None = None) -> HdxResource:
        """Return the first resource matching name/format, or fail loudly."""
        for res in self.resources:
            if name_contains and name_contains.lower() not in res.name.lower():
                continue
            if fmt and res.format.lower() != fmt.lower():
                continue
            return res
        raise FetchError(
            f"No HDX resource in '{self.dataset_id}' matching "
            f"name~={name_contains!r} fmt={fmt!r}. Available: "
            + ", ".join(f"{r.name}({r.format})" for r in self.resources)
        )


def get_dataset(dataset_id: str) -> HdxDataset:
    """Fetch an HDX dataset's metadata (resources + licence)."""
    payload = fetch_json(HDX_API, params={"id": dataset_id})
    if not payload.get("success"):
        raise FetchError(f"HDX package_show failed for '{dataset_id}'")
    result = payload["result"]
    resources = [
        HdxResource(name=r.get("name") or "", format=r.get("format") or "", url=r.get("url") or "")
        for r in result.get("resources", [])
    ]
    return HdxDataset(
        dataset_id=dataset_id,
        title=result.get("title") or dataset_id,
        license=result.get("license_title") or "unknown",
        resources=resources,
    )
