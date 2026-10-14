# Relatório de execução - Fase 2: recuperação documental

Data: 13 de outubro de 2026.

## O que foi identificado

- O acervo local contém 263 PDFs legados, todos legíveis pelo Poppler, mas apenas 217 hashes SHA-256 únicos. Existem 46 arquivos que repetem conteúdo de outro arquivo.
- O catálogo atual contém 263 registros entre 2018 e 2025 e 42 URLs repetidas.
- Os nomes legados `audit_report_rtrsN.pdf` não oferecem evidência suficiente para associar um PDF local a uma URL atual; essa associação permanece explicitamente como não verificada.
- Uma consulta HTTP `HEAD`, limitada a duas URLs, devolveu `200` e `application/pdf` para ambos os documentos. Não houve download novo nesta validação.

## O que foi implementado

- `src/rtrs_pipeline/documents.py`: inventário local com SHA-256, tamanho, páginas, quantidade de texto nativo e duplicatas; normalização do catálogo; e downloader HTTP retomável.
- `scripts/recover_documents.py`: interface para as operações locais `--inventory` e `--catalog-manifest`, e para download explícito (`--download`).
- `outputs/reports/document_manifest.csv`: 263 registros locais com estado e proveniência conhecida/desconhecida.
- `outputs/reports/catalog_manifest.csv`: 263 URLs normalizadas, com hash da URL e marcação de repetição.
- `docs/FASE_2_RECUPERACAO.md`: instruções de execução e limites operacionais.
- Testes legados de navegador/caminhos inexistentes foram substituídos por testes unitários sem rede; foi corrigido também o erro de importação no utilitário legado de coordenadas.

## Garantias do coletor novo

- limite de taxa compartilhado, concorrência configurável (padrão: 2), streaming e três tentativas com backoff exponencial;
- download temporário seguido de validação por assinatura `%PDF-` e `pdfinfo` antes de promover o arquivo ao destino;
- nomes estáveis derivados do hash da URL, em vez de índices de ordenação;
- retomada de arquivo já válido e log de cada resultado em `download_log.csv`;
- nenhuma tentativa de contornar bloqueios, autenticação, `robots.txt`, termos ou limites do servidor.

## Testes executados

- `python -m pytest -q`: **33 aprovados**.
- Inventário e normalização de catálogo: concluídos sem acessar a rede.
- Checagem de consistência: 263 documentos válidos, 217 hashes únicos, 42 URLs repetidas.
- Checagem HTTP mínima de duas URLs: ambas retornaram PDF válido via cabeçalho HTTP.

## Pendências e próximo passo

A Fase 2 está concluída para o acervo e catálogo disponíveis. Ela não estabelece uma associação histórica PDF--URL que a fonte original não registra. A Fase 3 deve criar a extração estruturada por página, iniciando por uma amostra estratificada de formatos de relatório e preservando para cada campo o PDF, a página, o trecho, o método e o status de validação.
