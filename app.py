import os
import urllib.request
import json
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


COR         = "#D85A30"
COR_NEUTRA  = "#888780"
PALETA_PIE  = ["#D85A30","#1D9E75","#378ADD","#BA7517","#534AB7"]
PALETA_REG  = ["#D85A30","#378ADD","#1D9E75","#BA7517","#534AB7"]
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

# Carregamento do Mapa (Garante que vai baixar o GeoJSON sem dar erro de CORS)
REGIAO_ESTADOS = {
    "Norte":       ["AM","RR","AP","PA","TO","RO","AC"],
    "Nordeste":    ["MA","PI","CE","RN","PE","PB","SE","AL","BA"],
    "Centro-Oeste":["MT","MS","GO","DF"],
    "Sudeste":     ["SP","RJ","ES","MG"],
    "Sul":         ["PR","SC","RS"],
}

@st.cache_data
def load_geojson():
    """Baixa o GeoJSON de estados e agrega geometrias por região."""
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        with urllib.request.urlopen(url) as response:
            estados_geo = json.loads(response.read().decode())
    except Exception:
        return None

    # Inverte o mapa: sigla → região
    sigla_regiao = {
        sigla: regiao
        for regiao, siglas in REGIAO_ESTADOS.items()
        for sigla in siglas
    }

    # Agrupa features por região
    from collections import defaultdict
    regioes_features = defaultdict(list)
    for feat in estados_geo["features"]:
        sigla = feat["properties"].get("sigla", "")
        regiao = sigla_regiao.get(sigla)
        if regiao:
            regioes_features[regiao].append(feat)

    # Constrói um GeoJSON com MultiPolygon por região
    # (usa shapely se disponível, senão faz merge ingênuo de coordenadas)
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union

        new_features = []
        for regiao, feats in regioes_features.items():
            geoms = [shape(f["geometry"]) for f in feats]
            merged = unary_union(geoms)
            new_features.append({
                "type": "Feature",
                "properties": {"regiao": regiao},
                "geometry": mapping(merged),
            })
        return {"type": "FeatureCollection", "features": new_features}

    except ImportError:
        # Fallback: agrupa coordenadas como MultiPolygon sem shapely
        new_features = []
        for regiao, feats in regioes_features.items():
            all_coords = []
            for f in feats:
                g = f["geometry"]
                if g["type"] == "Polygon":
                    all_coords.append(g["coordinates"])
                elif g["type"] == "MultiPolygon":
                    all_coords.extend(g["coordinates"])
            new_features.append({
                "type": "Feature",
                "properties": {"regiao": regiao},
                "geometry": {"type": "MultiPolygon", "coordinates": all_coords},
            })
        return {"type": "FeatureCollection", "features": new_features}

br_geojson = load_geojson()

# Carregamento
@st.cache_data
def load_data():
    base = "dados" if os.path.isdir("dados") else "data"

    vendas     = pd.read_csv(f"{base}/vendas.csv")
    clientes   = pd.read_csv(f"{base}/clientes.csv")
    vendedores = pd.read_csv(f"{base}/filiais.csv")
    produtos   = pd.read_csv(f"{base}/produtos.csv")
    
    clientes   = clientes.drop_duplicates(subset="ID_Cliente")   
    vendedores = vendedores.drop_duplicates(subset="ID_Filial")

    vendas["Data_Venda"]   = pd.to_datetime(vendas["Data_Venda"])
    vendas["Ano"]          = vendas["Data_Venda"].dt.year
    vendas["MesNum"]       = vendas["Data_Venda"].dt.month
    vendas["MesPT"]        = vendas["Data_Venda"].dt.month.map(MESES_PT)
    vendas["DiaSemana"]    = vendas["Data_Venda"].dt.strftime("%A").map(DIAS_PT)
    vendas["DiaSemanaNum"] = vendas["Data_Venda"].dt.dayofweek
    vendas["Hora"]         = vendas["Data_Venda"].dt.strftime("%H:%M")

    produtos["Categoria_PT"] = produtos["Categoria"].map(CAT_PT).fillna(produtos["Categoria"])

    ids_vendedores = sorted(vendedores["ID_Filial"].dropna().unique())
    ids_clientes   = sorted(clientes["ID_Cliente"].dropna().unique())
    mapa_vendedor  = {orig: i+1 for i, orig in enumerate(ids_vendedores)}
    mapa_cliente   = {orig: i+1 for i, orig in enumerate(ids_clientes)}

    vendas["ID_Vendedor_Num"]  = vendas["ID_Filial"].map(mapa_vendedor)
    vendas["ID_Cliente_Num"]   = vendas["ID_Cliente"].map(mapa_cliente)
    clientes["ID_Cliente_Num"] = clientes["ID_Cliente"].map(mapa_cliente)
    vendedores["ID_Vendedor_Num"] = vendedores["ID_Filial"].map(mapa_vendedor)

    df = (
        vendas
        .merge(clientes[["ID_Cliente","ID_Cliente_Num","Sexo","Regiao"]],
               on="ID_Cliente", how="left")
        .merge(vendedores[["ID_Filial","Estado"]],  
               on="ID_Filial", how="left")
        .merge(produtos[["ID_Produto","Categoria_PT"]],
               on="ID_Produto", how="left")
    )
    df.rename(columns={"Regiao":"Regiao_Cliente"}, inplace=True)
    return df, mapa_vendedor, mapa_cliente 

