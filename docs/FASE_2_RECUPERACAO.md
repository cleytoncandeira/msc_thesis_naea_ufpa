# Fase 2 - recuperação documental

O comando `scripts/recover_documents.py` separa três operações deliberadas:

```bash
# Operações locais, sem rede e sem modificar PDFs
.venv/bin/python scripts/recover_documents.py --inventory --catalog-manifest

# Operação de rede explícita: só execute após revisar o catálogo e o limite escolhido
.venv/bin/python scripts/recover_documents.py --download --workers 2 --min-interval 0.5
```

Os manifestos são gravados em `outputs/reports/`:

- `document_manifest.csv`: hash SHA-256, tamanho, páginas, texto nativo, duplicidade e estado de cada PDF local;
- `catalog_manifest.csv`: catálogo de URLs normalizado, com hash da URL e marcação de URLs repetidas;
- `download_log.csv`: resultado de cada operação de download.

Arquivos legados `audit_report_rtrsN.pdf` são explicitamente marcados como `unlinked_legacy_filename`. O pipeline não infere URL de origem apenas pelo número do nome. Novos downloads recebem um nome estável derivado do hash da URL, são gravados primeiro em arquivo temporário e só passam ao destino após validação por assinatura PDF e `pdfinfo`.

O downloader usa sessão HTTP, streaming, até três tentativas com backoff exponencial, limite de frequência compartilhado, concorrência controlada, verificação de PDFs preexistentes e log de falhas. Ele não contorna autenticação, bloqueios, robots.txt, termos de uso ou limites do servidor.
