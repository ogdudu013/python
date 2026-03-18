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
        print(f"✅ Sucesso! Arquivo disponível no seu servidor.")
        os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro FTP: {e}")

def buscar_pdf_universal(nome):
    print(f"🔎 Buscando '{nome}' na Web...")
    
    # Busca focada em PDF no Google
    query = f"{nome} filetype:pdf"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    # Headers completos para simular um navegador real e evitar o Erro 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/'
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        # Extrai links diretos de PDF dos resultados do Google
        links = re.findall(r'url\?q=(https?://[^&]+\.pdf)', r.text)
        
        if not links:
            # Tenta um padrão secundário de busca
            links = re.findall(r'href="(https?://[^"&]+\.pdf)"', r.text)

        if links:
            link_final = requests.utils.unquote(links[0])
            nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
            
            print(f"🔗 Link encontrado! Tentando baixar...")
            
            # Download com suporte a redirecionamento e stream para arquivos grandes
            with requests.get(link_final, headers=headers, stream=True, timeout=60, allow_redirects=True) as res:
                # Se ainda der 403, tenta sem os headers de Referer (alguns sites exigem isso)
                if res.status_code == 403:
                    res = requests.get(link_final, stream=True, timeout=60, allow_redirects=True)
                
                res.raise_for_status()
                
                with open(nome_arq, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=1024*1024): # 1MB por vez
                        if chunk:
                            f.write(chunk)
            return nome_arq
        else:
            print("❌ Nenhum PDF direto encontrado. Tente um nome mais específico.")
            
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
                # Configuração básica para o yt-dlp
                ydl_opts = {
                    'outtmpl': '%(title)s.%(ext)s',
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    arquivo = ydl.prepare_filename(info)
                    enviar_ftp(arquivo, "videos")
            except Exception as e:
                print(f"❌ Erro no YouTube: {e}")
                
        elif op == '2':
            nome = input("📖 Nome do Livro/HQ: ")
            arquivo_baixado = buscar_pdf_universal(nome)
            if arquivo_baixado:
                enviar_ftp(arquivo_baixado, "leitura")
                
        elif op == '0':
            print("Saindo...")
            break
            
        input("\n[Pressione Enter para voltar]")

if __name__ == "__main__":
    main()
