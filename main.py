import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        
        # Headers que o seu Eruda mostrou serem necessários
        self.headers_padrao = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36"
        }

    def login(self):
        print(f"[*] A aceder à SED: {self.ra_completo}...")
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        p = {"user": self.ra_completo, "senha": self.senha}
        
        try:
            r = self.session.post(url, json=p, headers=h)
            if r.status_code == 200:
                self.token_sed = r.json().get("token")
                print("[V] Login SED OK.")
                return True
            print(f"[X] Erro SED: {r.status_code}")
        except Exception as e:
            print(f"[X] Erro de rede: {e}")
        return False

    def trocar_token(self):
        print("[*] A obter chave x-api-key do CMSP...")
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        payload = {"token": self.token_sed}
        
        r = self.session.post(url, json=payload, headers=self.headers_padrao)
        if r.status_code == 200:
            self.auth_token_cmsp = r.json().get("auth_token")
            print("[V] Chave CMSP obtida.")
            return True
        print(f"[X] Erro no CMSP: {r.status_code}")
        return False

    def resolver(self):
        print("[*] A procurar tarefas pendentes...")
        # URL com os filtros que o seu log mostrou
        url = "https://edusp-api.ip.tv/tms/task/todo?expired_only=false&limit=100&offset=0&filter_expired=true&answer_statuses=draft&answer_statuses=pending"
        
        headers = self.headers_padrao.copy()
        headers["x-api-key"] = self.auth_token_cmsp # Usa a chave capturada no Eruda
        
        res = self.session.get(url, headers=headers)
        if res.status_code == 200:
            tarefas = res.json()
            if not tarefas:
                print("[!] Nenhuma tarefa encontrada com estes filtros.")
                return

            print(f"[+] Encontradas {len(tarefas)} tarefas!")
            for t in tarefas:
                t_id = t['id']
                print(f"[*] A completar: {t.get('title')}")
                
                # Endpoint de resposta
                u_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                p_ans = {"answers": {}, "last_question": True, "duration": 110}
                
                envio = self.session.post(u_ans, json=p_ans, headers=headers)
                if envio.status_code == 200:
                    print("    [OK] Feita.")
                else:
                    print(f"    [ERRO] Status: {envio.status_code}")
                time.sleep(1.5)
        else:
            print(f"[X] Falha ao listar tarefas: {res.status_code}")

# --- EXECUÇÃO ---
# Coloque os seus dados aqui
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

bot = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)
if bot.login():
    if bot.trocar_token():
        bot.resolver()
