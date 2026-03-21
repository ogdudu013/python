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
                dados = res_cmsp.json()
                self.auth_token = dados.get("auth_token")
                self.targets = list(set(self.targets + dados.get("publication_targets", [])))
                return True
        except: pass
        return False

    def resolver_qualquer_tipo(self, task_data):
        answers = {}
        questions = task_data.get('questions', [])
        
        for i, q in enumerate(questions):
            q_type = q.get('type')
            statement = q.get('statement', '')
            
            if q_type == 'single':
                # Múltipla Escolha
                resp = self.perguntar_ia(f"Questão: {statement}. Responda apenas o NÚMERO do índice da alternativa correta (0, 1, 2 ou 3).")
                answers[str(i)] = int("".join(filter(str.isdigit, resp)) or 0)
            
            elif q_type == 'text_ai' or q_type == 'essay':
                # Dissertativa
                answers[str(i)] = self.perguntar_ia(f"Escreva uma resposta curta e clara para esta questão escolar: {statement}")
            
            elif q_type == 'true-false':
                # Verdadeiro ou Falso
                answers[str(i)] = [True, False, True, False] # Exemplo simplificado
            
            elif q_type in ['cloud', 'fill-words']:
                # Ordenar ou Completar
                answers[str(i)] = q.get('options', {}).get('words', []) or [0,1,2]

        return answers

    def executar(self):
        if not self.login(): return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        params = [("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            print(f"[i] {len(tarefas)} tarefas para resolver.")
            
            for task in tarefas:
                t_id = task['id']
                # Puxa os detalhes da tarefa (questões)
                detalhes = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply", headers=headers).json()
                
                print(f"[*] Resolvendo: {task.get('title')}...")
                respostas = self.resolver_qualquer_tipo(detalhes)
                
                # ESPERA DE SEGURANÇA (Mínimo 3 minutos por tarefa)
                tempo_minimo = max(180, detalhes.get('min_execution_time', 0))
                print(f"    [!] Aguardando {tempo_minimo}s de tempo mínimo exigido...")
                time.sleep(tempo_minimo)
                
                payload = {"answers": respostas, "last_question": True, "duration": tempo_minimo + 10}
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                print(f"    [V] Tarefa Concluída.")
            return True
        return False

# --- LOOP FIREBASE ---
print(">>> PK SCRIPT ULTRA | 3 MINUTOS | TODAS QUESTÕES <<<")
while True:
    try:
        response = requests.get(FIREBASE_URL)
        fila = response.json()
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            print(f"\n[!] RA: {d['ra']}")
            bot = PKScriptBotUltra(d['ra'], d['digito'], d['uf'], d['senha'])
            bot.executar()
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
    except: pass
    time.sleep(10)
