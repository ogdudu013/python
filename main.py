import requests
import time
import json

# === CONFIGURAÇÕES OFICIAIS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36"

    def resolver_ia(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": f"Responda apenas o número do índice da alternativa correta (0, 1, 2...): {pergunta}"}]}], "generationConfig": {"temperature": 0.1}}, timeout=10)
            resp = res.json()['candidates'][0]['content']['parts'][0]['text']
            return int("".join(filter(str.isdigit, resp))[0])
        except: return 0

    def login(self):
        try:
            # Login SED
            u1 = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
            r1 = self.session.post(u1, json={"user": self.ra_completo, "senha": self.senha}, headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"})
            if r1.status_code != 200: return False
            
            # Login CMSP
            t_sed = r1.json().get("token")
            u2 = "https://edusp-api.ip.tv/registration/edusp/token"
            r2 = self.session.post(u2, json={"token": t_sed}, headers={"x-api-realm": "edusp"})
            if r2.status_code == 200:
                self.auth_token = r2.json().get("auth_token")
                return True
        except: pass
        return False

    def executar(self):
        print(f"[*] Iniciando: {self.ra_completo}")
        if not self.login(): 
            print("[!] Erro de login.")
            return False
            
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=15", headers=headers)
        
        if res.status_code == 200:
            for t in res.json():
                idx = self.resolver_ia(t.get('title', ''))
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t['id']}/answer", json={"answers": {"0": idx}, "last_question": True, "duration": 80}, headers=headers)
                print(f"    [V] {t.get('title')[:20]}... (IA: {idx})")
                time.sleep(1.5)
            return True
        return False

# --- MONITORAMENTO ---
print(">>> PK SCRIPT OFC | AGUARDANDO FILA FIREBASE <<<")
while True:
    try:
        response = requests.get(FIREBASE_URL)
        fila = response.json()
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            print(f"\n[!] Processando RA: {d['ra']}")
            
            bot = PKScriptBot(d['ra'], d['digito'], d['uf'], d['senha'])
            bot.executar()
            
            # Remove da fila
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
            print("[+] Removido da fila com sucesso.")
    except Exception as e:
        print(f"Erro: {e}")
    time.sleep(10)
