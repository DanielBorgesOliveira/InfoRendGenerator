from __future__ import annotations

from decimal import Decimal

from info_rend_generator.domain.informe import InformeCalculation, InformeRequest
from info_rend_generator.domain.transactions import Transaction, contains_all
from info_rend_generator.infrastructure.transaction_reader import read_raw_data


def export_audit_excel(
    request: InformeRequest,
    calculation: InformeCalculation,
    transactions: list[Transaction],
) -> None:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "The audit Excel export requires pandas. Install project dependencies with "
            "`python -m pip install -e .`."
        ) from exc

    try:
        import openpyxl  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "The audit Excel export requires openpyxl. Install project dependencies with "
            "`python -m pip install -e .`."
        ) from exc

    if request.audit_excel is None:
        return

    with pd.ExcelWriter(request.audit_excel, engine="openpyxl") as writer:
        _summary_frame(pd, request, calculation).to_excel(writer, sheet_name="summary", index=False)
        _transactions_frame(pd, request, transactions).to_excel(
            writer, sheet_name="transactions", index=False
        )
        raw_data = read_raw_data(request.ofx) if request.ofx is not None else []
        pd.DataFrame(raw_data).to_excel(writer, sheet_name="raw_data", index=False)
        _format_workbook(writer.book)


def _summary_frame(pd, request: InformeRequest, calculation: InformeCalculation):
    rows = [
        {
            "item": "input_file",
            "automatic_value": "",
            "manual_value": "",
            "final_value": str(request.ofx) if request.ofx is not None else "",
            "source": "input",
        },
        {
            "item": "output_pdf",
            "automatic_value": "",
            "manual_value": "",
            "final_value": str(request.output_pdf),
            "source": "input",
        },
        {
            "item": "ano_calendario",
            "automatic_value": "",
            "manual_value": "",
            "final_value": request.ano_calendario,
            "source": "input",
        },
        _summary_value_row(
            "rendimentos",
            calculation.automatic_totals.rendimentos,
            calculation.manual_totals.rendimentos,
            calculation.final_totals.rendimentos,
        ),
        _summary_value_row(
            "previdencia",
            calculation.automatic_totals.previdencia,
            calculation.manual_totals.previdencia,
            calculation.final_totals.previdencia,
        ),
        _summary_value_row(
            "irrf",
            calculation.automatic_totals.irrf,
            calculation.manual_totals.irrf,
            calculation.final_totals.irrf,
        ),
        _summary_value_row(
            "socio_microempresa",
            calculation.automatic_totals.socio_microempresa,
            calculation.manual_totals.socio_microempresa,
            calculation.final_totals.socio_microempresa,
        ),
        {
            "item": "rendimentos_keyword",
            "automatic_value": "",
            "manual_value": "",
            "final_value": ", ".join(request.rendimentos_keyword),
            "source": "filter",
        },
        {
            "item": "previdencia_keyword",
            "automatic_value": "",
            "manual_value": "",
            "final_value": ", ".join(request.previdencia_keyword),
            "source": "filter",
        },
        {
            "item": "irrf_keyword",
            "automatic_value": "",
            "manual_value": "",
            "final_value": ", ".join(request.irrf_keyword),
            "source": "filter",
        },
        {
            "item": "exceto_prolabore_keyword",
            "automatic_value": "",
            "manual_value": "",
            "final_value": ", ".join(request.exceto_prolabore_keyword),
            "source": "filter",
        },
    ]
    return pd.DataFrame(rows)


def _summary_value_row(
    item: str,
    automatic_value: Decimal | None,
    manual_value: Decimal | None,
    final_value: Decimal | None,
) -> dict[str, str | float]:
    has_manual = manual_value is not None
    return {
        "item": item,
        "automatic_value": _decimal_to_float(automatic_value),
        "manual_value": _decimal_to_float(manual_value) if has_manual else "",
        "final_value": _decimal_to_float(final_value),
        "source": "manual" if has_manual else "automatic",
    }


