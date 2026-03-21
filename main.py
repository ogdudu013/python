import requests
import time

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV17:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_limpo = str(ra).upper().replace("SP", "").strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        self.ra_completo = f"{(self.ra_limpo + self.digito).zfill(12)}{self.uf}"
        self.senha = str(senha).strip()
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def log_status(self, msg):
        print(f"[{self.ra_limpo}] {msg}")
        try: requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": msg})
        except: pass

    def iniciar_fluxo(self):
        self.log_status("Autenticando...")
        headers_sed = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": self.ua
        }
        
        try:
            # 1. LOGIN NA SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers=headers_sed
            )
            
            if res_sed.status_code != 200:
                self.log_status("Erro: Login SED Rejeitado")
                return

            dados_sed = res_sed.json()
            token_sed = dados_sed.get('token')
            nome_aluno = dados_sed.get('DadosUsuario', {}).get('NM_USUARIO', 'Estudante')
            self.log_status(f"Logado como: {nome_aluno}")

            # 2. TROCA DE TOKEN (SED -> CMSP)
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": token_sed}, 
                headers={"x-api-realm": "edusp", "User-Agent": self.ua}
            )
            
            data_cmsp = res_cmsp.json()
            if isinstance(data_cmsp, list): data_cmsp = data_cmsp[0]
            auth_token = data_cmsp.get('auth_token')
            
            # === CAPTURA DINÂMICA (Baseada no seu Log) ===
            # Extraímos os publication_targets que a API envia no perfil
            targets = data_cmsp.get('publication_targets', [])
            nick = data_cmsp.get('nick')
            
            # Adicionamos as variações de nick (individuais) como visto no seu log
            targets_finais = []
            for t in targets:
                targets_finais.append(t) # Sala (ex: r69b...)
                if nick:
                    targets_finais.append(f"{t}:{nick}") # Individual (ex: r69b...:eduarda...)
            
            if not targets_finais:
                self.log_status("Nenhuma sala encontrada.")
                return

            self.resolver_tarefas(auth_token, targets_finais)
            
        except Exception as e:
            self.log_status(f"Erro no sistema: {str(e)}")

    def resolver_tarefas(self, token, targets):
        headers = {
            "x-api-key": token, 
            "x-api-realm": "edusp", 
            "Content-Type": "application/json", 
            "User-Agent": self.ua
        }
        
        # Parâmetros de busca idênticos ao seu log de rede
        params = [
            ("expired_only", "false"),
            ("limit", "100"),
            ("answer_statuses", "pending")
        ]
        for t in targets:
            params.append(("publication_target", t))

        try:
            res_tarefas = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
            tarefas = res_tarefas.json()

            if not tarefas or not isinstance(tarefas, list):
                self.log_status("Nenhuma tarefa pendente.")
                return

            self.log_status(f"Fazendo {len(tarefas)} tarefas...")
            
            for task in tarefas:
                t_id = task['id']
                titulo = task.get('title', 'Sem título')
                self.log_status(f"Processando: {titulo}")
                
                # Simulação de envio (Aqui você integraria a chamada do Gemini)
                # payload = {"task_id": t_id, "answer": "..."}
                # self.session.post("https://edusp-api.ip.tv/tms/task/answer", json=payload, headers=headers)
                
                time.sleep(1.5)

            self.log_status("Concluído com sucesso!")
        except Exception as e:
            self.log_status(f"Erro ao listar: {str(e)}")

# Execução automática
if __name__ == "__main__":
    while True:
        try:
            fila = requests.get(f"{FIREBASE_URL}.json").json()
            if fila:
                for id_db, d in fila.items():
                    if d.get('status') == "Autenticando...":
                        PKMotorV17(d['ra'], d['digito'], d['uf'], d['senha'], id_db).iniciar_fluxo()
        except: pass
        time.sleep(5)
