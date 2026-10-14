# Diagnóstico técnico - Fase 1

Data da auditoria: 13 de outubro de 2026. Escopo: diagnóstico somente. Nenhum download em massa, modelo grande, notebook completo ou refatoração foi executado.

## Síntese executiva

O repositório conserva evidência valiosa da pesquisa: a dissertação, 263 PDFs válidos, uma base histórica de 128 empreendimentos/relatórios (2018--2023), os 28 textos de critérios e resultados já produzidos. Porém, ele **não é hoje um pipeline reproduzível ponta a ponta**. Há três linhas de trabalho parcialmente sobrepostas:

1. coleta por Selenium (`scripts/data_scrapping`);
2. OCR/annotação/LayoutLM experimental (`scripts/data_reader`);
3. notebooks Kaggle para LLaMA 2, BERT, TF-IDF e análises estatísticas.

O principal achado metodológico é que a dissertação atribui os escores ao LLaMA 2, mas o único código que calcula escores numéricos, correlação e PCA no repositório é o notebook de **BERT de sentimento sem fine-tuning**. O notebook LLaMA produz texto livre e não contém o parser nem a regra de conversão `sim/não -> escore`. Portanto, os resultados históricos devem ser preservados e tratados como artefatos de referência, não como uma reprodução ainda demonstrada.

## Inventário e estado dos artefatos

| Grupo | Artefatos | Estado e função |
|---|---:|---|
| Dissertação | `references/rtrs_na_amazonia_cleyton_versao_REVISADA.pdf`, 78 páginas | Íntegra; seções 1.2, 1.3 e Anexo 1 conferidos por extração e renderização visual. |
| PDFs brutos | 263 em `data/external_data/audit_reports/` | 263/263 abrem no Poppler; 6.838 páginas, mediana 18, intervalo 7--106. Há 46 grupos de hashes repetidos: a deduplicação é necessária. |
| Manifesto recente | `certified_producers_rtrs.csv`, 263 linhas | Catálogo atual de links; não há manifest histórico que associe de modo verificável cada nome sequencial `audit_report_rtrsN.pdf` à URL e ao hash baixado. |
| Base histórica principal | `processed_data/brazil_rtrs*.csv`, 128 x 40 | 12 variáveis cadastrais + 28 critérios. Há versões base, PT-BR e EN com mesma forma; a codificação exibida pelo shell sugere legado Latin-1/ISO-8859-14. |
| Estrutura fundiária | `farm_branches.csv`, 866 x 7 | 74 linhas exatamente duplicadas; faltantes residuais em `State`/`City`; sem chave explícita. |
| Prompts | `prompt_eng_rtrs.csv`, 28 x 4 | 28 linhas, mas só 27 valores únicos em `Criteria`; requer auditoria de duplicidade/ordem antes de reutilização. |
| Saída LLaMA | `llama2_result.csv`, 128 x 29 | Texto gerado por critério, sem esquema estruturado nem metadados de modelo, seed, versão ou parâmetros completos. |
| Saída de escores | `brazil_rtrs_sentiment_analysis.csv`, 128 x 44 | Inclui `score_per_enterprise`, `Yield` e `cluster`; a produção vem do notebook BERT. |
| Dados de LayoutLM | `datasets/foodchain_extracted.csv`, 87 x 43 | Protótipo: colunas de critérios estão 100% vazias; não é base operacional de extração. |
| Imagens/OCR | `processed_data/audit_reports_database/`, `organized_audit_reports/` | Artefatos grandes de OCR e organização por auditor; úteis como amostra, mas sem vínculo documentado a PDF/hash/página/origem. |

`data/ready_data/` duplica byte a byte os principais CSVs de `data/processed_data/`; deve deixar de ser uma segunda fonte de verdade após a migração, mas não deve ser apagada nesta fase.

## Dependências e capacidade observada

### Ambiente encontrado

