import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Osteria di Porto", layout="wide")

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .main_title {color: #8B0000; text-align: center; font-size: 3em; font-weight: bold; font-family: 'Helvetica', sans-serif;}
    .sub_title {color: #2E8B57; text-align: center; font-size: 1.2em;}
    div.stButton > button:first-child {background-color: #8B0000; color: white; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="main_title">🍝 Osteria di Porto</div>', unsafe_allow_html=True)
st.markdown('<div class="sub_title">Sistema de Gestão Integrada</div>', unsafe_allow_html=True)
st.divider()

# --- DADOS (MEMÓRIA TEMPORÁRIA) ---
if 'dados' not in st.session_state:
    st.session_state['dados'] = pd.DataFrame(columns=[
        "Data", "Produto", "Fornecedor", "Quantidade", "Unidade", "Preço Total", "Preço Unitário", "Mês/Ano"
    ])

# --- NAVEGAÇÃO ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTAR", "📊 RELATÓRIOS & VOLUME", "💰 PREÇOS & COMPARADOR"])

# ===================================================
# ABA 1: REGISTO
# ===================================================
with aba1:
    st.markdown("### Nova Entrada de Stock")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            data_compra = st.date_input("Data da Fatura", datetime.now())
            fornecedor = st.text_input("Fornecedor (ex: Macro)")
            produto = st.text_input("Produto (ex: Mozzarella)")
        with col2:
            c_qtd, c_uni = st.columns([2,1])
            with c_qtd:
                quantidade = st.number_input("Quantidade", min_value=0.01, format="%.2f")
            with c_uni:
                unidade = st.selectbox("Unid.", ["kg", "g", "L", "ml", "cx", "un"])
            preco_total = st.number_input("Total Pago (€)", min_value=0.00, format="%.2f")

        if st.button("💾 Adicionar ao Stock"):
            if produto and quantidade > 0 and preco_total > 0 and fornecedor:
                custo_unitario = preco_total / quantidade
                mes_ano = data_compra.strftime("%Y-%m")
                novo = pd.DataFrame([{
                    "Data": pd.to_datetime(data_compra),
                    "Produto": produto.title(),
                    "Fornecedor": fornecedor.title(),
                    "Quantidade": quantidade,
                    "Unidade": unidade,
                    "Preço Total": preco_total,
                    "Preço Unitário": custo_unitario,
                    "Mês/Ano": mes_ano
                }])
                st.session_state['dados'] = pd.concat([st.session_state['dados'], novo], ignore_index=True)
                st.success(f"✅ {produto} registado!")
            else:
                st.error("Preencha todos os campos.")

# ===================================================
# ABA 2: RELATÓRIOS DE VOLUME (NOVO!)
# ===================================================
with aba2:
    st.header("📊 Análise de Quantidades e Fornecedores")
    df = st.session_state['dados']
    
    if not df.empty:
        # --- FILTROS ---
        st.markdown("##### 🔎 Filtros de Pesquisa")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            lista_prods = ["Todos"] + list(df["Produto"].unique())
            filtro_prod = st.selectbox("Escolha o Produto:", lista_prods)
        
        with col_f2:
            lista_forn = ["Todos"] + list(df["Fornecedor"].unique())
            filtro_forn = st.selectbox("Escolha o Fornecedor:", lista_forn)
            
        with col_f3:
            data_min = df["Data"].min().date()
            data_max = df["Data"].max().date()
            if data_min == data_max:
                data_min = data_min - timedelta(days=1)
            datas = st.date_input("Intervalo de Tempo", [data_min, data_max])

        # APLICAR A LÓGICA DOS FILTROS
        df_filtrado = df.copy()
        
        if filtro_prod != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Produto"] == filtro_prod]
            
        if filtro_forn != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Fornecedor"] == filtro_forn]
            
        if len(datas) == 2:
            data_inicio, data_fim = datas
            mask = (df_filtrado['Data'].dt.date >= data_inicio) & (df_filtrado['Data'].dt.date <= data_fim)
            df_filtrado = df_filtrado.loc[mask]

        st.divider()

        # --- RESULTADOS ---
        if not df_filtrado.empty:
            total_qtd = df_filtrado["Quantidade"].sum()
            total_valor = df_filtrado["Preço Total"].sum()
            unidade_ref = df_filtrado.iloc[0]["Unidade"]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Quantidade Total", f"{total_qtd:.2f} {unidade_ref}")
            c2.metric("Valor Gasto", f"€ {total_valor:.2f}")
            if total_qtd > 0:
                c3.metric("Preço Médio Ponderado", f"€ {(total_valor/total_qtd):.2f} / {unidade_ref}")
            
            st.subheader("Histórico de Compras (Volume)")
            fig = px.bar(df_filtrado, x="Data", y="Quantidade", color="Fornecedor",
                         title=f"Entradas de {filtro_prod if filtro_prod != 'Todos' else 'Stock Geral'}",
                         text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Ver Tabela Detalhada das Compras"):
                st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.warning("Nenhuma compra encontrada com estes filtros.")
            
    else:
        st.info("Registe compras na Aba 1 para ver os relatórios.")

# ===================================================
# ABA 3: PREÇOS E COMPARADOR
# ===================================================
with aba3:
    st.header("💰 Análise de Preços")
    df = st.session_state['dados']
    if not df.empty:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("Quem é mais barato?")
            prod_comp = st.selectbox("Comparar Produto:", df["Produto"].unique())
            df_c = df[df["Produto"] == prod_comp]
            comp = df_c.groupby("Fornecedor")["Preço Unitário"].mean().reset_index().sort_values("Preço Unitário")
            fig_bar = px.bar(comp, x="Fornecedor", y="Preço Unitário", color="Preço Unitário",
                             text_auto='.2f', color_continuous_scale="RdYlGn_r", title="Preço Médio por Fornecedor")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graf2:
            st.subheader("Evolução do Preço")
            df_evo = df[df["Produto"] == prod_comp].sort_values("Data")
            fig_line = px.line(df_evo, x="Data", y="Preço Unitário", markers=True, 
                               title=f"Histórico de Custo: {prod_comp}")
            st.plotly_chart(fig_line, use_container_width=True)

 
