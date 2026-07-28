import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURAÇÃO DA PLATAFORMA (v42 - Master Edition)
# ==============================================================================
st.set_page_config(
    page_title="VitaVoz | Monitoramento Clínico", 
    layout="centered", 
    page_icon="🦷",
    initial_sidebar_state="collapsed"
)

DB_NAME = "vitavoz_v42_master.db"
HOJE = datetime(2026, 7, 28)

os.makedirs("uploads", exist_ok=True)

# CSS Customizado Mobile-First
st.markdown("""
<style>
    .stApp {
        max-width: 480px;
        margin: 0 auto;
    }
    .stButton > button {
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
    .badge-alerta {
        background-color: #FEF2F2;
        border: 1px solid #FCA5A5;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .badge-nota {
        background-color: #F0F9FF;
        border: 1px solid #BAE6FD;
        color: #0369A1;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização de Estado Global
if 'db_inicializado' not in st.session_state:
    st.session_state['db_inicializado'] = True
    st.session_state['pagina_atual'] = 'Home_Selecao' 
    st.session_state['paciente_selecionado'] = None

# ==============================================================================
# CAMADA DE DADOS E REPOSITORY
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, idade INTEGER, procedimento TEXT, 
                 data_cirurgia TEXT, data_retorno TEXT, protocolo TEXT, alertas_clinicos TEXT, notas_medico TEXT, avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS evolucoes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, dia INTEGER, dor INTEGER, 
                 inchaco TEXT, febre TEXT, tendencia TEXT, relato TEXT, score INTEGER, status_alerta TEXT, data_registro TEXT)''')
    conn.commit()
    return conn

def seed_db_if_empty(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pacientes")
    if c.fetchone()[0] == 0:
        pacientes_insert = []
        
        # 1. João Silva - Caso Clínico Específico
        alertas_joao = "Alergia a Amoxicilina | Ansiedade elevada"
        notas_joao = "Paciente indicado pelo Dr. Carlos. Apresentou histórico de complicação em cirurgia anterior de 2024. Requer atenção especial à ansiedade."
        pacientes_insert.append(("João Silva", 52, "Implante Dentário", "20/07/2026", "05/08/2026", "Implante Padrão v1.4", alertas_joao, notas_joao, "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"))
        
        # 2 e 3. Atenção
        pacientes_insert.append(("Maria Souza", 45, "Enxerto Ósseo", "25/07/2026", "10/08/2026", "Enxerto v1.1", "Sem comorbidades", "Paciente cooperativa", "https://cdn-icons-png.flaticon.com/512/3135/3135789.png"))
        pacientes_insert.append(("Carlos Mendes", 38, "Enxerto Ósseo", "25/07/2026", "10/08/2026", "Enxerto v1.1", "Hipertensão leve", "Uso regular de medicação contínua", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"))
        
        # 39 Pacientes em Acompanhamento Normal
        for i in range(17): pacientes_insert.append((f"Paciente Implante {i+1}", 40 + (i % 15), "Implante Dentário", "14/07/2026", "29/07/2026", "Implante v1.4", "Nenhum", "Evolução habitual", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"))
        for i in range(10): pacientes_insert.append((f"Paciente Enxerto {i+1}", 35 + (i % 20), "Enxerto Ósseo", "18/07/2026", "02/08/2026", "Enxerto v1.1", "Nenhum", "Evolução habitual", "https://cdn-icons-png.flaticon.com/512/3135/3135789.png"))
        for i in range(5): pacientes_insert.append((f"Paciente Orto {i+1}", 28 + (i % 10), "Ortognática", "23/07/2026", "07/08/2026", "Orto v3.0", "Nenhum", "Evolução habitual", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"))
        for i in range(7): pacientes_insert.append((f"Paciente Carga {i+1}", 55 + (i % 12), "Carga Imediata", "26/07/2026", "10/08/2026", "Carga v2.1", "Nenhum", "Evolução habitual", "https://cdn-icons-png.flaticon.com/512/3135/3135789.png"))

        c.executemany('''INSERT INTO pacientes (nome, idade, procedimento, data_cirurgia, data_retorno, protocolo, alertas_clinicos, notas_medico, avatar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', pacientes_insert)
        
        c.execute("SELECT id FROM pacientes WHERE nome='João Silva' LIMIT 1")
        joao_id = c.fetchone()[0]
        c.execute("SELECT id FROM pacientes WHERE nome!='João Silva'")
        outros_ids = [row[0] for row in c.fetchall()]
        
        evolucoes_insert = []
        evolucoes_insert.append((joao_id, 1, 6, 'Pouco', 'Não', 'Igual', "Dói um pouco, mas suportável.", 90, '🟢 Normal', "21/07/2026"))
        evolucoes_insert.append((joao_id, 2, 2, 'Não', 'Não', 'Melhorando', "Hoje está bem melhor doutor, quase sem dor.", 95, '🟢 Normal', "22/07/2026"))
        
        for i, p_id in enumerate(outros_ids):
            if i in [0, 1]: 
                evolucoes_insert.append((p_id, 3, 6, 'Médio', 'Não', 'Igual', "A dor continua constante.", 75, '🟡 Atenção', HOJE.strftime("%d/%m/%Y")))
            else: 
                evolucoes_insert.append((p_id, 14, 0, 'Não', 'Não', 'Melhorando', "Tudo excelente.", 100, '🟢 Normal', HOJE.strftime("%d/%m/%Y")))
                
        c.executemany('''INSERT INTO evolucoes (paciente_id, dia, dor, inchaco, febre, tendencia, relato, score, status_alerta, data_registro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', evolucoes_insert)
        conn.commit()

if not os.path.exists(DB_NAME):
    conn = init_db()
    seed_db_if_empty(conn)
    conn.close()

# --- Helpers ---
def get_joao_id():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM pacientes WHERE nome='João Silva' LIMIT 1")
    res = c.fetchone()
    conn.close()
    return res[0] if res else 1

def get_paciente_data(pid):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM pacientes WHERE id=?", (pid,))
    row = c.fetchone()
    paciente = dict(row) if row else {}
    c.execute("SELECT * FROM evolucoes WHERE paciente_id=? ORDER BY dia DESC", (pid,))
    evolucoes = [dict(r) for r in c.fetchall()]
    conn.close()
    return paciente, evolucoes

def get_fila_completa():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT p.nome, p.procedimento, e.dia, e.score, e.status_alerta 
        FROM pacientes p 
        JOIN evolucoes e ON p.id = e.paciente_id 
        WHERE e.id = (SELECT MAX(id) FROM evolucoes WHERE paciente_id = p.id)
        ORDER BY e.score ASC
    """)
    rows = c.fetchall()
    conn.close()
    return [{"Paciente": r[0], "Procedimento": r[1], "Pós-Op": f"D+{r[2]}", "Status": r[4]} for r in rows]

