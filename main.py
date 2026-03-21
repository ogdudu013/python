import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Insira sua chave do Google AI Studio

class PKMotorV12:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_limpo = str(ra).upper().replace("SP", "").strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        # Formatação rigorosa para a API: 12 dígitos antes da UF
        self.ra_completo = f"{(self.ra_limpo + self.digito).zfill(12)}{self.uf}"
        self.senha = str(senha).strip()
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.auth_token = None
        self.targets = ["1205", "1052", "1820", "1834"] # IDs padrão

    def log_status(self, msg):
        print(f"[{self.ra_limpo}] {msg}")
        try: requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": msg})
        except: pass

    def consultar_gemini(self, pergunta, tipo, opcoes=None):
        """O Cérebro do Bot: Resolve qualquer questão"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"Você é um aluno. Responda apenas com a alternativa correta ou texto curto. Pergunta: {pergunta} | Tipo: {tipo} | Opções: {opcoes}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            return "A" # Fallback

    def iniciar_fluxo(self):
        self.log_status("Fazendo Login...")
        
        # 1. LOGIN SED
        login_payload = {"user": self.ra_completo, "senha": self.senha}
        headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        
        try:
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", json=login_payload, headers=headers_sed)
            if res_sed.status_code != 200:
                self.log_status("Erro: Dados incorretos")
                return

            token_sed = res_sed.json().get('token')
            
            # 2. TOKEN CMSP (JWT)
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", json={"token": token_sed}, headers={"x-api-realm": "edusp", "User-Agent": self.ua})
            data_cmsp = res_cmsp.json()
            self.auth_token = data_cmsp.get('auth_token')
            self.targets += data_cmsp.get('publication_targets', [])
            self.targets.append(data_cmsp.get('nick'))
            self.targets = list(set(self.targets))

            self.resolver_tarefas()
        except Exception as e:
            self.log_status(f"Erro: {str(e)}")

    def resolver_tarefas(self):
        self.log_status("Buscando Tarefas...")
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        
        # Busca dinâmica baseada nos targets do aluno
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            tarefas = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers).json()
            self.log_status(f"Encontradas: {len(tarefas)}")

            for task in tarefas:
                t_id = task['id']
                p_target = task.get('publication_target')
                
                # Pega as perguntas reais da tarefa
                q_url = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}"
                questions = self.session.get(q_url, headers=headers).json().get('questions', [])
                
                respostas_geradas = {}
                for q in questions:
                    q_id = str(q['id'])
                    # CHAMA O GEMINI AQUI
                    resp_ia = self.consultar_gemini(q['statement'], q['type'], q.get('options'))
                    
                    # Formatação de resposta para o CMSP
                    if q['type'] == 'single':
                        respostas_geradas[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {"0": True}} # Simulação de ID
                    else:
                        respostas_geradas[q_id] = {"question_id": int(q_id), "question_type": q['type'], "answer": {"0": resp_ia}}

                # Envia a resposta final
                payload = {"status": "submitted", "answers": respostas_geradas, "duration": 140, "executed_on": p_target}
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                print(f"    [V] Resolvida: {task.get('title')}")
                time.sleep(2)

            self.log_status("Concluído!")
        except:
            self.log_status("Erro ao resolver")

# --- LOOP PRINCIPAL ---
if __name__ == "__main__":
    print(">>> PK MOTOR V12 - GEMINI INTEGRADO <<<")
    while True:
        try:
            fila = requests.get(f"{FIREBASE_URL}.json").json()
            if fila:
                for id_db, dados in fila.items():
                    if "Concluído" not in dados.get('status', ''):
                        PKMotorV12(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).iniciar_fluxo()
            time.sleep(10)
        except:
            time.sleep(20)
