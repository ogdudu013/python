import yt_dlp
import sys
import os
from ftplib import FTP, error_perm
import config

def gerenciar_ftp_e_upload(arquivo_local):
    print(f"🚀 Conectando ao servidor FTP...")
    try:
        ftp = FTP(config.FTP_HOST)
        ftp.login(user=config.FTP_USER, passwd=config.FTP_PASS)
        
        pasta_alvo = "videos"
        ftp.cwd(config.FTP_ROOT)
        
        # Verifica ou cria a pasta 'videos'
        try:
            ftp.cwd(pasta_alvo)
        except error_perm:
            print(f"📁 Criando pasta '{pasta_alvo}'...")
            ftp.mkd(pasta_alvo)
            ftp.cwd(pasta_alvo)

        nome_arquivo = os.path.basename(arquivo_local)
        print(f"📤 Enviando: {nome_arquivo}")
        
        with open(arquivo_local, 'rb') as f:
            ftp.storbinary(f'STOR {nome_arquivo}', f)
        
        ftp.quit()
        print(f"✅ Upload concluído!")
        
        if os.path.exists(arquivo_local):
            os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro no FTP: {e}")

def iniciar_download(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            arquivo = ydl.prepare_filename(info)
            gerenciar_ftp_e_upload(arquivo)
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        iniciar_download(sys.argv[1])
