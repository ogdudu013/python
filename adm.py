import os
import yt_dlp
import requests
from ftplib import FTP
import time

# --- DADOS DE ACESSO ---
FTP_HOST = "ftpupload.net"
FTP_PORT = 21 
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" 

SITE_URL = "http://Pikachutech.byethost6.com"
API_URL = f"{SITE_URL}/admin_api.php"
TOKEN = "og.dudu013"

def baixar_yt(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': False, # Ativado para você ver o progresso do download
        'noplaylist': True,
        # Argumentos para evitar detecção de bot e contornar falta de JS
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🔎 Buscando no YouTube: {busca}")
            info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
            
            timestamp = int(time.time())
            nome_arquivo = f"song_{timestamp}.mp3"
            
            # O yt-dlp pode salvar como .webm ou .m4a antes de converter para .mp3
            if os.path.exists('temp.mp3'):
                os.rename('temp.mp3', nome_arquivo)
            else:
                # Caso o post-processor não renomeie automaticamente
                filename = ydl.prepare_filename(info).replace(info['ext'], 'mp3')
                if os.path.exists(filename):
                    os.rename(filename, nome_arquivo)
                else:
                    # Busca genérica se os nomes falharem
                    for f in os.listdir('.'):
                        if f.startswith('temp.') or f.endswith('.mp3'):
                            os.rename(f, nome_arquivo)
                            break
            
            return nome_arquivo, info['title']
    except Exception as e:
        print(f"❌ Erro no download do YouTube: {e}")
        raise

def subir_ftp(arquivo):
    print(f"🚀 Conectando ao FTP {FTP_HOST}...")
    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT, timeout=30) 
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True) 
        
        print("📂 Mudando para diretório htdocs/uploads/songs...")
        ftp.cwd('htdocs/uploads/songs')
        
        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo}', f)
        
        ftp.quit()
        print("✅ Ficheiro enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro Crítico no FTP: {e}")
        return False

def registrar_api(arquivo, titulo):
    print("📝 Registrando no banco (Modo Camuflado)...")
    payload = {'filename': arquivo, 'title': titulo}
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    })

    try:
        # Ping inicial para validar cookies do ByetHost
        session.get(SITE_URL, timeout=10)
        time.sleep(3) 
        
        url_com_token = f"{API_URL}?action=register_ftp&token={TOKEN}"
        r = session.post(url_com_token, data=payload, timeout=20)
        
        print(f"📡 Resposta do Servidor: {r.text}")
    except Exception as e:
        print(f"❌ Erro na API: {e}")

if __name__ == "__main__":
    print("=== PIKACHU TECH - AUTO UPLOADER ===")
    busca = input("Nome da música: ")
    try:
        arquivo_mp3, titulo_musica = baixar_yt(busca)
        if subir_ftp(arquivo_mp3):
            registrar_api(arquivo_mp3, titulo_musica)
            if os.path.exists(arquivo_mp3):
                os.remove(arquivo_mp3)
                print("🧹 Cache local limpo.")
    except Exception as e:
        print(f"\n💥 Falha no processo: {e}")
