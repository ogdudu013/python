import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None

    def fazer_login_sed(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        headers = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36"
        }
        payload = {"user": self.ra_completo, "senha": self.senha}

        print(f"[*] Fazendo login na SED...")
        res = self.session.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            print("[V] Login SED realizado.")
            return True
        return False

    def obter_token_cmsp(self):
        print("[*] Trocando token para o CMSP (IP.TV)...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        
        # Headers IDÊNTICOS aos que você capturou no Eruda
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": "edusp-api.ip.tv", # Ajustado para o host real da API
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36"
        }
        
        payload = {"token": self.token_sed}
        
        res = self.session.post(url, json=payload, headers=headers)
        
        if res.status_code == 200:
            dados = res.json()
            self.auth_token_cmsp = dados.get("auth_token")
            print(f"[V] Token CMSP obtido! Usuário: {dados.get('name')}")
            return True
        else:
            print(f"[X] Erro na troca: {res.status_code} - {res.text}")
            return False

    def resolver_tarefas(self):
        print("[*] Buscando tarefas pendentes...")
        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=50"
        headers = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "User-Agent": "Mozilla/5.0"
        }

        res = self.session.get(url_list, headers=headers)
        if res.status_code == 200:
            tarefas = res.json().get("items", [])
            print(f"[i] Encontradas {len(tarefas)} tarefas.")
            
            for task in tarefas:
                t_id = task['id']
                print(f"[*] Resolvendo: {task['title']}")
                
                # Endpoint de resposta
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {}, # Envia vazio para marcar participação
                    "last_question": True,
                    "duration": 85 
                }
                
                resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                if resp.status_code == 200:
                    print("    [V] Tarefa finalizada.")
                else:
                    print(f"    [!] Erro: {resp.status_code}")
                time.sleep(1) # Delay de segurança
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
