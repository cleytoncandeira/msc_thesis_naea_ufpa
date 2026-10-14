# Revisão de vínculos históricos

Arquivo de trabalho: `outputs/validation/legacy_linkage_human_validation.csv`.

Cada linha pergunta se um **relatório PDF atual** corresponde a uma linha da
base histórica `brazil_rtrs.csv`. Isto não é revisão do conteúdo do relatório,
nem dos critérios RTRS.

Preencha `link_decision` assim:

| Decisão | Quando usar | O que preencher |
|---|---|---|
| `accept` | O candidato proposto é o mesmo certificado/organização e ano. | Deixe `selected_legacy_record_id` vazio. |
| `correct` | Outra opção em `candidate_options` é a linha histórica correta. | Copie o `id=` dessa opção para `selected_legacy_record_id`. |
| `reject` | Nenhuma das opções corresponde ao relatório. | Escreva o motivo em `review_notes`. |
| `ambiguous` | Não é possível decidir com a informação exibida. | Escreva o que falta em `review_notes`. |

Compare principalmente: nome da organização/fazenda, ano do documento, código
do certificado e link histórico. Não escolha por semelhança de nome apenas.
