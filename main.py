import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        
        self.headers_base = {
            "Host": "sedintegracoes.educacao.sp.gov.br",
            "Accept": "application/json, text/plain, */*",
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36",
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/",
            "Content-Type": "application/json"
        }

    def fazer_login(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        payload = {"user": self.ra_completo, "senha": self.senha}

        print(f"[*] Autenticando: {self.ra_completo}...")
        res = self.session.post(url, json=payload, headers=self.headers_base)
        
        if res.status_code == 200:
            dados = res.json()
            self.token_sed = dados.get("token")
            print(f"[V] Login SED OK! Bem-vindo, {dados['DadosUsuario']['NAME']}")
            return True
        else:
            print(f"[X] Erro no login SED: {res.status_code}")
            return False

    def obter_token_cmsp(self):
        """Troca o Bearer da SED pelo Token do CMSP (IP.TV)"""
        print("[*] Trocando token para acesso às tarefas...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        payload = {"token": self.token_sed}
        headers = {
            "x-api-realm": "edusp",
            "Content-Type": "application/json",
            "User-Agent": self.headers_base["User-Agent"]
        }
        
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.auth_token_cmsp = res.json().get("auth_token")
            print("[V] Token CMSP obtido com sucesso.")
            return True
        else:
            print(f"[X] Erro ao obter token CMSP: {res.status_code}")
            return False

    def listar_e_resolver_tarefas(self):
        if not self.auth_token_cmsp:
            if not self.obter_token_cmsp(): return

        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=50"
        headers_task = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "User-Agent": self.headers_base["User-Agent"]
        }

        res = self.session.get(url_list, headers=headers_task)
        if res.status_code != 200:
            print(f"[X] Erro ao listar tarefas: {res.status_code}")
            return

        tarefas = res.json().get("items", [])
        print(f"[*] Tarefas pendentes encontradas: {len(tarefas)}")

        for task in tarefas:
            t_id = task['id']
            print(f"[*] Resolvendo: {task['title']} (ID: {t_id})")
            
            url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
            payload_ans = {
                "answers": {}, 
                "last_question": True,
                "duration": 70 
            }
            
            finish = self.session.post(url_ans, json=payload_ans, headers=headers_task)
            if finish.status_code == 200:
                print("    [V] Concluída.")
            else:
                print(f"    [!] Falha: {finish.status_code}")
            
            time.sleep(1.5) # Pequena pausa para segurança

# --- EXECUÇÃO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "SUA_SENHA_AQUI" 

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)

if robo.fazer_login():
    if robo.obter_token_cmsp():
        robo.listar_e_resolver_tarefas()
