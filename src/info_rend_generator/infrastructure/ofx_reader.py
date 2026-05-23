from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

from info_rend_generator.domain.money import quantize_money
from info_rend_generator.domain.transactions import Transaction


def read_ofx_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="latin-1", errors="ignore")


def parse_ofx_transaction_blocks(text: str) -> list[str]:
    return re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, flags=re.S | re.I)


def parse_ofx_tags(block: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    matches = re.finditer(
        r"<([A-Z0-9]+)>(.*?)(?=</?[A-Z0-9]+>|\n<|\r\n<|$)",
        block,
        flags=re.S | re.I,
    )
    for match in matches:
        name = match.group(1).upper()
        value = html.unescape(match.group(2).strip().strip('"'))
        if value:
            tags[name] = value
    return tags


def read_ofx_raw_data(path: str | Path) -> list[dict[str, str | int]]:
    text = read_ofx_text(path)
    rows: list[dict[str, str | int]] = []

    global_text = re.sub(r"<STMTTRN>.*?</STMTTRN>", "", text, flags=re.S | re.I)
    for tag, value in parse_ofx_tags(global_text).items():
        rows.append(
            {
                "section": "global",
                "record_index": "",
                "tag": tag,
                "value": value,
            }
        )

    for index, block in enumerate(parse_ofx_transaction_blocks(text), start=1):
        for tag, value in parse_ofx_tags(block).items():
            rows.append(
                {
                    "section": "transaction",
                    "record_index": index,
                    "tag": tag,
                    "value": value,
                }
            )

    return rows


def read_ofx(path: str | Path) -> list[Transaction]:
    text = read_ofx_text(path)
    blocks = parse_ofx_transaction_blocks(text)

    def tag(block: str, name: str) -> str:
        # OFX SGML can omit closing tags; capture until the next tag.
        match = re.search(rf"<{name}>(.*?)(?=</{name}>|\n<|\r\n<|$)", block, flags=re.S | re.I)
        if not match:
            return ""
        return html.unescape(match.group(1).strip().strip('"'))

    transactions: list[Transaction] = []
    for block in blocks:
        date_raw = tag(block, "DTPOSTED")[:8]
        amount_raw = tag(block, "TRNAMT")
        if not date_raw or not amount_raw:
            continue

        transactions.append(
            Transaction(
                date=datetime.strptime(date_raw, "%Y%m%d"),
                trntype=tag(block, "TRNTYPE").upper(),
                amount=quantize_money(amount_raw),
                name=tag(block, "NAME"),
                memo=tag(block, "MEMO"),
            )
        )

    return transactions
