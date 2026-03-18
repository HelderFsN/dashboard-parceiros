import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide", page_title="Relatório Contratual UEMA")

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1JKXuQVSW6YpNuncPFhts2qIB8LcrJfHI3T8RHqZj63M/export?format=xlsx"
    xls = pd.ExcelFile(url)
    
    dfs = {
        'contratos': pd.DataFrame(),
        'contratadas': pd.DataFrame(),
        'pdi': pd.DataFrame(),
        'aditamentos': pd.DataFrame(),
        'pagamentos': pd.DataFrame()
    }
    
    if 'TB_Contratos_Rev0001' in xls.sheet_names:
        dfs['contratos'] = pd.read_excel(xls, sheet_name='TB_Contratos_Rev0001')
    if 'TB_Contratadas_Rev0001' in xls.sheet_names:
        dfs['contratadas'] = pd.read_excel(xls, sheet_name='TB_Contratadas_Rev0001')
    if 'TB_PDI_por_Contrato_Rev0001' in xls.sheet_names:
        dfs['pdi'] = pd.read_excel(xls, sheet_name='TB_PDI_por_Contrato_Rev0001')
    if 'TB_Contratacoes_e_Aditamentos_R' in xls.sheet_names:
        dfs['aditamentos'] = pd.read_excel(xls, sheet_name='TB_Contratacoes_e_Aditamentos_R')
    if 'TB_Pagamentos_Rev0001' in xls.sheet_names:
        dfs['pagamentos'] = pd.read_excel(xls, sheet_name='TB_Pagamentos_Rev0001')
        
    return dfs

with st.spinner("Carregando banco de dados corporativo..."):
    data = load_data()

# Filtro
if 'Nº_CONTRATO' in data['contratos'].columns:
    lista_contratos = data['contratos']['Nº_CONTRATO'].dropna().unique()
else:
    st.error("Erro estrutural: Base de dados sem número de contratos visível.")
    st.stop()

st.sidebar.title("Navegação")
selected_contrato = st.sidebar.selectbox("Código do Contrato:", lista_contratos)

# Referência de contrato
ct_row = data['contratos'][data['contratos']['Nº_CONTRATO'] == selected_contrato].iloc[0]
c_id = ct_row.get('ID', None)

if pd.isna(c_id):
    st.warning("O contrato selecionado não possui ID mapeado para cruzamento.")
    st.stop()

# Filtros seguros
def get_df_by_id(df, cid):
    if not df.empty and 'CONTRATO_ID' in df.columns:
        return df[df['CONTRATO_ID'] == cid].copy()
    return pd.DataFrame()

df_empr = get_df_by_id(data['contratadas'], c_id)
df_p = get_df_by_id(data['pdi'], c_id)
df_ad = get_df_by_id(data['aditamentos'], c_id)
df_pg = get_df_by_id(data['pagamentos'], c_id)

# Variáveis globais base para preenchimento
objeto = ct_row.get('DESCRIÇÃO_DO_OBJETO', '-')
regional = ct_row.get('REGIONAL_MUNICÍPIO', 'CAPITAL/INTERIOR')
status_geral = ct_row.get('STATUS_GERAL', 'NÃO VIGENTE')

nm_fantasia = "EMPRESA NÃO ENCONTRADA"
rz_social = "-"
cnpj = "-"
if not df_empr.empty:
    nm_fantasia = df_empr.iloc[0].get('CONTRATADA_MAIS_RESUMIDO', df_empr.iloc[0].get('RAZÃO_SOCIAL', 'FAST'))
    rz_social = df_empr.iloc[0].get('RAZÃO_SOCIAL', '-')
    cnpj = df_empr.iloc[0].get('CNPJ', '-')

vr_global = 0.0
ad_contrato = df_ad[df_ad.get('TERMO_TIPO', '') == 'Contrato']
if not ad_contrato.empty:
    vr_global = ad_contrato.iloc[0].get('VR_GLOBAL_COM_REAJUSTE_E_REPACTUACAO', 0.0)

# ======================== RENDERING HTML/CSS ========================

html_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');

