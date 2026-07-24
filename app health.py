import os
import json
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date
from fpdf import FPDF

# Importa o cliente e as configurações do nosso backend de saúde
from health import ai_client, processar_registro_saude, DB_NAME, inicializar_banco, RegistroSaude

st.set_page_config(page_title="VitaVoz", page_icon="🩺", layout="centered")
inicializar_banco()


# --- FUNÇÕES DE BANCO DE DADOS ---
def executar_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        res = cursor.fetchall()
    else:
        res = cursor.lastrowid
    conn.commit()
    conn.close()
    return res


def buscar_historico():
    return executar_query(
        "SELECT id, data_registro, tipo_registro, resumo_executivo, dados_completos_json FROM registros_saude ORDER BY id DESC",
        fetch=True)


def obter_remedios_ativos_texto():
    registros = buscar_historico()
    ativos = []
    for _, _, _, _, json_str in registros:
        dados = json.loads(json_str)
        for med in dados.get("medicamentos", []):
            if med.get("acao") in ["novo", "mantido", "alterado"]:
                ativos.append(med["nome"])
    return ", ".join(ativos) if ativos else "Nenhum remédio ativo."


# --- SISTEMA DE GAMIFICAÇÃO (STREAKS) ---
hoje = date.today().strftime("%Y-%m-%d")
stats = executar_query("SELECT id, ultimo_acesso, dias_seguidos FROM user_stats ORDER BY id DESC LIMIT 1", fetch=True)
streak_atual = 1

if not stats:
    executar_query("INSERT INTO user_stats (ultimo_acesso, dias_seguidos) VALUES (?, ?)", (hoje, 1))
else:
    stat_id, ultimo_acesso, dias_seguidos = stats[0]
    if ultimo_acesso != hoje:
        diferenca = (datetime.strptime(hoje, "%Y-%m-%d") - datetime.strptime(ultimo_acesso, "%Y-%m-%d")).days
        if diferenca == 1:
            streak_atual = dias_seguidos + 1
        else:
            streak_atual = 1
        executar_query("UPDATE user_stats SET ultimo_acesso = ?, dias_seguidos = ? WHERE id = ?",
                       (hoje, streak_atual, stat_id))
    else:
        streak_atual = dias_seguidos

# --- CABEÇALHO ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🩺 VitaVoz")
    st.caption("O prontuário da sua família movido a IA.")
with col2:
    st.markdown(f"<h3 style='text-align: right; color: #ff4b4b;'>🔥 {streak_atual} Dias</h3>", unsafe_allow_html=True)

# --- ABAS ---
aba_reg, aba_time, aba_rem, aba_bio, aba_pdf = st.tabs(
    ["🎙️ Novo", "📜 Histórico", "💊 Remédios", "⚖️ Peso & Biometria", "📄 Relatório Médico"])

# 1. ABA REGISTRAR
with aba_reg:
    st.write("Envie áudio ou foto. A IA vai cruzar com seus remédios atuais para evitar riscos.")
    arquivo_enviado = st.file_uploader("Escolha o arquivo:", type=["m4a", "mp3", "wav", "ogg", "jpg", "png", "pdf"])

    if arquivo_enviado and st.button("🚀 Processar IA", type="primary"):
        with st.spinner("Analisando relato, extraindo exames e checando interações..."):
            caminho_temp = f"temp_{arquivo_enviado.name}"
            with open(caminho_temp, "wb") as f:
                f.write(arquivo_enviado.getbuffer())

            remedios_atuais = obter_remedios_ativos_texto()
            mime_type = "image/jpeg" if arquivo_enviado.name.lower().endswith(("jpg", "jpeg", "png")) else "audio/ogg"
            resultado = processar_registro_saude(ai_client, caminho_temp, mime_type, remedios_atuais)

            if os.path.exists(caminho_temp): os.remove(caminho_temp)

            if resultado:
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                json_str = json.dumps(resultado.model_dump(), ensure_ascii=False)
                executar_query(
                    "INSERT INTO registros_saude (data_registro, tipo_registro, paciente, resumo_executivo, dados_completos_json) VALUES (?, ?, ?, ?, ?)",
                    (agora, resultado.tipo_registro, resultado.paciente, resultado.resumo_executivo, json_str))

                st.balloons()
                st.success("✅ Salvo com sucesso!")
                st.info(resultado.resumo_executivo)
                if resultado.alertas_interacao:
                    st.error(f"⚠️ **ALERTA DE IA (Interação Medicamentosa):** {resultado.alertas_interacao}")

# 2. ABA LINHA DO TEMPO
with aba_time:
    registros = buscar_historico()
    if not registros:
        st.info("Nenhum registro encontrado.")
    else:
        for reg_id, data_reg, tipo, resumo, json_str in registros:
            dados = json.loads(json_str)
            with st.expander(f"🗓️ {data_reg} - {tipo.upper()}", expanded=False):
                st.write(f"**Resumo:** {resumo}")
                if dados.get("alertas_interacao"):
                    st.warning(f"⚠️ {dados['alertas_interacao']}")

                # Lista de Medicamentos
                if dados.get("medicamentos"):
                    st.markdown("**💊 Medicamentos:**")
                    for med in dados["medicamentos"]:
                        st.write(
                            f"- **{med['nome']}** ({med.get('dosagem', 'N/A')}) - *{med.get('posologia', '')}* [{med['acao'].upper()}]")

                # Botão de Excluir
                if st.button("🗑️ Excluir Registro", key=f"del_{reg_id}"):
                    executar_query("DELETE FROM registros_saude WHERE id = ?", (reg_id,))
                    st.rerun()

