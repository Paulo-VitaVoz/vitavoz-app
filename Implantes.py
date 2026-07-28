import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURAÇÃO DA PLATAFORMA (Pitch Demo - v28 The Golden Path)
# ==============================================================================
st.set_page_config(page_title="VitaVoz | Pós-operatório inteligente", layout="centered", page_icon="🦷")

DB_NAME = "vitavoz_v28_pitch_final.db"
HOJE = datetime(2026, 7, 28)

os.makedirs("uploads", exist_ok=True)

if 'db_inicializado' not in st.session_state:
    try:
        if os.path.exists(DB_NAME): os.remove(DB_NAME)
    except PermissionError:
        pass
    st.session_state['db_inicializado'] = True
    # Inicia a Demo pelo Paciente, conforme a nova estratégia de Pitch
    st.session_state['pagina_atual'] = 'Visao_Paciente'
    st.session_state['paciente_selecionado'] = None


# ==============================================================================
# CAMADA DE DADOS: SCHEMA ROBUSTO (PREPARADO PARA O PRODUTO REAL)
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clinicas (id INTEGER PRIMARY KEY, nome TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 clinica_id INTEGER, 
                 nome TEXT, 
                 idade INTEGER, 
                 procedimento TEXT, 
                 data_cirurgia TEXT, 
                 data_retorno TEXT, 
                 dentista TEXT, 
                 protocolo TEXT, 
                 avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS evolucoes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 paciente_id INTEGER, 
                 dia INTEGER, 
                 dor INTEGER, 
                 inchaco TEXT, 
                 febre TEXT, 
                 tendencia TEXT, 
                 relato TEXT, 
                 score INTEGER, 
                 motivo_alerta TEXT, 
                 data_registro TEXT)''')
    c.execute("UPDATE sqlite_sequence SET seq = 1040 WHERE name = 'pacientes'")
    conn.commit()
    return conn


def seed_db_if_empty(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pacientes")
    if c.fetchone()[0] == 0:
        clinica_id = 1
        c.execute("INSERT INTO clinicas (nome) VALUES ('Clínica Prime')")

        pacientes_insert = []
        evolucoes_insert = []

        # Gerando 42 pacientes para a métrica do dashboard
        for i in range(42):
            if i == 0:
                nome, idade, proc, dentista, protocolo = "João Silva", 52, "Implante Unitário", "Dr. Davi", "Implante Padrão v1.4"
                data_cir = "2026-07-21"
                data_ret = "2026-08-05"
            elif i in [1, 2]:
                nome, idade, proc, dentista, protocolo = f"Paciente {i} (Atenção)", 45, "Enxerto Ósseo", "Dr. Davi", "Enxerto v1.1"
                data_cir = (HOJE - timedelta(days=3)).strftime("%Y-%m-%d")
                data_ret = (HOJE + timedelta(days=10)).strftime("%Y-%m-%d")
            else:
                nome, idade, proc, dentista, protocolo = f"Paciente {i}", 35, "Carga Imediata", "Dr. Davi", "Carga v2.1"
                data_cir = (HOJE - timedelta(days=14)).strftime("%Y-%m-%d")
                data_ret = (HOJE + timedelta(days=1)).strftime("%Y-%m-%d")

            avatar = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if i % 2 == 0 else "https://cdn-icons-png.flaticon.com/512/3135/3135789.png"
            pacientes_insert.append((clinica_id, nome, idade, proc, data_cir, data_ret, dentista, protocolo, avatar))

        c.executemany(
            '''INSERT INTO pacientes (clinica_id, nome, idade, procedimento, data_cirurgia, data_retorno, dentista, protocolo, avatar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            pacientes_insert)
        c.execute("SELECT id FROM pacientes")
        todos_p = [row[0] for row in c.fetchall()]

        for i, p_id in enumerate(todos_p):
            if i == 0:  # João
                evolucoes_insert.append(
                    (p_id, 1, 6, 'Pouco', 'Não', 'Igual', "Dói um pouco, mas ok.", 90, "", "2026-07-22"))
                evolucoes_insert.append(
                    (p_id, 3, 4, 'Pouco', 'Não', 'Melhorando', "Acho que tá desinchando.", 95, "", "2026-07-24"))
                # O D7 do João será simulado na hora do Pitch
            elif i in [1, 2]:
                evolucoes_insert.append((p_id, 3, 6, 'Médio', 'Não', 'Igual', "A dor continua.", 75, "Dor no limite",
                                         HOJE.strftime("%Y-%m-%d")))
            else:
                evolucoes_insert.append(
                    (p_id, 14, 0, 'Não', 'Não', 'Melhorando', "Tudo ótimo.", 100, "", HOJE.strftime("%Y-%m-%d")))

        c.executemany(
            '''INSERT INTO evolucoes (paciente_id, dia, dor, inchaco, febre, tendencia, relato, score, motivo_alerta, data_registro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            evolucoes_insert)
        conn.commit()


def get_paciente_data(pid):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM pacientes WHERE id=?", (pid,))
    paciente = dict(c.fetchone())
    c.execute("SELECT * FROM evolucoes WHERE paciente_id=? ORDER BY dia DESC", (pid,))
    evolucoes = [dict(r) for r in c.fetchall()]
    conn.close()
    return paciente, evolucoes


def mudar_pagina(nome):
    st.session_state['pagina_atual'] = nome
    st.rerun()


def render_mobile_header():
    st.markdown("<h3 style='text-align: center; color: #0F172A; margin-bottom: 0;'>VitaVoz</h3>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #64748B; font-size: 13px; margin-top: 0;'>Pós-operatório sem perder pacientes de vista</p>",
        unsafe_allow_html=True)


# ==============================================================================
# VIEW 1: EXPERIÊNCIA DO PACIENTE (O INÍCIO DO PITCH)
# ==============================================================================
conn = init_db()
seed_db_if_empty(conn)

if st.session_state['pagina_atual'] == 'Visao_Paciente':
    render_mobile_header()

    st.markdown("""
    <div style="background: #DCF8C6; padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #BEE5A0;">
        <p style="margin: 0; color: #0F172A; font-size: 15px;">
        Olá João 👋<br><br>
        Hoje completa 7 dias do seu implante.<br><br>
        Como está sua recuperação?
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎤 Segure para gravar áudio", type="primary", use_container_width=True):
        st.session_state['audio_enviado'] = True

    if st.session_state.get('audio_enviado'):
        with st.status("Transmitindo atualização...", expanded=True) as status:
            time.sleep(1)
            st.write("🎙️ Áudio capturado e enviado via WhatsApp (00:12s)")
            time.sleep(1.5)
            st.write("⚙️ **Plataforma VitaVoz processando relato...**")
            time.sleep(1.5)
            status.update(label="Processamento Concluído!", state="complete", expanded=False)

        with st.container(border=True):
            st.markdown("#### ⚡ Extração Estruturada (Bastidores)")
            st.caption("O que o sistema converteu automaticamente em milissegundos:")
            c1, c2 = st.columns(2)
            c1.markdown("🩸 **Dor:** 8/10")
            c1.markdown("🤒 **Febre:** Sim")
            c2.markdown("🎈 **Edema:** Muito")
            c2.markdown("📉 **Tendência:** Piorando")

            # Insere no banco para a visualização do médico depois
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                '''INSERT INTO evolucoes (paciente_id, dia, dor, inchaco, febre, tendencia, relato, score, motivo_alerta, data_registro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (1041, 7, 8, 'Muito', 'Sim', 'Piorando',
                 "Doutor, minha dor piorou muito hoje. Tá latejando e acho que tô com febre.", 42,
                 "Dor aumentou | Edema aumentado | Relato de febre", HOJE.strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📱 Simular Alerta no Celular do Médico", type="primary", use_container_width=True):
            mudar_pagina('Notificacao_WhatsApp')

# ==============================================================================
# VIEW 2: NOTIFICAÇÃO DO WHATSAPP (CELULAR DO DR. DAVI)
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Notificacao_WhatsApp':
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #25D366; padding: 15px; border-radius: 16px 16px 0 0; color: white; display: flex; align-items: center; gap: 10px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/512px-WhatsApp.svg.png" width="25">
        <b style="font-size: 16px;">WhatsApp</b> <span style="font-size: 12px; margin-left: auto;">AGORA</span>
    </div>
    <div style="background: white; border: 1px solid #E2E8F0; border-top: none; padding: 20px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <b style="color: #0F172A; font-size: 16px;">🤖 VitaVoz</b><br>
        <p style="color: #334155; font-size: 15px; margin-top: 8px;">🚨 <b>Atenção Dr. Davi</b><br><br>Paciente <b>João Silva</b><br>Implante D+7<br>Relato fora do padrão.<br><br>Clique para revisar:</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Abrir Paciente", type="primary", use_container_width=True):
        st.session_state['paciente_selecionado'] = 1041
        mudar_pagina('Dashboard_Medico')

# ==============================================================================
# VIEW 3: DASHBOARD DO MÉDICO ("MOMENTO APPLE")
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Dashboard_Medico':
    render_mobile_header()

    st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 25px;">
        <div style="background: #E2E8F0; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px;">👨‍⚕️</div>
        <div>
            <h2 style="margin: 0; color: #0F172A; font-size: 20px;">Bom dia, Dr. Davi</h2>
            <span style="color: #64748B; font-size: 13px;">Clínica Prime</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Resumo 28/07")
        st.markdown("**42** pacientes acompanhados")
        st.markdown("🟢 **39** normais")
        st.markdown("🟡 **2** observação")
        st.markdown("🔴 **1** intervenção")
        st.divider()
        st.markdown("<span style='color: #10B981; font-weight: bold;'>⏳ Tempo economizado hoje: 2h15min</span>",
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #EF4444; margin-bottom: 10px;'>🚨 Necessita avaliação</h4>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### João Silva")
        st.caption("Implante unitário | D+7")

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(
                "<div style='font-size: 28px; font-weight: 700; color: #EF4444; line-height: 1.1;'>42/100</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size: 13px; color: #64748B;'>VitaScore</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                "<div style='font-size: 13px; font-weight: 600; color: #EF4444; margin-top: 10px;'>Fora da curva esperada</div>",
                unsafe_allow_html=True)

        st.markdown("<br>**Motivo:**", unsafe_allow_html=True)
        st.markdown("- Dor aumentou\n- Edema aumentado\n- Relato de febre")

        if st.button("Ver paciente", type="primary", use_container_width=True):
            mudar_pagina('Prontuario_João')

# ==============================================================================
# VIEW 4: PRONTUÁRIO E AÇÃO RÁPIDA (A ENTREGA DE VALOR)
# ==============================================================================
elif st.session_state['pagina_atual'] == 'Prontuario_João':
    render_mobile_header()
    if st.button("← Voltar ao Resumo", use_container_width=True): mudar_pagina('Dashboard_Medico')

    paciente, evolucoes = get_paciente_data(1041)

    # Header Clínico Robusto
    st.markdown(f"### {paciente['nome']}")
    st.markdown(
        f"<span style='color: #475569; font-size: 14px;'>{paciente['idade']} anos | {paciente['procedimento']}</span>",
        unsafe_allow_html=True)
    st.markdown(
        f"<span style='color: #64748B; font-size: 13px;'>Cirurgia: {datetime.strptime(paciente['data_cirurgia'], '%Y-%m-%d').strftime('%d/%m/%Y')} • Retorno previsto: {datetime.strptime(paciente['data_retorno'], '%Y-%m-%d').strftime('%d/%m/%Y')}</span>",
        unsafe_allow_html=True)

    # O Gráfico de Curva
    with st.container(border=True):
        st.markdown("#### Curva de Dor")
        df_chart = pd.DataFrame({"Dia": ["D1", "D3", "D7"], "Dor": [6, 4, 8]}).set_index("Dia")
        st.line_chart(df_chart, color=["#EF4444"])
        st.error("⚠️ **O monitoramento identificou uma alteração na evolução esperada.**")

    # Comparativo de Sintomas
    colA, colB = st.columns(2)
    with colA:
        with st.container(border=True):
            st.markdown("<span style='color:#64748B; font-size:12px;'>Antes: D+3</span>", unsafe_allow_html=True)
            st.markdown("Dor: **4**")
            st.markdown("Tendência: **Melhorando**")
    with colB:
        with st.container(border=True):
            st.markdown("<span style='color:#EF4444; font-size:12px;'>Hoje: D+7</span>", unsafe_allow_html=True)
            st.markdown("Dor: **8**")
            st.markdown("Tendência: **Piorando**")

    # Transcrição Pura
    with st.container(border=True):
        st.markdown("#### 🎙️ Relato de Hoje")
        st.info(f"\"{evolucoes[0]['relato']}\"")

    st.markdown("<br>", unsafe_allow_html=True)

    # A Ação Rápida Humanizada
    st.markdown("#### ⚡ Ação Rápida")
    with st.container(border=True):
        st.markdown("Mensagem sugerida para o paciente:")
        st.success(
            "**Olá João, recebemos sua atualização. O Dr. Davi viu que sua evolução apresentou uma alteração e vai acompanhar seu caso. Vamos entrar em contato para orientar os próximos passos.**")

        if st.button("💬 Enviar via WhatsApp ao paciente", type="primary", use_container_width=True):
            st.balloons()
            st.success("Mensagem de acolhimento enviada com sucesso!")

    st.markdown("<br><hr>", unsafe_allow_html=True)
    if st.button("🔄 Reiniciar Demonstração (Limpar Banco)", use_container_width=True):
        st.session_state['db_inicializado'] = False
        if os.path.exists(DB_NAME): os.remove(DB_NAME)
        st.session_state.clear()
        mudar_pagina('Visao_Paciente')