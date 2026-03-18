import os
import yt_dlp
import requests
import re
from ftplib import FTP, error_perm
import config

def enviar_ftp(arquivo_local, pasta_remota):
    print(f"\n🚀 Enviando para o ByetHost...")
    try:
        ftp = FTP(config.FTP_HOST)
        ftp.login(user=config.FTP_USER, passwd=config.FTP_PASS)
        ftp.cwd('/htdocs/')
        try:
            ftp.cwd(pasta_remota)
        except error_perm:
            print(f"📁 Criando pasta {pasta_remota}...")
            ftp.mkd(pasta_remota)
            ftp.cwd(pasta_remota)
        
        with open(arquivo_local, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(arquivo_local)}', f)
        
        ftp.quit()
        print(f"✅ Sucesso! Salvo no servidor.")
        os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro FTP: {e}")

def buscar_pdf_universal(nome):
    print(f"🔎 Buscando '{nome}' na Web...")
    
    # Lista de termos de busca para aumentar as chances
    queries = [
        f'intitle:"{nome}" filetype:pdf',
        f'"{nome}" pdf archive.org',
        f'{nome} download gratis pdf'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }

    for query in queries:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            # Tenta encontrar links que terminam em .pdf ou links do archive.org
            links = re.findall(r'https?://[^\s"&<>]+(?:\.pdf)', r.text)
            
            # Filtro para remover links de lixo do próprio Google
            links = [l for l in links if "google.com" not in l and "schema.org" not in l]

            if links:
                link_final = requests.utils.unquote(links[0])
                nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
                
                print(f"🔗 Link encontrado: {link_final[:60]}...")
                print("📥 Iniciando download...")
                
                with requests.get(link_final, headers=headers, stream=True, timeout=60, allow_redirects=True) as res:
                    res.raise_for_status()
                    with open(nome_arq, 'wb') as f:
                        for chunk in res.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                return nome_arq
        except:
            continue
            
    print("❌ Infelizmente não encontrei um link direto para download.")
    return None

def main():
    while True:
        os.system('clear')
        print("====================================")
        print("      DOWNLOADER FTP - TERMUX       ")
        print("====================================")
        print("1. YouTube (Vídeo)")
        print("2. Livros/HQs (Busca PDF)")
        print("0. Sair")
        
        op = input("\n➔ Escolha: ")

        if op == '1':
            link = input("🔗 Link do YouTube: ")
            print("⏳ Baixando vídeo...")
            try:
                ydl_opts = {'outtmpl': '%(title)s.%(ext)s', 'quiet': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    enviar_ftp(ydl.prepare_filename(info), "videos")
            except Exception as e:
                print(f"❌ Erro no YouTube: {e}")
                
        elif op == '2':
            nome = input("📖 Nome do Livro/HQ: ")
            arq = buscar_pdf_universal(nome)
            if arq:
                enviar_ftp(arq, "leitura")
            input("\n[Pressione Enter para continuar]")
                
        elif op == '0':
            break

if __name__ == "__main__":
    main()
