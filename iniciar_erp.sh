#!/bin/bash

# Vai para a pasta do projeto
cd /home/cristhian/Documents/dev/estoque-camisas

# Ativa o ambiente virtual
source .venv/bin/activate

echo "Iniciando o Back-end (API)..."
uvicorn main:app --port 8000 &
API_PID=$!

# Garante que a API seja desligada automaticamente se você fechar o terminal
trap "kill $API_PID" EXIT

# Aguarda 2 segundos para a API subir completamente
sleep 2

echo "Iniciando o Front-end (Streamlit)..."
streamlit run app.py
