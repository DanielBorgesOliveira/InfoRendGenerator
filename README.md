# Gerador de Informe de Rendimentos

Gera um informe de rendimentos em PDF a partir de um extrato OFX ou XLSX.

## Estrutura

```text
src/info_rend_generator/
|-- cli.py
|-- application/
|   `-- generate_informe.py
|-- config/
|   `-- defaults.py
|-- domain/
|   |-- informe.py
|   |-- money.py
|   `-- transactions.py
`-- infrastructure/
    |-- audit_excel_exporter.py
    |-- excel_reader.py
    |-- ofx_reader.py
    `-- pdf_reportlab_renderer.py
```

- `domain`: modelos e regras puras de dinheiro, transacoes e totais.
- `application`: caso de uso que coordena leitura, calculo e geracao do PDF.
- `infrastructure`: adaptadores externos, como leitura de OFX/XLSX e renderizacao com ReportLab.
- `cli.py`: interface de linha de comando.

## Uso

```powershell
python gerar_informe_rendimentos.py --input-file data\extrato.ofx --output-pdf data\informe.pdf --ano-calendario 2025
```

Tambem e possivel usar uma planilha Excel com colunas `Data Lançamento`, `Descrição`,
`Valor`, `TipoTransacao` e `ClassificacaoContabil`:

```powershell
python gerar_informe_rendimentos.py `
  --input-file data\Extrato-01-01-2025-a-31-12-2026.xlsx `
  --output-pdf data\informe.pdf `
  --ano-calendario 2025 `
  --rendimentos-keyword "PRO-LABORE"
