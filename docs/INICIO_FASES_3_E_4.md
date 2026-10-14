# Início das Fases 3 e 4

## Implementado neste ciclo

- Extração de texto nativo por página (`outputs/intermediate/pages_native.jsonl`), com hash do PDF, página, método e status.
- Evidência candidata de cada ocorrência explícita dos 28 critérios (`criterion_evidence_candidates.jsonl`). Uma ocorrência não é rótulo de conformidade.
- Registro de processamento e fila de revisão para OCR. OCR permanece seletivo e não foi executado em massa.
- Parser de pares explícitos `['característica', 'yes/no']` nas saídas LLaMA históricas, sem convertê-los em escore.
- Amostra determinística de 80 registros para rotulagem humana nas cinco classes: `favorable`, `contrary`, `insufficient`, `not_applicable`, `ambiguous`.

## Limite científico atual

O parser histórico encontra padrões no texto salvo, mas o arquivo mistura prompt e geração. Por isso o resultado é somente uma fonte de revisão humana; não é uma reprodução aceita do escore LLaMA. A classificação modernizada só poderá ser comparada após a anotação humana e o cálculo de métricas.

## Próximas entregas

1. Revisar visualmente a fila de OCR e aplicar OCR somente às páginas de conteúdo que realmente precisarem.
2. Amostrar formatos de auditoria e implementar extratores determinísticos para metadados, cada qual com trecho e página de suporte.
3. Preencher e revisar a amostra humana; só então avaliar classificador/modelo com precisão, recall e F1.
