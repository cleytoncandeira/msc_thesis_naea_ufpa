# Análise dos Relatórios de Auditoria da Round Table on Responsible Soy (RTRS)

Este repositório documenta um projeto de pesquisa voltado a avaliar os efeitos econômicos e financeiros que a certificação **RTRS (Round Table on Responsible Soy)** pode trazer para empresas certificadas na Amazônia, especificamente. Por meio de uma abordagem sistemática de coleta, extração e análise de dados, buscou-se identificar se e como a certificação impacta a competitividade das organizações no mercado de soja responsável.

---

## Contexto do Problema

A RTRS disponibiliza, de maneira pública, relatórios de auditoria que descrevem o nível de conformidade das empresas em relação aos princípios e critérios de sustentabilidade. Esses relatórios podem ser acessados no site oficial:  
[https://responsiblesoy.org/public-audit-reports?lang=en](https://responsiblesoy.org/public-audit-reports?lang=en)

A **questão central** da pesquisa consiste em investigar quais **efeitos econômicos-financeiros** a certificação da RTRS produz nas empresas que adotam seus critérios. Ao identificar, classificar e analisar os dados provenientes dos relatórios, é possível verificar o grau de conformidade de cada empresa e, cruzando com demais bases de dados, correlacionar possíveis ganhos (ou prejuízos) decorrentes da certificação.

---

## Metodologia de Resolução

1. **Coleta de Dados (Web Scrapping)**  
   - **Tarefa 1**: Desenvolvi um algoritmo *web scrapping* para coletar os relatórios de auditoria públicos disponibilizados pela RTRS e armazená-los em um repositório aberto, hospedado em uma conta do Google Drive.  

2. **Extração e Transformação de Informações**  
   - **Tarefa 2**: Extrair dados dos arquivos PDF coletados (por exemplo, localização geográfica, datas, indicadores de conformidade e outras variáveis de auditoria).  
   - As informações foram convertidas em uma **base de dados** unificada, que permite consultas, atualizações e análises estatísticas.  
   - Técnicas de raspagem de texto (OCR, parsing de PDF, etc.) foram empregadas para assegurar a integridade e a consistência dos dados.

3. **Análise por LLM (Large Language Models)**  
   - **Tarefa 3**: Utilizou-se de um modelo de LLM para realizar análise de texto, identificando se as empresas cumprem ou deixam de cumprir cada princípio estabelecido pela RTRS.  

---

## Estrutura do Repositório

- `data/`  
  Contém a base de dados consolidada extraída dos PDFs.  
- `scripts/`  
  Inclui os códigos de *web scrapping*, extração, limpeza e transformação dos dados.  
- `notebooks/`  
  Abriga os notebooks ou arquivos relativos às análises estatísticas e ao uso de LLM para avaliação de conformidade.
- `tests/`  
  Abriga os testes necessários dos scripts.
- `README.md`  
  Este arquivo, oferecendo uma visão geral do projeto, do problema e dos objetivos.

---

## Como Contribuir

1. **Clonar ou fazer *fork*** deste repositório.  
2. **Instalar as dependências** `requirements.txt`
3. **Enviar *Pull Requests*** ou **abrir *issues*** com sugestões de melhorias, correções ou recursos adicionais.  

---

## Referências e Contato

- **Round Table on Responsible Soy (RTRS)**  
  [https://responsiblesoy.org/](https://responsiblesoy.org/)
- **Relatórios Públicos de Auditoria**  
  [https://responsiblesoy.org/public-audit-reports?lang=en](https://responsiblesoy.org/public-audit-reports?lang=en)

Para dúvidas ou esclarecimentos adicionais, sinta-se à vontade para criar uma *issue* neste repositório ou entrar em contato diretamente com o autor.  
