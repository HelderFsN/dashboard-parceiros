import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Relatório UEMA")

# Estilos CSS embutidos para replicar o design formal
st.markdown("""
<style>
/* Reset básico e tipografia */
body {
    font-family: Arial, sans-serif;
}
p {
    margin-bottom: 2px;
}
/* Cabeçalho Principal */
.header-blue {
    background-color: #0b406b;
    color: white;
    padding: 10px 15px;
    font-weight: bold;
    font-size: 16px;
    border-radius: 4px 4px 0 0;
}
.header-gray {
    background-color: #e0e0e0;
    color: #333;
    padding: 4px 15px;
    font-size: 11px;
    margin-bottom: 15px;
}
.title-section {
    text-align: center;
    font-weight: bold;
    margin: 20px 0 10px 0;
    line-height: 1.2;
}
.title-main {
    font-size: 18px;
}
.title-sub {
    font-size: 14px;
    color: #444;
}
.fiscal-info {
    text-align: right;
    font-size: 12px;
    margin-bottom: 5px;
}
/* Títulos de Blocos */
.block-title {
    background-color: #0b406b;
    color: white;
    padding: 5px 10px;
    font-weight: bold;
    font-size: 13px;
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
}
/* Grid Layouts */
.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 10px;
    font-size: 12px;
}
.grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 15px;
    margin-top: 10px;
    font-size: 12px;
}
/* Informações de Texto */
.lbl {
    font-weight: bold;
    font-size: 11px;
    margin-bottom: 1px;
    display: block;
    color: #000;
}
.val {
    font-size: 13px;
    margin-bottom: 10px;
    color: #333;
}
.val-destaque {
    font-size: 16px;
    font-weight: bold;
}
.val-alert {
    font-size: 16px;
    font-weight: bold;
    color: #d32f2f;
}
/* Tabelas Estilizadas */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    margin-top: 5px;
    margin-bottom: 15px;
}
.custom-table th {
    background-color: #f5f5f5;
    color: #333;
    border-bottom: 2px solid #ccc;
    padding: 5px;
    text-align: left;
}
.custom-table td {
    padding: 5px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
}
/* Status Color */
.status-pago {
    background-color: #c8e6c9;
    color: #2e7d32;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 10px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1JKXuQVSW6YpNuncPFhts2qIB8LcrJfHI3T8RHqZj63M/export?format=xlsx"
    xls = pd.ExcelFile(url)
    
    # Aba 1: Contratos
    df_contratos = pd.read_excel(xls, sheet_name='TB_Contratos_Rev0001')
    
    # Aba 2: Empresas (Contratadas)
    df_contratadas = pd.DataFrame()
    if 'TB_Contratadas_Rev0001' in xls.sheet_names:
        df_contratadas = pd.read_excel(xls, sheet_name='TB_Contratadas_Rev0001')
        
    # Aba 3: PDI
    df_pdi = pd.DataFrame()
    if 'TB_PDI_por_Contrato_Rev0001' in xls.sheet_names:
        df_pdi = pd.read_excel(xls, sheet_name='TB_PDI_por_Contrato_Rev0001')
        
    # Aba 4: Alterações e Aditamentos
    df_aditamentos = pd.DataFrame()
    if 'TB_Contratacoes_e_Aditamentos_R' in xls.sheet_names:
        df_aditamentos = pd.read_excel(xls, sheet_name='TB_Contratacoes_e_Aditamentos_R')
        
    # Aba 5: Pagamentos (Registros)
    df_pag = pd.DataFrame()
    if 'TB_Pagamentos_Rev0001' in xls.sheet_names:
        df_pag = pd.read_excel(xls, sheet_name='TB_Pagamentos_Rev0001')
        
    return {
        'contratos': df_contratos, 
        'contratadas': df_contratadas,
        'pdi': df_pdi,
        'aditamentos': df_aditamentos,
        'pagamentos': df_pag
    }

with st.spinner("Carregando banco de dados da UEMA..."):
    try:
        data = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

# Filtro Lateral
if 'Nº_CONTRATO' in data['contratos'].columns:
    lista_contratos = data['contratos']['Nº_CONTRATO'].dropna().unique()
else:
    st.error("Coluna 'Nº_CONTRATO' não encontrada na tabela principal.")
    st.stop()

st.sidebar.title("Opções")
selected_contrato = st.sidebar.selectbox("Selecione o Contrato:", lista_contratos)

# Filtrar dados pelo contrato selecionado
ct_row = data['contratos'][data['contratos']['Nº_CONTRATO'] == selected_contrato].iloc[0]
c_id = ct_row.get('ID', None)

# Se não tiver ID, tenta usar o próprio número de contrato para cruzar, mas a base mostrou que usa 'CONTRATO_ID'
if pd.isna(c_id): 
    st.warning("Este contrato não possui um ID válido.")
    st.stop()

# Busca tabelas dependentes
def filter_by_contrato_id(df, cid):
    if not df.empty and 'CONTRATO_ID' in df.columns:
        return df[df['CONTRATO_ID'] == cid]
    return pd.DataFrame()

df_empr = filter_by_contrato_id(data['contratadas'], c_id)
df_p = filter_by_contrato_id(data['pdi'], c_id)
df_ad = filter_by_contrato_id(data['aditamentos'], c_id)
df_pg = filter_by_contrato_id(data['pagamentos'], c_id)

# Extrações Seguras Principais
objeto = ct_row.get('DESCRIÇÃO_DO_OBJETO', 'Não preenchido')
regional = ct_row.get('REGIONAL_MUNICÍPIO', 'Não preenchido')
status_geral = ct_row.get('STATUS_GERAL', 'NÃO VIGENTE')

# Nome da contratada e CNPJ (pode estar na tabela de empresas)
razao_social = "NÃO LOCALIZADO"
cnpj = ""
if not df_empr.empty:
    razao_social = df_empr.iloc[0].get('RAZÃO_SOCIAL', 'Nome da Empresa não encontrado')
    cnpj = df_empr.iloc[0].get('CNPJ', '')

# --- Renderização HTML ---
# 1. Cabeçalhos Principais
st.markdown(f"""
<div class="header-blue">PRÓ-REITORIA DE INFRAESTRUTURA</div>
<div class="header-gray">CSOP | Segurança Patrimonial | Portaria | FAST | {selected_contrato}</div>

<div class="fiscal-info">Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}</div>

