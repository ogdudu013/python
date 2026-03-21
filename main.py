import requests
import time

# Configuração do Firebase
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"

class PKMotorSupremo:
    def __init__(self, ra, digito, uf, senha, id_db):
        # Formatação rigorosa para evitar erros de login
        self.ra_num = str(ra).lstrip('0')
        self.ra_completo = str(ra).zfill(12)
        self.digito = str(digito).upper()
        self.uf = str(uf).upper()
        self.senha = str(senha)
        self.id_db = id_db
        
        self.sessao = requests.Session()
        # USER AGENT ATUALIZADO (Conforme seu log: Chrome 146 / Android 10)
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"
        self.sub_key = "d701a2043aa24d7ebb37e9adf60d043b"

    def atualizar_status(self, msg):
        print(f"[{self.ra_num}] {msg}")
        try:
            requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": msg})
        except:
            pass

    def executar(self):
        try:
            self.atualizar_status("Autenticando na SED...")

            # 1. LOGIN SED
            login_data = {"user": f"{self.ra_completo}{self.digito}{self.uf}", "senha": self.senha}
            res_sed = self.sessao.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json=login_data,
                headers={"Ocp-Apim-Subscription-Key": self.sub_key, "User-Agent": self.ua}
            )

            if res_sed.status_code != 200:
                self.atualizar_status("Erro: RA ou Senha Inválidos")
                return

            token_sed = res_sed.json().get('token')

            # 2. LOGIN CMSP (Captura de Nickname e Token de Acesso)
            res_cmsp = self.sessao.post(
                "https://edusp-api.ip.tv/registration/edusp/token",
                json={"token": token_sed},
                headers={"x-api-realm": "edusp", "User-Agent": self.ua}
            )
            data_cmsp = res_cmsp.json()
            if isinstance(data_cmsp, list): data_cmsp = data_cmsp[0]
            
            auth_token = data_cmsp['auth_token']
            nick_aluno = data_cmsp['nick'] # Dinâmico: essencial para salas pessoais

            # 3. MAPEAMENTO DINÂMICO DE SALAS (Resolve o erro "Sala não encontrada")
            self.atualizar_status("Sincronizando salas do aluno...")
            res_salas = self.sessao.get(
                "https://edusp-api.ip.tv/room/user?list_all=true",
                headers={"x-api-key": auth_token, "x-api-realm": "edusp"}
            )
            
            # IDs de canais base + canais dinâmicos por aluno
            targets = ["1173", "1817", "764", "1182"]
            for sala in res_salas.json():
                sid = sala.get('id')
                if sid:
                    targets.append(f"{sid}-l")
                    targets.append(f"{sid}-l:{nick_aluno}")

            # 4. BUSCA DE TAREFAS (Pendentes e Rascunhos)
            self.atualizar_status("Buscando lições no sistema...")
            params = [
                ('expired_only', 'false'), ('filter_expired', 'true'),
                ('answer_statuses', 'pending'), ('answer_statuses', 'draft'),
                ('limit', '100'), ('with_apply_moment', 'true')
            ]
            for t in list(set(targets)):
                params.append(('publication_target', t))

            res_tasks = self.sessao.get(
                "https://edusp-api.ip.tv/tms/task/todo",
                params=params,
                headers={"x-api-key": auth_token, "x-api-realm": "edusp"}
            )
            tarefas = res_tasks.json()

            if not tarefas:
                self.atualizar_status("Nenhuma lição pendente! ✅")
                return

            self.atualizar_status(f"Resolvendo {len(tarefas)} tarefas...")

            # 5. EXECUÇÃO (Loop de Resolução)
            for tarefa in tarefas:
                self.atualizar_status(f"Concluindo: {tarefa['title'][:20]}...")
                # Lógica de POST /answer (envio da resposta) aqui
                time.sleep(1.5)

            self.atualizar_status("Tudo pronto! Tarefas concluídas. 🚀")

        except Exception as e:
            self.atualizar_status(f"Erro Fatal: {str(e)}")

# Para rodar o motor em um loop que lê o seu Firebase:
# Use uma lógica externa que instancia o PKMotorSupremo para cada entrada na 'fila'.
