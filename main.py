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
            ftp.mkd(pasta_remota)
            ftp.cwd(pasta_remota)
        with open(arquivo_local, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(arquivo_local)}', f)
        ftp.quit()
        print(f"✅ Sucesso!")
        os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro FTP: {e}")

def buscar_pdf_universal(nome):
    """Busca PDFs usando o motor do DuckDuckGo (mais rápido e sem bloqueio)"""
    print(f"🔎 Buscando '{nome}' na Web...")
    
    # Query focada em arquivos PDF e HQs
    query = f"{nome} filetype:pdf"
    url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        # Extrai links que terminam em .pdf
        links = re.findall(r'href="(https?://[^"]+\.pdf)"', r.text)
        
        if not links:
            print("❌ Nenhum arquivo encontrado diretamente. Tentando busca secundária...")
            # Tenta um padrão de link de download comum
            links = re.findall(r'(https?://[^\s<>"]+\.(?:pdf|epub|cbr))', r.text)

        if links:
            # Filtra links inúteis (como propagandas)
            link_final = links[0]
            nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
            
            print(f"🔗 Link encontrado! Baixando de: {link_final[:50]}...")
            
            with requests.get(link_final, stream=True, timeout=30, headers=headers) as res:
                res.raise_for_status()
                with open(nome_arq, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
            return nome_arq
        else:
            print("❌ Nada encontrado nos servidores públicos.")
            
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
    return None

def main():
    while True:
        os.system('clear')
        print("=== DOWNLOADER ULTRA-LEVE (NO-LXML) ===")
        print("1. YouTube (Vídeo)")
        print("2. Livros/HQs (Busca Universal PDF)")
        print("0. Sair")
        op = input("\n➔ Escolha: ")

        if op == '1':
            link = input("🔗 Link do YouTube: ")
            print("⏳ Processando vídeo...")
            try:
                with yt_dlp.YoutubeDL({'outtmpl': '%(title)s.%(ext)s', 'quiet': True}) as ydl:
                    info = ydl.extract_info(link, download=True)
                    enviar_ftp(ydl.prepare_filename(info), "videos")
            except Exception as e:
                print(f"❌ Erro no YouTube: {e}")
                
        elif op == '2':
            nome = input("📖 Nome do Livro/HQ: ")
            arq = buscar_pdf_universal(nome)
            if arq: 
                enviar_ftp(arq, "leitura")
            else:
                print("⚠️ Tente ser mais específico no nome.")
                
        elif op == '0': 
            break
        input("\n[Pressione Enter para voltar ao menu]")

if __name__ == "__main__":
    main()
