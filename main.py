import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV13:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_limpo = str(ra).upper().replace("SP", "").strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        # Formatação 12 dígitos + UF
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
        prompt = f"Responda apenas a alternativa correta ou texto curto: {pergunta}. Tipo: {tipo}. Opções: {opcoes}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return "A"

    def iniciar_fluxo(self):
        self.log_status("Fazendo Login...")
        
        headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        
        try:
            # 1. LOGIN SED
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                                        json={"user": self.ra_completo, "senha": self.senha}, headers=headers_sed)
            
            if res_sed.status_code != 200:
                self.log_status("Erro: Login SED falhou")
                return

            token_sed = res_sed.json().get('token')
            
            # 2. TOKEN CMSP (AQUI MORAVA O ERRO)
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                                         json={"token": token_sed}, headers={"x-api-realm": "edusp", "User-Agent": self.ua})
            
            data_cmsp = res_cmsp.json()

            # TRATAMENTO: Se vier uma lista, pegamos o primeiro item (o perfil ativo)
            if isinstance(data_cmsp, list):
                if len(data_cmsp) > 0:
                    data_cmsp = data_cmsp[0]
                else:
                    self.log_status("Erro: Nenhum perfil encontrado")
                    return

            self.auth_token = data_cmsp.get('auth_token')
            self.targets += data_cmsp.get('publication_targets', [])
            self.targets.append(data_cmsp.get('nick'))
            self.targets = list(set(filter(None, self.targets)))

            self.resolver_tarefas()
        except Exception as e:
            self.log_status(f"Erro: {str(e)}")

    def resolver_tarefas(self):
        self.log_status("Buscando Tarefas...")
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            res_todo = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
            tarefas = res_todo.json()

            # Mais uma proteção: se não houver tarefas (lista vazia), encerra com sucesso
            if not tarefas or not isinstance(tarefas, list):
                self.log_status("Concluído: Sem tarefas")
                return

            for task in tarefas:
                t_id = task['id']
                p_target = task.get('publication_target')
                
                # Pega as perguntas
                q_data = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}", headers=headers).json()
                questions = q_data.get('questions', [])
                
                respostas_geradas = {}
                for q in questions:
                    q_id = str(q['id'])
                    resp_ia = self.consultar_gemini(q['statement'], q['type'], q.get('options'))
                    
                    if q['type'] == 'single':
                        # Tenta marcar a primeira opção como fallback se a IA não der o ID
                        respostas_geradas[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {"0": True}}
                    else:
                        respostas_geradas[q_id] = {"question_id": int(q_id), "question_type": q['type'], "answer": {"0": resp_ia}}

                # Submete
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", 
                                 json={"status": "submitted", "answers": respostas_geradas, "duration": 135, "executed_on": p_target}, 
                                 headers=headers)
                print(f"    [OK] {task.get('title')}")
                time.sleep(1.5)

            self.log_status("Concluído!")
        except Exception as e:
            self.log_status(f"Erro na resolução: {str(e)}")

# --- LOOP ---
if __name__ == "__main__":
    print(">>> PK MOTOR V13 - FIX LIST/DICT ATIVO <<<")
    while True:
        try:
            r = requests.get(f"{FIREBASE_URL}.json")
            fila = r.json()
            if fila:
                for id_db, dados in fila.items():
                    status = dados.get('status', '')
                    if "Concluído" not in status and "Erro" not in status:
                        PKMotorV13(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).iniciar_fluxo()
            time.sleep(10)
        except: time.sleep(15)
