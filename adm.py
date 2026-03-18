import os
import yt_dlp
from ftplib import FTP
import time

# --- DADOS DE ACESSO ---
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" 

def baixar_yt(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        timestamp = int(time.time())
        nome_mp3 = f"song_{timestamp}.mp3"
        nome_txt = f"data_{timestamp}.txt"
        
        os.rename('temp.mp3', nome_mp3)
        
        # Cria o arquivo TXT com os dados: Titulo|NomeArquivo
        with open(nome_txt, 'w', encoding='utf-8') as f:
            f.write(f"{info['title']}|{nome_mp3}")
            
        return nome_mp3, nome_txt

def subir_ftp(arquivo, pasta):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        ftp.cwd(pasta)
        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo}', f)
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ Erro FTP ({arquivo}): {e}")
        return False

if __name__ == "__main__":
    busca = input("Nome da música: ")
    try:
        mp3, txt = baixar_yt(busca)
        
        print("🚀 Subindo música...")
        if subir_ftp(mp3, 'htdocs/uploads/songs'):
            print("✅ Música enviada!")
            
            print("📝 Subindo dados (.txt)...")
            if subir_ftp(txt, 'htdocs/uploads/queue'):
                print("✅ Dados enviados! Agora acesse o site para processar.")
                
        # Limpeza local
        for f in [mp3, txt]:
            if os.path.exists(f): os.remove(f)
    except Exception as e:
        print(f"💥 Erro: {e}")
