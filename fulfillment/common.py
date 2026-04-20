"""Shared utilities for fulfillment scripts.

Each fulfillment script turns an MCP server's core function into a sellable
deliverable — a CSV + plain-text README, zipped into one file ready to email.

Usage pattern:
    order = OrderContext("google-maps-leads", "dentist-dubai")
    rows = [...]  # list of dicts
    order.write_csv(rows, columns=[...])
    order.write_readme(summary_text)
    zip_path = order.finalize()
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# UTF-8 safe stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


ROOT = Path(__file__).resolve().parent
ORDERS_DIR = ROOT / "orders"
ORDERS_DIR.mkdir(exist_ok=True)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "untitled"


def mcp_path(name: str) -> Path:
    """Return the sibling MCP-server directory path, for sys.path injection."""
    p = ROOT.parent / "mcp-servers" / name
    if not p.exists():
        raise FileNotFoundError(f"MCP server not found: {p}")
    return p


@dataclass
class OrderContext:
    """One fulfillment run → one zipped deliverable."""

    product: str  # e.g. "google-maps-leads"
    order_label: str  # e.g. "dentist-dubai-500"
    stamp: str = field(default_factory=lambda: dt.datetime.now().strftime("%Y%m%d-%H%M"))
    params: dict = field(default_factory=dict)
    _csv_rows: int = 0
    _csv_name: str = ""
    _readme_name: str = "README-buyer.txt"

    @property
    def order_id(self) -> str:
        return f"order-{self.stamp}-{self.product}-{slugify(self.order_label)}"

    @property
    def work_dir(self) -> Path:
        d = ORDERS_DIR / self.order_id
        d.mkdir(exist_ok=True)
        return d

    def write_csv(self, rows: Iterable[dict], columns: list[str], filename: str | None = None) -> Path:
        """Write rows to CSV with UTF-8 BOM (opens cleanly in Excel).

        Nested values (dicts, lists) are JSON-stringified so the cell stays flat.
        Missing columns are rendered as empty string.
        """
        rows = list(rows)
        self._csv_rows = len(rows)
        self._csv_name = filename or f"{self.product}-{slugify(self.order_label)}.csv"
        path = self.work_dir / self._csv_name
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                flat = {}
                for c in columns:
                    v = r.get(c, "")
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, ensure_ascii=False)
                    flat[c] = v
                w.writerow(flat)
        return path

    def write_readme(self, product_title: str, summary: str, disclaimers: list[str] | None = None) -> Path:
        """Write a plain-text README-buyer.txt the buyer sees when they unzip."""
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"{product_title}",
            "=" * len(product_title),
            "",
            f"Order:      {self.order_id}",
            f"Delivered:  {now}",
            f"Rows:       {self._csv_rows}",
            f"CSV file:   {self._csv_name}",
            "",
            "Order parameters:",
        ]
        if self.params:
            for k, v in self.params.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append("  (none recorded)")
        lines += ["", "Summary:", "-" * 8, summary.strip(), ""]
        if disclaimers:
            lines += ["Disclaimers:", "-" * 12]
            for d in disclaimers:
                lines.append(f"- {d}")
            lines.append("")
        lines += [
            "",
            "Delivered by TechTools365 (techtools365.com).",
            "Questions or re-runs? Reply to the order email.",
            "",
        ]
        path = self.work_dir / self._readme_name
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def finalize(self) -> Path:
        """Zip the work dir contents into orders/<order_id>.zip. Returns zip path."""
        zip_path = ORDERS_DIR / f"{self.order_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in self.work_dir.iterdir():
                if f.is_file():
                    zf.write(f, arcname=f.name)
        return zip_path


def print_done(order: OrderContext, zip_path: Path) -> None:
    print("")
    print("=" * 60)
    print(f"[done] {order.order_id}")
    print(f"       rows:  {order._csv_rows}")
    print(f"       zip:   {zip_path}")
    print(f"       files: {', '.join(p.name for p in order.work_dir.iterdir())}")
    print("=" * 60)
