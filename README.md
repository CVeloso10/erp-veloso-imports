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

## Integração com Desktop (Linux/Ubuntu)

Para criar um atalho nativo no menu de aplicativos do sistema com o ícone customizado, execute o bloco de configuração abaixo no seu terminal. 

**Atenção:** Substitua `/caminho/absoluto/para/o/projeto/` pelo diretório real onde o repositório foi clonado em sua máquina.

```bash
cat << 'EOF' > ~/.local/share/applications/erp-veloso.desktop
[Desktop Entry]
Version=1.0
Name=ERP Veloso Imports
Comment=Sistema de Gestão de Estoque e Finanças
Exec=/caminho/absoluto/para/o/projeto/iniciar_erp.sh
Icon=/caminho/absoluto/para/o/projeto/icon.png
Terminal=true
Type=Application
Categories=Office;Finance;
EOF

update-desktop-database ~/.local/share/applications/