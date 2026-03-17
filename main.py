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
    
    # Lista de mirrors oficiais do Libgen
    mirrors = [
        "https://libgen.rs",
        "https://libgen.is",
        "https://libgen.st"
    ]
    
    nome_busca = nome.replace(' ', '+')
    
    for base_url in mirrors:
        try:
            print(f"📡 Tentando servidor: {base_url}...")
            search_url = f"{base_url}/search.php?req={nome_busca}&column=def"
            
            # Aumentamos o timeout para 20 segundos para conexões lentas
            r = requests.get(search_url, timeout=20)
            
            # Busca o ID do livro no HTML
            links = re.findall(r'href="http://library\.lol/main/([A-Z0-9]+)"', r.text)
            
            if links:
                page_url = f"http://library.lol/main/{links[0]}"
                print(f"🔗 Link encontrado! Acessando página de download...")
                
                r_page = requests.get(page_url, timeout=20)
                
                # Tenta encontrar o link direto (GET)
                download_link = re.findall(r'href="(https?://GET\.gen\.lib\.rus\.ec/[^"]+)"', r_page.text)
                
                if not download_link:
                    # Alternativa: IPFS/Cloudflare
                    download_link = re.findall(r'href="(https?://cloudflare-ipfs\.com/[^"]+)"', r_page.text)

                if download_link:
                    nome_arq = f"{nome[:20].replace(' ', '_')}.pdf"
                    print("📥 Baixando arquivo para o Termux...")
                    
                    with requests.get(download_link[0], stream=True, timeout=30) as res:
                        res.raise_for_status()
                        with open(nome_arq, 'wb') as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                f.write(chunk)
                    return nome_arq
        
        except Exception as e:
            print(f"⚠️ Servidor {base_url} falhou ou deu timeout. Tentando próximo...")
            continue

    print("❌ Todos os servidores do Libgen falharam. Tente novamente mais tarde.")
    return None
