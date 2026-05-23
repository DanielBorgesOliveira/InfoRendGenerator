from __future__ import annotations

from decimal import Decimal

from info_rend_generator.domain.informe import InformeCalculation, InformeRequest, InformeTotals
from info_rend_generator.domain.money import parse_money
from info_rend_generator.domain.transactions import Transaction, sum_transactions
from info_rend_generator.infrastructure.transaction_reader import read_transactions


def calculate_informe(
    request: InformeRequest,
    transactions: list[Transaction] | None = None,
) -> tuple[InformeCalculation, list[Transaction]]:
    transactions = transactions if transactions is not None else read_transactions(request.ofx)
    rendimentos_auto = sum_transactions(
        transactions,
        request.rendimentos_keyword,
        positive=True if request.rendimentos_positivos else False,
        year=request.ano_calendario,
    )
    previdencia_auto = (
        sum_transactions(
            transactions,
            request.previdencia_keyword,
            positive=False,
            year=request.ano_calendario,
        )
        if request.previdencia_keyword
        else Decimal("0.00")
    )
    irrf_auto = (
        sum_transactions(
            transactions,
            request.irrf_keyword,
            positive=False,
            year=request.ano_calendario,
        )
        if request.irrf_keyword
        else Decimal("0.00")
    )
    socio_microempresa_auto = (
        sum_transactions(
            transactions,
            request.socio_microempresa_keyword,
            positive=False,
            year=request.ano_calendario,
        )
        if request.socio_microempresa_keyword
        else Decimal("0.00")
    )

    rendimentos_manual = parse_money(request.valor_rendimentos)
    previdencia_manual = parse_money(request.valor_previdencia)
    irrf_manual = parse_money(request.valor_irrf)

    automatic_totals = InformeTotals(
        rendimentos=rendimentos_auto,
        previdencia=previdencia_auto,
        irrf=irrf_auto,
        socio_microempresa=socio_microempresa_auto,
    )
    manual_totals = InformeTotals(
        rendimentos=rendimentos_manual,
        previdencia=previdencia_manual,
        irrf=irrf_manual,
        socio_microempresa=None,
    )
    final_totals = InformeTotals(
        rendimentos=rendimentos_manual if rendimentos_manual is not None else rendimentos_auto,
        previdencia=previdencia_manual if previdencia_manual is not None else previdencia_auto,
        irrf=irrf_manual if irrf_manual is not None else irrf_auto,
        socio_microempresa=socio_microempresa_auto,
    )

    return (
        InformeCalculation(
            automatic_totals=automatic_totals,
            manual_totals=manual_totals,
            final_totals=final_totals,
        ),
        transactions,
    )


def calculate_totals(request: InformeRequest) -> InformeTotals:
    calculation, _transactions = calculate_informe(request)
    return calculation.final_totals


def generate_informe(request: InformeRequest) -> InformeTotals:
    calculation, transactions = calculate_informe(request)

    from info_rend_generator.infrastructure.pdf_reportlab_renderer import render_informe_pdf

    render_informe_pdf(request, calculation.final_totals)

    if request.audit_excel:
        from info_rend_generator.infrastructure.audit_excel_exporter import export_audit_excel

        export_audit_excel(request, calculation, transactions)

    return calculation.final_totals
