import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin

class PikachuBot:
    def __init__(self, url):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.diretorio = "pikachu_data"
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)

    def extrair_apis(self, html):
        """Busca por padrões de URLs de API e endpoints no texto/scripts"""
        print("\n🔍 [Pikachu] Rastreando Endpoints e APIs...")
        # Regex para encontrar padrões comuns de API e caminhos /v1/, /api/, etc.
        padrao_api = r'https?://[\w\.-]+(?:/api/|/v\d/|[\w\.-]+\.json)'
        endpoints = re.findall(padrao_api, html)
        
        # Busca caminhos relativos que sugerem APIs
        caminhos_relativos = re.findall(r'["\'](/\w+/(?:v\d/|api/)[\w\-/]+)["\']', html)
        
        encontrados = list(set(endpoints + caminhos_relativos))
        for api in encontrados:
            print(f" ✨ API/Endpoint Detectado: {api}")
        return encontrados

    def buscar_ferramentas_e_arquivos(self):
        print(f"⚡ [Pikachu] Iniciando Scan Potente: {self.url}")
        
        try:
            res = requests.get(self.url, headers=self.headers, timeout=15)
            html_content = res.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # 1. Extração de APIs
            self.extrair_apis(html_content)

            # 2. Extração de Arquivos e Ferramentas (Scripts JS, Configs)
            print("\n🛠️ [Pikachu] Analisando Ferramentas e Scripts...")
            tags_alvo = {
                'script': 'src',    # Arquivos JS (onde ficam as chaves e rotas)
                'a': 'href',        # Links de download
                'link': 'href',     # CSS e Manifestos
                'img': 'src'        # Mídia
            }

            arquivos = []
            extensoes_tools = ('.js', '.json', '.xml', '.config', '.env', '.pdf', '.zip')

            for tag, attr in tags_alvo.items():
                for item in soup.find_all(tag):
                    link = item.get(attr)
                    if link:
                        url_completa = urljoin(self.url, link)
                        if any(url_completa.lower().endswith(ext) for ext in extensoes_tools):
                            arquivos.append(url_completa)

            arquivos = list(set(arquivos))
            print(f"📦 Total de {len(arquivos)} ferramentas/arquivos identificados.")

            if arquivos:
                op = input("\n📥 Descarregar todos os arquivos encontrados? (s/n): ")
                if op.lower() == 's':
                    for link in arquivos:
                        self.baixar(link)
            
        except Exception as e:
            print(f"💥 Erro: {e}")

    def baixar(self, link):
        try:
            nome = os.path.join(self.diretorio, link.split("/")[-1].split("?")[0])
            with requests.get(link, headers=self.headers, stream=True, timeout=10) as r:
                r.raise_for_status()
                with open(nome, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
            print(f"✅ {nome} salvo!")
        except:
            pass

if __name__ == "__main__":
    url_input = input("Digite a URL alvo: ").strip()
    if not url_input.startswith("http"):
        url_input = "https://" + url_input
    
    bot = PikachuBot(url_input)
    bot.buscar_ferramentas_e_arquivos()