.report-container {
    font-family: 'Roboto', sans-serif;
    color: #000;
    max-width: 1100px;
    margin: 0 auto;
    background: #fff;
    padding: 0 10px 40px 10px;
}
/* CABEÇALHOS GERAIS */
.top-header {
    background-color: #053b5c; /* Azul marinho escuro UEMA */
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 15px;
    border-radius: 3px 3px 0 0;
}
.top-header .text {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
}
.top-header img {
    height: 30px;
}
.gray-bar {
    background-color: #efefef;
    display: flex;
    justify-content: space-between;
    padding: 2px 0 2px 15px;
    font-size: 11px;
    color: #f1f2f3;
    position: relative;
}
.gray-bar .text {
    color: #fff;
    font-weight: bold;
    opacity: 0.15; /* Simula o texto apagado da imagem */
}
.gray-bar .arrow {
    width: 0;
    height: 0;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    border-left: 10px solid #f29000;
}
.date-right {
    text-align: right;
    font-size: 10px;
    font-weight: bold;
    margin-top: 5px;
}
.main-title {
    text-align: center;
    font-size: 18px;
    font-weight: 900;
    margin-top: 10px;
}
.sub-title {
    text-align: center;
    font-size: 13px;
    margin-bottom: 20px;
}
.fiscal-title {
    text-align: right;
    font-size: 11px;
    font-weight: bold;
    margin-bottom: 5px;
}

/* GUIAS AZUIS */
.blue-bar {
    background-color: #053b5c;
    color: #fff;
    font-size: 12px;
    font-weight: bold;
    padding: 5px 10px;
    margin-top: 20px;
    display:flex;
    justify-content: space-between;
}
.blue-bar.half {
    width: 100%;
}
.blue-bar-yellow-btn {
    color: #ffcc00; /* Amarelo INICIAR NOVA CONTRATACAO */
    background-color: #116244;
    padding: 2px 8px;
    font-size: 11px;
}