- Ubuntu 24.04, kernel 7.0.0-38; Python 3.12.3.
- AMD Ryzen 5 5500U: 6 núcleos / 12 threads; GPU integrada AMD Lucienne, sem GPU dedicada nem VRAM dedicada detectável; NVMe de 238,5 GB, 117 GB livres.
- RAM física: 5,6 GiB; disponível na medição: 1,9 GiB; swap de 4 GiB, 2 GiB livres.
- Google Chrome 155 e Tesseract 5.3.4 estão disponíveis.
- O `.venv` instala o conjunto mínimo declarado (pandas, Selenium, PDF2Image, Tesseract, OpenCV), mas não PyMuPDF, pypdf, transformers, torch, scikit-learn, scipy, datasets ou langchain. Estes últimos aparecem nos notebooks e não estão travados em `requirements.txt`.

| Etapa | CPU/RAM observados | GPU | Estratégia local recomendada |
|---|---|---|---|
| Catálogo/download | baixo / <1 GiB | dispensável | HTTP concorrente limitado a 2--4 conexões, retentativas e cache. |
| Extração textual digital | moderado / 1--2 GiB | dispensável | PyMuPDF por PDF, streaming e persistência por página. |
| OCR seletivo | alto / 1--3 GiB | opcional | Tesseract em lotes de 1--2 PDFs, somente páginas sem texto. |
| Tabulação/validação | baixo / <2 GiB | dispensável | pandas/Parquet, processar por lote e testar chaves. |
| LLM 7B | inviável de forma segura na configuração medida | sem aceleração utilizável | não executar LLaMA 2 7B localmente. |
| Classificador compacto | moderado / 2--4 GiB conforme modelo | dispensável | somente após benchmark; CPU, lote 1 e cache. |
| Estatística/PCA | baixo / <2 GiB | dispensável | execução local com versões travadas e sementes fixas. |

O gargalo real é RAM, não armazenamento. Antes de qualquer modelo, feche aplicações pesadas e registre novamente memória disponível. Um 7B quantizado ainda é uma escolha de alto risco para esta máquina; LLaMA 2 histórico deve ser reproduzido apenas onde já for viável e identificável, não instalado agora.

## Metodologia do Capítulo 1 e correspondência computacional

| Metodologia descrita | Evidência na dissertação | Implementação encontrada | Diagnóstico |
|---|---|---|---|
| Coleta de 378 PDFs e duas bases CSV | seção 1.3 | `BotDriver`, CSVs e corpus atual de 263 PDFs | O corpus e a amostra histórica divergem; faltam versão de coleta e mapa PDF--URL. |
| 12 metadados do relatório + 28 critérios | Quadro 1, Anexo 1 | `brazil_rtrs.csv` (12 + 28 colunas) | Boa preservação da forma histórica; falta proveniência de cada campo/página/trecho. |
| `farm_branches` para grupo, multisite e individual | Quadro 2 | `farm_branches.csv` | Presente, mas sem chaves, com duplicidades e com geocodificação não reprodutível. |
| LLaMA 2 identifica características e responde `['característica','sim/não']` | seção 1.2.3 | `llama2-content-analysis.ipynb` | Prompt e modelo são recuperáveis; saída é texto livre, amostragem está ativa e não há parser/versionamento. |
| Contar sim/não para escore por critério, princípio e empreendimento | seções 1.2.3 e 1.3 | Ausente no notebook LLaMA | Lacuna crítica: não é possível reproduzir o cálculo LLaMA exato só com o repositório. |
| Escores, correlações, PCA e classificação discursiva | seção 1.3, Figuras 3--6 e Tabelas 1--2 | `bert-sentiment-analysis-and-pca.ipynb` | Implementa BERT de sentimento, mapeia -2..2, soma, Spearman e PCA; diverge da descrição de LLaMA/sim-não e do texto que menciona Pearson. |
| Alternativas TF-IDF/cosseno | notebooks exploratórios | `tf-idf-and-correlations.ipynb`, `cosine_similarity.csv` | Exploratória, sem vínculo demonstrado aos resultados do capítulo. |
| Extração por layout | notebooks/código LayoutLM | `reader.py`, `extracting_data_lmv.ipynb`, dataset Food Chain ID | Protótipo de anotação/OCR; não alimenta `brazil_rtrs.csv` de modo rastreável. |

### Fluxo histórico recuperado