<div class="title-section">
    <div class="title-main">ACOMPANHAMENTO E CONTROLE DE CONTRATOS</div>
    <div class="title-sub">CSOP | DSEG</div>
</div>

<!-- Placeholder para nome do Fiscal se existir nas planilhas, fixo por enquanto -->
<div class="fiscal-info">Fiscal: Suely de Fátima Facenda Kusaba</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="block-title">
    <span>Serviços Contratados</span>
    <span>Nº Contrato</span>
</div>
<div class="grid-2" style="margin-bottom: 0;">
    <div>
        <span class="lbl">Serviços Continuados | Posto Mensal</span>
        <span class="val-destaque">Segurança Patrimonial | Portaria</span>
    </div>
    <div style="text-align: right;">
        <span class="val-destaque">{selected_contrato}</span>
    </div>
</div>

<div class="grid-2" style="border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
    <div>
        <span class="lbl">Contratada</span>
        <span class="val-destaque">{razao_social}</span>
        <div style="font-size: 10px; color: #555;">{cnpj}</div>
    </div>
    <div style="text-align: right;">
        <span class="lbl">Status Geral</span>
        <span class="{'val-alert' if 'NÃO' in str(status_geral).upper() else 'val-destaque'}">{status_geral}</span>
    </div>
</div>

<div class="grid-2" style="border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
    <div>
        <span class="lbl">Descrição do Objeto</span>
        <span class="val">{objeto}</span>
    </div>
    <div>
        <span class="lbl">Regional/Município</span>
        <span class="val">{regional}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# 2. PDI
st.markdown("""<div class="block-title">Plano de Desenvolvimento Institucional (PDI) 2026-2030</div>""", unsafe_allow_html=True)
if not df_p.empty:
    pdi_html = "<table class='custom-table'><tr><th>Tópico</th><th>Projeto Estruturante</th><th>Entrega</th><th>Unidade Responsável</th></tr>"
    for _, row in df_p.iterrows():
        topico = row.get('TÓPICO', '')
        projeto = row.get('TÍTULO DO PROJETO', '')
        entrega = row.get('TÍTULO DA ENTREGA', '')
        resp = row.get('UNIDADE RESPONSÁVEL', '')
        pdi_html += f"<tr><td>{topico}</td><td>{projeto}</td><td>{entrega}</td><td>{resp}</td></tr>"
    pdi_html += "</table>"
    st.markdown(pdi_html, unsafe_allow_html=True)
else:
    st.markdown("<p style='font-size:12px; color:#666;'><em>Nenhum registro PDI encontrado para este contrato.</em></p>", unsafe_allow_html=True)


# 3. Prazos Contratuais / Valores Contratuais
# Valores podem ser obtidos do primeiro aditamento ('Contrato')
vr_global = 0.0
# Pega o valor do primeiro termo 'Contrato'
ct_ad_base = df_ad[df_ad.get('TERMO_TIPO', '') == 'Contrato']
if not ct_ad_base.empty:
    vr_global = ct_ad_base.iloc[0].get('VR_GLOBAL_COM_REAJUSTE_E_REPACTUACAO', 0.0)

st.markdown(f"""
<div class="block-title">Prazos Contratuais</div>
<div class="grid-3" style="padding: 10px 0;">
    <div><span class="lbl">Prazo de Execução</span></div>
    <div><span class="lbl">Início</span><span>-</span></div>
    <div><span class="lbl">Término</span><span>-</span></div>
</div>
<div class="grid-3" style="border-top: 1px solid #eee; padding: 10px 0;">
    <div><span class="lbl">Prazo de Vigência</span></div>
    <div><span class="lbl">Início</span><span>-</span></div>
    <div><span class="lbl">Término</span><span>-</span></div>
</div>

<div class="block-title">Valores Contratuais</div>
<div class="grid-2" style="padding: 10px 0;">
    <div><span class="lbl">Valor Global do Contrato</span></div>
    <div style="font-weight:bold;">R$ {vr_global:,.2f}</div>
</div>
""", unsafe_allow_html=True)

