import requests
import time
import sys
import json  # Adicionado para manipular os payloads e respostas

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

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
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            # Usamos json.dumps para garantir que o payload vá formatado corretamente
            res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return None

    def login(self):
        try:
            # Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json={"user": self.ra_completo, "senha": self.senha},
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            )
            if res_sed.status_code != 200: return False
            
            dados_sed = res_sed.json()
            self.nick = dados_sed.get("userName").lower()

            # Login CMSP
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token",
                json={"token": dados_sed.get("token")},
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            )
            if res_cmsp.status_code == 200:
                dados_c = res_cmsp.json()
                self.auth_token = dados_c.get("auth_token")
                self.targets.append(f"{self.nick}-{self.uf}")
                return True
        except: return False
        return False

    def resolver_com_ia(self):
        if not self.login(): return False

        headers = {
            "x-api-key": self.auth_token, 
            "x-api-realm": "edusp", 
            "x-api-platform": "webclient", 
            "Content-Type": "application/json",
            "User-Agent": self.ua
        }
        
        # Parâmetros de busca
        params = [("expired_only", "false"), ("limit", "50"), ("filter_expired", "true"), ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        if res.status_code != 200: return False

        tarefas = res.json()
        print(f"    [i] {len(tarefas)} tarefas encontradas.")

        for task in tarefas:
            t_id = task['id']
            a_id = task.get('answer_id')
            p_target = task.get("publication_target")
            
            respostas_ia = {}
            try:
                # Busca as questões da tarefa
                url_q = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}"
                questoes = self.session.get(url_q, headers=headers).json().get('questions', [])
                
                for q in questoes:
                    if q['type'] == 'single':
                        # Monta o prompt para a IA
                        opcoes_texto = "\n".join([f"{k}: {v['statement']}" for k,v in q['options'].items()])
                        prompt = f"Pergunta: {q['statement']}\nAlternativas:\n{opcoes_texto}\nResponda apenas com o número da alternativa correta."
                        
                        resp = self.perguntar_gemini(prompt)
                        id_correto = "".join(filter(str.isdigit, str(resp)))
                        
                        if id_correto in q['options']:
                            respostas_ia[str(q['id'])] = {
                                "question_id": q['id'], 
                                "question_type": "single", 
                                "answer": {k: (k == id_correto) for k in q['options']}
                            }
            except: pass

            payload = {
                "status": "submitted",
                "answers": respostas_ia,
                "accessed_on": "room",
                "executed_on": p_target,
                "duration": 185
            }

            url_envio = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
            if a_id:
                # Se for rascunho, usamos PUT e a URL com ID da resposta
                self.session.put(f"{url_envio}/{a_id}", data=json.dumps(payload), headers=headers)
            else:
                self.session.post(url_envio, data=json.dumps(payload), headers=headers)
            
            print(f"    [V] Tarefa {t_id} enviada.")
            time.sleep(2)
        return True

# --- LOOP PRINCIPAL ---
while True:
    try:
        r_fila = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = r_fila.json()
        if fila:
            for id_db, d in fila.items():
                print(f"\n[FILA] RA: {d['ra']}")
                bot = RoboSalaCompleto(d['ra'], d['digito'], d['uf'], d['senha'])
                if bot.resolver_com_ia():
                    requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                break 
    except: pass
    time.sleep(5)