# 3. ABA REMÉDIOS E RECOMPRA
with aba_rem:
    st.subheader("Painel de Controle e Recompra")
    registros = buscar_historico()
    meds_ativos = []

    for reg_id, data_reg, _, _, json_str in registros:
        dados = json.loads(json_str)
        for idx, med in enumerate(dados.get("medicamentos", [])):
            if med.get("acao") in ["novo", "mantido", "alterado"]:
                meds_ativos.append({"reg_id": reg_id, "idx": idx, "dados": dados, "med": med, "data_inicio": data_reg})

    if not meds_ativos:
        st.info("Nenhum medicamento ativo.")
    else:
        for item in meds_ativos:
            m = item["med"]
            duracao = m.get("duracao_dias")
            alerta_recompra = ""

            # Simula lógica de dias restantes se houver duração cadastrada
            if duracao:
                dias_passados = (datetime.now() - datetime.strptime(item["data_inicio"], "%Y-%m-%d %H:%M:%S")).days
                dias_restantes = duracao - dias_passados
                if 0 <= dias_restantes <= 3:
                    alerta_recompra = f" ⚠️ (Acaba em {dias_restantes} dias!)"
                elif dias_restantes < 0:
                    alerta_recompra = " ❌ (Tratamento Atrasado/Acabou)"

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**💊 {m['nome']}** {alerta_recompra}")
                st.caption(f"{m.get('posologia', 'Sem posologia')} | Duração total: {duracao or 'Contínua'} dias")
            with col2:
                if st.button("✅ Concluir", key=f"parar_{item['reg_id']}_{item['idx']}"):
                    item["dados"]["medicamentos"][item["idx"]]["acao"] = "descontinuado"
                    executar_query("UPDATE registros_saude SET dados_completos_json = ? WHERE id = ?",
                                   (json.dumps(item["dados"], ensure_ascii=False), item["reg_id"]))
                    st.toast(f"{m['nome']} finalizado!")
                    st.rerun()
            st.divider()

# 4. ABA BIOMETRIA & GRÁFICO
with aba_bio:
    st.subheader("Acompanhamento de Saúde")

    col1, col2 = st.columns(2)
    with col1:
        peso_input = st.number_input("Peso Atual (kg):", min_value=30.0, max_value=200.0, value=75.0, step=0.1)
    with col2:
        altura_input = st.number_input("Altura (m):", min_value=1.0, max_value=2.5, value=1.70, step=0.01)

    if st.button("💾 Salvar Biometria"):
        imc = round(peso_input / (altura_input ** 2), 2)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        executar_query("INSERT INTO historico_biometrico (data_registro, peso, altura, imc) VALUES (?, ?, ?, ?)",
                       (agora, peso_input, altura_input, imc))
        st.success(f"Salvo! Seu IMC é {imc}")
        st.rerun()

    # Exibir Gráfico
    historico_bio = executar_query("SELECT data_registro, peso FROM historico_biometrico ORDER BY data_registro ASC",
                                   fetch=True)
    if historico_bio:
        df_bio = pd.DataFrame(historico_bio, columns=["Data", "Peso (kg)"])
        df_bio["Data"] = pd.to_datetime(df_bio["Data"]).dt.strftime("%d/%m")
        df_bio.set_index("Data", inplace=True)
        st.line_chart(df_bio)

# 5. ABA GERADOR DE PDF PARA MÉDICO
with aba_pdf:
    st.subheader("Gerar Resumo para o Médico")
    st.write("Baixe o resumo dos medicamentos ativos e últimos relatos para levar na consulta.")

    if st.button("📄 Criar PDF Pré-Consulta"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="VitaVoz - Relatorio Pre-Consulta", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="1. Medicamentos em Uso Atualmente:", ln=True)
        pdf.set_font("Arial", '', 11)

        remedios = obter_remedios_ativos_texto()
        pdf.multi_cell(0, 10, txt=remedios if remedios else "Nenhum medicamento registrado.")
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="2. Resumo das Ultimas Ocorrencias:", ln=True)
        pdf.set_font("Arial", '', 11)

        ultimos = executar_query("SELECT data_registro, resumo_executivo FROM registros_saude ORDER BY id DESC LIMIT 3",
                                 fetch=True)
        for data_reg, resumo in ultimos:
            data_curta = data_reg.split(" ")[0]
            texto_limpo = f"[{data_curta}] {resumo}".encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, txt=texto_limpo)
            pdf.ln(2)

        # O fpdf2 já retorna um bytearray, só precisamos converter para bytes
        pdf_bytes = bytes(pdf.output())

        st.download_button(
            label="⬇️ Baixar PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_VitaVoz_{hoje}.pdf",
            mime="application/pdf"
        )