from __future__ import annotations

import argparse
from datetime import datetime

from info_rend_generator.application.generate_informe import generate_informe
from info_rend_generator.config.defaults import (
    DEFAULT_ANO_CALENDARIO,
    DEFAULT_EXERCICIO,
    DEFAULT_NATUREZA,
    DEFAULT_SOCIO_MICROEMPRESA_KEYWORDS,
)
from info_rend_generator.domain.informe import InformeRequest
from info_rend_generator.domain.money import format_money


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera Informe de Rendimentos em PDF a partir de OFX ou XLSX."
    )
    parser.add_argument("ofx", metavar="input_file", help="Arquivo OFX ou XLSX de entrada")
    parser.add_argument("output_pdf", help="PDF de saida")
    parser.add_argument("--exercicio", default=DEFAULT_EXERCICIO)
    parser.add_argument("--ano-calendario", type=int, default=DEFAULT_ANO_CALENDARIO)
    parser.add_argument("--fonte-cnpj", default="")
    parser.add_argument("--fonte-nome", default="")
    parser.add_argument("--beneficiario-cpf", default="")
    parser.add_argument("--beneficiario-nome", default="")
    parser.add_argument("--responsavel-nome", default="")
    parser.add_argument("--data", default=datetime.today().strftime("%d/%m/%Y"))
    parser.add_argument("--natureza", default=DEFAULT_NATUREZA)

    parser.add_argument(
        "--rendimentos-keyword",
        action="append",
        default=[],
        help="Filtra lancamentos de rendimento. Pode repetir.",
    )
    parser.add_argument(
        "--rendimentos-positivos",
        action="store_true",
        help="Soma creditos positivos em vez de pagamentos negativos.",
    )
    parser.add_argument(
        "--previdencia-keyword",
        action="append",
        default=[],
        help="Filtra contribuicao previdenciaria oficial. Pode repetir.",
    )
    parser.add_argument(
        "--irrf-keyword", action="append", default=[], help="Filtra IRRF. Pode repetir."
    )
    parser.add_argument(
        "--socio-microempresa-keyword",
        action="append",
        default=[],
        help=(
            "Filtra valores isentos pagos ao titular ou socio da microempresa/EPP. "
            "Por padrao usa ANTECIPACAO DE DIVIDENDOS."
        ),
    )

    parser.add_argument("--valor-rendimentos", help="Valor manual, ex.: 71.900,00")
    parser.add_argument("--valor-previdencia", help="Valor manual, ex.: 7.909,00")
    parser.add_argument("--valor-irrf", help="Valor manual, ex.: 6.753,26")
    parser.add_argument(
        "--audit-excel",
        help=(
            "Caminho opcional para gerar uma planilha Excel de auditoria com resumo, "
            "transacoes e dados brutos do arquivo de entrada."
        ),
    )
    return parser


def request_from_args(args: argparse.Namespace) -> InformeRequest:
    return InformeRequest(
        ofx=args.ofx,
        output_pdf=args.output_pdf,
        exercicio=args.exercicio,
        ano_calendario=args.ano_calendario,
        fonte_cnpj=args.fonte_cnpj,
        fonte_nome=args.fonte_nome,
        beneficiario_cpf=args.beneficiario_cpf,
        beneficiario_nome=args.beneficiario_nome,
        responsavel_nome=args.responsavel_nome,
        data=args.data,
        natureza=args.natureza,
        rendimentos_keyword=args.rendimentos_keyword,
        rendimentos_positivos=args.rendimentos_positivos,
        previdencia_keyword=args.previdencia_keyword,
        irrf_keyword=args.irrf_keyword,
        socio_microempresa_keyword=(
            args.socio_microempresa_keyword or DEFAULT_SOCIO_MICROEMPRESA_KEYWORDS
        ),
        valor_rendimentos=args.valor_rendimentos,
        valor_previdencia=args.valor_previdencia,
        valor_irrf=args.valor_irrf,
        audit_excel=args.audit_excel,
    )


def main() -> None:
    args = build_parser().parse_args()
    request = request_from_args(args)
    totals = generate_informe(request)

    print(f"PDF gerado: {request.output_pdf}")
    print("Totais usados:")
    print(f"  Rendimentos: R$ {format_money(totals.rendimentos)}")
    print(f"  Previdencia: R$ {format_money(totals.previdencia)}")
    print(f"  IRRF:        R$ {format_money(totals.irrf)}")
    print(f"  Socio ME/EPP: R$ {format_money(totals.socio_microempresa)}")
    if request.audit_excel:
        print(f"Auditoria Excel gerada: {request.audit_excel}")
