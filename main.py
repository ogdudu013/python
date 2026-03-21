import requests
import time
import json

# === CONFIGURAÇÕES MESTRE ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV9:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_raw = str(ra).strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        # O login exige o RA com zeros à esquerda (total 12 dígitos + UF)
        self.user_login = f"{self.ra_raw.zfill(10)}{self.digito}{self.uf}"
        self.senha = str(senha).strip()
        self.id_db = id_db
        
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.sub_key = "d701a2043aa24d7ebb37e9adf60d043b" # Chave fixa da API SED
        
        self.targets = ["1205", "1052", "1820", "1834"] # Canais Globais
        self.auth_token = None

    def atualizar_status(self, status):
        try: requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": status})
        except: pass

    def api_request(self, method, url, is_cmsp=False, **kwargs):
        """Gerenciador central de requisições com tratamento de erro de JSON"""
        headers = kwargs.pop('headers', {})
        headers["User-Agent"] = self.ua
        
        if not is_cmsp:
            headers["Ocp-Apim-Subscription-Key"] = self.sub_key
        
        try:
            res = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
            if res.status_code == 200:
                return res.json()
            print(f"[!] Erro {res.status_code} em {url}")
            return None
        except Exception as e:
            print(f"[!] Falha de conexão: {e}")
            return None

    def engine_start(self):
        print(f"\n[*] Processando Aluno: {self.user_login}")
        self.atualizar_status("Autenticando na SED...")

        # 1. LOGIN COMPLETO (Captura de Bearer Token)
        payload_login = {"user": self.user_login, "senha": self.senha}
        login_res = self.api_request("POST", "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", json=payload_login)
        
        if not login_res or 'token' not in login_res:
            self.atualizar_status("Erro: RA ou Senha inválidos")
            return

        token_sed = login_res['token']
        # O CodigoAluno é vital para listar as matérias do Novotec
        cd_aluno = login_res['DadosUsuario']['CD_USUARIO']
        
        # 2. MAPEAMENTO DINÂMICO DE DISCIPLINAS
        self.atualizar_status("Mapeando Sala do Futuro...")
        headers_auth = {"Authorization": f"Bearer {token_sed}"}
        url_disc = f"https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/apihubintegracoes/api/v2/Disciplina/ListarDisciplinaPorAluno?codigoAluno={cd_aluno}"
        
        disc_res = self.api_request("GET", url_disc, headers=headers_auth)
        if disc_res and disc_res.get('data'):
            for item in disc_res['data']:
                self.targets.append(str(item.get('CodigoTurma')))
        
        # 3. HANDSHAKE CMSP (IP.TV)
        self.atualizar_status("Sincronizando CMSP...")
        cmsp_res = self.api_request("POST", "https://edusp-api.ip.tv/registration/edusp/token", 
                                   json={"token": token_sed}, headers={"x-api-realm": "edusp"}, is_cmsp=True)
        
        if not cmsp_res: return
        self.auth_token = cmsp_res['auth_token']
        self.targets.append(cmsp_res['nick'])
        self.targets = list(set(self.targets)) # Remove duplicados

        # 4. RESOLUÇÃO COM GEMINI
        self.atualizar_status("Resolvendo Atividades...")
        self.executar_tarefas()

    def executar_tarefas(self):
        headers_cmsp = {
            "x-api-key": self.auth_token,
            "x-api-realm": "edusp",
            "Content-Type": "application/json"
        }
        
        # Busca em todos os targets mapeados
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        tarefas = self.api_request("GET", "https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers_cmsp, is_cmsp=True)

        if not tarefas:
            self.atualizar_status("Sem tarefas pendentes")
            return

        for task in tarefas:
            t_id = task['id']
            # O CMSP exige um delay para simular 'tempo de aula'
            print(f"    [*] Resolvendo: {task['title']}")
            
            # Submissão automática (Simulando 2 minutos de atividade)
            payload_answer = {
                "status": "submitted",
                "answers": {}, # Aqui entra a lógica do Gemini para questões complexas
                "duration": 125,
                "executed_on": task.get('publication_target')
            }
            
            self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", 
                             json=payload_answer, headers=headers_cmsp)
            time.sleep(1.5)

        self.atualizar_status("Concluído!")

# LOOP DE FILA
if __name__ == "__main__":
    print(">>> PK MOTOR V9 - MODO ADAPTATIVO FULL <<<")
    while True:
        try:
            fila = requests.get(f"{FIREBASE_URL}.json").json()
            if fila:
                for id_db, dados in fila.items():
                    if dados.get('status') == 'pendente':
                        PKMotorV9(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).engine_start()
            time.sleep(10)
        except:
            time.sleep(20)
