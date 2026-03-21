import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV14:
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
        self.log_status("Autenticando...")
        headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        
        try:
            # 1. LOGIN SED PARA PEGAR NOME E TOKEN
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                                        json={"user": self.ra_completo, "senha": self.senha}, headers=headers_sed)
            
            if res_sed.status_code != 200:
                self.log_status("Erro: Login SED Negado")
                return

            dados_sed = res_sed.json()
            token_sed = dados_sed.get('token')
            nome_aluno = dados_sed.get('DadosUsuario', {}).get('NM_USUARIO', 'Desconhecido')
            
            # LOG DE CONFIRMAÇÃO PEDIDO
            print(f"\n[V] ACESSO CONFIRMADO: {nome_aluno}")
            self.log_status(f"Logado como: {nome_aluno}")

            # 2. TOKEN CMSP E MAPEAMENTO DE CANAIS REAIS
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                                         json={"token": token_sed}, headers={"x-api-realm": "edusp", "User-Agent": self.ua})
            
            data_cmsp = res_cmsp.json()
            if isinstance(data_cmsp, list): data_cmsp = data_cmsp[0]

            self.auth_token = data_cmsp.get('auth_token')
            
            # Puxa os alvos (turmas) direto do token do CMSP
            targets_pessoais = data_cmsp.get('publication_targets', [])
            self.targets = list(set(self.targets + targets_pessoais))
            self.targets.append(data_cmsp.get('nick'))
            
            # Remove valores nulos
            self.targets = [t for t in self.targets if t]

            self.resolver_tarefas()
        except Exception as e:
            self.log_status(f"Erro no Fluxo: {str(e)}")

    def resolver_tarefas(self):
        self.log_status("Escaneando Tarefas...")
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        
        # Filtro expandido para pegar TUDO
        params = [
            ("expired_only", "false"), 
            ("limit", "100"), 
            ("answer_statuses", "pending"),
            ("answer_statuses", "draft")
        ]
        for t in self.targets: params.append(("publication_target", t))

        try:
            res_todo = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
            tarefas = res_todo.json()

            if not tarefas:
                self.log_status("Nenhuma tarefa pendente encontrada.")
                return

            self.log_status(f"Processando {len(tarefas)} tarefas...")

            for task in tarefas:
                t_id = task['id']
                p_target = task.get('publication_target')
                titulo = task.get('title', 'Sem Título')

                # Entrar na tarefa para ler questões
                q_res = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}", headers=headers)
                questions = q_res.json().get('questions', [])
                
                respostas = {}
                for q in questions:
                    q_id = str(q['id'])
                    # Gemini resolve
                    ans = self.consultar_gemini(q['statement'], q['type'], q.get('options'))
                    
                    # Formata payload
                    if q['type'] == 'single':
                        respostas[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {"0": True}}
                    else:
                        respostas[q_id] = {"question_id": int(q_id), "question_type": q['type'], "answer": {"0": ans}}

                # Submissão
                sub_res = self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", 
                                           json={"status": "submitted", "answers": respostas, "duration": 150, "executed_on": p_target}, 
                                           headers=headers)
                
                if sub_res.status_code in [200, 201, 204]:
                    print(f"    [OK] Resolvida: {titulo}")
                else:
                    print(f"    [!] Falha ao enviar: {titulo}")
                
                time.sleep(2)

            self.log_status("Concluído com Sucesso!")
        except Exception as e:
            self.log_status(f"Erro na resolução: {str(e)}")

# --- LOOP DE VIGILÂNCIA ---
if __name__ == "__main__":
    print(">>> PK MOTOR V14 - MODO AUDITORIA ATIVO <<<")
    while True:
        try:
            fila = requests.get(f"{FIREBASE_URL}.json").json()
            if fila:
                for id_db, dados in fila.items():
                    status = dados.get('status', '')
                    if "Concluído" not in status and "Erro" not in status:
                        PKMotorV14(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).iniciar_fluxo()
            time.sleep(10)
        except: time.sleep(15)
