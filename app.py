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

# Constantes 
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
    vendas["Hora"]         = vendas["Data_Venda"].dt.strftime("%H:%M")

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

# Helper: meses completos 
def meses_completos(df_slice):
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

#  Título 
st.markdown("## Dashboard de Varejo baseado no dataset público Olist Ecommerce")
st.markdown("---")

#  BLOCO 1: seletor de ano + filtros globais 
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

# Filtros globais
dff = df[
    df["Sexo"].isin(sexo_sel) &
    df["Regiao_Cliente"].isin(regiao_sel)
].copy()

dano = dff[dff["Ano"] == ano_sel].copy()

meses_ok, mes_cortado = meses_completos(dano)
dano_c = dano[dano["MesNum"].isin(meses_ok)]

if dano_c.empty:
    st.info("⚠️ Não temos dados para essa escolha de parâmetros :(")
    st.stop()

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

#  BLOCO 3: receita mês a mês
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

# BLOCO 4: evolução ano a ano 
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

# BLOCO 5: top-5 categorias + ticket médio por ano 
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


# BLOCO 6 (NOVO): Comparação de vendas entre filiais e regiões

st.markdown("#### Comparação de vendas entre filiais e regiões")
st.caption("Baseado no ano e filtros globais selecionados.")

col_reg, col_fil = st.columns(2)

with col_reg:
    st.markdown(f"##### Receita por região — {ano_sel}")
    receita_regiao = (
        dano_c
        .groupby("Regiao_Cliente")["Valor_Total"]
        .sum()
        .reset_index()
        .sort_values("Valor_Total", ascending=True)
    )
    receita_regiao.columns = ["Região","Receita"]

    fig_reg = px.bar(
        receita_regiao, x="Receita", y="Região",
        orientation="h",
        labels={"Receita":"Receita (R$)","Região":""},
        color_discrete_sequence=[COR],
        text=receita_regiao["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_reg.update_traces(textposition="outside")
    fig_reg.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, r=120), height=300,
    )
    st.plotly_chart(fig_reg, use_container_width=True)

with col_fil:
    st.markdown(f"##### Top filiais por receita — {ano_sel}")
    receita_filial = (
        dano_c
        .groupby("ID_Filial")["Valor_Total"]
        .sum()
        .reset_index()
        .sort_values("Valor_Total", ascending=False)
        .head(10)
        .sort_values("Valor_Total", ascending=True)
    )
    receita_filial["Filial"] = "Filial " + receita_filial["ID_Filial"].astype(str)

    fig_fil = px.bar(
        receita_filial, x="Valor_Total", y="Filial",
        orientation="h",
        labels={"Valor_Total":"Receita (R$)","Filial":""},
        color_discrete_sequence=[COR],
        text=receita_filial["Valor_Total"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_fil.update_traces(textposition="outside")
    fig_fil.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, r=120), height=300,
    )
    st.plotly_chart(fig_fil, use_container_width=True)

st.markdown("---")


# BLOCO 7 (NOVO): Filtros interativos — produto, cliente, período

st.markdown("#### Filtros interativos de vendas")

fi1, fi2, fi3 = st.columns(3)

categorias_disp = sorted(dff["Categoria_PT"].dropna().unique())
with fi1:
    cat_sel = st.multiselect(
        "Categoria de produto", categorias_disp,
        default=categorias_disp[:5] if len(categorias_disp) >= 5 else categorias_disp,
        key="cat_filtro"
    )

with fi2:
    data_min = dff["Data_Venda"].min().date()
    data_max = dff["Data_Venda"].max().date()
    periodo_sel = st.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
        key="periodo_filtro"
    )

with fi3:
    filiais_disp = sorted(dff["ID_Filial"].dropna().unique())
    filiais_labels = {f: f"Filial {f}" for f in filiais_disp}
    filial_filtro_sel = st.multiselect(
        "Filial",
        options=filiais_disp,
        format_func=lambda x: filiais_labels[x],
        default=filiais_disp,
        key="filial_filtro"
    )

# Aplica filtros interativos
if len(periodo_sel) == 2:
    d_inicio, d_fim = pd.Timestamp(periodo_sel[0]), pd.Timestamp(periodo_sel[1])
else:
    d_inicio = d_fim = pd.Timestamp(periodo_sel[0])

dff_int = dff[
    dff["Categoria_PT"].isin(cat_sel) &
    (dff["Data_Venda"] >= d_inicio) &
    (dff["Data_Venda"] <= d_fim) &
    dff["ID_Filial"].isin(filial_filtro_sel)
].copy()

