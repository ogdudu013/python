import os
import yt_dlp
import mysql.connector
from ftplib import FTP
import time

# --- CONFIGURAÇÕES FTP (Arquivos) ---
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" # <--- Coloque sua senha aqui

# --- CONFIGURAÇÕES MYSQL (Banco de Dados) ---
DB_HOST = "sql213.byethost6.com"
DB_USER = "b6_41303686"
DB_PASS = "0512pablo" # <--- Coloque sua senha aqui
DB_NAME = "b6_41303686_PikachuMusic"

def baixar_do_youtube(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"\n🔎 Buscando no YouTube: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        
        # Gera nome único para o arquivo
        timestamp = int(time.time())
        nome_arquivo = f"yt_{timestamp}.mp3"
        os.rename('temp_audio.mp3', nome_arquivo)
        
        return nome_arquivo, info['title']

def upload_ftp(arquivo_local):
    print(f"🚀 Enviando via FTP para htdocs/uploads/songs...")
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        
        # Navega até a pasta de destino
        ftp.cwd('htdocs/uploads/songs')
        
        with open(arquivo_local, 'rb') as f:
            ftp.storbinary(f'STOR {arquivo_local}', f)
        
        ftp.quit()
        print("✅ Arquivo enviado com sucesso ao FTP!")
        return True
    except Exception as e:
        print(f"❌ Erro no FTP: {e}")
        return False

def registrar_no_mysql(nome_arquivo, titulo_musica):
    print("🗄️ Conectando ao MySQL para registrar...")
    try:
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = db.cursor()
        
        sql = "INSERT INTO music_global (title, file_path, plays, created_at) VALUES (%s, %s, 0, NOW())"
        val = (titulo_musica, nome_arquivo)
        
        cursor.execute(sql, val)
        db.commit()
        
        print(f"✅ Sucesso! '{titulo_musica}' registrado no banco de dados.")
        db.close()
    except Exception as e:
        print(f"❌ Erro no MySQL: {e}")

if __name__ == "__main__":
    print("=== PIKACHU MUSIC - AUTOMATION SYSTEM ===")
    busca = input("Digite o nome da música ou link: ")
    
    try:
        # 1. Baixa
        arquivo, titulo = baixar_do_youtube(busca)
        
        # 2. Sobe o arquivo
        if upload_ftp(arquivo):
            # 3. Salva no banco
            registrar_no_mysql(arquivo, titulo)
            
            # Limpa o PC local
            if os.path.exists(arquivo):
                os.remove(arquivo)
                
    except Exception as e:
        print(f"Erro Geral no Processo: {e}")
