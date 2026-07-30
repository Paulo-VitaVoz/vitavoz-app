import streamlit as st
import pandas as pd
import numpy as np
import time

# ==============================================================================
# CONFIGURAÇÃO DA PLATAFORMA (v65 - The Clinical Operating System)
# ==============================================================================
st.set_page_config(
    page_title="VitaVoz | Clinical OS",
    layout="wide",
    page_icon="⚙️",
    initial_sidebar_state="expanded"
)

if 'menu_selecionado' not in st.session_state: st.session_state['menu_selecionado'] = 'Workflow Center'


def navegar_para(menu):
    st.session_state['menu_selecionado'] = menu
    st.rerun()


# ==============================================================================
# ESTILOS GERAIS & PAGERDUTY STYLE
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    .stButton > button { border-radius: 4px; font-weight: 600; }
    .section-title { font-size: 13px; color: #64748B; text-transform: uppercase; font-weight: 800; margin-bottom: 16px; letter-spacing: 0.5px; }
    .card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; }

    /* Global Filters */
    .filter-bar { display: flex; gap: 12px; background: #FFFFFF; padding: 12px 24px; border-bottom: 1px solid #E2E8F0; margin-top: -40px; margin-bottom: 24px; align-items: center; font-size: 12px; }
    .filter-item { border: 1px solid #CBD5E1; padding: 4px 12px; border-radius: 16px; color: #475569; font-weight: 600; background: #F8FAFC; cursor: pointer; }
    .filter-item:hover { border-color: #3B82F6; background: #EFF6FF; color: #1D4ED8; }

    /* Incident Priorities */
    .px-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; font-weight: 900; color: white; display: inline-block; }
    .p1 { background: #DC2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.4); animation: pulse 2s infinite; }
    .p2 { background: #F59E0B; }
    .p3 { background: #3B82F6; }
    .p4 { background: #94A3B8; }

    /* Incident Row */
    .incident-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 8px; background: #FFFFFF; transition: 0.2s; }
    .incident-row:hover { border-color: #CBD5E1; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

    /* Orchestration Block */
    .orchestration-box { background: #0F172A; border-radius: 8px; padding: 20px; color: white; margin-bottom: 20px; border-left: 4px solid #3B82F6; }
    .orch-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-top: 16px; }
    .orch-label { font-size: 11px; color: #94A3B8; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
    .orch-val { font-size: 14px; font-weight: bold; color: #F8FAFC; }

    /* Activity Stream */
    .activity-stream { border-left: 2px solid #E2E8F0; padding-left: 16px; margin-left: 8px; font-family: monospace; }
    .activity-item { position: relative; margin-bottom: 16px; font-size: 12px; color: #475569; }
    .activity-item::before { content: ''; position: absolute; left: -21px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: #CBD5E1; border: 2px solid #F8FAFC; }
    .act-time { font-weight: 900; color: #0F172A; margin-right: 8px; }
    .act-highlight::before { background: #3B82F6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
    .act-critical::before { background: #DC2626; box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2); }

    /* OS Actions */
    .os-action-btn { font-size: 12px; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: 1px solid #CBD5E1; background: white; cursor: pointer; text-transform: uppercase; }
    .os-action-btn.primary { background: #3B82F6; color: white; border: none; }
    .os-action-btn.resolve { background: #10B981; color: white; border: none; }

    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); } 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); } }
</style>
""", unsafe_allow_html=True)

# Global Filters Bar
st.markdown("""
<div class="filter-bar">
    <div style="font-weight: 900; color: #0F172A; margin-right: 16px;">VITA_OS</div>
    <div class="filter-item">⏱️ Últimas 24h ▼</div>
    <div class="filter-item">🏥 Hospital: Todos ▼</div>
    <div class="filter-item">🩺 Especialidade: Ortopedia ▼</div>
    <div class="filter-item">🤝 Convênio: Todos ▼</div>
    <div style="flex:1;"></div>
    <div style="font-size: 12px; font-weight: bold; color: #0F172A;">👤 Dr. Davi (On-Call)</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# MENU LATERAL & OS MODULES
# ==============================================================================
st.sidebar.markdown("<h2 style='color: #0F172A; margin-bottom: 0;'>VitaVoz</h2>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<p style='color: #3B82F6; font-size: 11px; font-weight: 700; line-height: 1.4; margin-top: 4px; margin-bottom: 24px; text-transform: uppercase;'>Clinical Operating System</p>",
    unsafe_allow_html=True)

menu = st.sidebar.radio("WORKSPACE", [
    "Workflow Center",
    "Digital Twin & AI Copilot",
    "Protocol Builder",
    "Integration Hub",
    "Analytics & ROI"
], index=["Workflow Center", "Digital Twin & AI Copilot", "Protocol Builder", "Integration Hub",
          "Analytics & ROI"].index(st.session_state['menu_selecionado']))

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="card" style="padding: 12px; background: #F8FAFC; border: 1px dashed #CBD5E1;">
    <div style="font-size: 11px; font-weight: bold; color: #64748B; margin-bottom: 8px;">SYSTEM STATUS</div>
    <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:bold; margin-bottom:4px;"><span>FHIR Sync</span> <span style="color:#10B981;">Online</span></div>
    <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:bold; margin-bottom:4px;"><span>AI Engine</span> <span style="color:#10B981;">Online</span></div>
    <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:bold;"><span>WhatsApp API</span> <span style="color:#10B981;">Online</span></div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 1: WORKFLOW CENTER (A Fila de Operações)
# ==============================================================================
if menu == "Workflow Center":
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 20px;'>Incident Management & Triage</h2>",
                unsafe_allow_html=True)

    col1, col2 = st.columns([7, 3])

    with col1:
        st.markdown("<div class='section-title'>Active Incidents (Open)</div>", unsafe_allow_html=True)

        # Incident P1
        st.markdown("""
        <div class="incident-row" style="border-left: 4px solid #DC2626;">
            <div style="width: 10%;"><span class="px-badge p1">P1</span></div>
            <div style="width: 30%;"><b style="color:#0F172A; font-size:14px;">Carlos Mendes</b><br><span style="color:#64748B; font-size:11px;">#INC-8492 • Ortopedia</span></div>
            <div style="width: 30%;"><span style="color:#DC2626; font-size:12px; font-weight:bold;">Risco Infeccioso / Dor Aguda</span></div>
            <div style="width: 15%; font-family:monospace; font-size:12px; font-weight:bold; color:#DC2626;">SLA: -02:14</div>
            <div style="width: 15%; text-align: right;"><span style="background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold;">Unassigned</span></div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Assign to Me", key="btn_carlos", type="primary"): navegar_para("Digital Twin & AI Copilot")

        # Incident P2
        st.markdown("""
        <div class="incident-row" style="border-left: 4px solid #F59E0B;">
            <div style="width: 10%;"><span class="px-badge p2">P2</span></div>
            <div style="width: 30%;"><b style="color:#0F172A; font-size:14px;">Ana Paula</b><br><span style="color:#64748B; font-size:11px;">#INC-8491 • Cardiologia</span></div>
            <div style="width: 30%;"><span style="color:#0F172A; font-size:12px; font-weight:bold;">Evasão de SLA de Resposta</span></div>
            <div style="width: 15%; font-family:monospace; font-size:12px; font-weight:bold; color:#F59E0B;">SLA: 01:45</div>
            <div style="width: 15%; text-align: right;"><span style="color:#0F172A; font-size:11px; font-weight:bold;">Dr. João</span></div>
        </div>

        <div class="incident-row" style="border-left: 4px solid #3B82F6;">
            <div style="width: 10%;"><span class="px-badge p3">P3</span></div>
            <div style="width: 30%;"><b style="color:#0F172A; font-size:14px;">João Silva</b><br><span style="color:#64748B; font-size:11px;">#INC-8488 • Odontologia</span></div>
            <div style="width: 30%;"><span style="color:#0F172A; font-size:12px; font-weight:bold;">Dúvida Medicação</span></div>
            <div style="width: 15%; font-family:monospace; font-size:12px; font-weight:bold; color:#3B82F6;">SLA: 06:20</div>
            <div style="width: 15%; text-align: right;"><span style="color:#0F172A; font-size:11px; font-weight:bold;">Dra. Juliana</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-title'>Global Activity Stream</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="padding-right: 10px; height: 350px; overflow-y: auto;">
            <div class="activity-stream">
                <div class="activity-item act-critical"><span class="act-time">10:47</span> Alerta P1 criado via Protocol Engine (INC-8492)</div>
                <div class="activity-item act-highlight"><span class="act-time">10:46</span> Risk Score recalculado (Carlos M: 35 → 84)</div>
                <div class="activity-item"><span class="act-time">10:45</span> Paciente respondeu ao check-in via WhatsApp</div>
                <div class="activity-item"><span class="act-time">10:42</span> Dr. João assumiu INC-8491 (P2)</div>
                <div class="activity-item"><span class="act-time">10:38</span> Caso INC-8480 resolvido (Alta Médica)</div>
                <div class="activity-item"><span class="act-time">10:30</span> Régua D+4 disparada para 18 pacientes</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 2: DIGITAL TWIN & AI COPILOT (A Orquestração)
# ==============================================================================
elif menu == "Digital Twin & AI Copilot":
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div>
            <span class="px-badge p1">P1</span>
            <span style="font-size: 20px; font-weight: 900; color: #0F172A; margin-left: 8px;">INC-8492: Carlos Mendes</span>
        </div>
        <div>
            <button class="os-action-btn primary">Assign to Me</button>
            <button class="os-action-btn">Escalate</button>
            <button class="os-action-btn resolve">Resolve</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # THE ORCHESTRATION BLOCK (OS Level)
    st.markdown("""
    <div class="orchestration-box">
        <div style="font-size: 12px; color: #3B82F6; font-weight: 900; letter-spacing: 1px; margin-bottom: 8px;">⚡ NEXT ACTION REQUIRED</div>
        <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">☎ Ligar Imediatamente (Risco de Evasão PS)</div>
        <div class="orch-grid">
            <div><div class="orch-label">Prazo (SLA)</div><div class="orch-val" style="color:#EF4444;">2 Minutos</div></div>
            <div><div class="orch-label">Responsável</div><div class="orch-val">Unassigned</div></div>
            <div><div class="orch-label">Protocolo Base</div><div class="orch-val">PTJ-4 (Ortopedia)</div></div>
            <div><div class="orch-label">Escalonamento</div><div class="orch-val">Nível 2 (Plantonista)</div></div>
            <div><div class="orch-label">Status</div><div class="orch-val" style="color:#F59E0B;">Aguardando Triage</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-title'>Digital Twin (Risk Trend)</div>", unsafe_allow_html=True)
        # Dynamic Risk Chart (Streamlit Native)
        chart_data = pd.DataFrame({
            "Risk Score": [12, 18, 35, 84]
        }, index=["Dia 1", "Dia 2", "Dia 3", "Hoje"])
        st.line_chart(chart_data, height=200, color=["#DC2626"])

        st.markdown("<div class='section-title'>Sintomas Extraídos</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="padding: 12px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="font-weight:bold;">Dor</span> <span style="color:#DC2626; font-weight:bold;">9/10 (Aguda)</span></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="font-weight:bold;">Edema</span> <span style="color:#F59E0B; font-weight:bold;">Moderado</span></div>
            <div style="display:flex; justify-content:space-between;"><span style="font-weight:bold;">Intenção</span> <span style="color:#DC2626; font-weight:bold;">Ida ao PS</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-title'>AI Copilot (Contexto)</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="height: 330px; background: #F8FAFC; border: 1px solid #CBD5E1; display:flex; flex-direction:column;">
            <div style="flex:1; overflow-y:auto; font-size:13px; color:#334155;">
                <div style="background:#FFFFFF; padding:12px; border-radius:8px; border:1px solid #E2E8F0; margin-bottom:12px;">
                    <b style="color:#3B82F6;">Copilot:</b> O risco deste paciente saltou de 35 para 84 na última hora. O áudio indicou dor refratária a analgésicos e medo de trombose.<br><br>
                    <b>Ações Sugeridas baseadas no PTJ-4:</b><br>
                    1. Descartar TVP via telemedicina.<br>
                    2. Ajustar analgesia (Tramadol sugerido).
                </div>
            </div>
            <div style="margin-top:12px;">
                <input type="text" placeholder="Fazer uma pergunta à IA sobre o histórico..." style="width:100%; padding:8px 12px; border-radius:6px; border:1px solid #CBD5E1; font-size:12px;">
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 3: PROTOCOL BUILDER (O Core do OS)
# ==============================================================================
elif menu == "Protocol Builder":
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 20px;'>Protocol Builder (No-Code)</h2>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size: 13px; color: #64748B;'>Desenhe a lógica operacional de escalonamento para qualquer especialidade.</p>",
        unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; gap: 16px; margin-bottom: 20px;">
        <div style="background:#0F172A; color:white; padding:8px 16px; border-radius:6px; font-size:12px; font-weight:bold;">📄 PTJ-4 (Prótese Joelho)</div>
        <div style="background:#FFFFFF; color:#64748B; border:1px solid #CBD5E1; padding:8px 16px; border-radius:6px; font-size:12px; font-weight:bold;">📄 BAR-1 (Sleeve Gástrico)</div>
        <div style="background:#FFFFFF; color:#3B82F6; border:1px dashed #3B82F6; padding:8px 16px; border-radius:6px; font-size:12px; font-weight:bold; cursor:pointer;">+ Novo Protocolo</div>
    </div>

    <div class="card" style="background: #F8FAFC; border: 1px dashed #CBD5E1;">
        <div style="font-size:12px; font-weight:bold; color:#475569; margin-bottom:12px;">REGRA DE ACIONAMENTO (DRAG & DROP)</div>

        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <div style="background:#3B82F6; color:white; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:bold;">IF</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px;">Symptom: Pain Score</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px;">Greater Than (>)</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px; color:#DC2626; font-weight:bold;">7</div>
        </div>

        <div style="display:flex; align-items:center; gap:8px; margin-bottom:20px;">
            <div style="background:#3B82F6; color:white; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:bold;">AND</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px;">Intent: Evasão PS</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px;">Equals (==)</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px; color:#DC2626; font-weight:bold;">True</div>
        </div>

        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <div style="background:#10B981; color:white; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:bold;">THEN (ACTION)</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px; color:#0F172A; font-weight:bold;">Create Incident</div>
            <div style="background:#FEF2F2; border:1px solid #DC2626; color:#DC2626; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:bold;">Priority: P1</div>
            <div style="background:white; border:1px solid #CBD5E1; padding:4px 12px; border-radius:4px; font-size:12px;">Assign: On-Call Ortho</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Save & Deploy Version v2.1", type="primary")

# ==============================================================================
# MÓDULO 4: INTEGRATION HUB
# ==============================================================================
elif menu == "Integration Hub":
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 20px;'>Integration Hub</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div class="card">
            <h4 style="margin-top:0; display:flex; justify-content:space-between;"><span>🏥 HL7 / FHIR API</span> <span style="color:#10B981; font-size:12px;">● Healthy</span></h4>
            <p style="font-size:12px; color:#64748B;">Sincronização de prontuários com Epic/Cerner.</p>
            <div style="font-size:11px; font-family:monospace; background:#F8FAFC; padding:8px; border-radius:4px;">Last sync: 2 min ago | Payload: 1.2MB</div>
        </div>
        <div class="card">
            <h4 style="margin-top:0; display:flex; justify-content:space-between;"><span>💬 WhatsApp Business API</span> <span style="color:#10B981; font-size:12px;">● Healthy</span></h4>
            <p style="font-size:12px; color:#64748B;">Canal de comunicação bidirecional com pacientes.</p>
            <div style="font-size:11px; font-family:monospace; background:#F8FAFC; padding:8px; border-radius:4px;">Messages sent (24h): 1,482 | Failure rate: 0.01%</div>
        </div>
        <div class="card">
            <h4 style="margin-top:0; display:flex; justify-content:space-between;"><span>📊 Clinicorp (Webhooks)</span> <span style="color:#10B981; font-size:12px;">● Healthy</span></h4>
            <p style="font-size:12px; color:#64748B;">Integração de agendas e evolução clínica.</p>
            <div style="font-size:11px; font-family:monospace; background:#F8FAFC; padding:8px; border-radius:4px;">Endpoints active: 4 | Latency: 42ms</div>
        </div>
        <div class="card" style="opacity: 0.7;">
            <h4 style="margin-top:0; display:flex; justify-content:space-between;"><span>⌚ Wearables (Apple Health)</span> <span style="color:#64748B; font-size:12px;">○ Inactive</span></h4>
            <p style="font-size:12px; color:#64748B;">Monitoramento de BPM e O2 contínuo.</p>
            <div style="font-size:11px; font-family:monospace; background:#F8FAFC; padding:8px; border-radius:4px;">Status: Configuration Required</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 5: ANALYTICS & ROI
# ==============================================================================
elif menu == "Analytics & ROI":
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 20px;'>Operational & Financial Impact</h2>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            "<div class='card' style='text-align: center;'><div style='font-size:32px; font-weight:900; color:#0F172A;'>142</div><div style='font-size:11px; color:#64748B; font-weight:bold; text-transform:uppercase;'>Readmissões Evitadas (Mês)</div></div>",
            unsafe_allow_html=True)
    with col2:
        st.markdown(
            "<div class='card' style='text-align: center;'><div style='font-size:32px; font-weight:900; color:#10B981;'>214h</div><div style='font-size:11px; color:#64748B; font-weight:bold; text-transform:uppercase;'>Horas Médicas Poupadas</div></div>",
            unsafe_allow_html=True)
    with col3:
        st.markdown(
            "<div class='card' style='text-align: center; background:#0F172A; color:white; border:none;'><div style='font-size:32px; font-weight:900; color:#10B981;'>R$ 68.500</div><div style='font-size:11px; color:#94A3B8; font-weight:bold; text-transform:uppercase;'>Economia Estimada</div></div>",
            unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Pacientes Monitorados (Últimos 30 Dias)</div>", unsafe_allow_html=True)
    # Gráfico nativo Streamlit para dar movimento
    chart_data = pd.DataFrame(
        np.random.randint(50, 100, size=(30, 2)),
        columns=['Ortopedia', 'Cardiologia']
    )
    st.bar_chart(chart_data, height=250)
