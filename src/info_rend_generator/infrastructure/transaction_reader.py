from __future__ import annotations

from pathlib import Path
from typing import Any

from info_rend_generator.domain.transactions import Transaction
from info_rend_generator.infrastructure.excel_reader import (
    read_excel_raw_data,
    read_excel_transactions,
)
from info_rend_generator.infrastructure.ofx_reader import read_ofx, read_ofx_raw_data

EXCEL_SUFFIXES = {".xlsx", ".xlsm"}
OFX_SUFFIXES = {".ofx"}


def read_transactions(path: str | Path) -> list[Transaction]:
    suffix = Path(path).suffix.lower()
    if suffix in OFX_SUFFIXES:
        return read_ofx(path)
    if suffix in EXCEL_SUFFIXES:
        return read_excel_transactions(path)
    raise ValueError(f"Unsupported input file type: {suffix}")


def read_raw_data(path: str | Path) -> list[dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    if suffix in OFX_SUFFIXES:
        return read_ofx_raw_data(path)
    if suffix in EXCEL_SUFFIXES:
        return read_excel_raw_data(path)
    raise ValueError(f"Unsupported input file type: {suffix}")
