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
        # Localização do ffmpeg no Termux (ajuste se estiver no Windows/PC)
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # VOLTA PARA MP3 PARA GARANTIR REPRODUÇÃO
            'preferredquality': '192',
        }],
        'quiet': False,
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando e Convertendo: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
        if 'entries' in info: info = info['entries'][0]
        
        titulo = info.get('title', 'Sem título')
        # Pega a melhor resolução de capa disponível
        capa = info.get('thumbnail', '') 
        # Pega a descrição, mas remove links e sujeira para tentar isolar a letra
        letra_raw = info.get('description', 'Sem letra disponível.')
        letra = letra_raw.replace('\n', '[LF]').replace('|', '-') 

        timestamp = int(time.time())
        nome_audio = f"audio_{timestamp}.mp3" # Sempre MP3 agora
        nome_txt = f"data_{timestamp}.txt"
        
        # O postprocessor do yt-dlp deixa o arquivo como temp.mp3
        if os.path.exists('temp.mp3'):
            os.rename('temp.mp3', nome_audio)
            
        with open(nome_txt, 'w', encoding='utf-8') as f:
            # Formato: Titulo | NomeArquivo | Capa | Letra
            f.write(f"{titulo}|{nome_audio}|{capa}|{letra}")
            
        return nome_audio, nome_txt

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
        print(f"❌ Erro FTP: {e}")
        return False

if __name__ == "__main__":
    busca = input("Nome da música ou Link: ")
    try:
        audio, txt = baixar_yt(busca)
        print(f"🚀 Enviando MP3: {audio}...")
        subir_ftp(audio, 'htdocs/uploads/songs')
        subir_ftp(txt, 'htdocs/uploads/queue')
        print("✅ Sucesso! Agora vá ao painel Admin e clique em 'Processar Fila'.")
        
        # Limpeza local
        if os.path.exists(audio): os.remove(audio)
        if os.path.exists(txt): os.remove(txt)
    except Exception as e:
        print(f"💥 Erro: {e}")