def _transactions_frame(pd, request: InformeRequest, transactions: list[Transaction]):
    rows = []
    for index, transaction in enumerate(transactions, start=1):
        year_matches = transaction.date.year == request.ano_calendario
        negative_amount = transaction.amount < 0
        positive_amount = transaction.amount > 0
        rendimentos_sign_matches = (
            positive_amount if request.rendimentos_positivos else negative_amount
        )
        rendimentos_keyword_matches = contains_all(
            _transaction_text(transaction), request.rendimentos_keyword
        )
        previdencia_keyword_matches = contains_all(
            _transaction_text(transaction), request.previdencia_keyword
        )
        irrf_keyword_matches = contains_all(_transaction_text(transaction), request.irrf_keyword)
        exceto_prolabore_keyword_matches = contains_all(
            _transaction_text(transaction), request.exceto_prolabore_keyword
        )

        included_rendimentos = (
            year_matches and rendimentos_sign_matches and rendimentos_keyword_matches
        )
        included_previdencia = (
            year_matches
            and negative_amount
            and bool(request.previdencia_keyword)
            and previdencia_keyword_matches
        )
        included_irrf = (
            year_matches and negative_amount and bool(request.irrf_keyword) and irrf_keyword_matches
        )
        included_exceto_prolabore = (
            year_matches
            and negative_amount
            and bool(request.exceto_prolabore_keyword)
            and exceto_prolabore_keyword_matches
        )
        included_types = []
        if included_rendimentos:
            included_types.append("rendimentos")
        if included_previdencia:
            included_types.append("previdencia")
        if included_irrf:
            included_types.append("irrf")
        if included_exceto_prolabore:
            included_types.append("exceto_prolabore")

        rows.append(
            {
                "transaction_index": index,
                "date": transaction.date.date().isoformat(),
                "year": transaction.date.year,
                "trntype": transaction.trntype,
                "amount": _decimal_to_float(transaction.amount),
                "absolute_amount": _decimal_to_float(abs(transaction.amount)),
                "name": transaction.name,
                "memo": transaction.memo,
                "year_matches": year_matches,
                "rendimentos_keyword_matches": rendimentos_keyword_matches,
                "rendimentos_sign_matches": rendimentos_sign_matches,
                "included_rendimentos": included_rendimentos,
                "previdencia_keyword_matches": previdencia_keyword_matches,
                "included_previdencia": included_previdencia,
                "irrf_keyword_matches": irrf_keyword_matches,
                "included_irrf": included_irrf,
                "exceto_prolabore_keyword_matches": exceto_prolabore_keyword_matches,
                "included_exceto_prolabore": included_exceto_prolabore,
                "included_value_type": ", ".join(included_types),
                "included_amount": (
                    _decimal_to_float(abs(transaction.amount)) if included_types else None
                ),
            }
        )

    return pd.DataFrame(rows)


def _format_workbook(workbook) -> None:
    from openpyxl.styles import Font, PatternFill

    header_fill = PatternFill("solid", fgColor="D9EAF7")
    header_font = Font(bold=True)
    widths = {
        "summary": {
            "A": 24,
            "B": 18,
            "C": 18,
            "D": 60,
            "E": 14,
        },
        "transactions": {
            "A": 18,
            "B": 12,
            "C": 10,
            "D": 12,
            "E": 14,
            "F": 16,
            "G": 36,
            "H": 60,
            "I": 14,
            "J": 28,
            "K": 26,
            "L": 22,
            "M": 28,
            "N": 22,
            "O": 22,
            "P": 16,
            "Q": 22,
            "R": 16,
            "S": 34,
            "T": 28,
        },
        "raw_data": {
            "A": 16,
            "B": 14,
            "C": 18,
            "D": 80,
        },
    }

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
        for column, width in widths.get(worksheet.title, {}).items():
            worksheet.column_dimensions[column].width = width


def _transaction_text(transaction: Transaction) -> str:
    return f"{transaction.name} {transaction.memo}"


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)
