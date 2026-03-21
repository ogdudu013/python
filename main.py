import requests
import time
import json

# === CONFIGURAÇÕES REAIS (Baseadas nos seus arquivos) ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV10:
    def __init__(self, ra, digito, uf, senha, id_db):
        # Ajuste automático: Garante que o RA tenha os zeros necessários para a SED
        self.ra_formatado = str(ra).strip().zfill(10)
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        self.ra_completo = f"{self.ra_formatado}{self.digito}{self.uf}"
        self.senha = senha
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.targets = ["1205", "1052", "1820", "1834"]

    def atualizar_status(self, status):
        """Atualiza o Firebase para você acompanhar pelo site"""
        try:
            requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": status})
        except: pass

    def iniciar(self):
        print(f"\n[*] Processando RA: {self.ra_completo}")
        self.atualizar_status("Em progresso...")

        # 1. LOGIN SED (Usando sua Key do main.py)
        headers_sed = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": self.ua
        }
        res_sed = self.session.post(
            "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
            json={"user": self.ra_completo, "senha": self.senha},
            headers=headers_sed
        )

        if res_sed.status_code != 200:
            self.atualizar_status("Erro: Login Inválido")
            return

        token_sed = res_sed.json().get("token")
        
        # 2. LOGIN CMSP E CAPTURA DE CANAIS
        res_cmsp = self.session.post(
            "https://edusp-api.ip.tv/registration/edusp/token",
            json={"token": token_sed},
            headers={"x-api-realm": "edusp", "User-Agent": self.ua}
        )
        
        if res_cmsp.status_code == 200:
            dados = res_cmsp.json()
            auth_token = dados.get("auth_token")
            # Adiciona os canais específicos do aluno aos globais
            self.targets = list(set(self.targets + dados.get("publication_targets", [])))
            self.targets.append(dados.get("nick"))

            # 3. RESOLUÇÃO DE TAREFAS
            self.resolver(auth_token)
        
    def resolver(self, auth_token):
        self.atualizar_status("Resolvendo Atividades...")
        headers = {"x-api-key": auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        
        # Parâmetros de busca idênticos ao seu log de sucesso
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        tarefas = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers).json()
        
        for task in tarefas:
            t_id = task['id']
            # Envio rápido para garantir a participação
            self.session.post(
                f"https://edusp-api.ip.tv/tms/task/{t_id}/answer",
                json={"status": "submitted", "duration": 130, "answers": {}},
                headers=headers
            )
            print(f"    [V] {task.get('title')} - OK")
            time.sleep(1)

        self.atualizar_status("Concluído")
        print(f"[!] RA {self.ra_completo} Finalizado.")

# === LOOP DE VIGILÂNCIA CORRIGIDO ===
if __name__ == "__main__":
    print(">>> PK MOTOR V10 - MODO ADAPTATIVO ATIVO <<<")
    while True:
        try:
            # Busca a fila e força a conversão para JSON
            r = requests.get(f"{FIREBASE_URL}.json")
            fila = r.json()
            
            if fila:
                for id_db, dados in fila.items():
                    # MUDANÇA CRÍTICA: Aceita "pendente" OU "Autenticando..."
                    status_atual = dados.get('status', '')
                    if "pendente" in status_atual or "Autenticando" in status_atual:
                        bot = PKMotorV10(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db)
                        bot.iniciar()
            
            time.sleep(10)
        except Exception as e:
            print(f"Erro no loop: {e}")
            time.sleep(15)
