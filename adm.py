import os
import yt_dlp
import time
import requests
from ftplib import FTP
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAÇÕES DE AMBIENTE ---
# Puxa a chave do sistema (Termux: export GEMINI_API_KEY="suachave")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- CONFIGURAÇÕES FIREBASE & FTP ---
FIREBASE_URL = "https://pk-scripts-default-rtdb.firebaseio.com/comando.json"
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

def buscar_letra_ia(nome_musica):
    """Busca letra usando Gemini 2.0 Flash com filtros de segurança desativados"""
    if not GEMINI_API_KEY:
        return "Letra nao disponivel (Erro de Config no Termux)."

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Retorne apenas a letra completa da musica '{nome_musica}'. Nao adicione introducoes, titulos ou creditos. Apenas a letra pura."}]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()
        
        if 'candidates' in data and data['candidates'][0]['content']['parts']:
            letra = data['candidates'][0]['content']['parts'][0]['text']
            # Substitui quebras de linha pelo marcador do seu sistema PHP
            return letra.replace('\n', '[LF]')
        
        # Log para depuração se a IA recusar
        print(f"⚠️ IA recusou a letra: {data.get('error', {}).get('message', 'Bloqueio de seguranca ou Copyright')}")
        return "Letra nao encontrada pela IA."
    except Exception as e:
        print(f"❌ Erro conexao IA: {e}")
        return "Erro ao buscar letra."

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
        # 1. DOWNLOAD (YT-DLP)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"📥 Baixando: {busca}")
            info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
            if 'entries' in info: info = info['entries'][0]
            
            titulo_real = info.get('title', busca).replace('|', '-')
            capa = info.get('thumbnail', '')

        # 2. BUSCAR LETRA
        print(f"🤖 Solicitando letra: {titulo_real}")
        letra_ia = buscar_letra_ia(titulo_real)

        # 3. CRIAR TXT DE METADADOS
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"{titulo_real}|{audio_file}|{capa}|{letra_ia}")

        # 4. ENVIO FTP
        print(f"📤 Enviando para o servidor: {titulo_real}")
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        
        # Pasta dos Áudios
        ftp.cwd('/htdocs/uploads/songs')
        with open(audio_file, 'rb') as f:
            ftp.storbinary(f'STOR {audio_file}', f)
        
        # Pasta da Fila (Metadados)
        ftp.cwd('/htdocs/uploads/queue')
        with open(txt_file, 'rb') as f:
            ftp.storbinary(f'STOR {txt_file}', f)
            
        ftp.quit()
        print(f"✅ Concluido: {titulo_real}")

    except Exception as e:
        print(f"❌ Erro fatal no processo: {e}")
    finally:
        # Limpa arquivos do Termux
        if os.path.exists(audio_file): os.remove(audio_file)
        if os.path.exists(txt_file): os.remove(txt_file)

def limpar_firebase():
    try: requests.delete(FIREBASE_URL)
    except: pass

# --- LOOP PRINCIPAL ---
print("-" * 30)
print("🚀 PIKACHU MUSIC BOT ONLINE")
print(f"📡 Monitorando: {FIREBASE_URL}")
print("-" * 30)

while True:
    try:
        response = requests.get(FIREBASE_URL)
        dados = response.json()

        if dados and 'musica' in dados:
            lista = [m.strip() for m in dados['musica'].split(';') if m.strip()]
            print(f"\n📦 Lote recebido: {len(lista)} musica(s).")
            
            # max_workers=2 para evitar ban no FTP do ByetHost
            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(baixar_e_enviar, lista)
            
            limpar_firebase()
            print("✨ Fila limpa no Firebase.")
        
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ Erro no Loop: {e}")
        time.sleep(10)
