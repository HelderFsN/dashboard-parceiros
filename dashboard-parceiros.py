import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import numpy as np

# Configurar layout da página
st.set_page_config(layout="wide", page_title="Dashboard de Parceiros Integrado")

@st.cache_data
def load_data():
    # ID da Planilha
    sheet_id = "1ncUO3qsAr8edPs3Cee_H4kFcwvZc4yTGV1tlVq5zXV8"
    
    # URL da Aba 1 (Datas e SLA) - Geralmente gid=0
    url_p1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=651550249"
    # URL da Aba 2 (O que aparece no seu print: Parceiros, UF, Status)
    # Nota: Você precisa verificar o número do GID na barra de endereços do navegador ao clicar na Página2
    # Vou usar o padrão '1452934057' como exemplo, mas substitua pelo GID correto da aba Página2
    url_p2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=452225427"

    # Lendo as duas abas
    df1 = pd.read_csv(url_p1)
    df2 = pd.read_csv(url_p2)

    # Padronizando colunas da Aba 1
    df1.columns = [
        'Parceiros', 'Estado_Original', 'Primeiro Contato', 'Entrevista', 
        'Início Homologação', 'Processo Equatorial', 'Assinatura Contrato', 
        'Fim Homologação', 'SLA (dias)'
    ]

    # Cruzando os dados (Merge) com base no nome do Parceiro
    # Isso traz a 'UF' e o 'Status' da Página 2 para dentro do dataframe principal
    df = pd.merge(df1, df2, on='Parceiros', how='left')

    # Converter para datetime
    date_cols = ['Primeiro Contato', 'Entrevista', 'Início Homologação', 'Processo Equatorial', 'Assinatura Contrato', 'Fim Homologação']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')

    return df

df = load_data()

if df.empty:
    st.stop()

# Lógica de Classificação da Situação (fase)
def get_phase_integrated(row):
    # 1. PRIORIDADE MÁXIMA: Status manual da Página 2 (ex: Echo, Homologado, Análise)
    # Se você escreveu algo no print que enviou, o sistema obedece cegamente.
    if pd.notnull(row['Status']):
        return row['Status']
    
    # 2. SEGUNDA PRIORIDADE: Verificação automática por datas
    if pd.notnull(row['Fim Homologação']):
        return "Homologado"
    
    if pd.notnull(row['Início Homologação']):
        return "Em Homologação"
    
    if pd.notnull(row['Entrevista']):
        return "Em Análise" # Ou "Em Entrevista", como preferir
        
    if pd.notnull(row['Primeiro Contato']):
        return "Parceiro - documentação"
    
    # 3. SE NÃO TIVER NADA: O parceiro ainda não entrou no fluxo
    return "Sem Contato"

df['Fase'] = df.apply(get_phase_integrated, axis=1)

def get_etapa_atual(row):
    if pd.notnull(row['Fim Homologação']):
        return "Concluído"
    elif pd.notnull(row['Assinatura Contrato']):
        return "Homologação" 
    elif pd.notnull(row['Início Homologação']):
        return "Assinatura de Contrato"
    elif pd.notnull(row['Entrevista']):
        return "Aguardando Homologação"
    elif pd.notnull(row['Primeiro Contato']):
        return "Entrevista"
    return "Não Iniciado"

df['Etapa Atual'] = df.apply(get_etapa_atual, axis=1)

# Lógica de "Situação" para a tabela (ATRASADO)
hoje = pd.to_datetime(datetime.today().date())
def get_situation(row):
    # Se já foi homologado / fim da homologação preenchido, ok
    if pd.notnull(row['Fim Homologação']):
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

if st.sidebar.button("🔄 Atualizar Dados"):
    load_data.clear()
    st.rerun()

st.sidebar.markdown("---")

estados = ['Todos'] + sorted(df['Estado'].dropna().unique().tolist())
select_estado = st.sidebar.selectbox("Estado", estados)

if select_estado != 'Todos':
    df_filtered = df[df['Estado'] == select_estado].copy()
else:
    df_filtered = df.copy()

fases = sorted(df_filtered['Fase'].dropna().unique().tolist())
select_fase = st.sidebar.multiselect("Fase (vazio = Todas)", options=fases, default=[])

if select_fase:
    df_filtered = df_filtered[df_filtered['Fase'].isin(select_fase)]

etapas = sorted(df_filtered['Etapa Atual'].dropna().unique().tolist())
select_etapa = st.sidebar.multiselect("Etapa Atual (vazio = Todas)", options=etapas, default=[])

if select_etapa:
    df_filtered = df_filtered[df_filtered['Etapa Atual'].isin(select_etapa)]

parceiros = ['Todos'] + sorted(df_filtered['Parceiros'].dropna().unique().tolist())
select_parceiro = st.sidebar.selectbox("Parceiro", parceiros)

if select_parceiro != 'Todos':
    df_filtered = df_filtered[df_filtered['Parceiros'] == select_parceiro]

# Preparar dados numéricos temporais para os gráficos
df_charts = df_filtered[['Parceiros']].copy()
def calc_dias_num(start, end, block_pending=False):
    hoje = pd.to_datetime(datetime.today().date())
    if pd.isnull(start) and pd.isnull(end): return None
    if pd.notnull(start) and pd.isnull(end):
        if block_pending: return None
        return (hoje - start).days
    if pd.isnull(start) and pd.notnull(end): return None
    return (end - start).days

