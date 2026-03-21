import requests
import time
import sys
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Gere em: https://aistudio.google.com/

class RoboSalaMaster:
    def __init__(self, ra, digito, uf, senha):
        self.ra = ra
        self.digito = digito
        self.uf = uf.upper()
        self.senha = senha
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"
        self.auth_token = None
        self.nick_original = None

    def perguntar_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            return None

    def login(self):
        try:
            # Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua},
                timeout=15
            )
            if res_sed.status_code != 200: return False
            
            dados = res_sed.json()
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

    def resolver_e_entregar(self):
        if not self.login(): 
            print(f"    [!] Erro de Login no RA {self.ra}")
            return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        nick_target = f"{self.nick_original}-{self.uf.lower()}"

        # Buscar tarefas
        res_todo = self.session.get(f"https://edusp-api.ip.tv/tms/task/todo?limit=30&publication_target={nick_target}", headers=headers)
        if res_todo.status_code != 200: return False
        
        tarefas = res_todo.json()
        print(f"    [i] {len(tarefas)} tarefas pendentes.")

        for task in tarefas:
            t_id = task['id']
            a_id = task.get('answer_id')
            p_target = task.get("publication_target")
            print(f"    [*] Resolvendo: {task.get('title')[:30]}...")

            # 1. Pegar conteúdo da tarefa
            res_q = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={nick_target}", headers=headers)
            respostas_ia = {}
            
            if res_q.status_code == 200:
                dados_q = res_q.json()
                for q in dados_q.get('questions', []):
                    q_id = str(q['id'])
                    if q['type'] == 'single':
                        opts = "\n".join([f"{k}: {v['statement']}" for k,v in q['options'].items()])
                        prompt = f"Questão: {q['statement']}\nOpções:\n{opts}\nResponda apenas o número da opção correta."
                        resp = self.perguntar_gemini(prompt)
                        # Tenta extrair o número da resposta
                        escolha = "".join(filter(str.isdigit, str(resp)))
                        if escolha in q['options']:
                            respostas_ia[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {k: (k == escolha) for k in q['options']}}

            # 2. Enviar (Simulando 3 minutos de aula para segurança)
            time.sleep(5) # Delay pequeno para o log não voar, o 'duration' no JSON engana o server
            
            payload = {
                "status": "submitted",
                "answers": respostas_ia,
                "accessed_on": "room",
                "executed_on": p_target,
                "duration": 185.5
            }

            if a_id: # Se rascunho, PUT. Se nova, POST.
                r = self.session.put(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer/{a_id}", json=payload, headers=headers)
            else:
                r = self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
            
            print(f"    [OK] Enviada. Status: {r.status_code}")

        return True

# --- LOOP PRINCIPAL ---
print(">>> PK SCRIPTS V3 ATIVADO <<<")
while True:
    try:
        r = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = r.json()
        
        if fila:
            for id_db, dados in fila.items():
                print(f"\n[FILA] Processando RA: {dados['ra']}")
                bot = RoboSalaMaster(dados['ra'], dados['digito'], dados['uf'], dados['senha'])
                
                # Só apaga do Firebase se a função retornar True (sucesso)
                if bot.resolver_e_entregar():
                    requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                    print(f"[LIMPEZA] RA {dados['ra']} removido.")
                else:
                    print(f"[AVISO] Pulando RA {dados['ra']} por erro.")
                
                time.sleep(2)
                break # Pega o próximo da fila no próximo loop
    except Exception as e:
        print(f"Erro: {e}")
    time.sleep(5)
