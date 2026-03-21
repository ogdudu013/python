import requests
import time
import sys

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Obtenha em aistudio.google.com

class RoboSalaCompleto:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.uf = uf.lower()
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.auth_token = None
        self.nick = None
        self.targets = ["r36cbf99f7e282664c-l", "rf5f73a6b29568391d-l", "1205", "1052", "1820", "764", "1834"]

    def perguntar_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return None

    def login(self):
        try:
            # 1. Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json={"user": self.ra_completo, "senha": self.senha},
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            )
            if res_sed.status_code != 200: return False
            
            dados_sed = res_sed.json()
            self.nick = dados_sed.get("userName").lower()

            # 2. Login CMSP
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token",
                json={"token": dados_sed.get("token")},
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            )
            if res_cmsp.status_code == 200:
                dados_c = res_cmsp.json()
                self.auth_token = dados_c.get("auth_token")
                self.targets.append(f"{self.nick}-{self.uf}")
                if dados_c.get("publication_targets"):
                    self.targets = list(set(self.targets + dados_c.get("publication_targets")))
                return True
        except: return False
        return False

    def resolver_com_ia(self):
        if not self.login(): return False

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        params = [("expired_only", "false"), ("limit", "50"), ("filter_expired", "true"), ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        if res.status_code != 200: return False

        tarefas = res.json()
        print(f"    [i] {len(tarefas)} tarefas encontradas para {self.nick}.")

        for task in tarefas:
            t_id = task['id']
            a_id = task.get('answer_id')
            p_target = task.get("publication_target")
            
            # 1. Buscar perguntas para o Gemini
            respostas_ia = {}
            try:
                url_q = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}"
                questoes = self.session.get(url_q, headers=headers).json().get('questions', [])
                for q in questoes:
                    if q['type'] == 'single':
                        opts = "\n".join([f"{k}: {v['statement']}" for k,v in q['options'].items()])
                        prompt = f"Questão: {q['statement']}\nOpções:\n{opts}\nResponda APENAS o número do ID da alternativa correta."
                        resp_gemini = "".join(filter(str.isdigit, str(self.perguntar_gemini(prompt))))
                        if resp_gemini in q['options']:
                            respostas_ia[str(q['id'])] = {"question_id": q['id'], "question_type": "single", "answer": {k: (k == resp_gemini) for k in q['options']}}
            except: pass

            # 2. Enviar Resposta
            payload = {"status": "submitted", "answers": respostas_ia, "accessed_on": "room", "executed_on": p_target, "duration": 185}
            url_base = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
            
            if a_id:
                self.session.put(f"{url_base}/{a_id}", json=payload, headers=headers)
            else:
                self.session.post(url_base, json=payload, headers=headers)
            
            print(f"    [V] Tarefa {t_id} finalizada.")
            time.sleep(2)
        return True

# --- LOOP AUTOMÁTICO DO FIREBASE ---
print(">>> SISTEMA INICIADO: AGUARDANDO FILA <<<")
while True:
    try:
        r_fila = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = r_fila.json()
        
        if fila:
            for id_db, dados in fila.items():
                ra, dig, uf, pw = dados.get('ra'), dados.get('digito'), dados.get('uf'), dados.get('senha')
                print(f"\n[FILA] Processando RA: {ra}")
                
                bot = RoboSalaCompleto(ra, dig, uf, pw)
                if bot.resolver_com_ia():
                    requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                    print(f"[LIMPEZA] RA {ra} removido da fila.")
                else:
                    print(f"[ERRO] Falha no RA {ra}. Pulando...")
                
                time.sleep(3)
                break # Processa um por um
    except Exception as e:
        print(f"Erro de conexão: {e}")
    time.sleep(5)
