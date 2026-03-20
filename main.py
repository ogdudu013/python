import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class PikachuBot:
    def __init__(self, url):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Cria uma pasta para salvar os arquivos
        self.diretorio = "pikachu_downloads"
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)

    def baixar_arquivo(self, link_arquivo):
        nome_arquivo = os.path.join(self.diretorio, link_arquivo.split("/")[-1])
        
        # Resolve links relativos (ex: /img/foto.jpg -> https://site.com/img/foto.jpg)
        url_completa = urljoin(self.url, link_arquivo)
        
        try:
            print(f"📥 Baixando: {nome_arquivo}...")
            with requests.get(url_completa, headers=self.headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(nome_arquivo, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"✅ Concluído!")
        except Exception as e:
            print(f"❌ Erro ao baixar {link_arquivo}: {e}")

    def capturar_e_baixar(self):
        print(f"⚡ [Pikachu] Analisando: {self.url}...")
        
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Lista de extensões que o Pikachu vai capturar
                extensoes_alvo = ('.pdf', '.zip', '.png', '.jpg', '.jpeg', '.mp4', '.docx')
                
                links = soup.find_all(['a', 'img']) # Procura em links e tags de imagem
                arquivos_para_baixar = []

                for tag in links:
                    # Pega o atributo 'href' de links ou 'src' de imagens
                    link_bruto = tag.get('href') or tag.get('src')
                    
                    if link_bruto and any(link_bruto.lower().endswith(ext) for ext in extensoes_alvo):
                        arquivos_para_baixar.append(link_bruto)

                # Remove duplicatas
                arquivos_para_baixar = list(set(arquivos_para_baixar))

                if arquivos_para_baixar:
                    print(f"🎯 Encontrei {len(arquivos_para_baixar)} arquivos!")
                    confirmar = input("Deseja iniciar o download de todos? (s/n): ")
                    if confirmar.lower() == 's':
                        for arq in arquivos_para_baixar:
                            self.baixar_arquivo(arq)
                    else:
                        print("⚡ Operação cancelada pelo mestre.")
                else:
                    print("❌ Nenhum arquivo interessante encontrado.")

            else:
                print(f"🚫 Site bloqueou o acesso. Status: {response.status_code}")

        except Exception as e:
            print(f"💥 Erro crítico: {e}")

if __name__ == "__main__":
    url_alvo = input("Digite a URL do site: ")
    if not url_alvo.startswith("http"):
        url_alvo = "https://" + url_alvo
        
    bot = PikachuBot(url_alvo)
    bot.capturar_e_baixar()