if dff_int.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
else:
    fi_k1, fi_k2, fi_k3 = st.columns(3)
    fi_k1.metric("Receita filtrada",  f"R$ {dff_int['Valor_Total'].sum():,.0f}")
    fi_k2.metric("Pedidos filtrados", f"{len(dff_int):,}")
    fi_k3.metric("Ticket médio",      f"R$ {dff_int['Valor_Total'].mean():,.2f}")

    # Receita por categoria no período
    rec_cat = (
        dff_int.groupby("Categoria_PT")["Valor_Total"]
        .sum().nlargest(8).reset_index()
        .sort_values("Valor_Total", ascending=True)
    )
    rec_cat.columns = ["Categoria","Receita"]

    fig_int = px.bar(
        rec_cat, x="Receita", y="Categoria",
        orientation="h",
        labels={"Receita":"Receita (R$)","Categoria":""},
        color_discrete_sequence=[COR],
        text=rec_cat["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_int.update_traces(textposition="outside")
    fig_int.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, r=130), height=320,
        title="Receita por categoria no período selecionado"
    )
    st.plotly_chart(fig_int, use_container_width=True)

st.markdown("---")


# BLOCO 8 (NOVO): Consulta de cliente

st.markdown("#### Consulta de cliente")
st.caption("Selecione um cliente para ver categoria de produto, sexo, hora da compra e filial.")

clientes_ids = sorted(df["ID_Cliente"].dropna().unique())
clientes_labels = [f"Cliente {c}" for c in clientes_ids]

col_lista, col_detalhe = st.columns([1, 2])

with col_lista:
    busca_cliente = st.text_input("🔍 Buscar cliente (ex: 1, 42...)", key="busca_cli")

    if busca_cliente.strip():
        try:
            busca_int = int(busca_cliente.strip())
            clientes_filtrados = [c for c in clientes_ids if str(busca_int) in str(c)]
        except ValueError:
            clientes_filtrados = clientes_ids
    else:
        clientes_filtrados = clientes_ids

    labels_filtrados = [f"Cliente {c}" for c in clientes_filtrados]

    if labels_filtrados:
        cliente_sel_label = st.selectbox(
            "Clientes disponíveis",
            options=labels_filtrados,
            key="cliente_sel"
        )
        cliente_sel_id = clientes_filtrados[labels_filtrados.index(cliente_sel_label)]
    else:
        st.info("Nenhum cliente encontrado.")
        cliente_sel_id = None

with col_detalhe:
    if cliente_sel_id is not None:
        dados_cli = df[df["ID_Cliente"] == cliente_sel_id].copy()

        if dados_cli.empty:
            st.warning("Nenhum dado encontrado para este cliente.")
        else:
            # Pega a compra mais recente para exibição principal
            ultima = dados_cli.sort_values("Data_Venda", ascending=False).iloc[0]

            st.markdown(f"##### Detalhes — Cliente {cliente_sel_id}")

            dc1, dc2, dc3, dc4 = st.columns(4)
            sexo_val = ultima["Sexo"] if pd.notna(ultima["Sexo"]) else "—"
            hora_val = ultima["Hora"] if pd.notna(ultima["Hora"]) else "—"
            filial_val = f"Filial {int(ultima['ID_Filial'])}" if pd.notna(ultima["ID_Filial"]) else "—"
            cat_val = ultima["Categoria_PT"] if pd.notna(ultima["Categoria_PT"]) else "—"

            dc1.metric("Sexo", sexo_val)
            dc2.metric("Hora da compra", hora_val)
            dc3.metric("Filial", filial_val)
            dc4.metric("Categoria", cat_val)

            # Histórico de compras do cliente
            st.markdown(f"###### Histórico de compras ({len(dados_cli)} pedido(s))")
            historico = (
                dados_cli[["Data_Venda","Hora","Categoria_PT","ID_Filial","Valor_Total"]]
                .sort_values("Data_Venda", ascending=False)
                .head(10)
                .copy()
            )
            historico["Filial"] = "Filial " + historico["ID_Filial"].astype(str)
            historico["Data"] = historico["Data_Venda"].dt.strftime("%d/%m/%Y")
            historico["Valor"] = historico["Valor_Total"].apply(lambda v: f"R$ {v:,.2f}")
            historico = historico.rename(columns={"Hora":"Hora","Categoria_PT":"Categoria"})
            st.dataframe(
                historico[["Data","Hora","Categoria","Filial","Valor"]],
                use_container_width=True,
                hide_index=True,
            )

st.markdown("---")


# BLOCO 9 (NOVO): Explorador de filial

st.markdown("#### Explorador de filial")
st.caption("Selecione ou busque uma filial (ex: filial7) para ver faturamento anual, mensal e categorias mais vendidas.")

filiais_ids = sorted(df["ID_Filial"].dropna().unique())

col_fil_sel, col_fil_ano = st.columns([2, 1])

