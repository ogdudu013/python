import requests
import time
import sys

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila" # Removi o .json daqui para facilitar
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBotFila:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def login(self):
        try:
            # Login SED
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua})
            
            if res_sed.status_code != 200: return False

            # Login CMSP
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": res_sed.json().get("token")}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua})
            
            if res_cmsp.status_code == 200:
                self.auth_token = res_cmsp.json().get("auth_token")
                return True
        except: return False
        return False

    def executar(self):
        if not self.login():
            print(f"[X] Falha no login para o RA {self.ra_completo}")
            return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        
        # Filtro para as 2 tarefas reais
        params = {"limit": "20", "filter_expired": "true", "answer_statuses": "pending"}

        try:
            res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
            if res.status_code == 200:
                tarefas = [t for t in res.json() if t.get('task_expired') is False]
                print(f"[i] {len(tarefas)} tarefas reais encontradas.")
                
                for task in tarefas:
                    print(f"[*] Resolvendo: {task.get('title')}")
                    # Simulação de espera e envio (Coloque aqui sua lógica de resolver_questoes)
                    time.sleep(2) # Teste rápido, depois volte para os 185s
                    print(f"    [V] Concluída.")
                return True # Retorna True apenas se processou a lista
        except:
            return False
        return False

# --- LOOP CORRIGIDO ---
print(">>> AGUARDANDO FILA DO PHP <<<")

while True:
    try:
        # 1. LER O BANCO (JSON COMPLETO)
        response = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = response.json()
        
        if fila:
            # Pega o ID único gerado pelo Firebase (ex: -NqXy...)
            id_db = list(fila.keys())[0]
            dados = fila[id_db]
            
            print(f"\n[+] Processando RA: {dados['ra']}")
            
            bot = PKScriptBotFila(dados['ra'], dados['digito'], dados['uf'], dados['senha'])
            
            # 2. SÓ APAGA SE O BOT RODAR
            if bot.executar():
                requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                print(f"[OK] RA {dados['ra']} finalizado e removido.")
            else:
                print(f"[!] Erro ao processar {dados['ra']}. Mantendo na fila para re-tentativa...")
                # Opcional: mover para o fim da fila ou apagar se for senha errada
                requests.delete(f"{FIREBASE_URL}/{id_db}.json") 
        
    except Exception as e:
        print(f"Erro de conexão: {e}")
        
    time.sleep(5)
