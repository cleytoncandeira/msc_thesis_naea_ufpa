# Protocolo de revisão de metadados

Arquivo de trabalho: `outputs/validation/metadata_human_validation.csv`.

Cada linha é uma decisão sobre um candidato extraído, não sobre a qualidade geral do relatório. Leia `review_excerpt`, confira o valor e preencha as quatro colunas finais:

| Campo | Preenchimento |
|---|---|
| `human_decision` | `accept`, `reject`, `correct` ou `ambiguous`. |
| `selected_value_raw` | Obrigatório para `accept`: o candidato exato que foi confirmado. |
| `corrected_value` | Obrigatório quando a decisão é `correct`; caso contrário, deixe vazio. |
| `reviewer` | Identificador do revisor. |
| `review_notes` | Motivo curto, especialmente para rejeição, ambiguidade ou conflito. |

## Regras de decisão

- `accept`: o trecho e a página sustentam exatamente o valor extraído.
- `reject`: o trecho não sustenta o valor, o rótulo é falso positivo ou pertence a outro campo.
- `correct`: o campo está presente, mas o valor deve ser substituído pelo valor em `corrected_value`.
- `ambiguous`: o trecho não permite resolver a interpretação; não adivinhe.

Não use conhecimento externo ao relatório. Em documentos multi-site ou grupo, registre em nota se o valor se aplica ao certificado, ao grupo ou a uma fazenda específica.

Uma decisão só entra nas métricas quando está semanticamente completa: `accept` sem
`selected_value_raw` e `correct` sem `corrected_value` são exportados para
`metadata_review_issues.csv`, mas não contam como revisão utilizável.

Após salvar o arquivo, execute:

```bash
.venv/bin/python scripts/check_metadata_review.py
```

O comando grava `metadata_review_progress.json` e, havendo decisões preenchidas, `metadata_review_metrics.csv`. A regra de promoção de campos à base final só será definida depois de observar essas métricas por campo e por formato de relatório.

## Áreas por cultura

Em `crop_area_human_validation.csv`, os campos de soja e milho representam
medidas distintas. Não some as culturas e não transfira um valor de milho para
soja (ou o inverso). Quando há mais de uma safra/página, selecione o valor
explicitamente associado ao escopo certificado ou use `ambiguous`.
