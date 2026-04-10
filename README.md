# 🛒 Dashboard Varejo

Dashboard interativo de vendas construído com Streamlit + Plotly.

## Estrutura
```
dashboard/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── data/
    ├── vendas.csv
    ├── clientes.csv
    ├── filiais.csv
    └── produtos.csv
```

## Como rodar

### Opção 1 — Docker Compose (recomendado)
```bash
docker compose up --build
```
Acesse: http://localhost:8501

### Opção 2 — Docker simples
```bash
docker build -t dashboard-varejo .
docker run -p 8501:8501 dashboard-varejo
```

### Opção 3 — Sem Docker (local)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Páginas
| Página | Conteúdo |
|--------|----------|
| 💰 Vendas | KPIs, vendas mensais, por estado, top filiais, mapa |
| 📦 Produtos | Top categorias, rosca, preferência por sexo, matriz |
| 👥 Clientes | Perfil, ticket médio por região e faixa etária, histograma de idade |
| 📅 Tempo | Dia da semana, trimestre × ano, dia do mês, heatmap |
