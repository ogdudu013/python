import requests
import os
import yt_dlp

# --- CONFIGURAÇÕES ---
BASE_URL = "http://pikachutech.byethost6.com" 
API_ADMIN = f"{BASE_URL}/admin_api.php"
TOKEN = "og.dudu013" # Deve ser igual ao do PHP
TEMP_DIR = "yt_downloads"

# Header de autenticação que o PHP vai ler
HEADERS = {
    "X-API-TOKEN": TOKEN,
    "User-Agent": "PikachuAdminPython/1.0"
}

def download_yt(query):
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"🔎 Buscando: {query}...")
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
        filename = f"{info['title']}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        return filepath, filename

def api_upload(path, name):
    print("🚀 Enviando para o servidor...")
    with open(path, 'rb') as f:
        files = {'media_file': (name, f, 'audio/mpeg')}
        r = requests.post(f"{API_ADMIN}?action=upload", files=files, headers=HEADERS)
    os.remove(path) # Limpa arquivo local
    return r.json()

def api_delete(mid):
    r = requests.get(f"{API_ADMIN}?action=delete&id={mid}", headers=HEADERS)
    return r.json()

def api_edit(mid, title):
    data = {'id': mid, 'title': title}
    r = requests.post(f"{API_ADMIN}?action=edit", data=data, headers=HEADERS)
    return r.json()

def menu():
    while True:
        print("\n--- ⚡ PIKACHU API ADMIN (TOKEN AUTH) ---")
        print("1. Buscar no YT e Upload Direto")
        print("2. Editar Música (por ID)")
        print("3. Deletar Música (por ID)")
        print("4. Sair")
        
        op = input("\nEscolha: ")

        if op == '1':
            q = input("Nome da música/artista: ")
            try:
                p, n = download_yt(q)
                res = api_upload(p, n)
                print(f"RESPOSTA: {res['message']}")
            except Exception as e: print(f"Erro: {e}")
        
        elif op == '2':
            mid = input("ID: ")
            txt = input("Novo Título: ")
            print(api_edit(mid, txt))
            
        elif op == '3':
            mid = input("ID para DELETAR: ")
            if input("Confirmar? (s/n): ") == 's':
                print(api_delete(mid))
        
        elif op == '4': break

if __name__ == "__main__":
    menu()
