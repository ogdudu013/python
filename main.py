import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorV8:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra = str(ra).strip()
        self.digito = str(digito).strip()
        self.uf = str(uf).strip().upper()
        self.senha = str(senha).strip()
        self.id_db = id_db
        self.session = requests.Session()
        
        # User-Agent idêntico ao seu log para o servidor não desconfiar
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.headers_sed = {
            "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
            "Content-Type": "application/json",
            "User-Agent": self.ua
        }
        self.targets = ["1205", "1052", "1820", "1834"]

    def atualizar_status(self, status):
        try: requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": status})
        except: pass

    def safe_post(self, url, data=None, headers=None):
        """Função que impede o erro de 'Expecting value'"""
        try:
            res = self.session.post(url, json=data, headers=headers, timeout=20)
            if res.status_code == 200:
                return res.json()
            print(f"[!] Erro {res.status_code} na URL: {url}")
            return None
        except:
            return None

    def resolver_com_gemini(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": f"Responda apenas com a alternativa correta: {pergunta}"}]}]}
        try:
            r = requests.post(url, json=payload, timeout=10)
            return r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return "A"

    def iniciar(self):
        print(f"\n[*] Iniciando RA: {self.ra}")
        self.atualizar_status("Logando na SED...")

        # LOGIN SED (Onde dava o erro)
        login_data = {"user": f"{self.ra}{self.digito}{self.uf}", "senha": self.senha}
        res_sed = self.safe_post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", login_data, self.headers_sed)

        if not res_sed or 'token' not in res_sed:
            print("[X] Falha crítica no login SED. Verificando dados...")
            self.atualizar_status("Erro: RA/Senha Inválidos")
            return

        token = res_sed['token']
        cd_aluno = res_sed['DadosUsuario']['CD_USUARIO']

        # MAPEAMENTO (ADAPTAÇÃO AO ALUNO)
        self.atualizar_status("Mapeando Matérias...")
        url_disc = f"https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/apihubintegracoes/api/v2/Disciplina/ListarDisciplinaPorAluno?codigoAluno={cd_aluno}"
        res_disc = self.session.get(url_disc, headers={"Authorization": f"Bearer {token}", **self.headers_sed}).json()
        
        for d in res_disc.get('data', []):
            self.targets.append(str(d.get('CodigoTurma')))

        # LOGIN CMSP
        res_cmsp = self.safe_post("https://edusp-api.ip.tv/registration/edusp/token", {"token": token}, {"x-api-realm": "edusp", "User-Agent": self.ua})
        if not res_cmsp: return

        auth_token = res_cmsp['auth_token']
        self.targets.append(res_cmsp['nick'])

        # RESOLUÇÃO
        self.atualizar_status("Resolvendo Tudo...")
        # ... (Aqui o código segue a lógica de loop de tarefas que já temos)
        
        self.atualizar_status("Concluído!")
        print(f"[V] RA {self.ra} Finalizado.")

# LOOP PRINCIPAL
print(">>> PK MOTOR V8 OPERACIONAL - VIGILÂNCIA ATIVA <<<")
while True:
    try:
        fila = requests.get(f"{FIREBASE_URL}.json").json()
        if fila:
            for id_db, dados in fila.items():
                if dados.get('status') == 'pendente':
                    PKMotorV8(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db).iniciar()
                    # Opcional: requests.delete(f"{FIREBASE_URL}/{id_db}.json")
        time.sleep(10)
    except:
        time.sleep(20)
