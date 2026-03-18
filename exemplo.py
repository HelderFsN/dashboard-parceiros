import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import numpy as np

# Configurar layout da página
st.set_page_config(layout="wide", page_title="Dashboard de Parceiros")

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1ncUO3qsAr8edPs3Cee_H4kFcwvZc4yTGV1tlVq5zXV8/export?format=csv"
    df = pd.read_csv(url)
    # Renomear colunas para evitar problemas de codificação
    df.columns = [
        'Parceiros', 'Estado', 'Primeiro Contato', 'Entrevista', 
        'Início Homologação', 'Processo Equatorial', 'Assinatura Contrato', 
        'Fim Homologação', 'SLA (dias)'
    ]
    
    # Converter para datetime
    date_cols = ['Primeiro Contato', 'Entrevista', 'Início Homologação', 'Processo Equatorial', 'Assinatura Contrato', 'Fim Homologação']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        
    return df

df = load_data()

# Lógica de Classificação da Situação (fase)
def get_phase(row):
    if pd.notnull(row['Fim Homologação']):
        return "Homologado"
    if pd.notnull(row['Início Homologação']) or pd.notnull(row['Processo Equatorial']):
        return "Em Homologação"
    if pd.notnull(row['Entrevista']):
        return "Em Análise"
    if pd.notnull(row['Primeiro Contato']):
        return "Parceiro - documentação..."
    return "Sem Contato"

df['Fase'] = df.apply(get_phase, axis=1)

# Lógica de "Situação" para a tabela (ATRASADO)
hoje = pd.to_datetime(datetime.today().date())
def get_situation(row):
    # Se já foi homologado, ok
    if row['Fase'] == 'Homologado':
        return 'CONCLUÍDO'
    
    # Podemos conferir SLA ou estimar um atraso (exemplo 30 dias após primeiro contato)
    # Ou usar SLA caso preenchido
    sla_max = 30
    if pd.notnull(row['SLA (dias)']):
        try:
            sla_max = float(row['SLA (dias)'])
        except:
            pass

    if pd.notnull(row['Primeiro Contato']):
        dias_corridos = (hoje - row['Primeiro Contato']).days
        if dias_corridos > sla_max:
            return 'ATRASADO'
    
    return 'NO PRAZO'

df['Situação'] = df.apply(get_situation, axis=1)

# Layout e Estilos
st.markdown("""
<style>
.metric-card {
    background-color: #f7f9fc;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0px;
    box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
    text-align: center;
}
.metric-title {
    color: #0076cf;
    font-size: 1.1em;
    font-weight: bold;
    margin-bottom: 10px;
}
.metric-value {
    color: #4a4a4a;
    font-size: 2em;
    font-weight: bold;
}
.metric-sub {
    color: #8c8c8c;
    font-size: 0.9em;
}
</style>
""", unsafe_allow_html=True)

# Filtros laterais
st.sidebar.title("Filtros")

estados = ['Todos'] + sorted(df['Estado'].dropna().unique().tolist())
select_estado = st.sidebar.selectbox("Estado", estados)

if select_estado != 'Todos':
    df_filtered = df[df['Estado'] == select_estado].copy()
else:
    df_filtered = df.copy()

fases = ['Todas'] + sorted(df_filtered['Fase'].dropna().unique().tolist())
select_fase = st.sidebar.selectbox("Fase", fases)

if select_fase != 'Todas':
    df_filtered = df_filtered[df_filtered['Fase'] == select_fase]

parceiros = ['Todos'] + sorted(df_filtered['Parceiros'].dropna().unique().tolist())
select_parceiro = st.sidebar.selectbox("Parceiro", parceiros)

if select_parceiro != 'Todos':
    df_filtered = df_filtered[df_filtered['Parceiros'] == select_parceiro]

# Cálculos para os cartões (Média de dias)
metric1 = (df_filtered['Entrevista'] - df_filtered['Primeiro Contato']).dt.days.mean()
metric2 = (df_filtered['Assinatura Contrato'] - df_filtered['Início Homologação']).dt.days.mean()
metric3 = (df_filtered['Fim Homologação'] - df_filtered['Início Homologação']).dt.days.mean()
metric4 = (df_filtered['Fim Homologação'] - df_filtered['Primeiro Contato']).dt.days.mean()

def format_days(val):
    if pd.isna(val):
        return "Sem dados"
    return f"{int(val)} dias médios"

# Construindo as colunas principais
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.markdown("### Tabela de Parceiros")
    
    # Preparar df para exibição
    df_exibir = df_filtered[['Parceiros', 'Situação']].copy()
    
    # Estilização condicional do Pandas para vermelho em ATRASADO
    def color_status(val):
        color = '#ff4b4b' if val == 'ATRASADO' else 'transparent'
        font_weight = 'bold' if val == 'ATRASADO' else 'normal'
        text_color = 'white' if val == 'ATRASADO' else 'inherit'
        return f'background-color: {color}; color: {text_color}; font-weight: {font_weight}'

    st.dataframe(
        df_exibir.style.applymap(color_status, subset=['Situação']),
        hide_index=True,
        use_container_width=True,
        height=350
    )
    
    st.markdown("### Distribuição das Fases")
    # Gráfico de Pizza com Altair
    fases_count = df_filtered['Fase'].value_counts().reset_index()
    fases_count.columns = ['Fase', 'Contagem']
    
    if not fases_count.empty:
        chart = alt.Chart(fases_count).mark_arc(innerRadius=0).encode(
            theta=alt.Theta(field="Contagem", type="quantitative"),
            color=alt.Color(field="Fase", type="nominal", legend=alt.Legend(title="Fase", orient="right")),
            tooltip=['Fase', 'Contagem']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Sem dados para o gráfico")

with col_right:
    st.markdown("### Métricas de Tempo")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Tempo para Iniciar entrevista</div>'
                    f'<div class="metric-value">{format_days(metric1)}</div></div>', unsafe_allow_html=True)
                    
        st.markdown(f'<div class="metric-card"><div class="metric-title">Período de Homologação</div>'
                    f'<div class="metric-value">{format_days(metric3)}</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Tempo para assinar o contrato</div>'
                    f'<div class="metric-value">{format_days(metric2)}</div></div>', unsafe_allow_html=True)
                    
        st.markdown(f'<div class="metric-card"><div class="metric-title">Tempo de todo processo</div>'
                    f'<div class="metric-value">{format_days(metric4)}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("Os *Tempos (SLA)* das métricas acima representam **a média em dias** de todos os parceiros filtrados. Se apenas um Parceiro for selecionado, você verá o tempo individual nato dessa empresa.")

st.markdown("---")
st.subheader("⏱️ Detalhamento de Tempo por Parceiro (em dias)")

# Calcular tempos individuais (em dias) mantendo vazio o que não tiver data
df_detalhe = df_filtered[['Parceiros', 'Fase', 'Situação']].copy()
df_detalhe['Tempo Iníciar Entrevista'] = (df_filtered['Entrevista'] - df_filtered['Primeiro Contato']).dt.days.astype('Int64')
df_detalhe['Tempo Assinar Contrato'] = (df_filtered['Assinatura Contrato'] - df_filtered['Início Homologação']).dt.days.astype('Int64')
df_detalhe['Período de Homologação'] = (df_filtered['Fim Homologação'] - df_filtered['Início Homologação']).dt.days.astype('Int64')
df_detalhe['Tempo de todo processo'] = (df_filtered['Fim Homologação'] - df_filtered['Primeiro Contato']).dt.days.astype('Int64')

st.dataframe(df_detalhe, hide_index=True, use_container_width=True)