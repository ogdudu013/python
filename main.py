import requests
import time
import io
import json
from ftplib import FTP

# ================= CONFIGURAÇÕES =================
API_URL = "http://pikachutech.byethost6.com/bot_api.php"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"
COOKIE_BYET = "9275145aed2835abcbd7e624548339d4"

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
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def enviar_log(self, msg):
        print(f"[LOG] {msg}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                linha = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
                ftp.storbinary('APPE htdocs/log.txt', io.BytesIO(linha.encode('utf-8')))
        except: pass

    def perguntar_gemini(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = f"Resolva essa questão de múltipla escolha escolar. Responda APENAS o número do índice da alternativa correta (0 para A, 1 para B, 2 para C...). Questão: {pergunta}"
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
        self.enviar_log(f"Iniciando RA {self.ra_completo}...")
        if not self.login():
            self.enviar_log("Erro: Login recusado (RA/Senha incorretos).")
            return

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=15", headers=headers, timeout=15)
        
        if res.status_code == 200:
            tarefas = res.json()
            self.enviar_log(f"Encontradas {len(tarefas)} tarefas.")
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Tarefa')
                escolha = self.perguntar_gemini(titulo)
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {"answers": {"0": escolha}, "last_question": True, "duration": 120}
                self.session.post(url_ans, json=payload, headers=headers, timeout=15)
                self.enviar_log(f"Feito: {titulo[:20]} (IA: {escolha})")
                time.sleep(2)
            self.enviar_log(">>> Finalizado com sucesso!")
            return True
        return False

# --- MONITORAMENTO COM BYPASS ---
def monitorar():
    print(f">>> PK SCRIPT ATIVO | COOKIE: {COOKIE_BYET[:10]}...")
    
    web_session = requests.Session()
    # Injetamos o cookie mágico aqui
    web_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Cookie": f"__test={COOKIE_BYET}"
    })

    while True:
        try:
            # 1. Pede o dado para a API (sem limpar ainda)
            response = web_session.get(API_URL, timeout=15)
            api_data = response.json()

            if api_data.get('status') == "sucesso":
                d = api_data['dados']
                # Tenta processar o RA
                bot = PKScriptBot(d['ra'], d['digito'], d['uf'], d['senha'])
                sucesso = bot.resolver_tudo()
                
                # 2. Se o bot terminou, avisa a API para limpar esse RA da fila
                if sucesso:
                    web_session.get(f"{API_URL}?limpar=1")
                    print("[+] Fila limpa para o próximo.")
            else:
                # Se não tem ninguém na fila, descansa 15 segundos
                time.sleep(15)
                
        except Exception as e:
            print(f"[-] Erro: {e}")
            time.sleep(20)

if __name__ == "__main__":
    monitorar()
