# === INÍCIO DO BLOCO: IMPORTAÇÕES E CONFIGURAÇÕES ===
import pyodbc # Conecta ao Azure SQL.
import os # Manipula caminhos do sistema.
import time # Monitora tempos para limites.
import asyncio # Processa tarefas assíncronas.
import edge_tts # Motor de voz neural.
import re # Limpa strings e aplica Regex.
from datetime import date # Controla limites diários.
import gradio as gr # Interface web.
from dotenv import load_dotenv # Carrega dados do .env.
from google import genai # SDK do Gemini.
from google.genai import types # Configurações da API.
from pydub import AudioSegment # Costura áudios.

load_dotenv() # Carrega credenciais.
CHAVE_API = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=CHAVE_API)
# === FIM DO BLOCO: IMPORTAÇÕES E CONFIGURAÇÕES ===

# === INÍCIO DO BLOCO: BANCO DE DADOS (AZURE SQL) ===
server = 'diolab-sql-servidor.database.windows.net'
database = 'SQL-diolab-test'
username = 'Procure seu username tipo CloudSA3e4bcbbc'
password = 'SenhaCriada.'
driver = '{ODBC Driver 18 for SQL Server}'
conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'

def salvar_interacao(texto_usuario, resposta_ia):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        sql = "INSERT INTO HistoricoConversas (texto_usuario, resposta_ia) VALUES (?, ?)"
        cursor.execute(sql, (texto_usuario, resposta_ia))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e: print(f"Erro SQL: {e}")
# === FIM DO BLOCO: BANCO DE DADOS ===

# === INÍCIO DO BLOCO: CONTROLE DE VOZ INTELIGENTE ===
vozes_map = {
    "pt": {"base": "pt-BR-FranciscaNeural", "estrangeiro": "en-US-JennyNeural"},
    "en": {"base": "en-US-JennyNeural", "estrangeiro": "en-US-JennyNeural"},
    "es": {"base": "es-ES-ElviraNeural", "estrangeiro": "en-US-JennyNeural"},
    "fr": {"base": "fr-FR-DeniseNeural", "estrangeiro": "en-US-JennyNeural"}
}

async def gerar_audio_inteligente(texto_completo, idioma_base, caminho_saida):
    partes = re.split(r'(\[[^\]]+\|[^\]]+\])', texto_completo)
    arquivos_temp = []

    for i, parte in enumerate(partes):
        temp_arq = f"temp_{i}.mp3"
        if parte.startswith('[') and '|' in parte:
            fonetica = parte.split('|')[1].replace(']', '')
            voz = vozes_map.get(idioma_base, {}).get("estrangeiro", "en-US-JennyNeural")
            comm = edge_tts.Communicate(fonetica, voz)
        else:
            voz = vozes_map.get(idioma_base, {}).get("base", "pt-BR-FranciscaNeural")
            comm = edge_tts.Communicate(parte, voz)
        await comm.save(temp_arq)
        arquivos_temp.append(temp_arq)

    combined = AudioSegment.empty()
    for f in arquivos_temp:
        if os.path.exists(f):
            combined += AudioSegment.from_mp3(f)
            os.remove(f)
    combined.export(caminho_saida, format="mp3")
# === FIM DO BLOCO: CONTROLE DE VOZ ===

# === INÍCIO DO BLOCO: LÓGICA DO GEMINI E GRADIO ===
def processar_conversa(audio_path, idioma_voz, historico):
    if historico is None: historico = ""
    if audio_path is None: return "Nenhum áudio.", None, historico

    audio_file = client.files.upload(file=audio_path)

    # Instrução rígida para evitar asteriscos e garantir formatação
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["Responda sem usar markdown ou asteriscos.", audio_file],
        config=types.GenerateContentConfig(system_instruction="""Diretrizes de Resposta:
1. Reconhecimento de Soletragem: Traduza e dê o significado.
2. Analogia de Pronúncia: Explique usando sons do português.
3. Tom de Voz: Simples, para iniciantes, velocidade normal, respostas curtas.
4. Pronúncia Estrangeira: SEMPRE que escrever uma palavra em inglês, use o formato exato [Palavra Original|Pronúncia Fonética]. Exemplo: "A palavra [Apple|Épou] é muito comum."
Restrições: Evite explicações gramaticais densas e NUNCA use markdown, asteriscos ou hashtags.""")
    )

    texto_resposta = response.text
    client.files.delete(name=audio_file.name)

    # Limpeza Rigorosa (Remove qualquer resquício de formatação)
    texto_limpo = re.sub(r'[*#_]', '', texto_resposta)
    texto_tela = re.sub(r'\[([^|\]]+)\|([^\]]+)\]', r'\1', texto_limpo)
    texto_audio = re.sub(r'\[([^|\]]+)\|([^\]]+)\]', r'\2', texto_limpo)

    caminho_saida = "resposta.mp3"
    asyncio.run(gerar_audio_inteligente(texto_audio, idioma_voz, caminho_saida))

    salvar_interacao("Audio input", texto_tela)
    return texto_tela, caminho_saida, ""

interface = gr.Interface(
    fn=processar_conversa,
    inputs=[gr.Audio(sources=["microphone"], type="filepath"), gr.Dropdown(["pt", "en", "es", "fr"], value="pt"), gr.State("")],
    outputs=[gr.Textbox(label="Resposta"), gr.Audio(autoplay=True), gr.State()]
)

interface.launch(share=True)
# === FIM DO BLOCO: LÓGICA DO GEMINI E GRADIO ===