df, mapa_vendedor, mapa_cliente = load_data()
# Mapas inversos: número → ID original
inv_vendedor = {v: k for k, v in mapa_vendedor.items()}
inv_cliente  = {v: k for k, v in mapa_cliente.items()}

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

#Título 
st.markdown("## Dashboard de Varejo baseado no dataset público Olist Ecommerce")
st.markdown("---")

# BLOCO 1: seletor de ano + filtros globais 
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

# Filtro global
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

# BLOCO 2: KPIs 
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita total",   f"R$ {dano_c['Valor_Total'].sum():,.0f}")
k2.metric("Pedidos",         f"{len(dano_c):,}")
k3.metric("Ticket médio",    f"R$ {dano_c['Valor_Total'].mean():,.2f}")
k4.metric("Clientes únicos", f"{dano_c['ID_Cliente'].nunique():,}")

if mes_cortado:
    st.caption(
        f"ℹ️  {MESES_PT[mes_cortado]}/{ano_sel} excluído dos KPIs e Gráficos — "
        "dados incompletos no último mês da série."
    )

st.markdown("---")

# BLOCO 3: receita mês a mês (Cortando os meses incompletos mas mantendo a linha azul)
st.markdown(f"#### Receita mês a mês — {ano_sel}")

# Usando dano_c para respeitar o corte de meses incompletos
mensal = (
    dano_c
    .groupby(["MesNum", "MesPT"])["Valor_Total"]
    .sum().reset_index().sort_values("MesNum")
)
mensal["MesPT"] = pd.Categorical(mensal["MesPT"], categories=MESES_ORDEM, ordered=True)
media_m = mensal["Valor_Total"].mean()

fig_mensal = px.bar(
    mensal, x="MesPT", y="Valor_Total",
    labels={"Valor_Total":"Receita (R$)","MesPT":""},
    color_discrete_sequence=[COR],
)

# Adiciona a linha de tendência (azul) apenas sobre as barras existentes
fig_mensal.add_trace(go.Scatter(
    x=mensal["MesPT"],
    y=mensal["Valor_Total"],
    mode="lines+markers",
    line=dict(color="blue", width=3),
    name="Tendência"
))

fig_mensal.add_hline(
    y=media_m, line_dash="dot", line_color=COR_NEUTRA,
    annotation_text=f"Média: R$ {media_m:,.0f}",
    annotation_position="top left",
    annotation_font_size=11,
)
fig_mensal.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20,b=10), height=320, showlegend=False
)
st.plotly_chart(fig_mensal, use_container_width=True)


#BLOCO 4: evolução ano a ano 
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

#BLOCO 5: top-5 categorias + ticket médio por ano 
col_pie, col_ticket = st.columns(2)

with col_pie:
    st.markdown(f"#### Top 7 categorias — {ano_sel}")
    st.caption("Filtrado por sexo e região selecionados.")

    top7 = (
        dano_c
        .groupby("Categoria_PT")["Valor_Total"]
        .sum().nlargest(7).reset_index()
    )
    top7.columns = ["Categoria","Receita"]

    fig_pie = px.pie(
        top7, values="Receita", names="Categoria",
        hole=0.45,
        color_discrete_sequence=PALETA_PIE,
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=13,
    )
    fig_pie.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, font_size=11),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=15,b=55),
        height=350,
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


# BLOCO 6: COMPARAÇÃO ENTRE REGIÕES E VENDEDORES + MAPA DE CALOR CORRIGIDO

st.markdown("#### Comparação de vendas entre regiões e vendedores")
st.caption("Baseado nos filtros globais de ano, sexo e região selecionados.")

col_reg, col_mapa, col_ven = st.columns([1, 1.2, 1])

# DataFrame base para as regiões
rec_reg = (
    dano_c
    .groupby("Regiao_Cliente")["Valor_Total"]
    .sum().reset_index()
    .sort_values("Valor_Total", ascending=False)
)
rec_reg.columns = ["Região", "Receita"]

