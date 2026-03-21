import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV15:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_limpo = str(ra).upper().replace("SP", "").strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        self.ra_completo = f"{(self.ra_limpo + self.digito).zfill(12)}{self.uf}"
        self.senha = str(senha).strip()
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.auth_token = None
        self.targets = ["1205", "1052", "1820", "1834"]

    def log_status(self, msg):
        print(f"[{self.ra_limpo}] {msg}")
        try: requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": msg})
        except: pass

    def consultar_gemini(self, pergunta, tipo, opcoes=None):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"Responda apenas o TEXTO da alternativa correta (sem letra A, B, C): {pergunta}. Opções: {opcoes}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return ""

    def iniciar_fluxo(self):
        self.log_status("Autenticando...")
        headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        
        try:
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                                        json={"user": self.ra_completo, "senha": self.senha}, headers=headers_sed)
            
            if res_sed.status_code != 200:
                self.log_status("Erro: Login SED Negado")
                return

            dados_sed = res_sed.json()
            token_sed = dados_sed.get('token')
            nome = dados_sed.get('DadosUsuario', {}).get('NM_USUARIO', 'Aluno')
            print(f"\n[V] ACESSO CONFIRMADO: {nome}")

            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                                         json={"token": token_sed}, headers={"x-api-realm": "edusp", "User-Agent": self.ua})
            
            data_cmsp = res_cmsp.json()
            if isinstance(data_cmsp, list): data_cmsp = data_cmsp[0]

            self.auth_token = data_cmsp.get('auth_token')
            self.targets = list(set(self.targets + data_cmsp.get('publication_targets', [])))
            self.targets.append(data_cmsp.get('nick'))
            self.targets = [t for t in self.targets if t]

            self.resolver_tarefas()
        except Exception as e:
            self.log_status(f"Erro no Fluxo: {str(e)}")

    def resolver_tarefas(self):
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            tarefas = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers).json()
            if not tarefas or not isinstance(tarefas, list):
                self.log_status("Sem tarefas.")
                return

            for task in tarefas:
                t_id = task['id']
                p_target = task.get('publication_target')
                print(f"    [*] Resolvendo: {task.get('title')}")
                
                # Entrar na tarefa
                q_res = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}", headers=headers).json()
                
                # CORREÇÃO DO ERRO 'STRING INDICES': Verifica se 'questions' existe e é lista
                questions = q_res.get('questions')
                if not isinstance(questions, list):
                    continue

                respostas = {}
                for q in questions:
                    q_id = str(q['id'])
                    tipo = q.get('type')
                    prompt_resp = self.consultar_gemini(q.get('statement'), tipo, q.get('options'))
                    
                    if tipo == 'single':
                        # Lógica inteligente: tenta encontrar qual ID de opção bate com a resposta do Gemini
                        id_opcao = "0"
                        for opt in q.get('options', []):
                            if prompt_resp.lower() in str(opt.get('text')).lower():
                                id_opcao = str(opt.get('id'))
                                break
                        respostas[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {id_opcao: True}}
                    else:
                        respostas[q_id] = {"question_id": int(q_id), "question_type": tipo, "answer": {"0": prompt_resp}}

                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", 
                                 json={"status": "submitted", "answers": respostas, "duration": 130, "executed_on": p_target}, 
                                 headers=headers)
                time.sleep(2)

            self.log_status("Concluído!")
        except Exception as e:
            self.log_status(f"Erro: {str(e)}")

if __name__ == "__main__":
    print(">>> PK MOTOR V15 - ESTÁVEL <<<")
    while True:
        try:
            fila = requests.get(f"{FIREBASE_URL}.json").json()
            if fila:
                for id_db, dados in fila.items():
                    if "Concluído" not in dados.get('status', ''):
                        PKMotorV15(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).iniciar_fluxo()
            time.sleep(10)
        except: time.sleep(15)
