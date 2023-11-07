#### gerada com a query ####
WITH q_empresas AS (
  SELECT cnpj_basico, razao_social, natureza_juridica, capital_social, porte
  FROM `basedosdados.br_me_cnpj.empresas`
  WHERE ((
    LOWER(razao_social) LIKE '%bunge%'
    OR LOWER(razao_social) LIKE '%slc agricola%'
    OR LOWER(razao_social) LIKE '%ggf agro%'
    OR LOWER(razao_social) LIKE '%amaggi%'
    OR LOWER(razao_social) LIKE '%louis dreyfus%'
    OR LOWER(razao_social) LIKE '%clube amigos da terra%'
    OR LOWER(razao_social) LIKE '%agrosb%'
    OR LOWER(razao_social) LIKE '%agrex do brasil%'
    OR LOWER(razao_social) LIKE '%agricola xingu%'
  ) AND capital_social > 10000000)
  OR cnpj_basico IN ('05257285', '28141519', '05491108', '10795255', '17393890', '09409968', '87700746', '00969790', '02433189', '93540896')
  AND data = '2023-02-15'
), 
q_estab as ( 

SELECT 
  *
FROM `basedosdados.br_me_cnpj.estabelecimentos` estab
RIGHT JOIN q_empresas
ON estab.cnpj_basico = q_empresas.cnpj_basico
WHERE data = '2023-02-15')

SELECT distinct * 
from q_estab
