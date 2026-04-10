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

    #  Mapeia IDs hash → números sequenciais legíveis
    ids_filiais  = sorted(filiais["ID_Filial"].dropna().unique())
    ids_clientes = sorted(clientes["ID_Cliente"].dropna().unique())
    mapa_filial  = {orig: i+1 for i, orig in enumerate(ids_filiais)}
    mapa_cliente = {orig: i+1 for i, orig in enumerate(ids_clientes)}

    vendas["ID_Filial_Num"]  = vendas["ID_Filial"].map(mapa_filial)
    vendas["ID_Cliente_Num"] = vendas["ID_Cliente"].map(mapa_cliente)
    clientes["ID_Cliente_Num"] = clientes["ID_Cliente"].map(mapa_cliente)
    filiais["ID_Filial_Num"]   = filiais["ID_Filial"].map(mapa_filial)

    df = (
    vendas
    .merge(clientes[["ID_Cliente","ID_Cliente_Num","Sexo","Regiao"]],
           on="ID_Cliente", how="left")
    .merge(filiais[["ID_Filial","Estado"]], 
           on="ID_Filial", how="left")
    .merge(produtos[["ID_Produto","Categoria_PT"]],
           on="ID_Produto", how="left")
)

df, mapa_filial, mapa_cliente = load_data()
# Mapas inversos: número → ID original
inv_filial  = {v: k for k, v in mapa_filial.items()}
inv_cliente = {v: k for k, v in mapa_cliente.items()}

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


# BLOCO 6 (NOVO): COMPARAÇÃO ENTRE FILIAIS E REGIÕES

st.markdown("#### Comparação de vendas entre filiais e regiões")
st.caption("Baseado nos filtros globais de ano, sexo e região selecionados.")

col_reg, col_fil = st.columns(2)

