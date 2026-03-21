import requests
import time
import sys

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class RoboSalaEstavelIA:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.uf = uf.lower()
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        self.nick = None
        # Seus targets de confiança do log
        self.targets = ["r36cbf99f7e282664c-l", "rf5f73a6b29568391d-l", "1205", "1052", "1820", "764", "1834"]
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def perguntar_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return None

    def login(self):
        # 1. Login SED
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        try:
            res = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h_sed, timeout=15)
            if res.status_code != 200: return False
            
            dados_sed = res.json()
            self.token_sed = dados_sed.get("token")
            self.nick = dados_sed.get("userName").lower()

            # 2. Login CMSP
            url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
            h_cmsp = {"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            res_c = self.session.post(url_cmsp, json={"token": self.token_sed}, headers=h_cmsp, timeout=15)
            
            if res_c.status_code == 200:
                dados_c = res_c.json()
                self.auth_token_cmsp = dados_c.get("auth_token")
                # Adiciona nick e targets dinâmicos
                self.targets.append(f"{self.nick}-{self.uf}")
                if dados_c.get("publication_targets"):
                    self.targets = list(set(self.targets + dados_c.get("publication_targets")))
                return True
        except: return False
        return False

    def resolver(self):
        if not self.login(): 
            print(f"    [!] Falha de login para {self.ra_completo}")
            return False

        headers = {"x-api-key": self.auth_token_cmsp, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        
        # Listagem baseada na sua versão estável
        params = [("expired_only", "false"), ("limit", "50"), ("filter_expired", "true"), ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
            if res.status_code != 200: return False
            
            tarefas = res.json()
            print(f"    [i] {len(tarefas)} tarefas encontradas.")

            for task in tarefas:
                t_id = task['id']
                a_id = task.get('answer_id')
                print(f"    [*] Processando: {task.get('title')}")

                # Tenta buscar as questões para o Gemini (Opcional, se falhar envia vazio como sua estável)
                respostas_ia = {}
                try:
                    url_q = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={task.get('publication_target')}"
                    q_data = self.session.get(url_q, headers=headers).json()
                    for q in q_data.get('questions', []):
                        if q['type'] == 'single':
                            opts = "\n".join([f"{k}: {v['statement']}" for k,v in q['options'].items()])
                            prompt = f"Questão: {q['statement']}\nOpções:\n{opts}\nResponda APENAS o ID numérico da correta."
                            escolha = "".join(filter(str.isdigit, str(self.perguntar_gemini(prompt))))
                            if escolha in q['options']:
                                respostas_ia[str(q['id'])] = {"question_id": q['id'], "question_type": "single", "answer": {k: (k == escolha) for k in q['options']}}
                except: pass # Se der erro na IA, o payload vai vazio (garante nota de participação)

                payload = {
                    "status": "submitted",
                    "answers": respostas_ia,
                    "accessed_on": "room",
                    "executed_on": task.get("publication_target"),
                    "duration": 185
                }

                # Lógica PUT/POST automática
                url_fin = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                if a_id:
                    resp = self.session.put(f"{url_fin}/{a_id}", json=payload, headers=headers)
                else:
                    resp = self.session.post(url_fin, json=payload, headers=headers)
                
                print(f"    [V] Enviada: {resp.status_code}")
                time.sleep(2)
            return True
        except: return False

# --- LOOP FIREBASE ---
while True:
    try:
        r = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = r.json()
        if fila:
            for id_db, d in fila.items():
                print(f"\n[FILA] Processando RA: {d['ra']}")
                bot = RoboSalaEstavelIA(d['ra'], d['digito'], d['uf'], d['senha'])
                # Só deleta se o processo terminar sem crash
                if bot.resolver():
                    requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                    print(f"[LIMPEZA] RA {d['ra']} removido.")
                break # Processa um por um para evitar ban de IP
    except: pass
    time.sleep(5)
