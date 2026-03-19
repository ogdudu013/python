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
        # Localização padrão do ffmpeg no Termux
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128'
        }],
        'quiet': False, # Mudei para False para você ver o progresso no Termux
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
        # Realiza a busca e pega o primeiro resultado
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        
        timestamp = int(time.time())
        nome_mp3 = f"song_{timestamp}.mp3"
        nome_txt = f"data_{timestamp}.txt"
        
        # O yt-dlp salva como temp.mp3 após a conversão
        if os.path.exists('temp.mp3'):
            os.rename('temp.mp3', nome_mp3)
        else:
            # Caso o ffmpeg mude a extensão inesperadamente
            for f in os.listdir('.'):
                if f.startswith('temp.'):
                    os.rename(f, nome_mp3)
        
        # Cria o arquivo TXT com os dados: Titulo|NomeArquivo
        with open(nome_txt, 'w', encoding='utf-8') as f:
            f.write(f"{info['title']}|{nome_mp3}")
            
        return nome_mp3, nome_txt

def subir_ftp(arquivo, pasta):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)
        
        # Tenta entrar na pasta, se falhar ele avisa
        try:
            ftp.cwd(pasta)
        except:
            print(f"⚠️ Pasta {pasta} não encontrada no servidor.")
            return False

        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo}', f)
        
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ Erro FTP ({arquivo}): {e}")
        return False

if __name__ == "__main__":
    busca = input("Nome da música: ")
    mp3, txt = None, None
    
    try:
        mp3, txt = baixar_yt(busca)
        
        print("🚀 Subindo música...")
        if subir_ftp(mp3, 'htdocs/uploads/songs'):
            print("✅ Música enviada!")
            
            print("📝 Subindo dados (.txt)...")
            if subir_ftp(txt, 'htdocs/uploads/queue'):
                print("✅ Dados enviados! Agora acesse o site para processar.")
    
    except Exception as e:
        print(f"💥 Erro Geral: {e}")
    
    finally:
        # Limpeza local garantida
        print("🧹 Limpando arquivos temporários...")
        for f in [mp3, txt, 'temp.mp3', 'temp.webm', 'temp.m4a']:
            if f and os.path.exists(f):
                os.remove(f)
