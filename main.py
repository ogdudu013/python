import requests
import time
import json

# === CONFIGURAÇÕES OFICIAIS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        # Limpa espaços e garante o formato string
        self.ra_val = str(ra).strip().zfill(9)
        self.digito = str(digito).strip().upper()
        self.uf = str(uf).strip().upper()
        self.user_sed = f"{self.ra_val}{self.digito}{self.uf}"
        self.senha = str(senha).strip()
        
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def resolver_ia(self, pergunta):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Responda apenas o número da alternativa (0 a 3): {pergunta}"}]}],
            "generationConfig": {"temperature": 0.1}
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return int("".join(filter(str.isdigit, resp_text))[0])
        except:
            return 0

    def login(self):
        try:
            # 1. Login SED
            url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
            headers_sed = {
                "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
                "Content-Type": "application/json",
                "User-Agent": self.ua
            }
            # Importante: algumas versões da API exigem o RA com 12 dígitos (com zeros à esquerda)
            payload_sed = {"user": self.user_sed, "senha": self.senha}
            
            print(f"[*] Tentando login SED para: {self.user_sed}")
            r1 = self.session.post(url_sed, json=payload_sed, headers=headers_sed, timeout=15)
            
            if r1.status_code != 200:
                print(f"[X] Falha na SED: Status {r1.status_code}. Verifique RA/Senha.")
                return False
            
            token_sed = r1.json().get("token")
            if not token_sed:
                print("[X] SED não retornou Token.")
                return False
            
            print("[V] Login SED OK. Gerando Token CMSP...")

            # 2. Login CMSP
            url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
            headers_cmsp = {
                "x-api-realm": "edusp",
                "Content-Type": "application/json",
                "User-Agent": self.ua
            }
            
            r2 = self.session.post(url_cmsp, json={"token": token_sed}, headers=headers_cmsp, timeout=15)
            
            if r2.status_code == 200:
                self.auth_token = r2.json().get("auth_token")
                print("[V] Autenticação Completa!")
                return True
            else:
                print(f"[X] Erro CMSP: {r2.status_code}")
                return False

        except Exception as e:
            print(f"[!] Erro técnico no login: {e}")
            return False

    def executar(self):
        if not self.login(): 
            return False
            
        headers = {
            "x-api-key": self.auth_token,
            "x-api-realm": "edusp",
            "User-Agent": self.ua
        }
        
        # Puxa tarefas
        print("[*] Buscando tarefas pendentes...")
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=20", headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            if not tarefas:
                print("[i] Nenhuma tarefa encontrada para este RA.")
                return True

            print(f"[i] {len(tarefas)} tarefas detectadas.")
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Tarefa')
                idx = self.resolver_ia(titulo)
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {"answers": {"0": idx}, "last_question": True, "duration": 100}
                
                self.session.post(url_ans, json=payload_ans, headers=headers)
                print(f"    [OK] Resolvida: {titulo[:20]}...")
                time.sleep(2)
            return True
        else:
            print(f"[X] Erro ao listar tarefas: {res.status_code}")
            return False

# --- MONITORAMENTO ---
print(">>> PK SCRIPT OFC | AGUARDANDO FILA <<<")
while True:
    try:
        response = requests.get(FIREBASE_URL, timeout=15)
        fila = response.json()
        
        if fila:
            id_db = list(fila.keys())[0]
            d = fila[id_db]
            
            print(f"\n[!] Processando RA: {d['ra']}")
            bot = PKScriptBot(d['ra'], d['digito'], d['uf'], d['senha'])
            
            if bot.executar():
                print(f"[+] Processo finalizado para {d['ra']}")
            else:
                print(f"[!] Não foi possível concluir o RA {d['ra']}")
            
            # Deleta para seguir a fila
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
            print("[+] Item removido da fila.")
            
    except Exception as e:
        print(f"[-] Erro de conexão/fila: {e}")
    
    time.sleep(10)
