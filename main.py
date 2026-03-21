import requests
import time
import sys
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Coloca aqui a tua chave da Google AI Studio

class RoboSalaInteligente:
    def __init__(self, ra, digito, uf, senha):
        self.ra = ra
        self.digito = digito
        self.uf = uf.upper()
        self.senha = senha
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.nick_original = None
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"

    def perguntar_gemini(self, prompt):
        """Envia a questão para a API do Gemini e retorna o texto"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, json=payload, timeout=15)
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            return None

    def login(self):
        try:
            # Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            )
            if res_sed.status_code != 200: return False
            
            dados = res_sed.json()
            self.user_id = dados.get("codigoUsuario")
            self.nick_original = dados.get("userName").lower()
            
            # Login CMSP
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": dados.get("token")}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            )
            if res_cmsp.status_code == 200:
                self.auth_token = res_cmsp.json().get("auth_token")
                return True
        except: return False
        return False

    def resolver_questoes(self, t_id, nick_target):
        """Busca o conteúdo da tarefa e usa IA para responder"""
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        
        # Abre a tarefa para ver as perguntas (baseado no seu log GET /apply)
        res = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={nick_target}", headers=headers)
        if res.status_code != 200: return {}

        tarefa_data = res.json()
        respostas_finais = {}

        for q in tarefa_data.get('questions', []):
            if q['type'] == 'info': continue # Pula slides de texto
            
            q_id = str(q['id'])
            enunciado = q.get('statement', '')
            
            # Lógica para Múltipla Escolha (Single)
            if q['type'] == 'single':
                opcoes = ""
                for k, v in q['options'].items():
                    opcoes += f"ID {k}: {v['statement']}\n"
                
                prompt = f"Questão: {enunciado}\nOpções:\n{opcoes}\nResponda APENAS o número do ID da alternativa correta."
                resp_ia = self.perguntar_gemini(prompt)
                
                # Monta o formato do log: {"0": false, "1": true...}
                id_correto = "".join(filter(str.isdigit, str(resp_ia)))
                if id_correto in q['options']:
                    respostas_finais[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {k: (k == id_correto) for k in q['options']}}

            # Lógica para Dissertativa (Text AI)
            elif q['type'] == 'text_ai':
                prompt = f"Responda de forma breve a seguinte questão escolar: {enunciado}"
                resp_ia = self.perguntar_gemini(prompt)
                respostas_finais[q_id] = {"question_id": int(q_id), "question_type": "text_ai", "answer": {"0": resp_ia}}

        return respostas_finais

    def executar(self):
        if not self.login(): return False
        
        nick_target = f"{self.nick_original}-{self.uf.lower()}"
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}

        # Busca tarefas pendentes
        res = self.session.get(f"https://edusp-api.ip.tv/tms/task/todo?limit=50&publication_target={nick_target}", headers=headers)
        
        if res.status_code == 200:
            for task in res.json():
                t_id = task['id']
                a_id = task.get('answer_id')
                print(f"    [*] A IA está a resolver: {task.get('title')}")

                # Chame o Gemini para gerar as respostas
                respostas = self.resolver_questoes(t_id, nick_target)

                payload = {
                    "status": "submitted",
                    "answers": respostas,
                    "accessed_on": "room",
                    "executed_on": task.get("publication_target"),
                    "duration": 185.0
                }

                # Delay de segurança
                time.sleep(5) 

                if a_id:
                    u = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer/{a_id}"
                    resp = self.session.put(u, json=payload, headers=headers)
                else:
                    u = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                    resp = self.session.post(u, json=payload, headers=headers)

                print(f"    [OK] Status: {resp.status_code}")
            return True
        return False

# --- LOOP FIREBASE ---
while True:
    try:
        r = requests.get(f"{FIREBASE_URL}.json")
        fila = r.json()
        if fila:
            for id_db, d in fila.items():
                print(f"\n[FILA] RA: {d['ra']}")
                bot = RoboSalaInteligente(d['ra'], d['digito'], d['uf'], d['senha'])
                if bot.executar():
                    requests.delete(f"{FIREBASE_URL}/{id_db}.json")
    except: pass
    time.sleep(5)
