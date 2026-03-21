import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        # User-Agent idêntico ao que funcionou no seu log
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

        print(f"[*] Fazendo login na SED: {self.ra_completo}...")
        try:
            res = self.session.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                self.token_sed = res.json().get("token")
                print("[V] Login SED realizado com sucesso.")
                return True
            else:
                print(f"[X] Erro no login SED: {res.status_code}")
                return False
        except Exception as e:
            print(f"[X] Erro de conexão: {e}")
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
        
        try:
            res = self.session.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                dados = res.json()
                self.auth_token_cmsp = dados.get("auth_token")
                print(f"[V] Token CMSP obtido! Usuário: {dados.get('name')}")
                return True
            else:
                print(f"[X] Erro na troca de token: {res.status_code}")
                return False
        except Exception as e:
            print(f"[X] Erro ao obter token CMSP: {e}")
            return False

    def resolver_tarefas(self):
        print("[*] Buscando tarefas pendentes...")
        url_list = "https://edusp-api.ip.tv/tms/task/todo"
        
        # Parâmetros exatos que o seu Eruda capturou para evitar Erro 400
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
        
        headers = {
            "Authorization": self.auth_token_cmsp,
            "x-api-realm": "edusp",
            "x-api-platform": "webclient",
            "User-Agent": self.ua,
            "Accept": "application/json"
        }

        try:
            res = self.session.get(url_list, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                # O CMSP pode retornar uma lista direta ou um objeto com 'items'
                tarefas = data.get("items", data) if isinstance(data, dict) else data
                
                if not tarefas:
                    print("[!] Nenhuma tarefa pendente encontrada no momento.")
                    return

                print(f"[i] Encontradas {len(tarefas)} tarefas.")
                
                for task in tarefas:
                    t_id = task['id']
                    # Limpa caracteres especiais do título para o terminal
                    titulo = task.get('title', 'Tarefa sem título').encode('ascii', 'ignore').decode('ascii')
                    print(f"[*] Resolvendo: {titulo}")
                    
                    url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                    payload_ans = {
                        "answers": {}, # Marca como feito/participação
                        "last_question": True,
                        "duration": 110 # Simula 1 minuto e 50 segundos de "estudo"
                    }
                    
                    resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                    if resp.status_code == 200:
                        print("    [V] Concluída.")
                    else:
                        print(f"    [!] Erro ao enviar resposta: {resp.status_code}")
                    
                    time.sleep(2) # Pausa entre tarefas para segurança
            else:
                print(f"[X] Erro ao listar tarefas: {res.status_code}")
                print(f"Detalhe: {res.text}")
        except Exception as e:
            print(f"[X] Erro durante o processamento: {e}")

# --- CONFIGURAÇÃO ---
# Substitua pelos seus dados reais
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

# --- EXECUÇÃO ---
robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)

if robo.fazer_login_sed():
    if robo.obter_token_cmsp():
        robo.resolver_tarefas()
