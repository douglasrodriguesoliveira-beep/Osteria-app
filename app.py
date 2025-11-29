import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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
st.markdown('<div class="sub_title">Sistema de Gestão de Compras & Preços</div>', unsafe_allow_html=True)
st.divider()

# --- DADOS (MEMÓRIA TEMPORÁRIA) ---
if 'dados' not in st.session_state:
    st.session_state['dados'] = pd.DataFrame(columns=[
        "Data", "Produto", "Fornecedor", "Quantidade", "Unidade", "Preço Total", "Preço Unitário", "Mês/Ano"
    ])

# --- NAVEGAÇÃO ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTAR COMPRA", "📈 ANÁLISE & ALERTAS", "💰 COMPARAR FORNECEDORES"])

# ===================================================
# ABA 1: REGISTO (Entrada de Dados)
# ===================================================
with aba1:
    st.markdown("### Nova Entrada de Stock")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            data_compra = st.date_input("Data da Fatura", datetime.now())
            fornecedor = st.text_input("Nome do Fornecedor (ex: Macro)")
            produto = st.text_input("Nome do Produto (ex: Mozzarella)")
        
        with col2:
            c_qtd, c_uni = st.columns([2,1])
            with c_qtd:
                quantidade = st.number_input("Quantidade", min_value=0.01, format="%.2f")
            with c_uni:
                unidade = st.selectbox("Unid.", ["kg", "g", "L", "ml", "cx", "un"])
            
            preco_total = st.number_input("Total Pago na Fatura (€)", min_value=0.00, format="%.2f")

        if st.button("💾 Adicionar ao Stock"):
            if produto and quantidade > 0 and preco_total > 0 and fornecedor:
                custo_unitario = preco_total / quantidade
                mes_ano = data_compra.strftime("%Y-%m")
                
                novo_registo = pd.DataFrame([{
                    "Data": pd.to_datetime(data_compra),
                    "Produto": produto.title(),
                    "Fornecedor": fornecedor.title(),
                    "Quantidade": quantidade,
                    "Unidade": unidade,
                    "Preço Total": preco_total,
                    "Preço Unitário": custo_unitario,
                    "Mês/Ano": mes_ano
                }])
                
                st.session_state['dados'] = pd.concat([st.session_state['dados'], novo_registo], ignore_index=True)
                st.success(f"✅ {produto} registado com sucesso! Custo: €{custo_unitario:.2f}/{unidade}")
            else:
                st.error("⚠️ Por favor, preencha todos os campos corretamente.")

    # Tabela Rápida (Últimos 3)
    if not st.session_state['dados'].empty:
        st.caption("Últimos registos adicionados agora:")
        st.dataframe(st.session_state['dados'].tail(3), use_container_width=True)

# ===================================================
# ABA 2: ANÁLISE E EVOLUÇÃO (Onde vemos os aumentos)
# ===================================================
with aba2:
    df = st.session_state['dados']
    
    if not df.empty:
        # Métricas de Topo
        total_gasto = df["Preço Total"].sum()
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Gasto (Sessão Atual)", f"€ {total_gasto:,.2f}")
        col_m2.metric("Nº de Compras", len(df))
        st.divider()

        st.header("📈 Monitor de Inflação")
        lista_prod = df["Produto"].unique()
        prod_sel = st.selectbox("Selecione um produto para ver a evolução:", lista_prod)
        
        # Filtra dados do produto
        df_prod = df[df["Produto"] == prod_sel].sort_values("Data")
        
        if len(df_prod) > 1:
            ultima = df_prod.iloc[-1]
            penultima = df_prod.iloc[-2]
            
            preco_hoje = ultima['Preço Unitário']
            preco_antes = penultima['Preço Unitário']
            var_pct = ((preco_hoje - preco_antes) / preco_antes) * 100
            
            col_kpi, col_chart = st.columns([1, 2])
            
            with col_kpi:
                st.subheader("Variação de Preço")
                st.metric(
                    label=f"Preço Atual ({ultima['Fornecedor']})",
                    value=f"€ {preco_hoje:.2f}",
                    delta=f"{var_pct:.1f}% vs. anterior",
                    delta_color="inverse" # Vermelho se subir, Verde se descer
                )
                if var_pct > 0:
                    st.warning(f"O preço do(a) **{prod_sel}** subiu!")
            
            with col_chart:
                fig = px.line(df_prod, x="Data", y="Preço Unitário", markers=True, 
                              title=f"Histórico de Preço: {prod_sel}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Ainda só tens 1 registo de {prod_sel}. Regista mais uma compra (com data diferente) para veres a seta de aumento/descida.")

    else:
        st.info("Os gráficos aparecerão aqui depois de registares as primeiras compras na Aba 1.")

# ===================================================
# ABA 3: COMPARADOR DE FORNECEDORES
# ===================================================
with aba3:
    st.header("🏆 Quem vende mais barato?")
    df = st.session_state['dados']
    
    if not df.empty:
        prod_comp = st.selectbox("Produto a comparar:", df["Produto"].unique(), key="s_comp")
        df_c = df[df["Produto"] == prod_comp]
        
        # Ranking
        ranking = df_c.groupby("Fornecedor")["Preço Unitário"].mean().reset_index().sort_values("Preço Unitário")
        
        col_rank_chart, col_rank_table = st.columns([2,1])
        
        with col_rank_chart:
            fig_bar = px.bar(ranking, x="Fornecedor", y="Preço Unitário", 
                             color="Preço Unitário", title=f"Preço Médio ({df_c.iloc[0]['Unidade']})",
                             text_auto='.2f', color_continuous_scale="RdYlGn_r")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_rank_table:
            st.markdown("### Ranking")
            st.dataframe(ranking.style.format({"Preço Unitário": "€ {:.2f}"}), hide_index=True)
    else:
        st.write("Sem dados para comparar.")
