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

def buscar_libgen_leve(nome):
    print(f"🔎 Buscando '{nome}'...")
    # Usando um mirror que aceita buscas simples via URL
    url = f"https://libgen.is/search.php?req={nome.replace(' ', '+')}&column=def"
    try:
        r = requests.get(url, timeout=10)
        # Busca links de download (pattern simples para não usar BS4/LXML)
        links = re.findall(r'href="http://library\.lol/main/([A-Z0-9]+)"', r.text)
        
        if not links:
            print("❌ Nenhum livro encontrado.")
            return None

        # Pega o primeiro resultado e vai para a página de download
        page_url = f"http://library.lol/main/{links[0]}"
        r_page = requests.get(page_url, timeout=10)
        download_link = re.findall(r'href="(https?://GET\.gen\.lib\.rus\.ec/[^"]+)"', r_page.text)
        
        if not download_link:
            # Tenta um segundo padrão de link (Cloudflare/IPFS)
            download_link = re.findall(r'href="(https?://cloudflare-ipfs\.com/[^"]+)"', r_page.text)

        if download_link:
            nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
            print("📥 Baixando arquivo...")
            res = requests.get(download_link[0], stream=True)
            with open(nome_arq, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return nome_arq
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
    return None

def main():
    while True:
        os.system('clear')
        print("=== DOWNLOADER VELOZ (SEM LXML) ===")
        print("1. YouTube")
        print("2. Livros/HQs")
        print("0. Sair")
        op = input("\n➔ Escolha: ")

        if op == '1':
            link = input("🔗 Link: ")
            with yt_dlp.YoutubeDL({'outtmpl': '%(title)s.%(ext)s'}) as ydl:
                info = ydl.extract_info(link, download=True)
                enviar_ftp(ydl.prepare_filename(info), "videos")
        elif op == '2':
            nome = input("📖 Nome: ")
            arq = buscar_libgen_leve(nome)
            if arq: enviar_ftp(arq, "leitura")
        elif op == '0': break
        input("\n[Enter para voltar]")

if __name__ == "__main__":
    main()
