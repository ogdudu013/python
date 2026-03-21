import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        
        # Headers padrão para simular o navegador
        self.headers_web = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36"
        }

    def fazer_login_sed(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        payload = {"user": self.ra_completo, "senha": self.senha}
        headers = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            return True
        return False

    def obter_token_cmsp(self):
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        payload = {"token": self.token_sed}
        # Adicionando os headers que vimos no seu Eruda
        headers = self.headers_web.copy()
        
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.auth_token_cmsp = res.json().get("auth_token")
            print(f"[V] Token CMSP obtido via IP.TV")
            return True
        return False

    def listar_e_resolver(self):
        # A URL exata que seu Eruda capturou (com os filtros de A Fazer)
        url_list = "https://edusp-api.ip.tv/tms/task/todo"
        params = {
            "expired_only": "false",
            "limit": "100",
            "offset": "0",
            "filter_expired": "true",
            "is_exam": "false",
            "with_answer": "true",
            "is_essay": "false",
            "answer_statuses": ["draft", "pending"],
            "with_apply_moment": "true"
        }
        
        # O PULO DO GATO: Usar o token no x-api-key em vez de Authorization
        headers = self.headers_web.copy()
        headers["x-api-key"] = self.auth_token_cmsp 
        
        print("[*] Buscando tarefas pendentes...")
        res = self.session.get(url_list, params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            if not tarefas:
                print("[!] Nenhuma tarefa pendente encontrada no momento.")
                return

            print(f"[i] Encontradas {len(tarefas)} tarefas.")
            for task in tarefas:
                t_id = task['id']
                print(f"[*] Resolvendo: {task.get('title', 'Tarefa s/ titulo')}")
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {}, 
                    "last_question": True,
                    "duration": 100 
                }
                
                # Responder também exige o x-api-key
                resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                if resp.status_code == 200:
                    print("    [V] Finalizada.")
                else:
                    print(f"    [!] Erro {resp.status_code}")
                time.sleep(2)
        else:
            print(f"[X] Erro ao listar: {res.status_code}")
            print(f"Dica: O servidor retornou: {res.text}")

# --- EXECUÇÃO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)
if robo.fazer_login_sed():
    if robo.obter_token_cmsp():
        robo.listar_e_resolver()
