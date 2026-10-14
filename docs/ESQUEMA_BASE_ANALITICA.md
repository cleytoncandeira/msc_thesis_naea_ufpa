# Esquema da base analítica RTRS

Unidade principal: **documento de auditoria**. Uma certificação de grupo ou
multi-site pode abranger várias fazendas; por isso, localização e fazenda ficam
na relação separada `document_farm_locations.csv`.

| Grupo de colunas | Colunas | Uso |
|---|---|---|
| Chave e fonte | `document_id`, `document_path` | Identificação reprodutível do PDF. |
| Metadados extraídos | `enterprise_name`, `enterprise_type`, `certificate_code`, `issue_date`, `expiration_date`, `audit_date` | Caracterização da certificação e recorte temporal. |
| Áreas | `certified_soy_area_ha`, `certified_corn_area_ha`, `cultivated_soy_area_ha` e colunas `__numeric` | Medidas por cultura; nunca agregar soja e milho sem uma regra analítica explícita. |
| Rastreabilidade | colunas `__provenance`, `promotion_status`, `human_decision`, `review_excerpt` | Origem e forma de validação de cada valor. |
| Legado | `legacy_match_status`, `legacy_match_score`, `legacy_record_id`, colunas `legacy_*` | Base histórica, incluindo `Organization`, `Name`, `Year`, `Links`, `RegTag`, `Companies`, produção, área total, membros, tipo e os 28 critérios. |
| Espaço | `farm`, `state`, `city`, `latitude`, `longitude` em `document_farm_locations.csv` | Relação um-para-muitos com documentos ligados de forma segura. |

Não trate células vazias como zero. Não use `Total_Farm_Area` como substituto
para área certificada de soja ou milho.
