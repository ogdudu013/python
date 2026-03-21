import requests
import time
from ftplib import FTP
import io

# ================= EXTERNO: CONFIGURAÇÕES FTP =================
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo" # Substitui pela tua senha real

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token_cmsp = None
        self.targets = ["r36cbf99f7e282664c-l", "1205", "1052", "1820", "764", "1834"]
        self.ua = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile"

    def atualizar_log_site(self, mensagem):
        print(f"LOG: {mensagem}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                msg_formatada = f"[{time.strftime('%H:%M:%S')}] {mensagem}\n"
                bio = io.BytesIO(msg_formatada.encode('utf-8'))
                # Appends (anexa) a mensagem ao log.txt existente
                ftp.storbinary('APPE log.txt', bio)
        except Exception as e:
            print(f"Erro ao subir log FTP: {e}")

    def login(self):
        # 1. Login na SED para pegar o Token
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h1 = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        res_sed = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h1)
        
        if res_sed.status_code != 200:
            return False, "Erro no login SED (Senha incorreta?)"

        token_sed = res_sed.json().get("token")

        # 2. Troca pelo Token do CMSP
        url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
        h2 = {"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient"}
        res_cmsp = self.session.post(url_cmsp, json={"token": token_sed}, headers=h2)
        
        if res_cmsp.status_code == 200:
            dados = res_cmsp.json()
            self.auth_token_cmsp = dados.get("auth_token")
            # Adiciona targets dinâmicos da conta
            self.targets = list(set(self.targets + dados.get("publication_targets", [])))
            return True, "Login realizado com sucesso!"
        return False, "Erro ao obter token CMSP."

    def resolver_tarefas(self):
        url_list = "https://edusp-api.ip.tv/tms/task/todo"
        headers = {"x-api-key": self.auth_token_cmsp, "x-api-realm": "edusp", "User-Agent": self.ua}
        
        params = [
            ("expired_only", "false"), ("limit", "50"), ("filter_expired", "true"),
            ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")
        ]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get(url_list, params=params, headers=headers)
        if res.status_code == 200:
            tarefas = res.json()
            if not tarefas:
                self.atualizar_log_site("Nenhuma tarefa pendente.")
                return

            self.atualizar_log_site(f"Encontradas {len(tarefas)} tarefas. Iniciando...")
            for task in tarefas:
                t_id = task['id']
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {"answers": {}, "last_question": True, "duration": 135}
                
                r = self.session.post(url_ans, json=payload, headers=headers)
                if r.status_code == 200:
                    self.atualizar_log_site(f"Tarefa OK: {task.get('title')[:20]}...")
                time.sleep(1.5)
            self.atualizar_log_site("--- Processo Finalizado ---")
        else:
            self.atualizar_log_site("Erro ao listar tarefas.")

def buscar_dados_ftp():
    try:
        with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            r = io.BytesIO()
            ftp.retrbinary('RETR dados.txt', r.write)
            linhas = r.getvalue().decode('utf-8').strip().split('\n')
            if not linhas or linhas[0] == "": return None
            
            ultima = linhas[-1]
            # Limpa o ficheiro após ler para não repetir o mesmo login
            ftp.storbinary('STORE dados.txt', io.BytesIO(b""))
            return ultima
    except: return None

# LOOP PRINCIPAL DO BOT
print(">>> PK SCRIPT BOT INICIADO <<<")
while True:
    print("[*] Verificando site via FTP...")
    dados_linha = buscar_dados_ftp()
    
    if dados_linha:
        try:
            # Parse dos dados: "RA: 123 | DIGITO: 1 | UF: SP | SENHA: 123"
            p = {x.split(': ')[0]: x.split(': ')[1] for x in dados_linha.split(' | ')}
            
            bot = PKScriptBot(p['RA'], p['DIGITO'], p['UF'], p['SENHA'])
            bot.atualizar_log_site(f"Bot acionado para RA {p['RA']}...")
            
            ok, msg = bot.login()
            bot.atualizar_log_site(msg)
            
            if ok:
                bot.resolver_tarefas()
        except Exception as e:
            print(f"Erro ao processar linha: {e}")
    
    time.sleep(15) # Espera 15 segundos antes de checar o site novamente
