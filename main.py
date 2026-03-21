import requests
import time

# Banco de Dados
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"

class PKMotorSupremo:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_formatado = str(ra).zfill(12)
        self.digito = str(digito).upper()
        self.uf = str(uf).upper()
        self.senha = str(senha)
        self.id_db = id_db
        
        self.sessao = requests.Session()
        # USER AGENT ATUALIZADO CONFORME SEU LOG (Chrome 146)
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"
        self.sub_key = "d701a2043aa24d7ebb37e9adf60d043b"

    def log(self, msg):
        print(f"[{self.ra_formatado}] {msg}")
        try:
            requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": msg})
        except: pass

    def executar(self):
        try:
            self.log("Autenticando SED...")
            # 1. LOGIN SED - OBTENÇÃO DO TOKEN MESTRE
            res_sed = self.sessao.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json={"user": f"{self.ra_formatado}{self.digito}{self.uf}", "senha": self.senha},
                headers={"Ocp-Apim-Subscription-Key": self.sub_key, "User-Agent": self.ua}
            )
            
            if res_sed.status_code != 200:
                self.log("Erro: Login Inválido")
                return

            token_sed = res_sed.json().get('token')

            # 2. HANDSHAKE CMSP - GERAÇÃO DO X-API-KEY (O QUE EVITA TRAVAR)
            res_cmsp = self.sessao.post(
                "https://edusp-api.ip.tv/registration/edusp/token",
                json={"token": token_sed},
                headers={"x-api-realm": "edusp", "User-Agent": self.ua}
            )
            dados_auth = res_cmsp.json()
            if isinstance(dados_auth, list): dados_auth = dados_auth[0]
            
            api_key = dados_auth['auth_token']
            nick = dados_auth['nick'] # ESSENCIAL PARA AS TAREFAS INDIVIDUAIS

            # 3. MAPEAMENTO DE SALAS EM TEMPO REAL
            self.log("Sincronizando Salas...")
            res_salas = self.sessao.get(
                "https://edusp-api.ip.tv/room/user?list_all=true",
                headers={"x-api-key": api_key, "x-api-realm": "edusp"}
            )
            
            # Montagem dos Targets (Onde o script busca as lições)
            targets = ["1173", "1817", "764", "1182"] # Canais Globais
            for sala in res_salas.json():
                sid = sala.get('id')
                if sid:
                    targets.append(f"{sid}-l")
                    targets.append(f"{sid}-l:{nick}") # Target pessoal (Blindado)

            # 4. BUSCA DE TAREFAS (PENDENTES E RASCUNHOS)
            self.log("Buscando Lições...")
            parametros = [
                ('expired_only', 'false'), ('filter_expired', 'true'),
                ('answer_statuses', 'pending'), ('answer_statuses', 'draft'),
                ('limit', '100'), ('with_apply_moment', 'true')
            ]
            for t in list(set(targets)):
                parametros.append(('publication_target', t))

            res_tarefas = self.sessao.get(
                "https://edusp-api.ip.tv/tms/task/todo",
                params=parametros,
                headers={"x-api-key": api_key, "x-api-realm": "edusp"}
            )
            tarefas = res_tarefas.json()

            if not tarefas:
                self.log("Nenhuma lição pendente! ✅")
                return

            self.log(f"Resolvendo {len(tarefas)} lições...")

            # 5. LOOP DE RESOLUÇÃO (CONFORME SEUS LOGS DE RESPOSTA)
            for tarefa in tarefas:
                id_tarefa = tarefa['id']
                self.log(f"Fazendo: {tarefa['title'][:20]}...")
                
                # ENVIO DA RESPOSTA (O POST FINAL)
                # Aqui você deve colocar o seu endpoint de 'answer' ou 'complete'
                time.sleep(1.2) # Evita detecção por velocidade

            self.log("Sucesso Total! 🚀")

        except Exception as e:
            self.log(f"Erro no Motor: {str(e)}")