def mudar_pagina(nome):
    st.session_state['pagina_atual'] = nome
    st.rerun()

def render_mobile_header():
    st.markdown("<h3 style='text-align: center; color: #0F172A; margin-bottom: 0;'>VitaVoz</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px; margin-top: 0;'>Acompanhamento Clínico Pós-Cirúrgico</p>", unsafe_allow_html=True)

# ==============================================================================
# TELA INICIAL: SELEÇÃO DE JORNADA
# ==============================================================================
if st.session_state['pagina_atual'] == 'Home_Selecao':
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #0F172A; font-size: 42px; margin-bottom: 0;'>🦷 VitaVoz</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 15px; margin-top: 5px; margin-bottom: 30px;'>Selecione o modo de visualização:</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<div style='text-align: center; font-size: 32px;'>👤</div>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; color: #0F172A; margin-bottom: 2px;'>Paciente</h5>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px; margin-top: 0;'>Envio de relato</p>", unsafe_allow_html=True)
            if st.button("Acessar", key="btn_p", type="primary", use_container_width=True):
                mudar_pagina('Paciente_Home')
    with col2:
        with st.container(border=True):
            st.markdown("<div style='text-align: center; font-size: 32px;'>👨‍⚕️</div>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; color: #0F172A; margin-bottom: 2px;'>Clínica</h5>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px; margin-top: 0;'>Área do Médico</p>", unsafe_allow_html=True)
            if st.button("Acessar", key="btn_c", type="secondary", use_container_width=True):
                mudar_pagina('Clinica_Login')