with col_reg:
    st.markdown(f"##### Receita por região — {ano_sel}")
    rec_reg = (
        dano_c
        .groupby("Regiao_Cliente")["Valor_Total"]
        .sum().reset_index()
        .sort_values("Valor_Total", ascending=False)
    )
    rec_reg.columns = ["Região", "Receita"]

    fig_reg = px.bar(
        rec_reg, x="Receita", y="Região",
        orientation="h",
        labels={"Receita":"Receita (R$)", "Região":""},
        color="Região",
        color_discrete_sequence=PALETA_REG,
        text=rec_reg["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_reg.update_traces(textposition="outside", showlegend=False)
    fig_reg.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=80),
        height=300,
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

with col_fil:
    st.markdown(f"##### Top filiais por receita — {ano_sel}")
    n_top = st.slider("Número de filiais", min_value=3, max_value=20, value=10, key="slider_top_filiais")

    rec_fil = (
        dano_c
        .groupby("ID_Filial_Num")["Valor_Total"]
        .sum().reset_index()
        .sort_values("Valor_Total", ascending=False)
        .head(n_top)
    )
    rec_fil.columns = ["Filial", "Receita"]
    rec_fil["Filial"] = "Filial " + rec_fil["Filial"].astype(str)

    fig_fil = px.bar(
        rec_fil, x="Receita", y="Filial",
        orientation="h",
        labels={"Receita":"Receita (R$)", "Filial":""},
        color_discrete_sequence=[COR],
        text=rec_fil["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_fil.update_traces(textposition="outside", showlegend=False)
    fig_fil.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=80),
        height=300,
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_fil, use_container_width=True)

st.markdown("---")


# BLOCO 7 (NOVO): CONSULTA DE CLIENTE

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

            sexo_val    = ultima.get("Sexo", "—")
            hora_val    = ultima.get("Hora", "—")
            filial_num  = ultima.get("ID_Filial_Num")
            filial_val  = f"Filial {int(filial_num)}" if pd.notna(filial_num) else "—"
            cat_val     = ultima.get("Categoria_PT", "—")
            total_compras       = len(compras_cliente)
            valor_total_cliente = compras_cliente["Valor_Total"].sum()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Sexo",           sexo_val)
            c2.metric("Hora da compra", hora_val)
            c3.metric("Filial",         filial_val)
            c4.metric("Categoria",      cat_val)

            st.caption(
                f"📦 Total de pedidos deste cliente: **{total_compras}** | "
                f"💰 Valor acumulado: **R$ {valor_total_cliente:,.2f}**"
            )

            with st.expander("Ver histórico de compras (últimas 10)"):
                hist = compras_cliente[["Data_Venda","Hora","Categoria_PT","ID_Filial_Num","Valor_Total"]].head(10).copy()
                hist["ID_Filial_Num"] = "Filial " + hist["ID_Filial_Num"].astype(str)
                hist["Data_Venda"]    = hist["Data_Venda"].dt.strftime("%d/%m/%Y")
                hist.columns = ["Data","Hora","Categoria","Filial","Valor (R$)"]
                hist["Valor (R$)"] = hist["Valor (R$)"].apply(lambda v: f"R$ {v:,.2f}")
                st.dataframe(hist, use_container_width=True, hide_index=True)

st.markdown("---")


# BLOCO 8 (NOVO): EXPLORADOR DE FILIAL

st.markdown("#### Explorador de filial")

nums_filiais = sorted(inv_filial.keys())   # [1, 2, 3, ...]

col_busca_exp, col_ano_exp_wrap = st.columns([2, 2])

with col_busca_exp:
    st.caption("🔍 Digite o número da filial para pesquisar.\n\nExemplo: **filial 1**, **filial 7** ou apenas **7**")
    busca_filial_exp = st.text_input(
        "Busca de filial",
        key="busca_filial_exp",
        placeholder="filial 1",
        label_visibility="collapsed",
    )

    filial_num_sel = None
    if busca_filial_exp.strip():
        num_str_fil = "".join(filter(str.isdigit, busca_filial_exp))
        if num_str_fil:
            n_fil = int(num_str_fil)
            if n_fil in inv_filial:
                filial_num_sel = n_fil
                st.caption(f"✅ Exibindo Filial {n_fil}")
            else:
                st.caption(f"⚠️ Filial {n_fil} não encontrada. Filiais disponíveis: 1 a {max(nums_filiais)}.")
        else:
            st.caption("⚠️ Digite um número válido.")
    else:
        st.caption(f"ℹ️ Filiais disponíveis: **1** a **{max(nums_filiais)}**")

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

if filial_num_sel is None:
    st.info("Use a busca acima para selecionar uma filial.")
else:
    filial_id_orig = inv_filial[filial_num_sel]
    df_filial = df[df["ID_Filial"] == filial_id_orig].copy()

    if df_filial.empty:
        st.info(f"Sem dados para Filial {filial_num_sel}.")
    else:
        st.markdown(f"##### Filial {filial_num_sel}")

        df_filial_ano   = df_filial[df_filial["Ano"] == ano_exp]
        meses_ok_f, _   = meses_completos(df_filial_ano)
        df_filial_ano_c = df_filial_ano[df_filial_ano["MesNum"].isin(meses_ok_f)]

        fk1, fk2, fk3 = st.columns(3)
        fk1.metric(f"Receita {ano_exp}", f"R$ {df_filial_ano_c['Valor_Total'].sum():,.0f}")
        fk2.metric("Pedidos",            f"{len(df_filial_ano_c):,}")
        fk3.metric(
            "Ticket médio",
            f"R$ {df_filial_ano_c['Valor_Total'].mean():,.2f}" if not df_filial_ano_c.empty else "—"
        )

        col_fat_ano, col_fat_mes = st.columns(2)

        with col_fat_ano:
            st.markdown("##### Faturamento por ano")
            fat_ano_filial = []
            for a in anos_exp:
                da_f = df_filial[df_filial["Ano"] == a]
                mc_f, _ = meses_completos(da_f)
                tot_f = da_f[da_f["MesNum"].isin(mc_f)]["Valor_Total"].sum()
                fat_ano_filial.append({"Ano": str(a), "Receita": tot_f, "Sel": a == ano_exp})
            df_fat_fil = pd.DataFrame(fat_ano_filial)

            fig_fat_fil = px.bar(
                df_fat_fil, x="Ano", y="Receita",
                labels={"Receita":"Receita (R$)","Ano":""},
                color="Sel",
                color_discrete_map={True: COR, False: COR_NEUTRA},
                text=df_fat_fil["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
            )
            fig_fat_fil.update_traces(textposition="outside", showlegend=False)
            fig_fat_fil.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=30, b=10), height=280,
            )
            st.plotly_chart(fig_fat_fil, use_container_width=True)

        with col_fat_mes:
            st.markdown(f"##### Faturamento por mês — {ano_exp}")
            if df_filial_ano_c.empty:
                st.info("Sem dados completos para este ano nesta filial.")
            else:
                mensal_fil = (
                    df_filial_ano_c
                    .groupby(["MesNum","MesPT"])["Valor_Total"]
                    .sum().reset_index().sort_values("MesNum")
                )
                mensal_fil["MesPT"] = pd.Categorical(
                    mensal_fil["MesPT"], categories=MESES_ORDEM, ordered=True
                )
                media_mf = mensal_fil["Valor_Total"].mean()

                fig_mensal_fil = px.bar(
                    mensal_fil, x="MesPT", y="Valor_Total",
                    labels={"Valor_Total":"Receita (R$)","MesPT":""},
                    color_discrete_sequence=[COR],
                )
                fig_mensal_fil.add_hline(
                    y=media_mf, line_dash="dot", line_color=COR_NEUTRA,
                    annotation_text=f"Média: R$ {media_mf:,.0f}",
                    annotation_position="top left",
                    annotation_font_size=11,
                )
                fig_mensal_fil.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=30, b=10), height=280,
                )
                st.plotly_chart(fig_mensal_fil, use_container_width=True)

        st.markdown(f"##### O que mais se compra nesta filial — {ano_exp}")
        if df_filial_ano_c.empty:
            st.info("Sem dados para este ano nesta filial.")
        else:
            top_cat_fil = (
                df_filial_ano_c
                .groupby("Categoria_PT")["Valor_Total"]
                .sum().nlargest(10).reset_index()
            )
            top_cat_fil.columns = ["Categoria", "Receita"]

            fig_cat_fil = px.bar(
                top_cat_fil, x="Receita", y="Categoria",
                orientation="h",
                labels={"Receita":"Receita (R$)", "Categoria":""},
                color_discrete_sequence=[COR],
                text=top_cat_fil["Receita"].apply(lambda v: f"R$ {v:,.0f}"),
            )
            fig_cat_fil.update_traces(textposition="outside", showlegend=False)
            fig_cat_fil.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=80),
                height=360,
                yaxis=dict(categoryorder="total ascending"),
            )
            st.plotly_chart(fig_cat_fil, use_container_width=True)