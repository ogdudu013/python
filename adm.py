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
    print("📝 Registrando no banco de dados (Modo Camuflado)...")
    payload = {'filename': arquivo, 'title': titulo}
    
    # Criamos uma sessão para simular um navegador real
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    try:
        # 1. Fazemos um "ping" no site para pegar os cookies de segurança do ByetHost
        session.get(SITE_URL, timeout=10)
        time.sleep(2) # Espera 2 segundos para o servidor "relaxar"
        
        # 2. Fazemos o POST com o Token na URL (mais seguro contra bloqueios)
        url_com_token = f"{API_URL}?action=register_ftp&token={TOKEN}"
        r = session.post(url_com_token, data=payload, timeout=20)
        
        if r.status_code == 200:
            print(f"📡 Sucesso! Resposta: {r.text}")
        else:
            print(f"⚠️ O servidor respondeu com código {r.status_code}. Verifique o admin_api.php")
            
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        print("DICA: Tente abrir o seu site no navegador agora e depois rode o script novamente.")
