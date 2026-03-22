import os
import yt_dlp
import time
import requests
from ftplib import FTP

# --- CONFIGURAÇÕES ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FIREBASE_URL = "https://pk-scripts-default-rtdb.firebaseio.com/comando.json"
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

def buscar_letra_ia(nome_musica):
    if not GEMINI_API_KEY: return "Erro: API Key ausente."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
    
    try:
        print(f"⏳ Respeitando cota da IA (15s)...")
        time.sleep(15) 
        res = requests.post(url, json={
            "contents": [{"parts": [{"text": f"Letra da musica {nome_musica}. Retorne apenas a letra."}]}]
        }, timeout=15)
        data = res.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text'].replace('\n', '[LF]')
        return "Letra nao encontrada."
    except:
        return "Erro na conexao com a IA."

def baixar_e_enviar(busca, id_unico):
    audio_file = f"audio_{id_unico}.mp3"
    txt_file = f"data_{id_unico}.txt"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audio_{id_unico}.%(ext)s',
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"📥 Baixando: {busca} (ID: {id_unico})")
            info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
            titulo = info.get('title', busca).replace('|', '-')
            capa = info.get('thumbnail', '')

        letra = buscar_letra_ia(titulo)

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"{titulo}|{audio_file}|{capa}|{letra}")

        print(f"📤 Enviando FTP: {titulo}")
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        
        with open(audio_file, 'rb') as f: ftp.storbinary(f'STOR /htdocs/uploads/songs/{audio_file}', f)
        with open(txt_file, 'rb') as f: ftp.storbinary(f'STOR /htdocs/uploads/queue/{txt_file}', f)
        
        ftp.quit()
        print(f"✅ Sucesso!")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if os.path.exists(audio_file): os.remove(audio_file)
        if os.path.exists(txt_file): os.remove(txt_file)

# --- LOOP PRINCIPAL ---
print("🚀 Pikachu Music Bot 2026 ONLINE")
while True:
    try:
        r = requests.get(FIREBASE_URL)
        dados = r.json()
        
        if dados:
            # Percorre o dicionário de músicas na fila
            for item_id in dados:
                musica_info = dados[item_id]
                # Pega o nome da música e o timestamp individual
                nome = musica_info.get('musica')
                tempo = musica_info.get('timestamp', int(time.time() * 1000))
                
                if nome:
                    baixar_e_enviar(nome, tempo)
            
            # Limpa a fila após processar tudo
            requests.delete(FIREBASE_URL)
            print("✨ Fila limpa.")
            
        time.sleep(10)
    except Exception as e:
        print(f"Erro no Loop: {e}")
        time.sleep(10)
