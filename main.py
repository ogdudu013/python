import requests
import time
import sys
import traceback # Importante para ver o erro real

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBotFila:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def login(self):
        print(f"    [>] Tentando login SED para: {self.ra_completo}")
        try:
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}, timeout=15)
            
            if res_sed.status_code != 200:
                print(f"    [X] Erro SED: Status {res_sed.status_code}")
                return False

            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": res_sed.json().get("token")}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}, timeout=15)
            
            if res_cmsp.status_code == 200:
                self.auth_token = res_cmsp.json().get("auth_token")
                print("    [V] Login CMSP OK.")
                return True
            print(f"    [X] Erro CMSP: Status {res_cmsp.status_code}")
        except Exception as e:
            print(f"    [X] Exceção no Login: {e}")
        return False

    def executar(self):
        if not self.login(): return False
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
        params = {"limit": "20", "filter_expired": "true", "answer_statuses": "pending"}

        print("    [>] Buscando tarefas...")
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers, timeout=15)
        
        if res.status_code == 200:
            tarefas = [t for t in res.json() if t.get('task_expired') is False]
            print(f"    [i] {len(tarefas)} tarefas reais encontradas.")
            
            if len(tarefas) == 0:
                return True # Retorna True para apagar da fila mesmo se não tiver tarefas

            for task in tarefas:
                print(f"    [*] Resolvendo: {task.get('title')}")
                # Aqui você colocaria a lógica de responder...
                time.sleep(1) 
            return True
        return False

# --- LOOP COM TRACEBACK ---
print(">>> MONITORANDO FILA <<<")
while True:
    try:
        response = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = response.json()
        
        if fila:
            id_db = list(fila.keys())[0]
            dados = fila[id_db]
            print(f"\n[+] RA Detectado: {dados['ra']}")
            
            bot = PKScriptBotFila(dados['ra'], dados['digito'], dados['uf'], dados['senha'])
            
            # Se a função executar() retornar True, apaga do Firebase
            if bot.executar():
                requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                print(f"[OK] RA {dados['ra']} concluído e removido.")
            else:
                print(f"[!] Falha na execução. Verifique os dados acima.")
                # Opcional: descomente a linha abaixo para apagar mesmo com erro (limpar fila)
                # requests.delete(f"{FIREBASE_URL}/{id_db}.json") 

    except Exception:
        print("\n--- ERRO DETECTADO NO PYTHON ---")
        traceback.print_exc() # Isso vai te dizer a linha exata do erro
        print("--------------------------------\n")
        
    time.sleep(5)
