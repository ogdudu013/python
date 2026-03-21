import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        
        # User-Agent simulando o App Android oficial
        self.ua = "okhttp/4.9.2" 
        
        self.headers_sed = {
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

        print(f"[*] Autenticando na SED: {self.ra_completo}...")
        res = self.session.post(url, json=payload, headers=self.headers_sed)
        
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            print(f"[V] Login SED OK!")
            return True
        else:
            print(f"[X] Erro SED: {res.status_code}")
            return False

    def obter_token_cmsp(self):
        print("[*] Trocando token para o CMSP...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        
        # Payload simplificado como o App faz
        payload = {"token": self.token_sed}
        
        headers_cmsp = {
            "x-api-realm": "edusp",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": self.ua,
            "Host": "edusp-api.ip.tv",
            "Connection": "Keep-Alive"
        }
        
        # Tentativa de POST com tratamento manual do JSON para evitar erro 400
        res = self.session.post(url, json=payload, headers=headers_cmsp)
        
        if res.status_code == 200:
            self.auth_token_cmsp = res.json().get("auth_token")
            print("[V] Token CMSP obtido!")
            return True
        else:
            print(f"[X] Erro CMSP {res.status_code}: {res.text}")
            return False

    def listar_e_resolver(self):
        print("[*] Buscando tarefas...")
        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=50"
        headers = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "User-Agent": self.ua
        }

        res = self.session.get(url_list, headers=headers)
        if res.status_code == 200:
            tarefas = res.json().get("items", [])
            print(f"[i] {len(tarefas)} tarefas pendentes.")
            
            for task in tarefas:
                t_id = task['id']
                print(f"[*] Resolvendo: {task['title']}")
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {}, 
                    "last_question": True,
                    "duration": 80 
                }
                
                envio = self.session.post(url_ans, json=payload_ans, headers=headers)
                if envio.status_code == 200:
                    print("    [V] Concluído.")
                else:
                    print(f"    [!] Erro: {envio.status_code}")
                time.sleep(1)
        else:
            print(f"[X] Erro ao listar: {res.status_code}")

# --- EXECUÇÃO ---
# Use os dados que funcionaram no passo anterior
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678" 

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)

if robo.fazer_login():
    if robo.obter_token_cmsp():
        robo.listar_e_resolver()
