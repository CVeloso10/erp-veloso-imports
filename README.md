# ERP Veloso Imports ⚽

Sistema de Gestão de Estoque e Finanças construído para controle logístico e contábil de um e-commerce de camisas de futebol.

## Tecnologias Utilizadas
* **Back-end:** Python, FastAPI, SQLAlchemy
* **Front-end:** Streamlit
* **Banco de Dados:** SQLite

## Arquitetura
O sistema utiliza uma arquitetura baseada em Lotes (Master-Detail) com cálculo dinâmico de Custo da Mercadoria Vendida (CMV), rateio automático de taxas alfandegárias/frete e validação condicional para vendas de pronta entrega vs. dropshipping.

## Como executar localmente
1. Instale as dependências: `pip install -r requirements.txt`
2. Inicie a API: `uvicorn main:app`
3. Em outro terminal, inicie a interface: `streamlit run app.py`