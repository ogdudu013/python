import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def fazer_login_sed(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        headers = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": self.ua
        }
        payload = {"user": self.ra_completo, "senha": self.senha}

        print(f"[*] Fazendo login na SED: {self.ra_completo}...")
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            print("[V] Login SED realizado.")
            return True
        return False

    def obter_token_cmsp(self):
        print("[*] Trocando token para o CMSP...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        headers = {
            "Content-Type": "application/json",
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": self.ua
        }
        payload = {"token": self.token_sed}
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.auth_token_cmsp = res.json().get("auth_token")
            print(f"[V] Token CMSP obtido!")
            return True
        return False

    def resolver_tarefas(self):
        print("[*] Buscando tarefas pendentes...")
        url_list = "https://edusp-api.ip.tv/tms/task/todo"
        
        # Headers corrigidos: x-api-key é OBRIGATÓRIO conforme o erro 400
        headers = {
            "x-api-key": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": self.ua,
            "Accept": "application/json"
        }

        params = {
            "expired_only": "false",
            "limit": "50",
            "filter_expired": "true",
            "answer_statuses": ["draft", "pending"]
        }

        res = self.session.get(url_list, params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            # Garante que tratamos lista ou dicionário
            lista = tarefas.get("items", tarefas) if isinstance(tarefas, dict) else tarefas
            
            if not lista:
                print("[!] Nenhuma tarefa pendente encontrada.")
                return

            print(f"[i] Encontradas {len(lista)} tarefas.")
            for task in lista:
                t_id = task['id']
                print(f"[*] Resolvendo: {task.get('title', 'Tarefa')}")
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {}, 
                    "last_question": True,
                    "duration": 100 
                }
                
                resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                if resp.status_code == 200:
                    print("    [V] Concluída.")
                else:
                    print(f"    [!] Erro: {resp.status_code}")
                time.sleep(2)
        else:
            print(f"[X] Erro ao listar: {res.status_code}")
            print(f"Detalhe: {res.text}")

# --- EXECUÇÃO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)
if robo.fazer_login_sed():
    if robo.obter_token_cmsp():
        robo.resolver_tarefas()