if not df_filtered.empty:
    df_charts['T_Entrevista'] = df_filtered.apply(lambda r: calc_dias_num(r['Primeiro Contato'], r['Entrevista']), axis=1)
    df_charts['T_Contrato'] = df_filtered.apply(lambda r: calc_dias_num(r['Início Homologação'], r['Assinatura Contrato'], block_pending=pd.isnull(r['Entrevista'])), axis=1)
    df_charts['T_Homolog'] = df_filtered.apply(lambda r: calc_dias_num(r['Início Homologação'], r['Fim Homologação'], block_pending=pd.isnull(r['Assinatura Contrato'])), axis=1)
    df_charts['T_Total'] = df_filtered.apply(lambda r: calc_dias_num(r['Primeiro Contato'], r['Fim Homologação'], block_pending=True), axis=1)

# Construindo as colunas principais
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("### Tabela de Parceiros")
    
    # Preparar df para exibição
    df_exibir = df_filtered[['Parceiros', 'Etapa Atual', 'Situação']].copy()
    
    # Estilização condicional do Pandas
    def color_status(val):
        if val == 'ATRASADO':
            color = '#ff4b4b'
            font_weight = 'bold' 
            text_color = 'white'
        elif val == 'CONCLUÍDO':
            color = '#00cc66'
            font_weight = 'bold'
            text_color = 'white'
        else:
            color = 'transparent'
            font_weight = 'normal'
            text_color = 'inherit'
        return f'background-color: {color}; color: {text_color}; font-weight: {font_weight}'

    st.dataframe(
        df_exibir.style.applymap(color_status, subset=['Situação']),
        hide_index=True,
        use_container_width=True,
        height=350
    )

with col_right:
    st.markdown("### Distribuição das Fases")
    # Gráfico de Pizza com Altair
    fases_count = df_filtered['Fase'].value_counts().reset_index()
    fases_count.columns = ['Fase', 'Contagem']
    
    if not fases_count.empty:
        # Cria rótulo com a quantidade apenas para a legenda
        fases_count['Fase + Total'] = fases_count.apply(lambda x: f"{x['Fase']} ({x['Contagem']})", axis=1)
        
        chart = alt.Chart(fases_count).mark_arc(innerRadius=0).encode(
            theta=alt.Theta(field="Contagem", type="quantitative"),
            color=alt.Color(
                field="Fase + Total", 
                type="nominal", 
                legend=alt.Legend(
                    title="Fase (Total)", 
                    orient="bottom", 
                    columns=2, 
                    labelLimit=0
                )
            ),
            tooltip=['Fase', 'Contagem']
        ).properties(height=380)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Sem dados para o gráfico")

st.markdown("---")
st.markdown("### Métricas por Parceiro (Dias)")

def plot_bar(col_id, title, color):
    if df_filtered.empty or col_id not in df_charts.columns:
        st.info(f"Sem dados para: {title}")
        return
    
    data = df_charts[['Parceiros', col_id]].dropna()
    if data.empty:
        st.info(f"Sem dados para: {title}")
        return
        
    chart = alt.Chart(data).mark_bar(color=color, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('Parceiros:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{col_id}:Q', title='Dias'),
        tooltip=['Parceiros', alt.Tooltip(f'{col_id}:Q', title='Dias')]
    ).properties(title=title, height=220)
    st.altair_chart(chart, use_container_width=True)

plot_bar('T_Entrevista', 'Tempo para iniciar entrevista', '#0076cf')
plot_bar('T_Contrato', 'Tempo para assinar o contrato', '#00cc66')
plot_bar('T_Homolog', 'Período de Homologação', '#ff9900')
plot_bar('T_Total', 'Tempo de todo processo', '#8a2be2')

st.markdown("---")
st.subheader("⏱️ Detalhamento de Tempo por Parceiro (em dias)")

# Calcular tempos individuais (em dias) com condicional de "Pendente" usando o dia atual
df_detalhe = df_filtered[['Parceiros', 'Fase', 'Situação']].copy()

def calc_detalhes_row(row):
    hoje = pd.to_datetime(datetime.today().date())
    
    def calc_tempo(start, end, block_pending=False):
        if pd.isnull(start) and pd.isnull(end):
            return "-"
        elif pd.notnull(start) and pd.isnull(end):
            if block_pending: return "-"
            return f"{(hoje - start).days} dias (Pendente)"
        elif pd.isnull(start) and pd.notnull(end):
            return "-"
        else:
            return f"{(end - start).days} dias"
            
    return pd.Series({
        'Etapa Atual': row['Etapa Atual'],
        'Entrevista': calc_tempo(row['Primeiro Contato'], row['Entrevista']),
        'Assinatura de Contrato': calc_tempo(row['Início Homologação'], row['Assinatura Contrato'], block_pending=pd.isnull(row['Entrevista'])),
        'Homologação': calc_tempo(row['Início Homologação'], row['Fim Homologação'], block_pending=pd.isnull(row['Assinatura Contrato'])),
        'Todo Processo': calc_tempo(row['Primeiro Contato'], row['Fim Homologação'], block_pending=True)
    })

if not df_filtered.empty:
    novas_colunas = df_filtered.apply(calc_detalhes_row, axis=1)
    df_detalhe = pd.concat([df_detalhe, novas_colunas], axis=1)
else:
    for col in ['Etapa Atual', 'Entrevista', 'Assinatura de Contrato', 'Homologação', 'Todo Processo']:
        df_detalhe[col] = pd.Series(dtype='object')

st.dataframe(df_detalhe, hide_index=True, use_container_width=True)