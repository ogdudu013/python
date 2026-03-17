import os
import sys
import yt_dlp
import requests
from ftplib import FTP, error_perm
from libgen_api import LibgenSearch
import config # Seu arquivo com as senhas

def limpar_tela():
    os.system('clear')

def enviar_ftp(arquivo_local, pasta_remota):
    print(f"\n🚀 Conectando ao ByetHost ({config.FTP_HOST})...")
    try:
        ftp = FTP(config.FTP_HOST)
        ftp.login(user=config.FTP_USER, passwd=config.FTP_PASS)
        
        ftp.cwd('/htdocs/')
        try:
            ftp.cwd(pasta_remota)
        except error_perm:
            print(f"📁 Criando pasta '{pasta_remota}'...")
            ftp.mkd(pasta_remota)
            ftp.cwd(pasta_remota)

        print(f"📤 Enviando: {os.path.basename(arquivo_local)}")
        with open(arquivo_local, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(arquivo_local)}', f)
        
        ftp.quit()
        print(f"✅ Sucesso! Arquivo enviado para /htdocs/{pasta_remota}/")
        os.remove(arquivo_local)
    except Exception as e:
        print(f"❌ Erro no FTP: {e}")

def menu_youtube():
    link = input("\n🔗 Cole o link do YouTube: ")
    print("⏳ Baixando vídeo...")
    ydl_opts = {'format': 'best', 'outtmpl': '%(title)s.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        arquivo = ydl.prepare_filename(info)
        enviar_ftp(arquivo, "videos")

def menu_livros_hq(tipo):
    nome = input(f"\n📖 Digite o nome do(a) {tipo}: ")
    print(f"🔎 Buscando '{nome}' no Libgen...")
    s = LibgenSearch()
    resultados = s.search_title(nome)
    
    if not resultados:
        print("❌ Nada encontrado.")
        return

    # Mostra os 3 primeiros resultados
    print("\nResultados encontrados:")
    for i, res in enumerate(resultados[:3]):
        print(f"[{i+1}] {res['Title']} ({res['Extension']}) - {res['Size']}")
    
    escolha = input("\nEscolha o número (ou '0' para cancelar): ")
    if escolha == '1' or escolha == '2' or escolha == '3':
        item = resultados[int(escolha)-1]
        links = s.resolve_download_links(item)
        print("📥 Baixando arquivo...")
        
        nome_arq = f"{item['Title'][:30]}.{item['Extension']}".replace(" ", "_")
        r = requests.get(links['GET'], allow_redirects=True)
        with open(nome_arq, 'wb') as f:
            f.write(r.content)
        
        pasta = "livros" if tipo == "Livro" else "hqs"
        enviar_ftp(nome_arq, pasta)

def main():
    while True:
        limpar_tela()
        print("=== MASTER DOWNLOADER TERMUX ===")
        print("1. Baixar Vídeo (YouTube)")
        print("2. Buscar Livro")
        print("3. Buscar HQ / Comic")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            menu_youtube()
        elif opcao == '2':
            menu_livros_hq("Livro")
        elif opcao == '3':
            menu_livros_hq("HQ")
        elif opcao == '0':
            print("Saindo...")
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para voltar ao menu...")

if __name__ == "__main__":
    main()
