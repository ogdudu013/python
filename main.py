import requests
import time
import json

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        
        # Headers base extraídos dos seus logs reais
        self.headers = {
            "Host": "sedintegracoes.educacao.sp.gov.br",
            "Accept": "application/json, text/plain, */*",
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36",
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "Content-Type": "application/json"
        }

    def fazer_login(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        payload = {
            "user": self.ra_completo,
            "senha": self.senha
        }

        print(f"[*] Autenticando: {self.ra_completo}...")
        try:
            res = self.session.post(url, json=payload, headers=self.headers)
            
            if res.status_code == 200:
                dados = res.json()
                self.token = dados.get("token")
                self.user_id = dados["DadosUsuario"]["CD_USUARIO"]
                # Atualiza o header com o Bearer para as próximas chamadas
                self.headers["Authorization"] = f"Bearer {self.token}"
                print(f"[V] Login OK! Bem-vindo, {dados['DadosUsuario']['NAME']}")
                return True
            else:
                print(f"[X] Erro {res.status_code}: {res.text}")
                return False
        except Exception as e:
            print(f"[X] Falha na conexão: {e}")
            return False

    def obter_token_cmsp(self):
        """Troca o token da SED pelo token do CMSP (IP.TV) para resolver tarefas"""
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        payload = {"token": self.token}
        headers_iptv = {
            "x-api-realm": "edusp",
            "Content-Type": "application/json",
            "User-Agent": self.headers["User-Agent"]
        }
        
        res = self.session.post(url, json=payload, headers=headers_iptv)
        if res.status_code == 200:
            self.auth_token_cmsp = res.json().get("auth_token")
            return True
        return False

    def listar_e_resolver_tarefas(self):
        if not hasattr(self, 'auth_token_cmsp'):
            self.obter_token_cmsp()

        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=50"
        headers_task = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp"
        }

        res = self.session.get(url_list, headers=headers_task)
        tarefas = res.json().get("items", [])
        
        print(f"[*] Total de tarefas pendentes: {len(tarefas)}")

        for task in tarefas:
            task_id = task['id']
            print(f"[*] Resolvendo: {task['title']}")
            
            # Endpoint de conclusão
            url_ans = f"https://edusp-api.ip.tv/tms/task/{task_id}/answer"
            payload_ans = {
                "answers": {}, # Envia vazio para marcar como visto/feito
                "last_question": True,
                "duration": 75 # Simula que o aluno ficou 75 segundos na tarefa
            }
            
            finish = self.session.post(url_ans, json=payload_ans, headers=headers_task)
            if finish.status_code == 200:
                print(f"    [V] Tarefa finalizada.")
            else:
                print(f"    [!] Erro ao finalizar.")
            
            time.sleep(1) # Delay para evitar detecção

# --- CONFIGURAÇÃO E EXECUÇÃO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678" # Insira sua senha real entre as aspas

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)

if robo.fazer_login():
    robo.listar_e_resolver_tarefas()
