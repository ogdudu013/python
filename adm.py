import requests
import os
import yt_dlp
import time

# --- CONFIGURAÇÕES ---
SITE_URL = "http://Pikachutech.byethost6.com"
API_URL = f"{SITE_URL}/admin_api.php"
TOKEN = "og.dudu013"

def baixar_youtube(busca):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'musica_temp.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 A procurar no YouTube: {busca}")
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)['entries'][0]
        return "musica_temp.mp3", info['title']

def enviar_para_site(caminho, titulo):
    print(f"🚀 A enviar '{titulo}' para o site...")
    
    # Enviamos o token na URL para evitar bloqueios de firewall do ByetHost
    params = {'action': 'upload', 'token': TOKEN}
    headers = {'X-API-TOKEN': TOKEN}
    
    try:
        with open(caminho, 'rb') as f:
            files = {'media_file': (f"{titulo}.mp3", f, 'audio/mpeg')}
            # Algumas hospedagens gratuitas exigem cookies, fazemos o post direto
            r = requests.post(API_URL, params=params, files=files, headers=headers)
        
        if "success" in r.text:
            print("✅ Sucesso! Música adicionada ao catálogo.")
        else:
            print(f"⚠️ Resposta do Servidor: {r.text}")
            
    except Exception as e:
        print(f"❌ Erro na ligação: {e}")
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)

def menu():
    while True:
        print("\n--- ⚡ PIKACHU TECH ADMIN BOT ---")
        print("1. Download YT -> Upload Site")
        print("2. Editar Nome (ID)")
        print("3. Deletar Música (ID)")
        print("4. Sair")
        
        op = input("\nEscolha: ")

        if op == '1':
            nome = input("Nome da música/artista: ")
            try:
                arq, tit = baixar_youtube(nome)
                enviar_para_site(arq, tit)
            except Exception as e:
                print(f"Erro: {e}")

        elif op == '2':
            idx = input("ID da música: ")
            novo = input("Novo título: ")
            r = requests.post(f"{API_URL}?action=edit&token={TOKEN}", data={'id':idx, 'title':novo})
            print(r.text)

        elif op == '3':
            idx = input("ID para deletar: ")
            r = requests.get(f"{API_URL}?action=delete&id={idx}&token={TOKEN}")
            print(r.text)

        elif op == '4':
            break

if __name__ == "__main__":
    menu()