```

Nesse XLSX, a coluna `ClassificacaoContabil` entra no campo pesquisavel da transacao. Por
exemplo, `--rendimentos-keyword "PRO-LABORE"` soma os pagamentos classificados como
pro-labore. Se a planilha agrupar INSS e IRRF na mesma classificacao, use valores manuais
para separar os campos finais quando necessario.

Os pagamentos classificados como `ANTECIPAÇÃO DE DIVIDENDOS` sao somados automaticamente
na linha 6 de rendimentos isentos: valores pagos ao titular ou socio da microempresa/EPP.

Depois de instalar o projeto:

```powershell
gerar-informe --input-file data\extrato.ofx --output-pdf data\informe.pdf --ano-calendario 2025
```

## Argumentos da CLI

Formato geral:

```powershell
python gerar_informe_rendimentos.py --output-pdf OUTPUT_PDF [--input-file INPUT_FILE] [opcoes]
```

### Arquivos

`--input-file`

Caminho opcional do arquivo OFX ou XLSX de entrada. Informe este argumento para
calcular valores automaticamente a partir das transacoes. Omita este argumento
quando for preencher todos os valores manualmente.

Exemplo:

```powershell
data\Extrato-01-01-2025-a-31-12-2026.xlsx
```

`--output-pdf`

Caminho obrigatorio onde o PDF gerado sera salvo.

Exemplo:

```powershell
data\informe.pdf
```

### Dados do informe

`--exercicio`

Ano de exercicio exibido no PDF.

Padrao: `2026`

Exemplo:

```powershell
--exercicio 2026
```

`--ano-calendario`

Ano-calendario usado para filtrar as transacoes do OFX.

Padrao: `2025`

Exemplo:

```powershell
--ano-calendario 2025
```

`--fonte-cnpj`

CNPJ ou CPF da fonte pagadora.

Exemplo:

```powershell
--fonte-cnpj "33.352.491/0001-99"
```

`--fonte-nome`

Nome da empresa ou pessoa pagadora.

Exemplo:

```powershell
--fonte-nome "GRANUFLOW ENGENHARIA LTDA"
```

`--beneficiario-cpf`

CPF da pessoa beneficiaria dos rendimentos.

Exemplo:

```powershell
--beneficiario-cpf "971.453.760-67"
```

`--beneficiario-nome`

Nome da pessoa beneficiaria dos rendimentos.

Exemplo:

```powershell
--beneficiario-nome "GUMERCINDO DA SILVA SAURO"
```

`--responsavel-nome`

Nome da pessoa responsavel pelas informacoes.

Exemplo:

```powershell
--responsavel-nome "BRUNO ALEXANDRE GUEDES CHAVES"
```

`--data`

Data exibida na secao de assinatura.

Padrao: data atual.

Exemplo:

```powershell
--data "28/02/2026"
```

`--natureza`

Natureza do rendimento exibida no PDF.

Padrao: `RENDIMENTO DO TRABALHO ASSALARIADO NO PAIS`

Exemplo:

```powershell
--natureza "RENDIMENTO DO TRABALHO ASSALARIADO NO PAIS"
```

### Deteccao automatica pelo OFX

`--rendimentos-keyword`

Palavra-chave usada para encontrar transacoes de rendimento no OFX. Pode ser repetida.

Exemplo:

```powershell
--rendimentos-keyword "PRO-LABORE"
```

Com multiplas palavras-chave:

```powershell
--rendimentos-keyword "PRO-LABORE" --rendimentos-keyword PAGAR
```

Quando varias palavras-chave sao informadas, a transacao precisa conter todas elas no nome ou memo.

`--rendimentos-positivos`

Por padrao, os rendimentos sao somados a partir de transacoes negativas. Use esta flag se os rendimentos aparecem como creditos positivos no OFX.

Exemplo:

```powershell
--rendimentos-positivos
```

`--previdencia-keyword`

Palavra-chave usada para encontrar contribuicoes previdenciarias oficiais. Pode ser repetida.

Exemplo:

```powershell
--previdencia-keyword INSS
```

`--irrf-keyword`

Palavra-chave usada para encontrar imposto de renda retido na fonte. Pode ser repetida.

Exemplo:

```powershell
--irrf-keyword "RECEITA FEDERAL"
```

`--exceto-prolabore-keyword`

Palavra-chave usada para encontrar valores isentos pagos ao titular ou socio da
microempresa/EPP, exceto pro labore, alugueis ou servicos prestados. Pode ser
repetida.

Padrao: `ANTECIPACAO DE DIVIDENDOS`

Exemplo:

```powershell
--exceto-prolabore-keyword "ANTECIPACAO DE DIVIDENDOS"
```

### Valores manuais

Os valores manuais substituem o calculo automatico pelo OFX.
Quando todos os valores forem informados manualmente, `--input-file` pode ser
omitido.

`--valor-rendimentos`

Valor manual do total de rendimentos tributaveis.

Exemplo:

```powershell
--valor-rendimentos 71.900,00
```

`--valor-exceto-prolabore`

Valor manual para a linha 6 de rendimentos isentos: valores pagos ao titular ou
socio da microempresa/EPP, exceto pro labore, alugueis ou servicos prestados.

Exemplo:

```powershell
--valor-exceto-prolabore 71.900,00
```

`--valor-previdencia`

Valor manual da contribuicao previdenciaria oficial.

Exemplo:

```powershell
--valor-previdencia 7.909,00
```

`--valor-irrf`

Valor manual do imposto de renda retido na fonte.

Exemplo:

```powershell
--valor-irrf 6.753,26
```

### Auditoria em Excel

`--audit-excel`

Caminho opcional para gerar uma planilha Excel de auditoria.

Exemplo:

```powershell
--audit-excel data\auditoria.xlsx
```

A planilha gerada tem tres abas:

- `summary`: caminhos de entrada/saida, filtros usados, totais automaticos, valores manuais e valores finais.
- `transactions`: transacoes parseadas do arquivo de entrada, flags de match e tipo de valor incluido.
- `raw_data`: dados brutos extraidos do arquivo de entrada.

## Exemplo completo

```powershell
python gerar_informe_rendimentos.py `
  --input-file data\Extrato-01-01-2025-a-31-12-2026-OFX.ofx `
  --output-pdf data\informe.pdf `
  --exercicio 2026 `
  --ano-calendario 2025 `
  --fonte-cnpj "33.352.491/0001-99" `
  --fonte-nome "GRANUFLOW ENGENHARIA LTDA" `
  --beneficiario-cpf "971.453.760-67" `
  --beneficiario-nome "GUMERCINDO DA SILVA SAURO" `
  --responsavel-nome "BRUNO ALEXANDRE GUEDES CHAVES" `
  --data "28/02/2026" `
  --valor-rendimentos 71.900,00 `
  --valor-previdencia 7.909,00 `
  --valor-irrf 6.753,26 `
  --audit-excel data\auditoria.xlsx
```
