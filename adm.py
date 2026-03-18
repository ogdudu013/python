import os
import yt_dlp
import requests
from ftplib import FTP
import time

# --- DADOS DE ACESSO ---
FTP_HOST = "ftpupload.net"
FTP_PORT = 21 # <--- Porta definida aqui
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" 

SITE_URL = "http://Pikachutech.byethost6.com"
API_URL = f"{SITE_URL}/admin_api.php"
TOKEN = "og.dudu013"

def subir_ftp(arquivo):
    print(f"🚀 Conectando a {FTP_HOST}:{FTP_PORT}...")
    try:
        ftp = FTP()
        # Conecta explicitamente usando a porta 21
        ftp.connect(FTP_HOST, FTP_PORT, timeout=30) 
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        
        ftp.set_pasv(True) # OBRIGATÓRIO para ByetHost
        
        print("📂 Mudando para diretório htdocs/uploads/songs...")
        ftp.cwd('htdocs/uploads/songs')
        
        with open(arquivo, 'rb') as f:
            # O comando STOR envia o arquivo
            ftp.storbinary(f'STOR {arquivo}', f)
        
        ftp.quit()
        print("✅ Arquivo enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro Crítico no FTP: {e}")
        return False

# ... (resto das funções baixar_yt e registrar_api permanecem iguais)

def baixar_yt(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        nome_arquivo = f"song_{int(time.time())}.mp3"
        os.rename('temp.mp3', nome_arquivo)
        return nome_arquivo, info['title']

def registrar_api(arquivo, titulo):
    print("📝 Registrando no banco de dados...")
    payload = {'filename': arquivo, 'title': titulo}
    try:
        # Adicionamos um timeout maior para a API
        r = requests.post(f"{API_URL}?action=register_ftp&token={TOKEN}", data=payload, timeout=20)
        print(f"📡 Resposta: {r.text}")
    except Exception as e:
        print(f"❌ Erro na API (Banco): {e}")

if __name__ == "__main__":
    musica = input("Nome da música: ")
    try:
        arq, tit = baixar_yt(musica)
        if subir_ftp(arq):
            registrar_api(arq, tit)
            if os.path.exists(arq): os.remove(arq)
    except Exception as e:
        print(f"Erro Geral: {e}")