with col_fil_sel:
    busca_filial = st.text_input(
        "🔍 Buscar filial (ex: filial3, 7...)",
        key="busca_filial"
    )

    # Tenta extrair número da busca
    filial_encontrada = None
    if busca_filial.strip():
        num_str = busca_filial.strip().lower().replace("filial","").strip()
        try:
            num_busca = int(num_str)
            if num_busca in filiais_ids:
                filial_encontrada = num_busca
        except ValueError:
            pass

    # Lista scrollável
    labels_filiais = [f"Filial {f}" for f in filiais_ids]

    if filial_encontrada is not None:
        idx_default = filiais_ids.index(filial_encontrada)
    else:
        idx_default = 0

    filial_sel_label = st.selectbox(
        "Filiais disponíveis",
        options=labels_filiais,
        index=idx_default,
        key="filial_exp_sel"
    )
    filial_sel_id = filiais_ids[labels_filiais.index(filial_sel_label)]

with col_fil_ano:
    ano_filial = st.radio(
        "Ano da filial",
        options=anos_disp,
        index=len(anos_disp) - 1,
        key="ano_filial"
    )

# Dados da filial selecionada
df_filial = df[df["ID_Filial"] == filial_sel_id].copy()

if df_filial.empty:
    st.warning(f"Nenhum dado encontrado para Filial {filial_sel_id}.")
else:
    ef1, ef2, ef3 = st.columns(3)

    # KPIs da filial (ano selecionado)
    df_filial_ano = df_filial[df_filial["Ano"] == ano_filial]
    meses_ok_f, _ = meses_completos(df_filial_ano)
    df_filial_ano_c = df_filial_ano[df_filial_ano["MesNum"].isin(meses_ok_f)]

    ef1.metric(f"Receita {ano_filial}", f"R$ {df_filial_ano_c['Valor_Total'].sum():,.0f}")
    ef2.metric("Pedidos",               f"{len(df_filial_ano_c):,}")
    ef3.metric("Ticket médio",          f"R$ {df_filial_ano_c['Valor_Total'].mean():,.2f}" if len(df_filial_ano_c) > 0 else "—")

    col_fat_ano, col_fat_mes = st.columns(2)

    # Faturamento por ANO
    with col_fat_ano:
        st.markdown(f"##### Faturamento por ano — Filial {filial_sel_id}")
        fat_ano = []
        for a in anos_disp:
            da = df_filial[df_filial["Ano"] == a]
            mc, _ = meses_completos(da)
            tot = da[da["MesNum"].isin(mc)]["Valor_Total"].sum()
            fat_ano.append({"Ano": str(a), "Receita": tot, "Sel": a == ano_filial})
        df_fat_ano = pd.DataFrame(fat_ano)

        fig_fat_ano = px.bar(
            df_fat_ano, x="Ano", y="Receita",
            labels={"Receita":"Receita (R$)","Ano":""},
            color="Sel",
            color_discrete_map={True: COR, False: COR_NEUTRA},
            text=df_fat_ano["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
        )
        fig_fat_ano.update_traces(textposition="outside", showlegend=False)
        fig_fat_ano.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20,b=10), height=280,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_fat_ano, use_container_width=True)

    # Faturamento por MÊS do ano selecionado
    with col_fat_mes:
        st.markdown(f"##### Faturamento mensal — {ano_filial} — Filial {filial_sel_id}")
        if df_filial_ano_c.empty:
            st.info("Sem dados para esse ano nessa filial.")
        else:
            mensal_f = (
                df_filial_ano_c
                .groupby(["MesNum","MesPT"])["Valor_Total"]
                .sum().reset_index().sort_values("MesNum")
            )
            mensal_f["MesPT"] = pd.Categorical(mensal_f["MesPT"], categories=MESES_ORDEM, ordered=True)

            fig_fat_mes = px.bar(
                mensal_f, x="MesPT", y="Valor_Total",
                labels={"Valor_Total":"Receita (R$)","MesPT":""},
                color_discrete_sequence=[COR],
            )
            fig_fat_mes.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20,b=10), height=280,
            )
            st.plotly_chart(fig_fat_mes, use_container_width=True)

    # Categorias mais compradas na filial (todos os anos)
    st.markdown(f"##### Categorias mais compradas — Filial {filial_sel_id} ({ano_filial})")
    if not df_filial_ano_c.empty:
        top_cat_filial = (
            df_filial_ano_c
            .groupby("Categoria_PT")["Valor_Total"]
            .sum().nlargest(8).reset_index()
            .sort_values("Valor_Total", ascending=True)
        )
        top_cat_filial.columns = ["Categoria","Receita"]

        fig_cat_fil = px.bar(
            top_cat_filial, x="Receita", y="Categoria",
            orientation="h",
            labels={"Receita":"Receita (R$)","Categoria":""},
            color_discrete_sequence=[COR],
            text=top_cat_filial["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
        )
        fig_cat_fil.update_traces(textposition="outside")
        fig_cat_fil.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, r=130), height=340,
        )
        st.plotly_chart(fig_cat_fil, use_container_width=True)
    else:
        st.info("Sem dados para esse ano nessa filial.")

st.markdown("---")
st.caption("Dashboard Olist Ecommerce · Dados via Kaggle")