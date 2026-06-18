#!/usr/bin/env python3
"""
helpers.py
Utility functions shared across all pipeline phases.

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import time
import json
import hashlib
import numpy as np
from pathlib import Path
from functools import wraps
from datetime import datetime


# ---------------------------------------------------------------------------
# Timing decorator
# ---------------------------------------------------------------------------

def timer(func):
    """Decorator: prints execution time for any function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"[Timer] {func.__name__} → {elapsed:.3f} ms")
        return result
    return wrapper


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def file_md5(path: str | Path) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def save_json(data: dict, path: str | Path):
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, default=str))


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------------------
# Array utilities
# ---------------------------------------------------------------------------

def safe_divide(numerator: np.ndarray, denominator: np.ndarray,
                fill: float = 0.0) -> np.ndarray:
    """Element-wise division; replaces division-by-zero with fill value."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(denominator != 0, numerator / denominator, fill)
    return result


def zscore(x: np.ndarray) -> np.ndarray:
    """Standardise array to zero mean, unit variance."""
    std = x.std()
    return (x - x.mean()) / std if std > 0 else np.zeros_like(x)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_header(title: str, width: int = 60):
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def format_table(headers: list[str], rows: list[list], col_width: int = 16) -> str:
    lines = []
    header_line = "".join(h.ljust(col_width) for h in headers)
    lines.append(header_line)
    lines.append("-" * (col_width * len(headers)))
    for row in rows:
        lines.append("".join(str(v).ljust(col_width) for v in row))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------

def now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
