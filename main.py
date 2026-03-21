import requests
import time

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBotFocado:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def perguntar_ia(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return "0"

    def login(self):
        try:
            # Login SED
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua})
            
            if res_sed.status_code != 200: return False
            token_sed = res_sed.json().get("token")

            # Login CMSP
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": token_sed}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua})
            
            if res_cmsp.status_code == 200:
                self.auth_token = res_cmsp.json().get("auth_token")
                return True
        except: pass
        return False

    def executar(self):
        if not self.login(): return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        
        # --- O PULO DO GATO: FILTROS QUE O SITE USA ---
        # Removi os targets genéricos e adicionei filtros de data e status 'pending' estrito
        params = {
            "limit": "20",
            "offset": "0",
            "filter_expired": "true", # IGNORE O QUE JÁ VENCEU (As 16 extras)
            "expired_only": "false",
            "answer_statuses": "pending",
            "is_exam": "false",
            "is_essay": "false"
        }

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            # Filtro manual para garantir que só pegamos tarefas que expiram no futuro
            tarefas_reais = [t for t in tarefas if t.get('task_expired') is False]
            
            print(f"[i] {len(tarefas_reais)} tarefas pendentes encontradas (Filtradas).")
            
            for task in tarefas_reais:
                t_id = task['id']
                print(f"[*] Resolvendo: {task.get('title')}")
                
                # Apply para pegar questões e token
                res_apply = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?preview_mode=false", headers=headers).json()
                apply_token = res_apply.get('apply_token')
                
                # Lógica simplificada de resposta
                answers = {}
                for q in res_apply.get('questions', []):
                    q_id = str(q['id'])
                    if q['type'] == 'single':
                        resp = self.perguntar_ia(f"Questão: {q.get('statement')}. Responda o índice (0-4).")
                        answers[q_id] = int("".join(filter(str.isdigit, resp)) or 0)
                    else:
                        answers[q_id] = "Resposta automática"

                # ESPERA DE 3 MINUTOS
                print(f"    [!] Aguardando 185s...")
                time.sleep(185)
                
                # Entrega
                payload = {"answers": answers, "last_question": True, "duration": 185, "apply_token": apply_token, "iteration": 1}
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                print(f"    [V] Concluída.")
            return True

# --- LOOP FIREBASE ---
while True:
    try:
        response = requests.get(FIREBASE_URL)
        fila = response.json()
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            bot = PKScriptBotFocado(d['ra'], d['digito'], d['uf'], d['senha'])
            bot.executar()
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
    except: pass
    time.sleep(10)
