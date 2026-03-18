import os
import yt_dlp
import requests
from ftplib import FTP
import time

# --- CONFIGURAÇÕES ---
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "TUA_SENHA_AQUI" 

SITE_URL = "http://Pikachutech.byethost6.com"
API_URL = f"{SITE_URL}/admin_api.php"
TOKEN = "og.dudu013"

# Criamos uma sessão para manter os cookies (importante no ByetHost)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
})

def baixar_yt(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando no YT: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        nome_arquivo = f"song_{int(time.time())}.mp3"
        os.rename('temp.mp3', nome_arquivo)
        return nome_arquivo, info['title']

def subir_ftp(arquivo):
    print(f"🚀 Enviando via FTP...")
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.cwd('htdocs/uploads/songs') 
        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo}', f)
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ Erro no FTP: {e}")
        return False

def avisar_banco(arquivo, titulo):
    print("📝 Registrando na Base de Dados...")
    # Passamos o token na URL E no post para garantir
    url_final = f"{API_URL}?action=register_ftp&token={TOKEN}"
    payload = {'filename': arquivo, 'title': titulo}
    
    try:
        # Fazemos um GET primeiro para "abrir a porta" do ByetHost
        session.get(SITE_URL) 
        time.sleep(1) # Espera 1 segundo
        
        # Agora fazemos o POST
        r = session.post(url_final, data=payload, timeout=15)
        print(f"📡 Resposta API: {r.text}")
    except Exception as e:
        print(f"❌ Erro ao avisar API: {e}")

if __name__ == "__main__":
    musica = input("Nome da música: ")
    try:
        arq, tit = baixar_yt(musica)
        if subir_ftp(arq):
            avisar_banco(arq, tit)
            if os.path.exists(arq): os.remove(arq)
    except Exception as e:
        print(f"Erro Geral: {e}")
