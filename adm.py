import os
import yt_dlp
import time
import requests
from ftplib import FTP
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAÇÕES DE AMBIENTE ---
# Puxa a chave do sistema. No GitHub, esta variável estará vazia e a chave segura.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- CONFIGURAÇÕES FIREBASE & FTP ---
FIREBASE_URL = "https://pk-scripts-default-rtdb.firebaseio.com/comando.json"
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

def buscar_letra_ia(nome_musica):
    """Usa o modelo Gemini 2.0 Flash (v1) para buscar a letra"""
    if not GEMINI_API_KEY:
        return "Letra nao disponivel (Erro de Config)."

    # URL atualizada para a versão estável v1 com o modelo que apareceu no teu ListModels
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Retorne apenas a letra da musica '{nome_musica}'. Nao escreva introducoes ou titulos."}]
        }]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        
        if 'candidates' in data:
            letra = data['candidates'][0]['content']['parts'][0]['text']
            # O marcador [LF] é para o teu sistema PHP processar a quebra de linha
            return letra.replace('\n', '[LF]')
        return "Letra nao encontrada pela IA."
    except:
        return "Erro ao conectar na IA."

def baixar_e_enviar(busca):
    if not busca.strip(): return

    timestamp = int(time.time() * 1000)
    nome_base = f"audio_{timestamp}"
    audio_file = f"{nome_base}.mp3"
    txt_file = f"data_{timestamp}.txt"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{nome_base}.%(ext)s',
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'noplaylist': True,
    }

    try:
        # 1. DOWNLOAD DO YOUTUBE
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"📥 Processando: {busca}")
            info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
            if 'entries' in info: info = info['entries'][0]
            
            titulo_real = info.get('title', busca).replace('|', '-')
            capa = info.get('thumbnail', '')

        # 2. BUSCA DE LETRA (GEMINI 2.0)
        print(f"🤖 IA buscando letra para: {titulo_real}")
        letra_ia = buscar_letra_ia(titulo_real)

        # 3. CRIAR FICHEIRO DE METADADOS
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"{titulo_real}|{audio_file}|{capa}|{letra_ia}")

        # 4. UPLOAD FTP (LOGIN ÚNICO)
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        
        # Envia Áudio
        ftp.cwd('/htdocs/uploads/songs')
        with open(audio_file, 'rb') as f:
            ftp.storbinary(f'STOR {audio_file}', f)
        
        # Envia TXT (Gatilho para o PHP)
        ftp.cwd('/htdocs/uploads/queue')
        with open(txt_file, 'rb') as f:
            ftp.storbinary(f'STOR {txt_file}', f)
            
        ftp.quit()
        print(f"✅ Sucesso: {titulo_real}")

    except Exception as e:
        print(f"❌ Erro em {busca}: {e}")
    finally:
        # Limpeza de ficheiros temporários no Termux
        if os.path.exists(audio_file): os.remove(audio_file)
        if os.path.exists(txt_file): os.remove(txt_file)

def limpar_firebase():
    try: requests.delete(FIREBASE_URL)
    except: pass

# --- LOOP DE MONITORAMENTO ---
print("🚀 Pikachu Music Bot 2026 Online!")
print("Utilizando Gemini 2.0 Flash via REST API.")

while True:
    try:
        response = requests.get(FIREBASE_URL)
        dados = response.json()

        if dados and 'musica' in dados:
            lista = [m.strip() for m in dados['musica'].split(';') if m.strip()]
            print(f"\n📦 Lote detectado: {len(lista)} musica(s).")
            
            # Processa 2 de cada vez para não ser bloqueado pelo FTP gratuito
            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(baixar_e_enviar, lista)
            
            limpar_firebase()
            print("✨ Fila processada.")
        
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ Monitoramento: {e}")
        time.sleep(10)
