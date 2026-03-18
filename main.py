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
        print(f"✅ Sucesso! Salvo em /{pasta_remota}/ no servidor.")
        os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro FTP: {e}")

def buscar_pdf_universal(nome):
    print(f"🔎 Buscando '{nome}' na Web...")
    
    # Query otimizada para PDF
    query = f'"{nome}" pdf'
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        
        # Tenta capturar links de PDF de 3 formas diferentes
        links = re.findall(r'url\?q=(https?://[^&]+\.pdf)', r.text)
        if not links:
            links = re.findall(r'href="(https?://[^"]+\.pdf)"', r.text)
        if not links:
            links = re.findall(r'https?://[^\s"&<>]+(?:\.pdf)', r.text)

        if links:
            # Limpa o link (remove códigos do Google como %20, %2F)
            link_final = requests.utils.unquote(links[0])
            
            # Filtro básico para evitar links do próprio Google
            if "google.com" in link_final:
                link_final = links[1] if len(links) > 1 else None

            if link_final:
                nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
                print(f"🔗 Link encontrado! Baixando de: {link_final[:60]}...")
                
                # Download com redirecionamento e stream
                with requests.get(link_final, headers=headers, stream=True, timeout=60, allow_redirects=True) as res:
                    # Se der 403, tenta um último recurso sem Referer
                    if res.status_code == 403:
                        res = requests.get(link_final, stream=True, timeout=60, allow_redirects=True)
                    
                    res.raise_for_status()
                    with open(nome_arq, 'wb') as f:
                        for chunk in res.iter_content(chunk_size=1024*1024): # 1MB chunks
                            if chunk:
                                f.write(chunk)
                return nome_arq
        
        print("❌ Nenhum PDF encontrado. Tente ser mais específico (ex: 'A Culpa é das Estrelas John Green')")
            
    except Exception as e:
        print(f"❌ Erro no download: {e}")
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
                
        elif op == '0':
            break
        input("\n[Pressione Enter para voltar]")

if __name__ == "__main__":
    main()
