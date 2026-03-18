import os
import yt_dlp
import requests
from ftplib import FTP
import time

# --- CONFIGURAÇÕES ---
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" # Use sua senha do vPanel

SITE_URL = "http://Pikachutech.byethost6.com"
API_URL = f"{SITE_URL}/admin_api.php"
TOKEN = "og.dudu013"

def baixar_yt(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
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
        print("✅ Arquivo no servidor!")
        return True
    except Exception as e:
        print(f"❌ Erro no FTP: {e}")
        return False

def avisar_api_banco(arquivo, titulo):
    print("📝 Registrando no banco via API...")
    # Enviamos via POST para a API PHP
    payload = {'filename': arquivo, 'title': titulo}
    # Passamos o token na URL para o ByetHost não bloquear o header
    try:
        r = requests.post(f"{API_URL}?action=register_ftp&token={TOKEN}", data=payload, timeout=10)
        print(f"📡 Resposta do Site: {r.text}")
    except Exception as e:
        print(f"⚠️ O arquivo subiu, mas a API falhou: {e}")

if __name__ == "__main__":
    musica = input("Nome da música: ")
    try:
        arq, tit = baixar_yt(musica)
        if subir_ftp(arq):
            avisar_api_banco(arq, tit)
            if os.path.exists(arq): os.remove(arq)
    except Exception as e:
        print(f"Erro: {e}")
