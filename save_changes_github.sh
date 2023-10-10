#!/bin/bash

# Verifica se foram fornecidos dois parâmetros posicionais
if [ $# -lt 2 ]; then
  echo "Erro: Forneça dois parâmetros posicionais: 'repositorio' e 'gitkey'"
  exit 1
fi

repositorio="$1"
gitkey="$2"
branch="${3:-main}" # Se o terceiro parâmetro não for fornecido, atribui o valor "main" a ele

# Adiciona o repositório remoto
git remote add repositorio "https://github.com/cleytoncandeira/$repositorio.git"
# Define a URL do repositório remoto com a chave Git
git remote set-url repositorio "https://$gitkey@github.com/cleytoncandeira/$repositorio.git"

# Exibe o resultado do comando git remote -v
echo "Resultado do comando 'git remote -v':"
git remote -v

# Executa o comando git push
echo "Resultado do 'git push':"
git push repositorio $branch