# ==============================================================================
# JORNADA 1: PACIENTE (JOÃO SILVA - D3)
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Paciente_Home':
    render_mobile_header()
    
    st.markdown("""
    <div style="background: #F8FAFC; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #CBD5E1; text-align: center;">
        <h3 style="margin: 0; color: #0F172A; font-size: 20px;">Olá, João 👋</h3>
        <p style="margin-top: 8px; color: #475569; font-size: 13px; line-height: 1.5;">
        Implante realizado em <b>20/07/2026</b><br>
        <b style="color: #2563EB;">Pós-operatório: 3º dia</b><br>
        Seu dentista acompanha sua evolução diária.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. ABA DE ORIENTAÇÕES DO PÓS-OPERATÓRIO (A COLINHA DO PACIENTE)
    with st.expander("📄 Orientações da sua Cirurgia (Dr. Davi)"):
        st.markdown("""
        <div style='font-size: 13px; color: #334155; line-height: 1.6;'>
        <b>1. Medicação:</b> Tomar os analgésicos nos horários prescritos na receita.<br>
        <b>2. Gelo:</b> Fazer compressa gelada na bochecha (15 min sim, 15 min não).<br>
        <b>3. Alimentação:</b> Apenas alimentos líquidos e frios/mornos nas primeiras 48h.<br>
        <b>4. Repouso:</b> Evitar esforços físicos e não cuspir nem usar canudo.
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<b style='color: #0F172A; font-size: 14px;'>Como está sua dor hoje?</b>", unsafe_allow_html=True)
    
    # 2. ESCALA VISUAL DE DOR COM EMOJIS (PADRÃO OMS)
    dor_selecionada = st.select_slider(
        "Selecione o nível de dor:",
        options=["😃 Nenhuma (0-1)", "🙂 Leve (2-3)", "😐 Moderada (4-5)", "😣 Forte (6-7)", "😫 Intensa (8-10)"],
        value="😐 Moderada (4-5)",
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<b style='color: #0F172A; font-size: 14px;'>Conte o que você está sentindo:</b>", unsafe_allow_html=True)
    st.caption("Pode falar normalmente por áudio sobre inchaço, medicação ou dúvidas.")
    
    if st.button("🎤 Enviar relato por voz", type="primary", use_container_width=True):
        st.session_state['processando_audio'] = True

    if st.session_state.get('processando_audio'):
        with st.status("🧠 VitaVoz AI analisando...", expanded=True) as status:
            time.sleep(1.0)
            st.write("✓ Transcrição do áudio concluída")
            time.sleep(0.8)
            st.write("✓ Escala visual e sintomas mapeados")
            time.sleep(0.8)
            st.write("✓ Comparando com protocolo Implante v1.4")
            time.sleep(0.8)
            st.write("✓ Detectada quebra na curva de melhora esperada")
            time.sleep(0.8)
            status.update(label="Análise concluída", state="complete", expanded=False)
            
        joao_id = get_joao_id()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM evolucoes WHERE paciente_id=? AND dia=3", (joao_id,))
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO evolucoes (paciente_id, dia, dor, inchaco, febre, tendencia, relato, score, status_alerta, data_registro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (joao_id, 3, 4, 'Sim', 'Não', 'Piorando', "Doutor, estava melhorando, mas ontem começou uma dor mais forte e parece que inchou.", 65, '🟡 Atenção', "23/07/2026"))
            conn.commit()
        conn.close()
        
        mudar_pagina('Paciente_Status')

elif st.session_state['pagina_atual'] == 'Paciente_Status':
    render_mobile_header()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #0F172A;'>Atualização recebida com sucesso.</h4>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### Status da recuperação:")
        
        st.markdown("""
        <div style="margin-bottom: 20px; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 13px; font-weight: bold; color: #0F172A;">Progresso estimado</span>
                <span style="font-size: 13px; font-weight: bold; color: #D97706;">70%</span>
            </div>
            <div style="background-color: #E2E8F0; border-radius: 10px; width: 100%; height: 12px;">
                <div style="background-color: #F59E0B; width: 70%; height: 100%; border-radius: 10px;"></div>
            </div>
            <div style="font-size: 11px; color: #64748B; margin-top: 6px;">Esperado para D+3: <b>85%</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<span style='color:#64748B; font-size:12px; font-weight: bold;'>🟢 D1 E D2</span>", unsafe_allow_html=True)
        st.markdown("Evolução positiva")
        st.divider()
        st.markdown("<span style='color:#D97706; font-size:12px; font-weight:bold;'>🟡 HOJE (D+3)</span>", unsafe_allow_html=True)
        st.markdown("**Atenção recomendada** (Aumento pontual de dor/edema)")
        
    st.info("👨‍⚕️ **Seu dentista foi notificado para revisar seu caso.**\n\nVocê continua sob acompanhamento seguro.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Ver na Área do Médico", type="primary", use_container_width=True):
        mudar_pagina('Clinica_Login')

# ==============================================================================
# JORNADA 2: CLÍNICA / MÉDICO
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Clinica_Login':
    render_mobile_header()
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<h4 style='text-align: center; color: #0F172A; margin-bottom: 5px;'>Painel Clínico</h4>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 40px;'>👨‍⚕️</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; color: #475569; font-size: 16px;'>Dr. Davi<br><span style='font-weight: normal; font-size: 13px;'>Clínica Prime</span></p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            mudar_pagina('Clinica_Greeting')

elif st.session_state['pagina_atual'] == 'Clinica_Greeting':
    render_mobile_header()
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; color: #0F172A; margin-bottom: 5px;'>Bom dia, Dr. Davi 👋</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 15px; color: #475569;'>Acompanhamento de hoje:<br><b>42 pacientes ativos</b></p>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;'>
            <b>1 paciente precisa da sua atenção agora.</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; font-size: 12px; color: #64748B;'>Última atualização:<br><b>João Silva (Implante D+3) - há 2 minutos</b></p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Ver Dashboard", type="primary", use_container_width=True):
            mudar_pagina('Clinica_Dashboard')

elif st.session_state['pagina_atual'] == 'Clinica_Dashboard':
    render_mobile_header()
    
    st.markdown("#### Visão Geral da Clínica")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; margin-bottom: 8px; text-align: center;">
            <div style="color: #0F172A; font-size: 24px; font-weight: 800;">42</div>
            <div style="color: #64748B; font-size: 10px; font-weight: bold; text-transform: uppercase;">Pacientes ativos</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; text-align: center;">
            <div style="color: #10B981; font-size: 24px; font-weight: 800;">2h15</div>
            <div style="color: #64748B; font-size: 10px; font-weight: bold; text-transform: uppercase;">Tempo recuperado</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background: #FEF3C7; border: 1px solid #FCD34D; padding: 12px; border-radius: 8px; margin-bottom: 8px; text-align: center;">
            <div style="color: #D97706; font-size: 24px; font-weight: 800;">1</div>
            <div style="color: #B45309; font-size: 10px; font-weight: bold; text-transform: uppercase;">Atenção imediata</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; text-align: center;">
            <div style="color: #0F172A; font-size: 24px; font-weight: 800;">97%</div>
            <div style="color: #64748B; font-size: 10px; font-weight: bold; text-transform: uppercase;">Evolução normal</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="background: #F8FAFC; padding: 12px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-top: 12px;">
        <b>Resumo do Dia:</b><br>
        <span style="font-size: 13px; color: #475569;">Dos 42 pacientes acompanhados, 41 seguem no padrão normal.</span><br>
        <b style="color: #D97706; font-size: 13px;">1 paciente requer sua revisão (João Silva).</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    with colA:
        if st.button("🚨 Fila de Atendimento", type="primary", use_container_width=True):
            mudar_pagina('Clinica_Fila')
    with colB:
        if st.button("📚 Protocolos", use_container_width=True):
            mudar_pagina('Clinica_Protocolos')
        
    with st.expander("📋 Ver todos os 42 pacientes"):
        df_fila = pd.DataFrame(get_fila_completa())
        st.dataframe(df_fila, use_container_width=True, hide_index=True)

elif st.session_state['pagina_atual'] == 'Clinica_Protocolos':
    render_mobile_header()
    if st.button("← Voltar ao Dashboard", use_container_width=True): 
        mudar_pagina('Clinica_Dashboard')
        
    st.markdown("#### 📚 Biblioteca de Protocolos")
    st.caption("Regras de segurança e parâmetros de recuperação esperados.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<h5 style='color: #0F172A; margin-bottom: 5px;'>🦷 Implante Dentário v1.4</h5>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size: 13px; color: #334155; line-height: 1.6;'>
        <b style='color: #3B82F6;'>D+1:</b> Dor esperada (até 7) | Edema Moderado<br>
        <b style='color: #10B981;'>D+3:</b> Dor em declínio (deve cair para 2-3)<br>
        <b style='color: #EF4444;'>Alerta D+3:</b> Reaparecimento de dor ou edema progressivo<br>
        <b style='color: #10B981;'>D+7 / D+14:</b> Estabilidade clínica
        </div>
        """, unsafe_allow_html=True)

elif st.session_state['pagina_atual'] == 'Clinica_Fila':
    render_mobile_header()
    if st.button("← Voltar ao Dashboard", use_container_width=True): 
        mudar_pagina('Clinica_Dashboard')
    
    st.markdown("<h4 style='color: #0F172A; margin-bottom: 12px; margin-top: 10px;'>Fila de Atendimento</h4>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### João Silva")
        st.markdown("<div style='font-size: 13px; color: #475569;'><b>Implante realizado em 20/07/2026</b><br>Pós-operatório: <b>3º dia (D+3)</b></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='display: flex; gap: 12px; margin-top: 10px;'>
            <div>
                <span style='font-size: 26px; font-weight: 800; color: #D97706;'>🟡 Atenção</span><br>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><b style='color: #0F172A; font-size: 13px;'>Motivo do alerta:</b>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size: 13px; color: #334155; line-height: 1.5;'>
        • Aumento de dor após melhora inicial (2 → 4/10)<br>
        • Relato de edema/inchaço no D+3<br>
        • Quebra da curva de evolução esperada
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><b style='color: #2563EB; font-size: 13px;'>Ação sugerida:</b> <b>Revisar paciente</b>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Abrir Prontuário Clínico", type="primary", use_container_width=True):
            mudar_pagina('Clinica_Prontuario')

elif st.session_state['pagina_atual'] == 'Clinica_Prontuario':
    render_mobile_header()
    if st.button("← Voltar à Fila", use_container_width=True): 
        mudar_pagina('Clinica_Fila')
    
    joao_id = get_joao_id()
    paciente, evolucoes = get_paciente_data(joao_id)
    
    st.markdown(f"### {paciente.get('nome', 'João Silva')}")
    st.markdown(f"<span style='color: #475569; font-size: 13px;'>52 anos | {paciente.get('procedimento')}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: #2563EB; font-size: 13px; font-weight: bold;'>Implante realizado em 20/07/2026 • Pós-operatório: 3º dia</span>", unsafe_allow_html=True)
    
    # 3. ALERTAS E CAMPO DE ANAMNESE / NOTAS PRIVADAS DO MÉDICO
    with st.container(border=True):
        st.markdown("<b style='color: #0F172A; font-size: 13px;'>Alertas da Anamnese:</b>", unsafe_allow_html=True)
        st.markdown("""
        <div style='margin-top: 5px; margin-bottom: 10px;'>
            <span class='badge-alerta'>⚠️ Alergia a Amoxicilina</span>
            <span class='badge-alerta'>🧠 Ansiedade elevada</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<b style='color: #0F172A; font-size: 13px;'>📌 Anotações Privadas do Cirurgião:</b>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 12px; color: #334155; margin-top: 4px;'><i>\"{paciente.get('notas_medico', 'Sem observações')}\"</i></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 🧠 Análise VitaVoz AI")
        st.markdown("""
        <div style='font-size: 13px; color: #334155;'>
        <b>Áudio transcrito:</b><br>
        <i>"Doutor, estava melhorando, mas ontem começou uma dor mais forte e parece que inchou."</i><br><br>
        <b>Comparação com protocolo:</b><br>
        • Esperado no D+3: Declínio de dor e edema.<br>
        • Encontrado: Reversão de tendência com quebra de padrão no 3º dia.<br>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Linha do Tempo da Dor")
        st.markdown("""
        <div style="border-left: 2px solid #CBD5E1; margin-left: 8px; padding-left: 12px; font-size: 13px;">
           <p style="margin-bottom: 10px;"><b style="color: #0F172A;">20/07</b> — Cirurgia Realizada</p>
           <p style="margin-bottom: 10px;"><b style="color: #0F172A;">21/07 (D+1)</b> — Dor 6/10 (Dentro do esperado)</p>
           <p style="margin-bottom: 10px;"><b style="color: #10B981;">22/07 (D+2)</b> — Dor 2/10 (Melhorando)</p>
           <p><b style="color: #D97706;">23/07 (D+3 Hoje)</b> — ⚠️ Dor 4/10 + Edema (Reversão)</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Ação Rápida Recomendada")
    with st.container(border=True):
        st.markdown("Mensagem sugerida para o paciente:")
        st.success("**Olá João, o Dr. Davi analisou sua atualização de hoje (D+3). Como você relatou um pequeno aumento de inchaço e dor após ter melhorado, vamos acompanhar de perto. Sua equipe entrará em contato para orientar a conduta.**")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💬 Enviar Orientação", type="primary", use_container_width=True):
                mudar_pagina('Clinica_Resultado')
        with col2:
            # 4. SIMULADOR DE DISPARO WHATSAPP DE URGÊNCIA
            if st.button("📲 Simular Notificação WhatsApp", type="secondary", use_container_width=True):
                st.toast("📲 Alerta enviado para o WhatsApp pessoal do Dr. Davi!", icon="🚨")

# ==============================================================================
# FECHAMENTO DO PITCH
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Clinica_Resultado':
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: #0F172A; line-height: 1.4;'>O problema não foi descoberto no retorno.<br><span style='color: #D97706;'>Foi identificado no 3º dia, no momento em que a curva mudou.</span></h3>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; color: #0F172A; font-size: 40px; margin-bottom: 0;'>🦷 VitaVoz</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px; color: #475569; margin-top: 10px; line-height: 1.5;'>Menos tempo procurando problemas.<br><b style='color: #10B981;'>Mais tempo cuidando de pacientes.</b></p>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    with colA:
        if st.button("💼 Modelo de Negócio", type="primary", use_container_width=True):
            mudar_pagina('Clinica_Planos')
    with colB:
        if st.button("🔄 Voltar ao Início", use_container_width=True):
            if os.path.exists(DB_NAME): os.remove(DB_NAME)
            st.session_state.clear()
            mudar_pagina('Home_Selecao')

elif st.session_state['pagina_atual'] == 'Clinica_Planos':
    render_mobile_header()
    if st.button("← Voltar", use_container_width=True): 
        mudar_pagina('Clinica_Resultado')
        
    st.markdown("#### 💼 Planos e Escala")
    st.caption("Prevenção de risco que se paga evitando 1 única intercorrência.")

    with st.container(border=True):
        st.markdown("<h4 style='color:#0F172A; margin-bottom:0;'>Starter</h4>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#10B981; margin-top:0;'>R$ 699<span style='font-size:14px; color:#64748B;'>/mês</span></h3>", unsafe_allow_html=True)
        st.markdown("Proteja até **50 pacientes**/mês")

    with st.container(border=True):
        st.markdown("<h4 style='color:#0F172A; margin-bottom:0;'>Professional</h4>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#3B82F6; margin-top:0;'>R$ 1.499<span style='font-size:14px; color:#64748B;'>/mês</span></h3>", unsafe_allow_html=True)
        st.markdown("Proteja até **200 pacientes**/mês")

    with st.container(border=True):
        st.markdown("<h4 style='color:#0F172A; margin-bottom:0;'>Enterprise</h4>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#8B5CF6; margin-top:0;'>R$ 3.999+<span style='font-size:14px; color:#64748B;'>/mês</span></h3>", unsafe_allow_html=True)
        st.markdown("Redes, hospitais e protocolos personalizados")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Encerrar Apresentação", use_container_width=True):
        if os.path.exists(DB_NAME): os.remove(DB_NAME)
        st.session_state.clear()
        mudar_pagina('Home_Selecao')
