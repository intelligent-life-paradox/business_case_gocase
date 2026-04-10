# 🛒 Retail Analytics Dashboard - Business Case Gocase (UGO)

Este projeto apresenta uma solução completa de análise de dados para uma rede de varejo brasileira, utilizando o dataset real de e-commerce da **Olist (Kaggle)**. O projeto cobre desde a ingestão e limpeza de dados até a criação de um dashboard interativo e a otimização de consultas SQL de alta performance.

## 🚀 O que o projeto faz?

O ecossistema foi dividido em três camadas principais para garantir a separação de responsabilidades e escalabilidade:

1.  **Engenharia & Qualidade (Notebook 01):** Realiza o download automático dos dados, trata valores nulos e duplicatas, e prepara a carga de dados para o banco de dados no próximo notebook. 
2.  **Modelagem & SQL (Notebook 02):** Estrutura os dados brutos em um modelo **Star Schema** (Esquema Estrela) dentro de um banco **SQLite**. Implementa consultas otimizadas utilizando **Window Functions** e **Índices de Cobertura** para responder aos desafios de negócio propostos.
3.  **Visualização (Streamlit):** Um dashboard interativo que permite aos gestores filtrar faturamento, ticket médio e tendências por **Ano, Sexo e Região**, com tratamento de erros para seleções sem dados e exclusão inteligente de meses incompletos.

---

## 📂 Estrutura do Repositório

```text
.
├── app/
│   └── main.py             # Dashboard interativo (Streamlit + Plotly)
├── notebooks/
│   ├── 01_etl_quality.ipynb # Ingestão, limpeza e Data Quality Report
│   └── 02_sql_analysis.ipynb # Modelagem Star Schema e Queries Otimizadas
├── data/                   # Base de dados SQLite e arquivos CSV
│   ├── varejo_gocase.db    # Banco de dados relacional otimizado
│   ├── vendas.csv          # Tabela Fato (Transacional)
│   ├── clientes.csv        # Dimensão Clientes (Enriquecida com Sexo/Idade)
│   ├── filiais.csv         # Dimensão Filiais (Sellers)
│   └── produtos.csv        # Dimensão Produtos
├── Dockerfile              # Configuração de containerização
├── docker-compose.yml      # Orquestração do serviço
└── requirements.txt        # Dependências do projeto (Pandas, Plotly, Streamlit, etc.)


```

# 🛠️ Como Rodar

## Opção 1 --- Docker Compose (Recomendado)

Ideal para garantir que o ambiente rode exatamente como configurado, sem
conflitos de dependências.

``` bash
docker compose up --build
```

Acesse: http://localhost:8501

## Opção 2 --- Docker Simples

``` bash
docker build -t dashboard-varejo .
docker run -p 8501:8501 dashboard-varejo
```

## Opção 3 --- Instalação Local (Python)

Certifique-se de ter o Python 3.9+ instalado.

``` bash
# Instalar dependências
pip install -r requirements.txt

# Rodar o dashboard
streamlit run app/main.py
```

------------------------------------------------------------------------

# 📊 Seções do Dashboard

  ------------------------------------------------------------------------
  Seção           Conteúdo                  Indicadores
  --------------- ------------------------- ------------------------------
 **Filtros         Controle total da visão   Ano, Sexo do Cliente e Região
  Dinâmicos**                                do Brasil

  **KPIs de         Visão macro do negócio    Receita Total, Pedidos, Ticket
  Performance**                               **Médio e Clientes Únicos**

  **Tendência       Evolução temporal         Gráfico de barras com linha de
  Mensal**                                    **média móvel e tratamento de
                                            meses incompletos**

  **Evolução Anual  Comparativo histórico**     **Gráfico de linhas destacando o
                                            ano selecionado na série
                                            temporal**

  **Mix de Produtos Análise de portfólio      Top 5 categorias mais
                                            rentáveis (Gráfico de Rosca)**

  Comportamento   Perfil de consumo         Ticket médio anual comparativo
                                            por ano selecionado
  ------------------------------------------------------------------------

------------------------------------------------------------------------

# 🧠 Destaques Técnicos (Diferenciais)

-   **SQL de Alta Performance:** Uso de `LAG()` para cálculo de
    crescimento MoM e `ROW_NUMBER()` para filtros de ranking por região,
    evitando Table Scans e utilizando índices compostos. Além disso,
    fiz a implementação de um plano de execução (recurso comum do sql-server)
-   **Data Quality:** Implementação de validação de meses incompletos
    (exclui automaticamente o último mês da série se ele tiver menos de
    28 dias de dados para não enviesar as médias).
-   **UX/UI Robusta:** Tratamento de estados vazios (`st.stop`) que
    exibe mensagens amigáveis em vez de erros de NaN quando os filtros
    selecionados não possuem registros.
-   **Modelagem Star Schema:** Relacionamentos 1:N garantindo a
    integridade referencial entre as tabelas de Dimensão e Fato,
    facilitando a manutenção e futuras expansões.
