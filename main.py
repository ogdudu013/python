import requests
import time
import json

# === CONFIGURAÇÕES GLOBAIS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Gere em https://aistudio.google.com/

class PKMotorV7:
    def __init__(self, ra, digito, uf, senha, id_db):
        # Limpeza de dados para evitar o erro de duplicação de UF
        self.ra = str(ra).strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        self.ra_completo = f"{self.ra}{self.digito}{self.uf}"
        self.senha = senha
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.targets = ["1205", "1052", "1820", "1834"] # Canais Padrão
        self.auth_token = None

    def log(self, msg):
        print(f"[{self.ra}] {msg}")

    def atualizar_status(self, status):
        try:
            requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": status})
        except: pass

    def safe_request(self, method, url, **kwargs):
        """Previne o erro 'Expecting value: line 1 column 1'"""
        try:
            response = self.session.request(method, url, timeout=20, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Erro HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log(f"Falha na conexão: {e}")
            return None

    def gemini_brain(self, pergunta, tipo, opcoes=None):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"Como aluno, responda: {pergunta}. Tipo: {tipo}. Opções: {opcoes}. Responda apenas o texto da resposta ou ID."
        res = self.safe_request("POST", url, json={"contents": [{"parts": [{"text": prompt}]}]})
        try: return res['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return "A"

    def rodar(self):
        self.atualizar_status("Autenticando...")
        # LOGIN SED
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        res_sed = self.safe_request("POST", url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b"})
        
        if not res_sed: return False

        token_sed = res_sed.get("token")
        cd_aluno = res_sed['DadosUsuario']['CD_USUARIO']

        # MAPEAMENTO DE TURMAS (ADAPTAÇÃO AUTOMÁTICA)
        self.atualizar_status("Mapeando Disciplinas...")
        url_disc = f"https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/apihubintegracoes/api/v2/Disciplina/ListarDisciplinaPorAluno?codigoAluno={cd_aluno}"
        res_disc = self.safe_request("GET", url_disc, headers={"Authorization": f"Bearer {token_sed}", "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b"})
        
        if res_disc:
            for item in res_disc.get("data", []):
                self.targets.append(str(item.get("CodigoTurma")))

        # LOGIN CMSP
        res_cmsp = self.safe_request("POST", "https://edusp-api.ip.tv/registration/edusp/token", json={"token": token_sed}, headers={"x-api-realm": "edusp"})
        if not res_cmsp: return False
        
        self.auth_token = res_cmsp['auth_token']
        self.targets.append(res_cmsp['nick'])
        self.targets = list(set(self.targets))

        # RESOLVER TAREFAS
        self.atualizar_status("Resolvendo...")
        headers_tms = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json"}
        params = [("expired_only", "false"), ("limit", "50"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        tarefas = self.safe_request("GET", "https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers_tms)
        
        if tarefas:
            for task in tarefas:
                t_id = task['id']
                self.log(f"Resolvendo: {task['title']}")
                # Aqui o bot enviaria as respostas via Gemini...
                # Simulação de envio para brevidade
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json={"status": "submitted", "duration": 120}, headers=headers_tms)
                time.sleep(2)

        self.atualizar_status("Finalizado")
        return True

# LOOP DE VIGILÂNCIA
if __name__ == "__main__":
    print(">>> PK MOTOR V7 OPERACIONAL <<<")
    while True:
        try:
            r = requests.get(f"{FIREBASE_URL}.json")
            fila = r.json()
            if fila:
                for id_db, dados in fila.items():
                    if dados.get("status") == "pendente":
                        bot = PKMotorV7(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db)
                        bot.rodar()
            time.sleep(10) # Delay de segurança
        except Exception as e:
            print(f"Erro no loop: {e}")
            time.sleep(20)