/* TABELAS E GRIDS GERAIS */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
}
td, th {
    padding: 4px;
    vertical-align: top;
    text-align: left;
}
.no-border td { border: none !important; }
.border-b { border-bottom: 1px solid #000; }
.border-t { border-top: 1px solid #000; }

.small-lbl {
    font-size: 9px;
    font-weight: bold;
    display: block;
}
.val-lbl {
    font-size: 12px;
}
.val-huge {
    font-size: 18px;
    font-weight: 900;
}

/* Resumo Específico */
.resumo-table th { background-color: #053b5c; color: white; border: none; font-size: 11px; }
.resumo-table td { border-bottom: 1px solid #eee; }
.resumo-table tr:nth-child(even) { background-color: #f9f9f9; }
.resumo-table .total-row { background-color: #efefef; font-weight: bold; }

/* Status Pago */
.box-pago {
    background-color: #aed581; /* Verde clarinho igual imagem */
    border: 1px solid #558b2f;
    font-size: 9px;
    padding: 2px 4px;
    display: block;
    line-height: 1.2;
}
.box-text-small {
    font-size: 8px;
    display: block;
}

</style>
"""

# HTML Assembly - Part 1: Cabeçalho base
html_content = html_style + f"""
<div class="report-container">
    <div class="top-header">
        <span class="text">PRÓ-REITORIA DE INFRAESTRUTURA</span>
        <img src="https://www.uema.br/wp-content/uploads/2018/06/marca_UEMA.png" alt="UEMA">
    </div>
    <div class="gray-bar">
        <span class="text">CSOP | Segurança Patrimonial | Portaria | FAST | {selected_contrato}</span>
        <div class="arrow"></div>
    </div>
    <div class="date-right">Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}</div>
    
    <div class="main-title">ACOMPANHAMENTO E CONTROLE DE CONTRATOS</div>
    <div class="sub-title">CSOP | DSEG</div>
    
    <div class="fiscal-title">Fiscal: Suely de Fátima Facenda Kusaba</div>
    
    <div class="blue-bar">
        <span>Serviços Contratados</span>
        <span>Nº Contrato</span>
    </div>
    <table class="no-border" style="margin-top: 5px;">
        <tr>
            <td style="color: #666; font-size: 11px;">Serviços Continuados | Posto Mensal</td>
            <td style="text-align: right; font-weight: bold; font-size: 13px;">{selected_contrato}</td>
        </tr>
        <tr>
            <td colspan="2" style="font-weight: bold; font-size: 13px; border-bottom: 1px solid #ccc; padding-bottom: 10px;">Segurança Patrimonial | Portaria</td>
        </tr>
        <tr>
            <td style="padding-top: 10px;">
                <span class="small-lbl">Contratada</span>
                <span style="font-weight:900; font-size:14px;">{nm_fantasia.upper()}</span><br>
                <span style="font-size:10px;">{rz_social} ({cnpj})</span>
            </td>
            <td style="text-align: right; padding-top: 10px;">
                <span class="small-lbl">Status Geral</span>
                <span class="val-huge">{status_geral.upper()}</span>
            </td>
        </tr>
    </table>
    <table class="no-border border-t" style="margin-top: 5px; padding-top: 5px;">
        <tr>
            <td style="width: 70%;">
                <span class="small-lbl">Descrição do Objeto</span>
                <span class="val-lbl">{str(objeto)}</span>
            </td>
            <td style="width: 30%;">
                <span class="small-lbl">Regional/Município</span>
                <span class="val-lbl">{str(regional)}</span>
            </td>
        </tr>
    </table>
"""

# Part 2: PDI Table
html_content += """<div class="blue-bar">Plano de Desenvolvimento Institucional (PDI) 2026-2030</div>"""
if not df_p.empty:
    html_content += """<table class="border-b" style="margin-top:5px; margin-bottom:15px;">
        <tr style="border-bottom: 1px solid #000;">
            <th>Tópico</th><th>Projeto Estruturante</th><th>Entrega</th><th>Unidade Responsável</th>
        </tr>"""
    for _, row in df_p.iterrows():
        t = str(row.get('TÓPICO', ''))
        p = str(row.get('TÍTULO DO PROJETO', ''))
        e = str(row.get('TÍTULO DA ENTREGA', ''))
        u = str(row.get('UNIDADE RESPONSÁVEL', ''))
        html_content += f"<tr><td>{t}</td><td>{p}</td><td>{e}</td><td>{u}</td></tr>"
    html_content += "</table>"
else:
    html_content += "<table class='border-b'><tr><td>Nenhum registro PDI mapeado</td></tr></table>"

# Dotação (Hardcoded structure to match image visually perfectly since we didn't extract the tab)
html_content += """
    <div class="blue-bar">Dotação Orçamentária (Rubrica)</div>
    <table class="no-border border-b" style="margin-top:5px;">
        <tr>
            <td><span class="small-lbl">Programa</span><span class="val-lbl">411 - Apoio Administrativo</span></td>
            <td><span class="small-lbl">Subfunção</span><span class="val-lbl">122 - Administração Geral</span></td>
            <td><span class="small-lbl">Ação</span><span class="val-lbl">4457 - Administração da Unidade</span></td>
        </tr>
        <tr>
            <td colspan="2"><span class="small-lbl">Subação</span><span class="val-lbl">3854 - VIGILÂNCIA</span></td>
            <td><span class="small-lbl">Natureza da Despesa</span><span class="val-lbl">333903930 - Serviço de Bilheteria e Portaria</span></td>
        </tr>
    </table>
"""

# Prazos and Valores 
html_content += f"""
    <div class="blue-bar">
        <span>Prazos Contratuais</span>
        <span class="blue-bar-yellow-btn" style="float:right;">INICIAR NOVA CONTRATAÇÃO</span>
    </div>
    <table class="no-border border-b" style="margin-top:5px;">
        <tr>
            <td style="width:30%; font-weight:bold;">Prazo de Execução</td>
            <td style="width:20%;"><span class="small-lbl">Início</span>-</td>
            <td style="width:20%;"><span class="small-lbl">Término</span>-</td>
            <td style="width:30%;"><span class="small-lbl">Obs.:</span> </td>
        </tr>
        <tr>
            <td style="font-weight:bold;">Prazo de Vigência</td>
            <td><span class="small-lbl">Início</span>-</td>
            <td><span class="small-lbl">Término</span>-</td>
            <td><span class="small-lbl">Obs.:</span>Após xº Termo Aditivo</td>
        </tr>
    </table>

    <div class="blue-bar">Valores Contratuais</div>
    <table class="no-border border-b" style="margin-top:5px;">
        <tr>
            <td style="width:70%; font-weight:bold;">Valor Global do Contrato</td>
            <td style="width:30%; font-weight:bold; font-size:14px; text-align:right;">R$ {vr_global:,.2f}</td>
        </tr>
    </table>
"""

# TRATAMENTO DE ADITAMENTOS COM TÍTULOS DENTRO DA BLUE-BAR
html_content += """
    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
        <tr>
            <td class="blue-bar" style="margin-top:0; width:45%;">Contrato e Alterações</td>
            <td class="blue-bar" style="margin-top:0; width:35%; text-align:center;">Valores Contratuais</td>
            <td class="blue-bar" style="margin-top:0; width:20%; text-align:center;">Prazos Contratuais</td>
        </tr>
    </table>
    <table class="custom-table border-b">
        <tr>
            <th>Processo<br>Administrativo</th>
            <th>Instrumento Contratual<br>(Termo)</th>
            <th style="text-align:center;">Acréscimo<br>(%)</th>
            <th style="text-align:center;">Supressão<br>(%)</th>
            <th style="text-align:center;">Reajuste ou<br>Repactuação<br>(% Acum.)</th>
            <th style="text-align:right;">Valor Global (R$)</th>
            <th style="text-align:center;">Execução<br>Término</th>
            <th style="text-align:center;">Vigência<br>Término</th>
        </tr>
"""
if not df_ad.empty:
    for _, row in df_ad.iterrows():
        proc = str(row.get('Nº_PROCESSO', '-'))
        # Para que apareça como "1º Termo Aditivo \n Repactuação" substituimos nan ou none
        termo = str(row.get('TERMO_TIPO', '-'))
        vg = row.get('VR_GLOBAL_COM_REAJUSTE_E_REPACTUACAO', 0.0)
        vig_end = str(row.get('TÉRMINO_VIGÊNCIA', '-'))[:10]
        acre = row.get('PORCENTAGEM_ACRESCIMO', '') # Campos hipotéticos pois nao tem na base
        supp = row.get('PORCENTAGEM_SUPRESSAO', '')
        repac = row.get('PORCENTAGEM_REPACTUACAO', '')
        
        if pd.isna(vg): vg = 0
        if vig_end == 'NaT' or vig_end == 'nan': vig_end = '-'
        if str(proc) == 'nan': proc = '-'
        if str(termo) == 'nan': termo = '-'
        
        html_content += f"""<tr>
            <td>{proc}</td>
            <td>{termo}</td>
            <td style="text-align:center;">{"-" if pd.isna(acre) else acre}</td>
            <td style="text-align:center;">{"-" if pd.isna(supp) else supp}</td>
            <td style="text-align:center;">{"-" if pd.isna(repac) else repac}</td>
            <td style="text-align:right;">R$ {float(vg):,.2f}</td>
            <td style="text-align:center;">-</td>
            <td style="text-align:center;">{vig_end}</td>
        </tr>"""
else:
    html_content += "<tr><td colspan='8'>Sem aditamentos.</td></tr>"
html_content += "</table>"

# Parte 3: PAGAMENTOS Resumo e Registros
# Simulação da Header azul dupla "Resumo Financeiro | % Acumulado"
html_content += """
    <div class="blue-bar" style="justify-content:flex-start;">
        <span style="width: 25%;">Resumo Financeiro (por vigência)</span>
        <span style="width: 15%; text-align:right;">Valor Total (R$)</span>
        <span style="width: 15%; text-align:right;">Pago (R$)</span>
        <span style="width: 10%; text-align:right;">% Pago</span>
        <span style="width: 10%; text-align:right;">A Pagar (R$)</span>
        <span style="width: 15%; text-align:right;">Acumulado (R$)</span>
        <span style="width: 10%; text-align:right;">Saldo (R$)</span>
    </div>
"""
# Simulador the lines internally. I will fetch from "Aditamentos" to generate the list.
html_content += "<table class='resumo-table'>"
if not df_ad.empty:
    for idx, row in df_ad.iterrows():
        name = str(row.get('TERMO_TIPO', f'Termo {idx}'))
        vr = float(row.get('VR_GLOBAL_COM_REAJUSTE_E_REPACTUACAO', 0))
        if pd.isna(vr): vr = 0
        # Placeholder sums as we don't have the explicit table for Resumo Financeiro
        html_content += f"<tr><td>{name}</td><td style='text-align:right;'>R$ {vr:,.2f}</td><td style='text-align:right;'>-</td><td style='text-align:right;'>-</td><td style='text-align:right;'>-</td><td style='text-align:right;'>-</td><td style='text-align:right;'>-</td></tr>"
html_content += "<tr class='total-row'><td>Total a Pagar</td><td style='text-align:right;'>-</td><td style='text-align:right;'>-</td><td></td><td style='text-align:right;'>-</td><td></td><td></td></tr></table>"

# Tabela PAGO / SITUACAO
html_content += """
    <div class="blue-bar" style="justify-content: space-between; margin-top: 15px;">
        <span>Pagamentos</span>
        <span>SITUAÇÃO ATUAL: NÃO APRESENTA ATRASO DE PAGAMENTO</span>
    </div>
    <div style="background-color:#f5f5f5; padding:10px; font-size:11px; display:flex; justify-content:space-between;">
        <div style="text-align:center;"><span style="font-size:13px; font-weight:bold;">Há 46 dias</span><br>Período da última aferição: até 31/01/2026</div>
        <div style="text-align:center;"><span style="font-size:13px; font-weight:bold;">14 dias em aberto</span><br>Média - Nota Fiscal Atestada</div>
        <div style="text-align:center;"><span style="font-size:13px; font-weight:bold;">14% do período c/ atraso</span><br>Total: 25 dias atraso</div>
        <div style="text-align:center;"><span style="font-size:13px; font-weight:bold;">0% do período c/ atraso</span><br>Sem Registros</div>
    </div>
"""

# Registros Headers
num_reg = len(df_pg) if not df_pg.empty else 0
html_content += f"""
    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
        <tr>
            <td class="blue-bar" style="margin-top:0; width:30%;">Registros: {num_reg}</td>
            <td class="blue-bar" style="margin-top:0; width:70%;">Período de Execução</td>
        </tr>
    </table>
    <table class="custom-table border-b">
        <tr style="background:#053b5c; color:#fff;">
            <th>Ord.</th>
            <th>Processo Administrativo</th>
            <th>Termo</th>
            <th>Medição</th>
            <th>Início</th>
            <th>Término</th>
            <th style="text-align:right;">Valor Total (R$)</th>
            <th style="text-align:center;">Nota Fiscal (NF)</th>
            <th style="text-align:center;">Ateste NF</th>
            <th>Situação</th>
        </tr>
"""
if not df_pg.empty:
    for idx, row in df_pg.iterrows():
        proc_nf = str(row.get('Nº_PROCESSO', '-'))
        if proc_nf == 'nan': proc_nf = '-'
        termo_nf = str(row.get('TIPO', '')) # 'TERMO' may be missing, put placeholder
        if termo_nf == 'nan': termo_nf = ''
        
        med = str(row.get('Nº_MEDIÇÃO', ''))
        med_in = str(row.get('MED_INICIO', '-'))[:10]
        med_out = str(row.get('MED_TÉRMINO', '-'))[:10]
        vr_fat = float(row.get('VALOR_FATURADO', 0.0))
        if pd.isna(vr_fat): vr_fat = 0.0
        
        nf = str(row.get('Nº_NF', '-'))
        ateste = str(row.get('DT_ATESTO_NF', '-'))[:10]
        
        sit = str(row.get('SITUAÇÃO', '-'))
        status_amplo = str(row.get('STATUS_AMPLO', '')).replace('\n', '<br>')
        
        if med_in == 'NaT' or med_in == 'nan': med_in = '-'
        if med_out == 'NaT' or med_out == 'nan': med_out = '-'
        if ateste == 'NaT' or ateste == 'nan': ateste = '-'
        
        # Colorir Status
        sit_html = sit
        if 'PAGO' in sit.upper():
            sit_html = f'<div class="box-pago"><b>{sit}</b><span class="box-text-small">{status_amplo}</span></div>'
            
        html_content += f"""<tr>
            <td>{idx+1}</td>
            <td><b>{proc_nf}</b></td>
            <td>{termo_nf}</td>
            <td>{med}</td>
            <td>{med_in}</td>
            <td>{med_out}</td>
            <td style="text-align:right;"><b>R$ {vr_fat:,.2f}</b></td>
            <td style="text-align:center;">{nf}</td>
            <td style="text-align:center;">{ateste}</td>
            <td>{sit_html}</td>
        </tr>"""
else:
    html_content += "<tr><td colspan='10'>Nenhum pagamento cadastrado.</td></tr>"

html_content += "</table></div>" # Fecha classe report-container

# Remover identação para evitar blocos <pre> do markdown do Streamlit
html_content = re.sub(r'^[ \t]+', '', html_content, flags=re.MULTILINE)

# Render no streamlit final
st.markdown(html_content, unsafe_allow_html=True)