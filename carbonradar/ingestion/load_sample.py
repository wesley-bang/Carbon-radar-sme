"""Load deterministic sample CSV data for v0.1."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"
OUTPUT_DIR = DATA_DIR / "outputs"

SAMPLE_FILES = {
    "factory_master": "factory_master.csv",
    "utility_bills": "utility_bills.csv",
    "fuel_logs": "fuel_logs.csv",
    "supplier_disclosure": "supplier_disclosure.csv",
    "emission_factors": "emission_factors.csv",
}


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def sample_path(name: str) -> Path:
    if name not in SAMPLE_FILES:
        raise KeyError(f"Unknown sample dataset: {name}")
    return SAMPLE_DIR / SAMPLE_FILES[name]


def load_csv(name: str) -> pd.DataFrame:
    path = sample_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Missing sample data file: {path}")
    return pd.read_csv(path)


def load_sample_data() -> dict[str, pd.DataFrame]:
    return {name: load_csv(name) for name in SAMPLE_FILES}


def build_sample_manifest() -> pd.DataFrame:
    rows = []
    for name, filename in SAMPLE_FILES.items():
        path = SAMPLE_DIR / filename
        df = pd.read_csv(path) if path.exists() else pd.DataFrame()
        rows.append(
            {
                "dataset": name,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "row_count": len(df),
                "exists": path.exists(),
            }
        )
    return pd.DataFrame(rows)