# 4. Alterações e Aditamentos
st.markdown("""<div class="block-title">Contrato e Alterações</div>""", unsafe_allow_html=True)
if not df_ad.empty:
    html_ad = """<table class='custom-table'>
    <tr>
        <th>Processo Administrativo</th>
        <th>Instrumento Contratual (Termo)</th>
        <th>Acréscimo/Supressão</th>
        <th>Valor Global (R$)</th>
        <th>Início Vigência</th>
        <th>Término Vigência</th>
    </tr>"""
    for _, row in df_ad.iterrows():
        proc = row.get('Nº_PROCESSO', '')
        termo = row.get('TERMO_TIPO', '')
        acres = row.get('VR_ACRÉSCIMOS_LEI', 0)
        sup = row.get('VR_SUPRESSÃO', 0)
        vr_g = row.get('VR_GLOBAL_COM_REAJUSTE_E_REPACTUACAO', 0)
        inv = str(row.get('INÍCIO_VIGÊNCIA', ''))[:10]
        termv = str(row.get('TÉRMINO_VIGÊNCIA', ''))[:10]
        
        diff = ""
        if pd.notnull(acres) and acres > 0: diff = f"+ R$ {acres:,.2f}"
        elif pd.notnull(sup) and sup > 0: diff = f"- R$ {sup:,.2f}"
        
        # Tratamento de NaNs (nan para string renderiza 'nan')
        if pd.isna(proc) or str(proc) == 'nan': proc = '-'
        if pd.isna(vr_g): vr_g = 0
        if inv == 'NaT' or inv == 'nan': inv = '-'
        if termv == 'NaT' or termv == 'nan': termv = '-'

        html_ad += f"""<tr>
            <td>{proc}</td>
            <td>{termo}</td>
            <td>{diff}</td>
            <td>R$ {vr_g:,.2f}</td>
            <td>{inv}</td>
            <td>{termv}</td>
        </tr>"""
    html_ad += "</table>"
    st.markdown(html_ad, unsafe_allow_html=True)
else:
    st.markdown("<p style='font-size:12px; color:#666;'><em>Nenhum aditamento encontrado.</em></p>", unsafe_allow_html=True)


# 5. Registros de Pagamento (NFs)
st.markdown("""<div class="block-title">Registros (Notas Fiscais / Pagamentos)</div>""", unsafe_allow_html=True)
if not df_pg.empty:
    # Ordenar se houver data de medição ou emissão
    try:
        df_pg = df_pg.sort_values(by='MED_INICIO', ascending=True)
    except:
        pass
    
    html_pg = """<table class='custom-table'>
    <tr>
        <th>Nº Processo</th>
        <th>Período Exe. (Início)</th>
        <th>Período Exe. (Término)</th>
        <th>Valor Faturado (R$)</th>
        <th>Nota Fiscal (NF)</th>
        <th>Liquidação/Ateste</th>
        <th>Situação</th>
    </tr>"""
    
    for _, row in df_pg.iterrows():
        proc_nf = row.get('Nº_PROCESSO', '-')
        med_in = str(row.get('MED_INICIO', '-'))[:10]
        med_out = str(row.get('MED_TÉRMINO', '-'))[:10]
        vr_fat = row.get('VALOR_FATURADO', 0)
        nf = row.get('Nº_NF', '-')
        liq = str(row.get('DT_LIQUIDAÇÃO', '-'))[:10]
        sit = row.get('SITUAÇÃO', '')
        
        if pd.isna(proc_nf) or str(proc_nf) == 'nan': proc_nf = '-'
        if pd.isna(vr_fat): vr_fat = 0
        if pd.isna(nf) or str(nf) == 'nan': nf = '-'
        if med_in == 'NaT' or med_in == 'nan': med_in = '-'
        if med_out == 'NaT' or med_out == 'nan': med_out = '-'
        if liq == 'NaT' or liq == 'nan': liq = '-'
        if pd.isna(sit) or str(sit) == 'nan': sit = '-'
        
        sit_class = ""
        if 'PAGO' in str(sit).upper(): sit_class = "status-pago"
        # Se for pendente pode criar outra classe depois: elif 'PENDENTE' in ...
        
        html_pg += f"""<tr>
            <td>{proc_nf}</td>
            <td>{med_in}</td>
            <td>{med_out}</td>
            <td><b>R$ {vr_fat:,.2f}</b></td>
            <td>{nf}</td>
            <td>{liq}</td>
            <td><span class="{sit_class}">{sit}</span></td>
        </tr>"""
    html_pg += "</table>"
    st.markdown(html_pg, unsafe_allow_html=True)
else:
    st.markdown("<p style='font-size:12px; color:#666;'><em>Sem registros financeiros para este contrato.</em></p>", unsafe_allow_html=True)