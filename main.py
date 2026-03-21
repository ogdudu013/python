import requests
import time
import io
from ftplib import FTP # Mantemos o FTP apenas para enviar o log.txt de volta

# ================= CONFIGURAÇÕES =================
API_URL = "http://pikachutech.byethost6.com/bot_api.php"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"
# FTP para LOGS (Opcional, para aparecer no seu site)
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

def enviar_log_ftp(mensagem):
    try:
        with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            linha = f"[{time.strftime('%H:%M:%S')}] {mensagem}\n"
            ftp.storbinary('APPE htdocs/log.txt', io.BytesIO(linha.encode('utf-8')))
    except: pass

def perguntar_ao_gemini(texto):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"Resolva a tarefa escolar: {texto}. Responda apenas o numero da alternativa correta (0, 1, 2...)."
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        resp = res.json()['candidates'][0]['content']['parts'][0]['text']
        return int("".join(filter(str.isdigit, resp))[0])
    except: return 0

def processar_login(dados):
    ra = dados.get('ra')
    digito = dados.get('digito')
    uf = dados.get('uf')
    senha = dados.get('senha')
    
    print(f"[!] Processando RA: {ra}...")
    enviar_log_ftp(f"Iniciando Bot para RA {ra}")
    
    # --- Aqui entra sua logica de requests do CMSP ---
    # (Use a mesma lógica de login e resposta que já tínhamos)
    
    time.sleep(5) # Simulação de tempo de tarefa
    enviar_log_ftp(f"RA {ra} finalizado com sucesso!")

# --- LOOP DA FILA ---
print(">>> PK SCRIPT FILA DE ESPERA ATIVA <<<")
while True:
    try:
        response = requests.get(API_URL, timeout=15)
        res_json = response.json()
        
        if res_json['status'] == "sucesso":
            processar_login(res_json['dados'])
        else:
            # Se a fila estiver vazia, ele espera 10 segundos e tenta de novo
            time.sleep(10)
            
    except Exception as e:
        print(f"Erro ao conectar na API: {e}")
        time.sleep(20)
