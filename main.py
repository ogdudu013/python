import requests
import time
import io
import json
from ftplib import FTP

# ================= CONFIGURAÇÕES =================
API_URL = "http://pikachutech.byethost6.com/bot_api.php"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"
COOKIE_BYET = "9275145aed2835abcbd7e624548339d4" # Verifique se este ainda é o atual

# Configurações de Log (FTP)
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        # User-agent de Android (mais discreto)
        self.ua = "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"

    def enviar_log(self, msg):
        print(f"[LOG] {msg}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                linha = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
                ftp.storbinary('APPE htdocs/log.txt', io.BytesIO(linha.encode('utf-8')))
        except: pass

    def perguntar_gemini(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = f"Resolva essa questão de múltipla escolha escolar. Responda APENAS o número do índice da alternativa correta (0 para A, 1 para B...). Questão: {pergunta}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            txt = res.json()['candidates'][0]['content']['parts'][0]['text']
            num = "".join(filter(str.isdigit, txt))
            return int(num[0]) if num else 0
        except: return 0

    def login(self):
        try:
            url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
            h_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
            r_sed = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h_sed, timeout=15)
            if r_sed.status_code != 200: return False
            t_sed = r_sed.json().get("token")
            url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
            r_cmsp = self.session.post(url_cmsp, json={"token": t_sed}, headers={"x-api-realm": "edusp"}, timeout=15)
            if r_cmsp.status_code == 200:
                self.auth_token = r_cmsp.json().get("auth_token")
                return True
        except: pass
        return False

    def resolver_tudo(self):
        self.enviar_log(f"Processando RA {self.ra_completo}")
        if not self.login():
            self.enviar_log("Erro: Login recusado.")
            return False

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=10", headers=headers, timeout=15)
        
        if res.status_code == 200:
            tarefas = res.json()
            for t in tarefas:
                t_id = t['id']
                escolha = self.perguntar_gemini(t.get('title', ''))
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {"answers": {"0": escolha}, "last_question": True, "duration": 60}
                self.session.post(url_ans, json=payload, headers=headers, timeout=10)
                time.sleep(1)
            self.enviar_log("Concluido!")
            return True
        return False

def monitorar():
    print(">>> PK SCRIPT INICIADO <<<")
    
    web_session = requests.Session()
    headers_api = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
        "Cookie": f"__test={COOKIE_BYET}",
        "Accept": "application/json"
    }

    while True:
        try:
            response = web_session.get(API_URL, headers=headers_api, timeout=15)
            
            # Se não for JSON, o ByetHost bloqueou
            if "text/html" in response.headers.get("Content-Type", ""):
                print("[-] Erro: Cookie expirado ou bloqueio AES. Atualize o Cookie!")
                time.sleep(30)
                continue

            api_data = response.json()

            if api_data.get('status') == "sucesso":
                d = api_data['dados']
                bot = PKScriptBot(d['ra'], d['digito'], d['uf'], d['senha'])
                if bot.resolver_tudo():
                    # Avisa o PHP para apagar a linha processada
                    web_session.get(f"{API_URL}?limpar=1", headers=headers_api)
                    print("[+] Fila limpa.")
            else:
                time.sleep(15)
                
        except json.decoder.JSONDecodeError:
            print("[-] O Servidor não enviou JSON (Bloqueio do ByetHost).")
            time.sleep(20)
        except Exception as e:
            print(f"[-] Erro inesperado: {e}")
            time.sleep(20)

if __name__ == "__main__":
    monitorar()
