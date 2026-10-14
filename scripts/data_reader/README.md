# Pipeline de leitura de PDFs (data_reader)

Este diretório organiza as etapas de leitura, OCR, anotação e preparação de dataset
para os relatórios de auditoria da RTRS.

## Visão geral do fluxo

1. **Conversão de PDFs para imagens**
   - `pdf_processing.py` converte cada PDF em páginas JPG.
2. **Organização por empresa**
   - `report_organizer.py` usa OCR leve para identificar a empresa e mover os relatórios.
3. **Anotação manual**
   - `annotation_tool.py` abre as páginas e captura bounding boxes por variável.
4. **Geração de dataset OCR**
   - `ocr_dataset.py` transforma as anotações em JSONL com labels BIO.
5. **CLI de orquestração**
   - `cli.py` encadeia as etapas acima.

## Estrutura de pastas (padrão)

- `data/external_data/audit_reports` -> PDFs brutos
- `data/processed_data/audit_reports_database` -> páginas JPG por relatório
- `data/processed_data/organized_audit_reports` -> relatórios separados por empresa

Os caminhos podem ser sobrescritos com `--raw-dir`, `--images-dir` e `--organized-dir`.

## Exemplos de uso via CLI

Converter PDFs em imagens (DPI padrão 120):

```bash
python -m scripts.data_reader.cli --convert
```

Converter com DPI customizado e diretórios personalizados:

```bash
python -m scripts.data_reader.cli --convert --dpi 150 --raw-dir data/external_data/audit_reports --images-dir data/processed_data/audit_reports_database
```

Organizar por empresa:

```bash
python -m scripts.data_reader.cli --organize
```

Gerar estatísticas:

```bash
python -m scripts.data_reader.cli --stats --min-reports 5
```

Anotar relatórios (com limites e variáveis customizadas):

```bash
python -m scripts.data_reader.cli --annotate --variables-file scripts/data_reader/variables.json --limits-file scripts/data_reader/limits.json
```

Gerar dataset anotado (JSONL) com IOU:

```bash
python -m scripts.data_reader.cli --dataset --iou-threshold 0.5
```

## Arquivos de configuração (exemplos)

`variables.json`:

```json
["endereço", "cod_certificado", "validade_certificado", "nome_organização"]
```

`limits.json`:

```json
{"Control Union": 5, "SGS Argentina": 2, "Food Chain ID": 5}
```

## Observações

- `pdf2image` exige uma instalação do Poppler no sistema.
- `pytesseract` exige o Tesseract OCR instalado.
- `reader.py` é um script experimental de LayoutLMv2 (não é parte do pipeline principal).