```text
RTRS web page --Selenium--> certified_producers_rtrs.csv --requests-->
audit_report_rtrsN.pdf --PDF para JPG/OCR--> organização/anotação (experimental)
                                                     |
                                                     v
                     rtrs_brazil.csv (128 x 40; origem de extração não recuperada)
                          + prompt_eng_rtrs.csv (28 prompts)
                                                     |
                         LLaMA 2 7B (Kaggle) --> llama2_result.csv (texto livre)
                                                     ?  [parser/escore ausente]

rtrs_brazil.csv --> BERT de sentimento --> -2..2 por critério --> somas/PCA/cluster
                                      --> brazil_rtrs_sentiment_analysis.csv
```

O notebook LLaMA ainda declara `do_sample=True` e `top_k=10`, embora o wrapper mencione temperatura zero. Isso torna a inferência não determinística; não há seed, `model_revision`, versão de bibliotecas ou configuração completa salva. No código mostrado, o laço seleciona `[:64]` observações, mas o CSV salvo contém 128 linhas, outra inconsistência que precisa ser explicada por histórico de execução antes de qualquer comparação numérica.

### Fluxo recomendado (separando história e modernização)

```text
manifesto versionado (URL, data, hash, status)
  -> PDF validado e deduplicado
  -> classificação por página: texto digital / OCR / misto / erro
  -> texto por página + coordenadas + método + hash
  -> extração determinística de cadastro e de blocos dos 28 critérios
  -> tabelas normalizadas: documento, certificado, empreendimento, fazenda, critério, evidência
  -> validações de integridade e amostra humana
  -> [histórico] parser reconstruído + LLaMA 2, se executável e auditável
  -> [moderno] classificador validado, determinístico e versionado
  -> escores com regra explícita -> correlações/PCA -> regras conceituais de discurso
```

As camadas devem permanecer separadas: (1) localizar/extrair fato documental, (2) classificar evidência de conformidade em favorável, contrária, insuficiente, não aplicável ou ambígua, e (3) interpretar posição discursiva. Ausência de texto não é não conformidade.

## Problemas priorizados

### Bloqueadores de reprodutibilidade

1. Não existe ligação verificável entre PDF bruto, URL de origem, metadados extraídos, página/trecho e linha da base histórica.
2. A regra que transforma geração LLaMA em pontos não está no repositório; a execução de BERT usa uma tarefa de sentimento genérico como substituto conceitualmente diferente.
3. Ambiente insuficientemente especificado: não há `pyproject.toml`/lockfile e faltam dependências usadas pelos notebooks.
4. Notebooks dependem de caminhos absolutos locais ou de Kaggle e misturam exploração, resultado e visualização.
5. A definição temporal diverge: tese informa 378 PDFs; corpus atual contém 263; base histórica contém 128 linhas, cobrindo 2018--2023.

### Erros e riscos técnicos

1. A coleta usa Selenium para a página e `requests` sequencial para arquivos. Não há rate limit, backoff, hash, validação de PDF, log de falhas, retomada, nem prevenção de nomes sequenciais ambíguos.
2. `download_all_reports()` chama todo arquivo de `audit_report_rtrs{i}.pdf`; ao reexecutar com outra ordem, preserva o nome existente e pode associá-lo a outra URL sem detectar o conflito.
3. O pipeline PDF converte indiscriminadamente todos os PDFs em imagens e depois faz OCR; não tenta texto nativo primeiro, desperdiçando CPU e degradando conteúdo digital.
4. O `LayoutLMv2ForTokenClassification` é carregado sem checkpoint fine-tuned compatível para os rótulos; as labels resultantes não têm semântica confiável. O seu dataset de treinamento disponível tem campos vazios.
5. `farm_branches.csv` tem 74 duplicidades completas. Chaves, normalização de empresa/fazenda e regras de múltiplos empreendimentos ainda não existem.
6. `clean_up_loc_farms.py` escreve fora do bloco `if __name__ == '__main__'`; só importá-lo causa `NameError` e impede a coleta do pytest. Ele também contém caminhos absolutos e lógica geográfica que força sinal negativo.
7. `get_city_state_loc.py` contém uma credencial de Google Maps no código. Ela deve ser revogada/rotacionada e removida do histórico público antes de qualquer uso futuro; uma variável de ambiente não deve ser registrada no repositório.
8. Há rotinas de geocodificação sem timeout, tratamento de rate limit, cache ou licença/custo documentados.
9. O teste completo não passa: 1 erro na coleta por `clean_up_loc_farms`; em execução parcial, 20 passam e 7 falham. Os sete são principalmente testes de integração inválidos/obsoletos (drivers `path/to/...`, métodos removidos do Selenium e servidor HTTP inexistente); há também um descompasso do mock no teste de pop-up.
10. A tese descreve Pearson para ao menos uma correlação, enquanto o notebook BERT usa Spearman; isso requer uma decisão explícita na reprodução histórica, não uma troca silenciosa.