with col_reg:
    st.markdown(f"##### Receita por região — {ano_sel}")
    fig_reg = px.bar(
        rec_reg, x="Receita", y="Região",
        orientation="h",
        labels={"Receita":"Receita (R$)", "Região":""},
        color="Região",
        color_discrete_sequence=PALETA_REG,
        text=rec_reg["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_reg.update_traces(textposition="auto", showlegend=False)
    fig_reg.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=15, r=50),
        height=350,
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

with col_mapa:
    st.markdown(f"##### Mapa de Calor por Região")
    
    if br_geojson:
        fig_mapa = px.choropleth(
            rec_reg,
            geojson=br_geojson,
            locations="Região",
            featureidkey="properties.regiao",
            color="Receita",
            color_continuous_scale="Oranges", 
            labels={"Receita": "Receita (R$)"}
        )
        
        # Oculta bordas e fundo da terra padrão para evitar o quadrado branco
        fig_mapa.update_geos(
            fitbounds="locations", 
            visible=False,
            bgcolor="rgba(0,0,0,0)"
        )
        
        fig_mapa.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            height=350,
            coloraxis_colorbar=dict(title="", thickness=10)
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.warning("Não foi possível carregar as coordenadas do mapa.")

with col_ven:
    st.markdown(f"##### Top vendedores por receita — {ano_sel}")
    n_top = st.slider("Número de vendedores", min_value=3, max_value=12, value=10, key="slider_top_vendedores")

    rec_ven = (
        dano_c
        .groupby("ID_Vendedor_Num")["Valor_Total"]
        .sum().reset_index()
        .sort_values("Valor_Total", ascending=False)
        .head(n_top)
    )
    rec_ven.columns = ["Vendedor", "Receita"]
    rec_ven["Vendedor"] = "Vendedor " + rec_ven["Vendedor"].astype(str)

    fig_ven = px.bar(
        rec_ven, x="Receita", y="Vendedor",
        orientation="h",
        labels={"Receita":"Receita (R$)", "Vendedor":""},
        color_discrete_sequence=[COR],
        text=rec_ven["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_ven.update_traces(textposition="auto", showlegend=False)
    fig_ven.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=15, r=100),
        height=350,
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_ven, use_container_width=True)

st.markdown("---")


# BLOCO 7: CONSULTA DE CLIENTE

st.markdown("#### Consulta de cliente")

# Todos os números sequenciais de clientes disponíveis
nums_clientes = sorted(inv_cliente.keys())   # [1, 2, 3, ...]

col_busca_cli, col_detalhe_cli = st.columns([1, 2])

with col_busca_cli:
    st.caption("🔍 Digite o número do cliente para pesquisar.\n\nExemplo: **cliente 1**, **cliente 42** ou apenas **42**")
    busca_cli = st.text_input(
        "Busca de cliente",
        key="busca_cliente",
        placeholder="cliente 1",
        label_visibility="collapsed",
    )

    cliente_num_sel = None
    if busca_cli.strip():
        num_str_cli = "".join(filter(str.isdigit, busca_cli))
        if num_str_cli:
            n = int(num_str_cli)
            if n in inv_cliente:
                cliente_num_sel = n
                st.caption(f"✅ Exibindo Cliente {n}")
            else:
                st.caption(f"⚠️ Cliente {n} não encontrado. Clientes disponíveis: 1 a {max(nums_clientes)}.")
        else:
            st.caption("⚠️ Digite um número válido.")
    else:
        st.caption(f"ℹ️ Clientes disponíveis: **1** a **{max(nums_clientes)}**")

with col_detalhe_cli:
    if cliente_num_sel is None:
        st.info("Use a busca ao lado para selecionar um cliente.")
    else:
        cliente_id_orig = inv_cliente[cliente_num_sel]
        compras_cliente = df[df["ID_Cliente"] == cliente_id_orig].sort_values("Data_Venda", ascending=False)

        if compras_cliente.empty:
            st.info("Nenhuma compra encontrada para este cliente.")
        else:
            ultima = compras_cliente.iloc[0]

            sexo_val      = ultima.get("Sexo", "—")
            hora_val      = ultima.get("Hora", "—")
            vendedor_num  = ultima.get("ID_Vendedor_Num")
            vendedor_val  = f"Vendedor {int(vendedor_num)}" if pd.notna(vendedor_num) else "—"
            cat_val       = ultima.get("Categoria_PT", "—")
            total_compras = len(compras_cliente)
            valor_total_cliente = compras_cliente["Valor_Total"].sum()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Sexo",           sexo_val)
            c2.metric("Hora da compra", hora_val)
            c3.metric("Vendedor",       vendedor_val)
            c4.metric("Categoria",      cat_val)

            st.caption(
                f"📦 Total de pedidos deste cliente: **{total_compras}** | "
                f"💰 Valor acumulado: **R$ {valor_total_cliente:,.2f}**"
            )

            with st.expander("Ver histórico das últimas 10 compras deste cliente (lembre-se que muitas vezes um cliente faz uma compra única)"):
                hist = compras_cliente[["Data_Venda","Hora","Categoria_PT","ID_Vendedor_Num","Valor_Total"]].head(10).copy()
                hist["ID_Vendedor_Num"] = "Vendedor " + hist["ID_Vendedor_Num"].astype(str)
                hist["Data_Venda"]      = hist["Data_Venda"].dt.strftime("%d/%m/%Y")
                hist.columns = ["Data","Hora","Categoria","Vendedor","Valor (R$)"]
                hist["Valor (R$)"] = hist["Valor (R$)"].apply(lambda v: f"R$ {v:,.2f}")
                st.dataframe(hist, use_container_width=True, hide_index=True)

st.markdown("---")


# BLOCO 8: EXPLORADOR DE VENDEDOR

st.markdown("#### Explorador de vendedor")

nums_vendedores = sorted(inv_vendedor.keys())   # [1, 2, 3, ...]

col_busca_exp, col_ano_exp_wrap = st.columns([2, 2])

with col_busca_exp:
    st.caption("🔍 Digite o número do vendedor para pesquisar.\n\nExemplo: **vendedor 1**, **vendedor 7** ou apenas **7**")
    busca_vendedor_exp = st.text_input(
        "Busca de vendedor",
        key="busca_vendedor_exp",
        placeholder="vendedor 1",
        label_visibility="collapsed",
    )

    vendedor_num_sel = None
    if busca_vendedor_exp.strip():
        num_str_ven = "".join(filter(str.isdigit, busca_vendedor_exp))
        if num_str_ven:
            n_ven = int(num_str_ven)
            if n_ven in inv_vendedor:
                vendedor_num_sel = n_ven
                st.caption(f"✅ Exibindo Vendedor {n_ven}")
            else:
                st.caption(f"⚠️ Vendedor {n_ven} não encontrado. Vendedores disponíveis: 1 a {max(nums_vendedores)}.")
        else:
            st.caption("⚠️ Digite um número válido.")
    else:
        st.caption(f"ℹ️ Vendedores disponíveis: **1** a **{max(nums_vendedores)}**")

with col_ano_exp_wrap:
    anos_exp = sorted(df["Ano"].dropna().unique())
    st.markdown("##### Ano (explorador)")
    ano_exp = st.radio(
        "Ano explorador",
        options=anos_exp,
        index=len(anos_exp) - 1,
        horizontal=True,
        key="radio_ano_explorador",
        label_visibility="collapsed",
    )

if vendedor_num_sel is None:
    st.info("Use a busca acima para selecionar um vendedor.")
else:
    vendedor_id_orig = inv_vendedor[vendedor_num_sel]
    df_vendedor = df[df["ID_Filial"] == vendedor_id_orig].copy()

    if df_vendedor.empty:
        st.info(f"Sem dados para Vendedor {vendedor_num_sel}.")
    else:
        st.markdown(f"##### Vendedor {vendedor_num_sel}")

        df_vendedor_ano   = df_vendedor[df_vendedor["Ano"] == ano_exp]
        meses_ok_v, _     = meses_completos(df_vendedor_ano)
        df_vendedor_ano_c = df_vendedor_ano[df_vendedor_ano["MesNum"].isin(meses_ok_v)]

        fk1, fk2, fk3 = st.columns(3)
        fk1.metric(f"Receita {ano_exp}", f"R$ {df_vendedor_ano_c['Valor_Total'].sum():,.0f}")
        fk2.metric("Pedidos",            f"{len(df_vendedor_ano_c):,}")
        fk3.metric(
            "Ticket médio",
            f"R$ {df_vendedor_ano_c['Valor_Total'].mean():,.2f}" if not df_vendedor_ano_c.empty else "—"
        )

        col_fat_ano, col_fat_mes = st.columns(2)

        with col_fat_ano:
            st.markdown("##### Faturamento por ano")
            fat_ano_vendedor = []
            for a in anos_exp:
                da_v = df_vendedor[df_vendedor["Ano"] == a]
                mc_v, _ = meses_completos(da_v)
                tot_v = da_v[da_v["MesNum"].isin(mc_v)]["Valor_Total"].sum()