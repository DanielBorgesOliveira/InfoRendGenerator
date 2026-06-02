from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class InformeRequest:
    ofx: str | Path | None
    output_pdf: str | Path
    exercicio: str
    ano_calendario: int
    fonte_cnpj: str
    fonte_nome: str
    beneficiario_cpf: str
    beneficiario_nome: str
    responsavel_nome: str
    data: str
    natureza: str
    rendimentos_keyword: list[str]
    rendimentos_positivos: bool
    previdencia_keyword: list[str]
    irrf_keyword: list[str]
    exceto_prolabore_keyword: list[str]
    valor_rendimentos: str | None = None
    valor_exceto_prolabore: str | None = None
    valor_previdencia: str | None = None
    valor_irrf: str | None = None
    audit_excel: str | Path | None = None


@dataclass(frozen=True)
class InformeTotals:
    rendimentos: Decimal | None
    previdencia: Decimal | None
    irrf: Decimal | None
    socio_microempresa: Decimal | None


@dataclass(frozen=True)
class InformeCalculation:
    automatic_totals: InformeTotals
    manual_totals: InformeTotals
    final_totals: InformeTotals
