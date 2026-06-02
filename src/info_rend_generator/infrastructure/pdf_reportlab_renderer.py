from __future__ import annotations

from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from xml.etree import ElementTree

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from info_rend_generator.domain.informe import InformeRequest, InformeTotals
from info_rend_generator.domain.money import format_money


class InformePDF:
    def __init__(self, output: str | Path):
        self.c = canvas.Canvas(str(output), pagesize=A4)
        self.w, self.h = A4
        self.left = 8 * mm
        self.right = self.w - 8 * mm
        self.top = self.h - 10 * mm
        self.y = self.top
        self.row_h = 5.2 * mm

    def set_font(self, bold=False, size=8):
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

    def text_fit(self, x, y, text, max_w, size=8, bold=False):
        self.set_font(bold, size)
        text = str(text or "")
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        while stringWidth(text, font_name, size) > max_w and len(text) > 3:
            text = text[:-4] + "..."
        self.c.drawString(x, y, text)

    def wrap_text(self, text, max_w, size=7, bold=False):
        text = str(text or "")
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        lines: list[str] = []
        current = ""

        for word in text.split():
            candidate = f"{current} {word}".strip()
            if stringWidth(candidate, font_name, size) <= max_w:
                current = candidate
                continue

            if current:
                lines.append(current)
            current = word

        if current:
            lines.append(current)
        return lines or [""]

    def wrapped_text(self, x, y_top, text, max_w, max_h, size=7, bold=False):
        self.set_font(bold, size)
        line_h = size * 0.42 * mm
        max_lines = max(1, int(max_h // line_h))
        wrapped_lines = self.wrap_text(text, max_w, size, bold)
        lines = wrapped_lines[:max_lines]

        if len(wrapped_lines) > max_lines and len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-3].rstrip() + "..."

        for index, line in enumerate(lines):
            self.c.drawString(x, y_top - (index * line_h), line)

    def rect(self, x, y, w, h):
        self.c.rect(x, y, w, h, stroke=1, fill=0)

    def logo(self, x, y, w, h):
        try:
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg
        except ImportError:
            self.c.circle(x + w / 2, y + h / 2, min(w, h) / 2, stroke=1, fill=0)
            self.c.drawCentredString(x + w / 2, y + h / 2 - 1.5 * mm, "BR")
            return

        logo_path = files("info_rend_generator.assets").joinpath("logo_brasil.svg")
        drawing = svg2rlg(str(logo_path))
        self.preserve_svg_viewbox_aspect(drawing, logo_path)
        scale = min(w / drawing.width, h / drawing.height)
        drawing.scale(scale, scale)

        scaled_w = drawing.width * scale
        scaled_h = drawing.height * scale
        renderPDF.draw(drawing, self.c, x + (w - scaled_w) / 2, y + (h - scaled_h) / 2)

    def preserve_svg_viewbox_aspect(self, drawing, logo_path) -> None:
        root = ElementTree.parse(str(logo_path)).getroot()
        view_box = root.attrib.get("viewBox")
        if not view_box or not drawing.contents:
            return

        min_x, min_y, view_box_w, view_box_h = [float(value) for value in view_box.split()]
        scale = min(drawing.width / view_box_w, drawing.height / view_box_h)
        x_offset = (drawing.width - view_box_w * scale) / 2
        y_offset = (drawing.height - view_box_h * scale) / 2

        drawing.contents[0].transform = (
            scale,
            0,
            0,
            -scale,
            x_offset - min_x * scale,
            y_offset + (min_y + view_box_h) * scale,
        )

    def header(self, exercicio, ano_calendario):
        c = self.c
        h = 26 * mm
        x = self.left
        y = self.y - h
        self.rect(x, y, self.right - self.left, h)
        mid = x + (self.right - self.left) * 0.55
        c.line(mid, y, mid, y + h)
        self.set_font(True, 8)
        self.logo(x + 3 * mm, y + 4 * mm, 14 * mm, 18 * mm)
        c.drawString(x + 20 * mm, y + h - 8 * mm, "MINISTERIO DA ECONOMIA")
        c.drawString(x + 20 * mm, y + h - 13 * mm, "SECRETARIA DA RECEITA FEDERAL DO BRASIL")
        c.drawString(x + 20 * mm, y + h - 18 * mm, "IMPOSTO SOBRE A RENDA DA PESSOA FISICA")
        c.drawString(x + 20 * mm, y + h - 23 * mm, "EXERCICIO:")
        c.drawString(x + 48 * mm, y + h - 23 * mm, str(exercicio))
        c.drawString(mid + 3 * mm, y + h - 8 * mm, "COMPROVANTE DE RENDIMENTOS PAGOS E DE")
        c.drawString(mid + 3 * mm, y + h - 13 * mm, "IMPOSTO SOBRE A RENDA RETIDO NA FONTE")
        c.drawString(mid + 3 * mm, y + h - 23 * mm, "ANO-CALENDARIO:")
        c.drawString(mid + 37 * mm, y + h - 23 * mm, str(ano_calendario))
        self.y = y

        notice_h = 8 * mm
        y2 = self.y - notice_h
        self.rect(x, y2, self.right - self.left, notice_h)
        self.set_font(False, 7)
        c.drawString(
            x + 2 * mm,
            y2 + 4.7 * mm,
            "Verifique as condicoes e o prazo para a apresentacao da Declaracao do Imposto "
            "sobre a Renda da Pessoa Fisica para este ano-calendario no site",
        )
        c.drawString(
            x + 2 * mm,
            y2 + 1.5 * mm,
            "da Secretaria Especial da Receita Federal do Brasil na Internet, no endereco "
            "<https://www.gov.br/receitafederal/pt-br>",
        )
        self.y = y2 - 6 * mm

    def section_title(self, title, right_title=None):
        self.set_font(True, 8)
        self.c.drawString(self.left, self.y, title)
        if right_title:
            self.c.drawRightString(self.right, self.y, right_title)
        self.y -= 2 * mm

    def cell2(self, labels_values):
        total_w = self.right - self.left
        h = 8 * mm
        y = self.y - h
        x = self.left
        for label, value, ratio in labels_values:
            w = total_w * ratio
            self.rect(x, y, w, h)
            self.set_font(False, 7)
            self.c.drawString(x + 2 * mm, y + h - 3.2 * mm, label)
            self.text_fit(x + 2 * mm, y + 1.6 * mm, value, w - 4 * mm, 7, False)
            x += w
        self.y = y

    def natureza(self, text):
        h = 8 * mm
        y = self.y - h
        self.rect(self.left, y, self.right - self.left, h)
        self.set_font(False, 7)
        self.c.drawString(self.left + 2 * mm, y + h - 3.2 * mm, "Natureza do Rendimento")
        self.text_fit(
            self.left + 2 * mm, y + 1.5 * mm, text, self.right - self.left - 4 * mm, 7, False
        )
        self.y = y - 6 * mm

    def value_table(self, rows):
        label_w = (self.right - self.left) * 0.865
        val_w = (self.right - self.left) - label_w
        for label, value, row_multiplier in rows:
            h = self.row_h * row_multiplier
            y = self.y - h
            self.rect(self.left, y, label_w, h)
            self.rect(self.left + label_w, y, val_w, h)
            self.set_font(False, 7)
            self.wrapped_text(
                self.left + 2 * mm,
                y + h - 3.6 * mm,
                label,
                label_w - 4 * mm,
                h - 2 * mm,
                7,
                False,
            )
            self.c.drawRightString(self.right - 1.5 * mm, y + h - 3.6 * mm, format_money(value))
            self.y = y
        self.y -= 6 * mm

    def accumulated_income_table(self):
        total_w = self.right - self.left
        value_w = total_w * 0.19
        label_w = total_w - value_w
        top_w = total_w * 0.81
        months_label_w = total_w * 0.16
        months_value_w = total_w - top_w - months_label_w
        top_h = 10 * mm
        y = self.y - top_h

        self.rect(self.left, y, top_w, top_h)
        self.rect(self.left + top_w, y + top_h / 2, months_label_w, top_h / 2)
        self.rect(
            self.left + top_w + months_label_w,
            y + top_h / 2,
            months_value_w,
            top_h / 2,
        )

        self.set_font(False, 7)
        self.c.drawString(self.left + 2 * mm, y + top_h - 3.2 * mm, "6.1 Numero do processo:")
        self.c.drawString(
            self.left + top_w + 2 * mm,
            y + top_h - 3.2 * mm,
            "Quantidade de meses",
        )
        self.c.drawRightString(self.right - 1.5 * mm, y + top_h - 3.2 * mm, "0,0")
        self.c.drawString(self.left + 2 * mm, y + 2.2 * mm, "Natureza do rendimento:")

        self.y = y - 4 * mm
        self.section_title("", "Valores em reais")

        rows = [
            (
                "1. Total dos rendimentos tributaveis (inclusive ferias e decimo "
                "terceiro salario)",
                1,
            ),
            ("2. Exclusao: Despesas com a acao judicial", 1),
            ("3. Deducao: Contribuicao previdenciaria oficial", 1),
            ("4. Deducao: Pensao alimenticia (preencher tambem o quadro 7)", 1),
            ("5. Imposto sobre a renda retido na fonte (IRRF)", 1),
            (
                "6. Rendimentos isentos de pensao, proventos de aposentadoria ou reforma "
                "por molestia grave ou aposentadoria ou reforma por acidente em servico",
                2,
            ),
        ]

        for label, row_multiplier in rows:
            h = self.row_h * row_multiplier
            y = self.y - h
            self.rect(self.left, y, label_w, h)
            self.rect(self.left + label_w, y, value_w, h)
            self.set_font(False, 7)
            self.wrapped_text(
                self.left + 2 * mm,
                y + h - 3.6 * mm,
                label,
                label_w - 4 * mm,
                h - 2 * mm,
                7,
                False,
            )
            self.c.drawRightString(self.right - 1.5 * mm, y + h - 3.6 * mm, "0,00")
            self.y = y

        self.y -= 6 * mm

    def blank_box(self, h_mm=6):
        h = h_mm * mm
        y = self.y - h
        self.rect(self.left, y, self.right - self.left, h)
        self.y = y - 6 * mm

    def footer(self, responsavel_nome, data):
        self.section_title("8. Responsavel pelas Informacoes")
        total_w = self.right - self.left
        h = 8 * mm
        y = self.y - h
        widths = [0.50, 0.14, 0.36]
        labels = [("Nome", responsavel_nome), ("Data", data), ("Assinatura", "")]
        x = self.left
        for (label, value), ratio in zip(labels, widths):
            w = total_w * ratio
            self.rect(x, y, w, h)
            self.set_font(False, 7)
            self.c.drawString(x + 2 * mm, y + h - 3.2 * mm, label)
            self.text_fit(x + 2 * mm, y + 1.5 * mm, value, w - 4 * mm, 7, False)
            x += w
        self.y = y - 8 * mm
        self.set_font(False, 7)
        self.c.drawString(
            self.left,
            self.y,
            "Aprovado pela Instrucao Normativa RFB no 2.060, de 13 de dezembro de 2021.",
        )

    def save(self):
        self.c.showPage()
        self.c.save()


def render_informe_pdf(request: InformeRequest, totals: InformeTotals):
    pdf = InformePDF(request.output_pdf)
    pdf.header(request.exercicio, request.ano_calendario)
    pdf.section_title("1. Fonte Pagadora Pessoa Juridica ou Pessoa Fisica")
    pdf.cell2(
        [
            ("CNPJ/CPF", request.fonte_cnpj, 0.265),
            ("Nome Empresarial / Nome Completo", request.fonte_nome, 0.735),
        ]
    )
    pdf.y -= 6 * mm
    pdf.section_title("2. Pessoa Fisica Beneficiaria dos Rendimentos")
    pdf.cell2(
        [
            ("CPF", request.beneficiario_cpf, 0.265),
            ("Nome Completo", request.beneficiario_nome, 0.735),
        ]
    )
    pdf.natureza(request.natureza)

    pdf.section_title(
        "3. Rendimentos Tributaveis, Deducoes e Imposto sobre a Renda Retido na Fonte",
        "Valores em Reais",
    )
    pdf.value_table(
        [
            ("1. Total dos rendimentos (inclusive ferias).", totals.rendimentos, 1),
            ("2. Contribuicao previdenciaria oficial.", totals.previdencia, 1),
            (
                "3. Contribuicao a entidades de previdencia complementar, publica ou privada, "
                "e a Fundo de Aposentadoria Programada Individual - (Fapi) (preencher tambem "
                "o Quadro 7).",
                Decimal("0.00"),
                2,
            ),
            ("4. Pensao alimenticia (preencher tambem o Quadro 7).", Decimal("0.00"), 1),
            ("5. Imposto sobre a Renda Retido na Fonte (IRRF).", totals.irrf, 1),
        ]
    )

    pdf.section_title("4. Rendimentos Isentos e Nao Tributaveis", "Valores em Reais")
    pdf.value_table(
        [
            (
                f"{number}. {text}",
                totals.socio_microempresa if number == 6 else Decimal("0.00"),
                1 if number not in (1, 4) else 2,
            )
            for number, text in [
                (
                    1,
                    "Parcela isenta dos proventos de aposentadoria, reserva remunerada, "
                    "reforma e pensao (65 anos ou mais), exceto a parcela isenta do "
                    "13o salario.",
                ),
                (
                    2,
                    "Parcela isenta do 13o salario de aposentadoria, reserva remunerada, "
                    "reforma e pensao (65 anos ou mais).",
                ),
                (3, "Diarias e ajudas de custo."),
                (
                    4,
                    "Pensao e proventos de aposentadoria ou reforma por molestia grave; "
                    "proventos de aposentadoria ou reforma por acidente em servico.",
                ),
                (
                    5,
                    "Lucros e dividendos, apurados a partir de 1996, pagos por pessoa "
                    "juridica (lucro real, presumido ou arbitrado).",
                ),
                (
                    6,
                    "Valores pagos ao titular ou socio da microempresa ou empresa de pequeno "
                    "porte, exceto pro-labore, alugueis ou servicos prestados.",
                ),
                (
                    7,
                    "Indenizacoes por rescisao de contrato de trabalho, inclusive a titulo de "
                    "PDV e por acidente de trabalho.",
                ),
                (
                    8,
                    "Juros de mora recebidos, devidos pelo atraso no pagamento de remuneracao "
                    "por exercicio de emprego, cargo ou funcao.",
                ),
                (9, "Outros (especificar)."),
            ]
        ]
    )

    pdf.section_title(
        "5. Rendimentos Sujeitos a Tributacao Exclusiva (rendimento liquido)",
        "Valores em Reais",
    )
    pdf.value_table(
        [
            ("1. 13o (decimo terceiro) salario.", Decimal("0.00"), 1),
            (
                "2. Imposto sobre a Renda Retido na Fonte sobre 13o (decimo terceiro) salario.",
                Decimal("0.00"),
                1,
            ),
            ("3. Outros.", Decimal("0.00"), 1),
        ]
    )

    pdf.section_title(
        "6. Rendimentos Recebidos Acumuladamente - Art. 12-A da Lei no 7.713, de 1988 "
        "(sujeitos a tributacao exclusiva)"
    )
    pdf.accumulated_income_table()
    pdf.section_title("7. Informacoes Complementares")
    pdf.blank_box(5)
    pdf.footer(request.responsavel_nome, request.data)
    pdf.save()
