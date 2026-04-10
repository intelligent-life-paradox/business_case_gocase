import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Varejo baseado em dados do Kaggle Olist dataset",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 500; }
[data-testid="stMetricLabel"] { font-size: 0.82rem; color: #888; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
div[data-testid="stMetricValue"] > div { white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

#  Constantes
COR         = "#D85A30"
COR_NEUTRA  = "#888780"
PALETA_PIE  = ["#D85A30","#1D9E75","#378ADD","#BA7517","#534AB7"]
ORDEM_DIAS  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
DIAS_PT     = {
    "Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
    "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo",
}
MESES_PT    = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
               7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
MESES_ORDEM = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

CAT_PT = {
    "perfumery":"Perfumaria","art":"Arte","sports_leisure":"Esporte/Lazer",
    "baby":"Bebê","housewares":"Utilidades Domésticas","musical_instruments":"Instr. Musicais",
    "cool_stuff":"Cool Stuff","furniture_decor":"Decoração","home_appliances":"Eletrodomésticos",
    "toys":"Brinquedos","bed_bath_table":"Cama/Mesa/Banho","computers_accessories":"Comp./Acessórios",
    "health_beauty":"Saúde/Beleza","electronics":"Eletrônicos","telephony":"Telefonia",
    "fashion_shoes":"Calçados","watches_gifts":"Relógios/Presentes","pet_shop":"Pet Shop",
    "garden_tools":"Ferramentas Jardim","auto":"Automotivo","stationery":"Papelaria",
    "computers":"Computadores","home_construction":"Construção","luggage_accessories":"Malas",
    "office_furniture":"Móveis Escritório","fashion_bags_accessories":"Bolsas",
    "construction_tools_safety":"Ferramentas Seg.","small_appliances":"Pequenos Eletro",
    "agro_industry_and_commerce":"Agro/Indústria","furniture_living_room":"Sala de Estar",
    "consoles_games":"Games","books_general_interest":"Livros","fashion_underwear_beach":"Moda Praia",
    "fashion_male_clothing":"Moda Masculina","fixed_telephony":"Telefonia Fixa",
    "drinks":"Bebidas","food":"Alimentos","food_drink":"Alimentos/Bebidas",
    "music":"Música","audio":"Áudio","flowers":"Flores","party_supplies":"Festas",
    "tablets_printing_image":"Tablets/Impressoras","fashion_sport":"Moda Esporte",
    "christmas_supplies":"Natal","dvds_blu_ray":"DVDs/Blu-Ray","cine_photo":"Foto/Cinema",
    "arts_and_craftmanship":"Artesanato","furniture_bedroom":"Quarto",
    "books_technical":"Livros Técnicos","la_cuisine":"Culinária",
    "fashio_female_clothing":"Moda Feminina","cds_dvds_musicals":"CDs/DVDs",
    "fashion_childrens_clothes":"Moda Infantil","home_appliances_2":"Eletrodomésticos 2",
    "small_appliances_home_oven_and_coffee":"Café/Forno",
    "kitchen_dining_laundry_garden_furniture":"Cozinha/Jardim",
}

# Carregamento
@st.cache_data
def load_data():
    base = "dados" if os.path.isdir("dados") else "data"

    vendas   = pd.read_csv(f"{base}/vendas.csv")
    clientes = pd.read_csv(f"{base}/clientes.csv")
    filiais  = pd.read_csv(f"{base}/filiais.csv")
    produtos = pd.read_csv(f"{base}/produtos.csv")

    vendas["Data_Venda"]   = pd.to_datetime(vendas["Data_Venda"])
    vendas["Ano"]          = vendas["Data_Venda"].dt.year
    vendas["MesNum"]       = vendas["Data_Venda"].dt.month
    vendas["MesPT"]        = vendas["Data_Venda"].dt.month.map(MESES_PT)
    vendas["DiaSemana"]    = vendas["Data_Venda"].dt.strftime("%A").map(DIAS_PT)
    vendas["DiaSemanaNum"] = vendas["Data_Venda"].dt.dayofweek

    produtos["Categoria_PT"] = produtos["Categoria"].map(CAT_PT).fillna(produtos["Categoria"])

    df = (
        vendas
        .merge(clientes[["ID_Cliente","Sexo","Regiao"]],
               on="ID_Cliente", how="left")
        .merge(filiais[["ID_Filial","Estado"]],
               on="ID_Filial", how="left")
        .merge(produtos[["ID_Produto","Categoria_PT"]],
               on="ID_Produto", how="left")
    )
    df.rename(columns={"Regiao":"Regiao_Cliente"}, inplace=True)
    return df

df = load_data()

# Helper: meses completos de um slice de dados
def meses_completos(df_slice):
    """
    Retorna (lista_meses_ok, mes_cortado_ou_None).
    Um mês é incompleto se for o mês máximo presente e
    tiver menos de 28 dias distintos de registros.
    """
    if df_slice.empty:
        return [], None
    por_mes = df_slice.groupby("MesNum")["Data_Venda"].apply(
        lambda s: s.dt.day.nunique()
    )
    mes_max = int(por_mes.index.max())
    if por_mes[mes_max] < 28:
        meses_ok = [m for m in por_mes.index if m < mes_max]
        return meses_ok, mes_max
    return list(por_mes.index), None

st.markdown("## Dashboard de Varejo")
st.markdown("---")

#  BLOCO 1: seletor de ano + filtros 
anos_disp    = sorted(df["Ano"].dropna().unique())
regioes_disp = sorted(df["Regiao_Cliente"].dropna().unique())
sexos_disp   = sorted(df["Sexo"].dropna().unique())

col_ano, col_gap, col_filtros = st.columns([3, 0.3, 4])

with col_ano:
    st.markdown("##### Ano")
    ano_sel = st.radio(
        label="ano",
        options=anos_disp,
        index=len(anos_disp) - 1,
        horizontal=True,
        label_visibility="collapsed",
    )

with col_filtros:
    st.markdown("##### Filtros")
    fc1, fc2 = st.columns(2)
    with fc1:
        sexo_sel = st.multiselect(
            "Sexo", sexos_disp, default=sexos_disp, key="sexo"
        )
    with fc2:
        regiao_sel = st.multiselect(
            "Região", regioes_disp, default=regioes_disp, key="regiao"
        )

st.markdown("---")

# vamos filtrar os dados globalmente: 
dff = df[
    df["Sexo"].isin(sexo_sel) &
    df["Regiao_Cliente"].isin(regiao_sel)
].copy()

# Slice do ano selecionado
dano = dff[dff["Ano"] == ano_sel].copy()

# Remove mês incompleto
meses_ok, mes_cortado = meses_completos(dano)
dano_c = dano[dano["MesNum"].isin(meses_ok)]

if dano_c.empty:
    st.info("⚠️ Não temos dados para essa escolha de parâmetros :(")
    st.stop() # Interrompe a execução para não mostrar os KPIs e Gráficos vazios

#  BLOCO 2: KPIs 
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita total",   f"R$ {dano_c['Valor_Total'].sum():,.0f}")
k2.metric("Pedidos",         f"{len(dano_c):,}")
k3.metric("Ticket médio",    f"R$ {dano_c['Valor_Total'].mean():,.2f}")
k4.metric("Clientes únicos", f"{dano_c['ID_Cliente'].nunique():,}")

if mes_cortado:
    st.caption(
        f"ℹ️  {MESES_PT[mes_cortado]}/{ano_sel} excluído — "
        "dados incompletos no último mês da série."
    )

st.markdown("---")

# BLOCO 3: receita mês a mês 
st.markdown(f"#### Receita mês a mês — {ano_sel}")

mensal = (
    dano_c
    .groupby(["MesNum","MesPT"])["Valor_Total"]
    .sum().reset_index().sort_values("MesNum")
)
mensal["MesPT"] = pd.Categorical(mensal["MesPT"], categories=MESES_ORDEM, ordered=True)
media_m = mensal["Valor_Total"].mean()

fig_mensal = px.bar(
    mensal, x="MesPT", y="Valor_Total",
    labels={"Valor_Total":"Receita (R$)","MesPT":""},
    color_discrete_sequence=[COR],
)
fig_mensal.add_hline(
    y=media_m, line_dash="dot", line_color=COR_NEUTRA,
    annotation_text=f"Média: R$ {media_m:,.0f}",
    annotation_position="top left",
    annotation_font_size=11,
)
fig_mensal.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20,b=10), height=280,
)
st.plotly_chart(fig_mensal, use_container_width=True)

