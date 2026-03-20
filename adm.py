import os
import yt_dlp
from ftplib import FTP
import time

# --- DADOS DE ACESSO ---
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" 

def baixar_yt(busca):
    timestamp = int(time.time())
    nome_saida_base = f"audio_{timestamp}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        # Forçamos o nome do arquivo final desde o início para evitar erros de renomeação
        'outtmpl': f'{nome_saida_base}.%(ext)s',
        'ffmpeg_location': '/data/data/com.termux/files/usr/bin/ffmpeg',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
        
        # Se for uma lista de resultados, pega o primeiro
        if 'entries' in info:
            info = info['entries'][0]
        
        titulo = info.get('title', 'Sem título').replace('|', '-') # Evita quebrar seu split no PHP
        capa = info.get('thumbnail', '')
        letra = info.get('description', 'Sem letra').replace('\n', '[LF]')
        
        nome_audio = f"{nome_saida_base}.mp3"
        nome_txt = f"data_{timestamp}.txt"

        # Verificação Crítica: O arquivo realmente existe?
        if not os.path.exists(nome_audio):
            raise FileNotFoundError(f"Erro: O arquivo {nome_audio} não foi gerado pelo FFmpeg.")

        with open(nome_txt, 'w', encoding='utf-8') as f:
            f.write(f"{titulo}|{nome_audio}|{capa}|{letra}")
            
        return nome_audio, nome_txt

def subir_ftp(arquivo, pasta_destino):
    """
    Sobe arquivos garantindo a estrutura de pastas htdocs
    """
    if not os.path.exists(arquivo):
        print(f"⚠️ Arquivo {arquivo} não encontrado para upload.")
        return False

    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.set_pasv(True)

        # 1. Entrar na htdocs (obrigatório no ByetHost/InfinityFree)
        ftp.cwd('/')
        try:
            ftp.cwd('htdocs')
        except:
            pass # Já está na raiz ou htdocs não necessária (raro nesses hosts)

        # 2. Criar/Entrar no caminho de destino (ex: uploads/songs)
        for pasta in pasta_destino.split('/'):
            if not pasta: continue
            try:
                ftp.cwd(pasta)
            except:
                ftp.mkd(pasta)
                ftp.cwd(pasta)
        
        print(f"📤 Enviando {arquivo} para {ftp.pwd()}...")
        with open(arquivo, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(arquivo)}', f)
        
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ Erro FTP ao enviar {arquivo}: {e}")
        return False

if __name__ == "__main__":
    busca = input("Nome da música: ").strip()
    if not busca:
        print("Digite algo para buscar!")
        exit()

    audio_file = None
    txt_file = None

    try:
        audio_file, txt_file = baixar_yt(busca)
        
        # Ordem de segurança: primeiro o áudio (pesado), depois o TXT (gatilho)
        # Isso evita que o PHP processe um TXT antes do áudio terminar de subir
        if subir_ftp(audio_file, 'uploads/songs'):
            if subir_ftp(txt_file, 'uploads/queue'):
                print("\n✅ Sucesso Total! Áudio e metadados sincronizados.")
            else:
                print("\n⚠️ Áudio enviado, mas falha ao enviar o TXT.")
        else:
            print("\n❌ Falha crítica: O áudio não foi enviado. Abortando TXT.")

    except Exception as e:
        print(f"\n💥 Erro Geral: {e}")
    
    finally:
        # Limpeza de segurança (sempre executa, mesmo se der erro)
        for f in [audio_file, txt_file]:
            if f and os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Temporário {f} removido.")
