import requests
import time

class RoboSalaDoFuturo:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.token_sed = None
        self.auth_token_cmsp = None
        self.nick = None
        # Lista de targets extraída do seu log do Eruda
        self.targets = [
            "r36cbf99f7e282664c-l",
            "rf5f73a6b29568391d-l",
            "1205", "1052", "1820", "764", "1834"
        ]
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def fazer_login_sed(self):
        url = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        headers = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
        res = self.session.post(url, json={"user": self.ra_completo, "senha": self.senha}, headers=headers)
        if res.status_code == 200:
            self.token_sed = res.json().get("token")
            print("[V] Login SED realizado.")
            return True
        return False

    def obter_token_cmsp(self):
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        headers = {"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        res = self.session.post(url, json={"token": self.token_sed}, headers=headers)
        if res.status_code == 200:
            dados = res.json()
            self.auth_token_cmsp = dados.get("auth_token")
            # Adicionamos os targets dinâmicos que vêm do login aos fixos do log
            novos_targets = dados.get("publication_targets", [])
            self.targets = list(set(self.targets + novos_targets))
            print(f"[V] Token CMSP obtido! Monitorando {len(self.targets)} canais de tarefas.")
            return True
        return False

    def resolver_tarefas(self):
        print("[*] Verificando tarefas pendentes (A Fazer)...")
        url_list = "https://edusp-api.ip.tv/tms/task/todo"
        headers = {"x-api-key": self.auth_token_cmsp, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}

        # Parâmetros baseados no seu log de sucesso (GET 200)
        params = [
            ("expired_only", "false"),
            ("limit", "100"),
            ("filter_expired", "true"),
            ("answer_statuses", "pending"),
            ("answer_statuses", "draft"),
            ("with_answer", "true")
        ]
        for t in self.targets:
            params.append(("publication_target", t))

        res = self.session.get(url_list, params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            if not tarefas:
                print("[!] Tudo em dia! Nenhuma tarefa pendente encontrada no momento.")
                return

            print(f"[i] {len(tarefas)} tarefas encontradas para resolver.")
            for task in tarefas:
                t_id = task['id']
                print(f"[*] Resolvendo: {task.get('title', 'Sem Título')}")
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                # Simulando tempo de leitura e enviando resposta vazia (participação)
                payload_ans = {"answers": {}, "last_question": True, "duration": 120}
                
                resp = self.session.post(url_ans, json=payload_ans, headers=headers)
                if resp.status_code == 200:
                    print("    [V] Finalizada com sucesso.")
                else:
                    print(f"    [!] Falha ao enviar: {resp.status_code}")
                time.sleep(2)
        else:
            print(f"[X] Erro na listagem: {res.status_code}")

# --- INÍCIO ---
RA = "110877468"
DIGITO = "4"
UF = "SP"
SENHA = "Pp@12345678"

robo = RoboSalaDoFuturo(RA, DIGITO, UF, SENHA)
if robo.fazer_login_sed():
    if robo.obter_token_cmsp():
        robo.resolver_tarefas()
