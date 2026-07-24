import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

logging.basicConfig(level=logging.WARNING)
for logger_name in ["httpx", "google", "google.genai", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
ai_client: Optional[genai.Client] = None

if API_KEY:
    try:
        ai_client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"❌ Erro ao inicializar o cliente Gemini: {e}")
        ai_client = None

DB_NAME = "carevoice_saude.db"


def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela principal de registros
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro TEXT NOT NULL,
            tipo_registro TEXT,
            paciente TEXT,
            resumo_executivo TEXT,
            dados_completos_json TEXT NOT NULL
        )
    """)
    # Nova Tabela: Biometria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_biometrico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro TEXT NOT NULL,
            peso REAL,
            altura REAL,
            imc REAL
        )
    """)
    # Nova Tabela: Gamificação (Streaks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ultimo_acesso TEXT NOT NULL,
            dias_seguidos INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


# --- ESQUEMAS DE DADOS (Agora com duração e alertas de interação) ---
class Medicamento(BaseModel):
    nome: str = Field(description="Nome do medicamento.")
    dosagem: Optional[str] = Field(default=None, description="Ex: 50mg, 10ml, 1 comprimido.")
    posologia: Optional[str] = Field(default=None, description="Instrução de uso. Ex: Tomar de 12 em 12 horas.")
    acao: str = Field(description="Status: 'novo', 'alterado', 'mantido' ou 'descontinuado'.")
    quantidade_caixa: Optional[int] = Field(default=None, description="Quantidade total de comprimidos na caixa.")
    duracao_dias: Optional[int] = Field(default=None, description="Quantos dias o tratamento vai durar.")


class ProximoPasso(BaseModel):
    tipo: str = Field(description="Ex: 'exame', 'retorno', 'comprar_remedio'.")
    descricao: str = Field(description="Descrição do que precisa ser feito.")
    prazo: Optional[str] = Field(default=None, description="Ex: '3 meses', 'amanhã'.")


class RegistroSaude(BaseModel):
    tipo_registro: str = Field(description="Classificação: 'consulta', 'receita', 'exame' ou 'relato_sintomas'.")
    paciente: Optional[str] = Field(default=None)
    medicamentos: List[Medicamento] = Field(default_factory=list)
    orientacoes_gerais: List[str] = Field(description="Dicas, restrições ou alertas passados.")
    proximos_passos: List[ProximoPasso] = Field(default_factory=list)
    alertas_interacao: Optional[str] = Field(default=None,
                                             description="Avisos sobre possíveis interações medicamentosas graves entre novos e antigos remédios.")
    resumo_executivo: str = Field(description="Um resumo claro de 2 a 3 frases.")


SYSTEM_INSTRUCTION = """
Você é o assistente clínico do 'CareVoice'.
Extraia as informações do áudio/imagem com precisão absoluta.
ATENÇÃO À INTERAÇÃO MEDICAMENTOSA: Se o prompt fornecer os remédios atuais do paciente, cruze-os com os novos e preencha o campo 'alertas_interacao' caso haja risco grave. Se não houver risco, deixe nulo.
Extraia também duração de tratamentos (em dias) e quantidade na caixa, se mencionado.
"""


def processar_registro_saude(client: genai.Client, caminho_arquivo: str, mime_type: str, remedios_atuais: str = "") -> \
Optional[RegistroSaude]:
    if not client: return None
    try:
        arquivo_upload = client.files.upload(file=caminho_arquivo, config={"mime_type": mime_type})
        prompt = f"Análise este arquivo e extraia as informações de saúde. REMÉDIOS ATUAIS DO PACIENTE (para checar interações): {remedios_atuais}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[arquivo_upload, prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=RegistroSaude
            )
        )
        client.files.delete(name=arquivo_upload.name)
        return RegistroSaude.model_validate_json(response.text)
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")
        return None