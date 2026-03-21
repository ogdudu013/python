import requests
import time
import json

# === CONFIGURAÇÕES OFICIAIS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        # Baseado no seu arquivo funcional
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        # Targets baseados no seu código base
        self.targets = ["r36cbf99f7e282664c-l", "rf5f73a6b29568391d-l", "1205", "1052", "1820", "764", "1834"]

    def resolver_ia(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": f"Responda apenas o número da alternativa (0 a 3): {pergunta}"}]}]}, timeout=10)
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return int("".join(filter(str.isdigit, resp_text))[0])
        except: return 0

    def login(self):
        try:
            # 1. Login SED (Igual ao seu arquivo funcional)
            url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
            headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            r1 = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=headers_sed)
            
            if r1.status_code == 200:
                self.token_sed = r1.json().get("token")
                print("[V] Login SED realizado.")
            else:
                print(f"[X] Erro SED: {r1.status_code}")
                return False

            # 2. Login CMSP (Corrigido com headers do seu arquivo base)
            url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
            headers_cmsp = {
                "Content-Type": "application/json", 
                "x-api-realm": "edusp", 
                "x-api-platform": "webclient", # Parâmetro vital do seu arquivo funcional
                "User-Agent": self.ua
            }
            r2 = self.session.post(url_cmsp, json={"token": self.token_sed}, headers=headers_cmsp)
            
            if r2.status_code == 200:
                dados = r2.json()
                self.auth_token_cmsp = dados.get("auth_token")
                # Atualiza targets dinâmicos como no seu código base
                novos_targets = dados.get("publication_targets", [])
                self.targets = list(set(self.targets + novos_targets))
                print(f"[V] Token CMSP obtido! ({len(self.targets)} targets)")
                return True
            else:
                print(f"[X] Erro CMSP: {r2.status_code}") # Se der 400 aqui, cheque o token_sed
                return False
        except Exception as e:
            print(f"[!] Erro: {e}")
            return False

    def executar(self):
        if not self.login(): return False
            
        # Headers para listagem e resposta baseados no seu código base
        headers = {
            "x-api-key": self.auth_token_cmsp, 
            "x-api-realm": "edusp", 
            "x-api-platform": "webclient",
            "User-Agent": self.ua
        }
        
        # Parâmetros de busca idênticos ao seu arquivo funcional
        params = [
            ("expired_only", "false"), ("limit", "100"), ("filter_expired", "true"),
            ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")
        ]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            print(f"[i] {len(tarefas)} tarefas encontradas.")
            for t in tarefas:
                t_id = t['id']
                # IA resolve a questão antes de enviar
                idx = self.resolver_ia(t.get('title', ''))
                
                payload_ans = {"answers": {"0": idx}, "last_question": True, "duration": 120}
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload_ans, headers=headers)
                print(f"    [OK] Resolvida: {t.get('title', 'Sem Título')[:20]}")
                time.sleep(2)
            return True
        return False

# --- MONITORAMENTO FIREBASE ---
print(">>> PK SCRIPT OFC | MODO FIREBASE + BASE FUNCIONAL <<<")
while True:
    try:
        response = requests.get(FIREBASE_URL, timeout=15)
        fila = response.json()
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            print(f"\n[!] Processando: {d['ra']}")
            
            bot = PKScriptBot(d['ra'], d['digito'], d['uf'], d['senha'])
            bot.executar()
            
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
            print("[+] Removido da fila.")
    except Exception as e: print(f"Erro: {e}")
    time.sleep(10)
