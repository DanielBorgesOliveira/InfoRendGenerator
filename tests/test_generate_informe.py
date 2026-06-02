from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from info_rend_generator.application.generate_informe import calculate_informe
from info_rend_generator.domain.informe import InformeRequest
from info_rend_generator.domain.transactions import Transaction


def test_valor_exceto_prolabore_overrides_item_6() -> None:
    request = InformeRequest(
        ofx="input.ofx",
        output_pdf="output.pdf",
        exercicio="2026",
        ano_calendario=2025,
        fonte_cnpj="",
        fonte_nome="",
        beneficiario_cpf="",
        beneficiario_nome="",
        responsavel_nome="",
        data="28/02/2026",
        natureza="",
        rendimentos_keyword=["PRO-LABORE"],
        rendimentos_positivos=False,
        previdencia_keyword=[],
        irrf_keyword=[],
        exceto_prolabore_keyword=["ANTECIPACAO DE DIVIDENDOS"],
        valor_exceto_prolabore="71.900,00",
    )
    transactions = [
        Transaction(
            date=datetime(2025, 1, 10),
            trntype="DEBIT",
            amount=Decimal("-1000.00"),
            name="PRO-LABORE",
            memo="",
        ),
        Transaction(
            date=datetime(2025, 1, 20),
            trntype="DEBIT",
            amount=Decimal("-2000.00"),
            name="ANTECIPACAO DE DIVIDENDOS",
            memo="",
        ),
    ]

    calculation, _transactions = calculate_informe(request, transactions)

    assert calculation.manual_totals.socio_microempresa == Decimal("71900.00")
    assert calculation.final_totals.socio_microempresa == Decimal("71900.00")
    assert calculation.final_totals.rendimentos == Decimal("1000.00")


def test_manual_values_do_not_require_input_file() -> None:
    request = InformeRequest(
        ofx=None,
        output_pdf="output.pdf",
        exercicio="2026",
        ano_calendario=2025,
        fonte_cnpj="",
        fonte_nome="",
        beneficiario_cpf="",
        beneficiario_nome="",
        responsavel_nome="",
        data="28/02/2026",
        natureza="",
        rendimentos_keyword=[],
        rendimentos_positivos=False,
        previdencia_keyword=[],
        irrf_keyword=[],
        exceto_prolabore_keyword=[],
        valor_rendimentos="R$ 71.950,00",
        valor_previdencia="R$ 7.914,50",
        valor_irrf="R$ 6.765,49",
        valor_exceto_prolabore="R$ 172.121,46",
    )

    calculation, transactions = calculate_informe(request)

    assert transactions == []
    assert calculation.final_totals.rendimentos == Decimal("71950.00")
    assert calculation.final_totals.previdencia == Decimal("7914.50")
    assert calculation.final_totals.irrf == Decimal("6765.49")
    assert calculation.final_totals.socio_microempresa == Decimal("172121.46")
