import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        # User-Agent padronizado para todas as chamadas
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def fazer_login_sed(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        headers = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": self.ua,
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/"
        }
        payload = {"user": self.ra_completo, "senha": self.senha}

        print(f"[*] Fazendo login na SED...")
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            print("[V] Login SED realizado.")
            return True
        else:
            print(f"[X] Erro SED: {res.status_code}")
            return False

    def obter_token_cmsp(self):
        print("[*] Trocando token para o CMSP (IP.TV)...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": self.ua
        }
        
        payload = {"token": self.token_sed}
        res = self.session.post(url, json=payload, headers=headers)
        
        if res.status_code == 200:
            dados = res.json()
            self.auth_token_cmsp = dados.get("auth_token")
            print(f"[V] Token CMSP obtido! Usuário: {dados.get('name')}")
            return True
        else:
            print(f"[X] Erro na troca: {res.status_code}")
            return False

    def resolver_tarefas(self):
        print("[*] Buscando tarefas pendentes...")
        # Adicionamos os filtros que vimos no seu Eruda para evitar lista vazia
        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=100&answer_statuses=pending&answer_statuses=draft"
        
        headers = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": self.ua,
            "Accept": "application/json"
        }

        res = self.session.get(url_list, headers=headers)
        if res.status_code == 200:
            tarefas = res.json().get("items", [])
            print(f"[i] Encontradas {len(tarefas)} tarefas.")
            
            for task in tarefas:
                t_id = task['id']
                print(f"[*] Resolvendo: {task['title']}")
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {}, 
                    "last_question": True,
                    "duration": 90 # Simula um tempo maior para evitar detecção
                }
                
                resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                if resp.status_code == 200:
                    print("    [V] Tarefa finalizada.")
                else:
                    print(f"    [!] Erro: {resp.status_code}")
                time.sleep(2) # Pausa maior entre tarefas
        else:
            print(f"[X] Erro ao listar: {res.status_code}")

# --- EXECUÇÃO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)

if robo.fazer_login_sed():
    if robo.obter_token_cmsp():
        robo.resolver_tarefas()