## Tecnologias: manter, substituir, incorporar

| Decisão | Tecnologia | Justificativa |
|---|---|---|
| Manter | pandas, BeautifulSoup, requests (transitoriamente), Tesseract, pytest, CSV histórico | São adequados ou necessários para compatibilidade; consolidar versões e uso. |
| Substituir gradualmente | Selenium + WebDriver Manager como primeira opção; `pdf2image` + OCR para todo PDF; notebooks como execução oficial | Usar HTTP/HTML quando a página permitir; texto nativo antes de OCR; migrar etapas oficiais para módulos/CLI testáveis. |
| Incorporar, após autorização | `httpx` ou `requests` com sessão/retry; PyMuPDF; pypdf; Parquet (`pyarrow`); `pandera` ou validações próprias; `pytest` com fixtures locais | Cobrem catálogo, integridade, extração com páginas, armazenamento e testes sem dependências remotas. |
| Avaliar, não instalar/executar ainda | modelos compactos multilíngues ou classificador supervisionado; quantização | Só após criação de amostra manual e benchmark. LLaMA 2 7B permanece trilha histórica, não padrão local. |
| Não usar como classificador de conformidade | BERT de sentimento genérico sem fine-tuning | Polaridade afetiva não equivale a evidência de conformidade RTRS. Pode ser mantido como comparação exploratória rotulada. |

## Plano por fases e critérios de aceitação

| Fase | Prioridade e entrega | Critério objetivo de aceitação |
|---|---|---|
| 1. Diagnóstico | Inventário, mapa metodológico, capacidade, riscos (esta entrega) | Diagnóstico versionado; testes e medições registrados; sem mudanças no pipeline. |
| 2. Recuperação | Manifesto de documentos e coletor resiliente; classificação PDF | Amostra controlada baixa/retoma sem duplicar; cada PDF tem URL, hash, status e validação; teste com respostas HTTP simuladas. |
| 3. Estruturação | Extração por página e tabelas normalizadas | Cada campo extraído possui documento, página, trecho, método e status; testes de chaves, tipos, duplicidade e 28 critérios. |
| 4. PLN | Trilhas histórica e modernizada, protocolo de anotação | Parser histórico documentado ou lacuna declarada; conjunto humano de validação; precisão/recall/F1 e matriz de confusão por classe. |
| 5. Análise | Tabelas/figuras de critérios, empreendimento, princípios, correlação e PCA | Código com seed e parâmetros gera artefatos versionados; diferenças para a tese são tabuladas, não mascaradas. |
| 6. Validação | Relatório final de reprodução | Proveniência completa, testes verdes, comparação histórico/modernizado e limitações explícitas. |

## Primeira intervenção proposta (aguardando autorização)

Implementar somente a fundação de proveniência e integridade documental, sem baixar novos arquivos: criar uma estrutura `src/` mínima e um comando de inventário que lê os 263 PDFs locais, produz um manifesto versionado (nome atual, SHA-256, páginas, tamanho, texto nativo por página, duplicidade e status) e conserva os CSVs e scripts originais intactos. O comando incluirá testes com pequenos PDFs/fixtures e não instalará nem executará modelos.

Isso resolve primeiro a ambiguidade que bloqueia todas as fases seguintes: saber precisamente quais documentos existem e como eles se relacionam - ou ainda não se relacionam - às bases históricas.

## Evidências de verificação realizadas

- `pdfinfo` validou 263/263 PDFs; a extração com `pdftotext` em amostras confirmou texto nativo significativo.
- As páginas metodológicas da dissertação foram renderizadas e inspecionadas visualmente, além de extraídas em texto.
- `python -m scripts.data_reader.cli --dry-run --stats` executou sem escrita operacional.
- `pytest -q` foi executado: a coleta falha durante a importação de `clean_up_loc_farms.py`. Excluindo essa coleta, foram observados 20 testes aprovados e 7 falhos pelos problemas acima.
