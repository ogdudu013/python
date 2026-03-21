import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBotUltra:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.targets = ["r36cbf99f7e282664c-l", "rf5f73a6b29568391d-l", "1205", "1052", "1820", "764", "1834"]

    def perguntar_ia(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            return "0"

    def login(self):
        try:
            # 1. Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            )
            if res_sed.status_code != 200: return False
            token_sed = res_sed.json().get("token")

            # 2. Login CMSP
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": token_sed}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            )
            
            if res_cmsp.status_code == 200:
                dados = res_cmsp.json()
                self.auth_token = dados.get("auth_token")
                self.targets = list(set(self.targets + dados.get("publication_targets", [])))
                return True
        except: return False
        return False

    def resolver_questoes(self, task_data):
        answers = {}
        questions = task_data.get('questions', [])
        
        for q in questions:
            q_id = str(q.get('id'))
            q_type = q.get('type')
            statement = q.get('statement', '')
            
            if q_type == 'info': continue

            if q_type == 'single':
                prompt = f"Questão: {statement}. Responda apenas o número da alternativa correta (0, 1, 2, 3 ou 4)."
                resp = self.perguntar_ia(prompt)
                idx = "".join(filter(str.isdigit, resp))
                answers[q_id] = int(idx) if idx else 0
            
            elif q_type in ['text_ai', 'essay']:
                prompt = f"Escreva uma resposta curta e escolar para: {statement}"
                answers[q_id] = self.perguntar_ia(prompt)
            
            elif q_type in ['cloud', 'fill-words', 'true-false']:
                if 'options' in q and 'words' in q['options']:
                    answers[q_id] = q['options']['words']
                else:
                    answers[q_id] = [0, 1]
        return answers

    def executar(self):
        if not self.login(): return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        params = [("limit", "100"), ("answer_statuses", "pending"), ("answer_statuses", "draft")]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            print(f"[i] {len(tarefas)} tarefas encontradas.")
            
            for task in tarefas:
                t_id = task['id']
                
                # --- PASSO CRUCIAL: PEGAR O APPLY_TOKEN ---
                try:
                    url_apply = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?preview_mode=false"
                    res_apply = self.session.get(url_apply, headers=headers)
                    detalhes = res_apply.json()
                    apply_token = detalhes.get('apply_token') 
                except: continue

                print(f"[*] Resolvendo: {task.get('title')}")
                respostas = self.resolver_questoes(detalhes)
                
                # --- TEMPO DE ESPERA (3 MINUTOS) ---
                tempo_espera = 185
                print(f"    [!] Aguardando {tempo_espera}s de segurança...")
                time.sleep(tempo_espera)
                
                # --- ENTREGA COM O TOKEN ---
                payload = {
                    "answers": respostas, 
                    "last_question": True, 
                    "duration": tempo_espera,
                    "apply_token": apply_token
                }
                
                final = self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                
                if final.status_code == 200:
                    print(f"    [V] Concluída com sucesso.")
                else:
                    print(f"    [X] Erro {final.status_code} na entrega.")
            return True
        return False

# --- LOOP FIREBASE ---
print(">>> PK SCRIPT ULTRA - ATIVADO <<<")
while True:
    try:
        response = requests.get(FIREBASE_URL, timeout=15)
        fila = response.json()
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            print(f"\n[NOVO] RA: {d['ra']}")
            bot = PKScriptBotUltra(d['ra'], d['digito'], d['uf'], d['senha'])
            bot.executar()
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
    except: pass
    time.sleep(10)