#  BLOCO 4: evolução ano a ano
st.markdown("#### Evolução da receita — ano a ano")
st.caption("Cada ponto é o total dos meses completos do ano. Ponto destacado = ano selecionado.")

receita_anual = []
for a in anos_disp:
    da  = dff[dff["Ano"] == a]
    mc, _ = meses_completos(da)
    tot = da[da["MesNum"].isin(mc)]["Valor_Total"].sum()
    receita_anual.append({"Ano": str(a), "Receita": tot})
df_anual = pd.DataFrame(receita_anual)

fig_anual = px.line(
    df_anual, x="Ano", y="Receita", markers=True,
    labels={"Receita":"Receita (R$)","Ano":""},
    color_discrete_sequence=[COR],
)
fig_anual.update_traces(marker=dict(size=9), line=dict(width=2.5))
# Destaca ano selecionado
ponto = df_anual[df_anual["Ano"] == str(ano_sel)]
if not ponto.empty:
    fig_anual.add_trace(go.Scatter(
        x=ponto["Ano"], y=ponto["Receita"],
        mode="markers",
        marker=dict(size=15, color=COR, line=dict(width=2.5, color="white")),
        showlegend=False, hoverinfo="skip",
    ))
fig_anual.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20,b=10), height=240,
    hovermode="x unified",
)
st.plotly_chart(fig_anual, use_container_width=True)

