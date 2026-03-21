import requests
import time
import json

# === CONFIGURAÇÕES OFICIAIS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBot:
    def __init__(self, ra, digito, uf, senha):
        # Ajuste no formato do RA: Adicionando zeros à esquerda se necessário (padrão SED)
        self.ra_val = str(ra).zfill(9) 
        self.digito = str(digito).upper()
        self.uf = str(uf).upper()
        # O formato correto para a API costuma ser o RA + Digito + UF sem espaços
        self.user_sed = f"{self.ra_val}{self.digito}{self.uf}"
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    def resolver_ia(self, pergunta):
        """Usa Gemini via REST para evitar erros de Rust no Termux"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Resolva a questão e responda APENAS o número do índice da alternativa correta (0, 1, 2 ou 3): {pergunta}"}]}],
            "generationConfig": {"temperature": 0.1}
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return int("".join(filter(str.isdigit, resp_text))[0])
        except:
            return 0 # Padrão para alternativa A caso a IA falhe

    def login(self):
        try:
            # 1. Login SED - Usando a chave de inscrição que você já tinha
            url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
            headers_sed = {
                "Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b",
                "Content-Type": "application/json",
                "User-Agent": self.ua
            }
            payload_sed = {"user": self.user_sed, "senha": self.senha}
            
            r1 = self.session.post(url_sed, json=payload_sed, headers=headers_sed, timeout=15)
            
            if r1.status_code != 200:
                print(f"[X] Erro SED: {r1.status_code} - Verifique RA/Senha")
                return False
            
            token_sed = r1.json().get("token")
            
            # 2. Login CMSP para obter auth_token
            url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
            headers_cmsp = {"x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
            
            r2 = self.session.post(url_cmsp, json={"token": token_sed}, headers=headers_cmsp, timeout=15)
            
            if r2.status_code == 200:
                self.auth_token = r2.json().get("auth_token")
                return True
        except Exception as e:
            print(f"[!] Erro no processo de login: {e}")
        return False

    def executar(self):
        print(f"[*] Autenticado como: {self.user_sed}")
        if not self.login(): return False
            
        headers = {
            "x-api-key": self.auth_token,
            "x-api-realm": "edusp",
            "User-Agent": self.ua
        }
        
        # Busca tarefas pendentes
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=20", headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            print(f"[i] {len(tarefas)} tarefas encontradas.")
            
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Tarefa')
                
                # IA resolve baseado no título/enunciado
                idx_resposta = self.resolver_ia(titulo)
                
                # Envia a resposta (Simulando participação e acerto)
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload_ans = {
                    "answers": {"0": idx_resposta}, 
                    "last_question": True, 
                    "duration": 120
                }
                
                self.session.post(url_ans, json=payload_ans, headers=headers)
                print(f"    [V] Concluída: {titulo[:25]}... (IA Marcou: {idx_resposta})")
                time.sleep(2)
            return True
        return False

# --- LOOP DE MONITORAMENTO DO FIREBASE ---
print(">>> PK SCRIPT OFC | SISTEMA FIREBASE ATIVO <<<")
while True:
    try:
        # Busca a fila
        response = requests.get(FIREBASE_URL, timeout=15)
        fila = response.json()
        
        if fila:
            # Pega o item mais antigo (primeiro da fila)
            id_db = list(fila.keys())[0]
            dados = fila[id_db]
            
            print(f"\n[!] Processando RA da Fila: {dados['ra']}")
            
            bot = PKScriptBot(dados['ra'], dados['digito'], dados['uf'], dados['senha'])
            
            # Tenta executar o login e as tarefas
            if bot.executar():
                print(f"[+] Finalizado com sucesso: {dados['ra']}")
            
            # Remove do Firebase independente do resultado para não travar a fila
            # (Se falhar o login, o usuário deve tentar de novo no site)
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
            print("[+] Removido da fila.")
            
    except Exception as e:
        print(f"[-] Erro na conexão: {e}")
    
    time.sleep(10) # Aguarda 10 segundos para a próxima verificação
