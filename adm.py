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
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg', # Ajuste se não for Termux
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': False,
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
        if 'entries' in info: info = info['entries'][0]
        
        titulo = info.get('title', 'Sem título')
        capa = info.get('thumbnail', 'https://pikachutech.byethost6.com/icon.png')
        letra = info.get('description', 'Sem letra disponível.').replace('\n', '[LF]')

        timestamp = int(time.time())
        nome_audio = f"audio_{timestamp}.mp3"
        nome_txt = f"data_{timestamp}.txt"
        
        if os.path.exists("temp.mp3"):
            os.rename("temp.mp3", nome_audio)
            
        with open(nome_txt, 'w', encoding='utf-8') as f:
            f.write(f"{titulo}|{nome_audio}|{capa}|{letra}")
            
        return nome_audio, nome_txt

def subir_ftp(arquivo, destino):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        
        # Garante que entra na htdocs do ByetHost
        caminho_completo = f"htdocs/{destino}"
        
        # Navega/Cria pastas
        for pasta in caminho_completo.split('/'):
            if pasta:
                try: ftp.cwd(pasta)
                except:
                    ftp.mkd(pasta)
                    ftp.cwd(pasta)
        
        print(f"📤 Enviando {arquivo}...")
        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo}', f)
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ Erro FTP: {e}")
        return False

if __name__ == "__main__":
    busca = input("Nome da música: ")
    try:
        audio, txt = baixar_yt(busca)
        if subir_ftp(audio, 'uploads/songs'):
            subir_ftp(txt, 'uploads/queue')
            print("✅ Enviado! Agora execute o processar.php no site.")
        os.remove(audio); os.remove(txt)
    except Exception as e: print(f"💥 Erro: {e}")