st.markdown("---")

#BLOCO 5: top-5 categorias + ticket médio por ano 
col_pie, col_ticket = st.columns(2)

with col_pie:
    st.markdown(f"#### Top 5 categorias — {ano_sel}")
    st.caption("Filtrado por sexo e região selecionados.")

    top5 = (
        dano_c
        .groupby("Categoria_PT")["Valor_Total"]
        .sum().nlargest(5).reset_index()
    )
    top5.columns = ["Categoria","Receita"]

    fig_pie = px.pie(
        top5, values="Receita", names="Categoria",
        hole=0.42,
        color_discrete_sequence=PALETA_PIE,
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=11,
    )
    fig_pie.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, font_size=11),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10,b=50),
        height=340,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_ticket:
    st.markdown("#### Ticket médio por ano")
    st.caption("Calculado sobre os meses completos de cada ano.")

    ticket_anual = []
    for a in anos_disp:
        da  = dff[dff["Ano"] == a]
        mc, _ = meses_completos(da)
        tkt = da[da["MesNum"].isin(mc)]["Valor_Total"].mean()
        ticket_anual.append({"Ano": str(a), "Ticket": round(tkt, 2), "Sel": a == ano_sel})
    df_tkt = pd.DataFrame(ticket_anual)

    fig_tkt = px.bar(
        df_tkt, x="Ano", y="Ticket",
        labels={"Ticket":"Ticket médio (R$)","Ano":""},
        color="Sel",
        color_discrete_map={True: COR, False: COR_NEUTRA},
        text=df_tkt["Ticket"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_tkt.update_traces(textposition="outside", showlegend=False)
    fig_tkt.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20,b=10),
        height=340,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_tkt, use_container_width=True)

st.markdown("---")

