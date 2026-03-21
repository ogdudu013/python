import requests
import time
import sys
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class RoboSalaFinal:
    def __init__(self, ra, digito, uf, senha):
        # Formata o RA exatamente como o sistema SED exige
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.uf = uf.lower()
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.auth_token = None
        self.nick = None
        self.targets = ["1205", "1052", "1820", "764", "1834"]

    def perguntar_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return None

    def login(self):
        try:
            # 1. Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json={"user": self.ra_completo, "senha": self.senha},
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua},
                timeout=15
            )
            if res_sed.status_code != 200: 
                print(f"    [!] Erro SED: {res_sed.status_code} (RA/Senha Incorretos)")
                return False
            
            dados_sed = res_sed.json()
            self.nick = dados_sed.get("userName").lower()

            # 2. Login CMSP
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token",
                json={"token": dados_sed.get("token")},
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua},
                timeout=15
            )
            if res_cmsp.status_code == 200:
                self.auth_token = res_cmsp.json().get("auth_token")
                self.targets.append(f"{self.nick}-{self.uf}")
                return True
            return False
        except Exception as e:
            print(f"    [X] Erro na conexão de Login: {e}")
            return False

    def resolver_tudo(self):
        if not self.login(): return False

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json", "User-Agent": self.ua}
        params = [("expired_only", "false"), ("limit", "50"), ("filter_expired", "true"), ("answer_statuses", "pending"), ("answer_statuses", "draft"), ("with_answer", "true")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers, timeout=15)
            tarefas = res.json()
            print(f"    [i] {len(tarefas)} tarefas para resolver.")

            for task in tarefas:
                t_id, a_id, p_target = task['id'], task.get('answer_id'), task.get("publication_target")
                respostas_ia = {}

                # Tenta IA (Opcional)
                try:
                    url_q = f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}"
                    q_list = self.session.get(url_q, headers=headers).json().get('questions', [])
                    for q in q_list:
                        if q['type'] == 'single':
                            prompt = f"ID:{q['id']}\nPergunta:{q['statement']}\nOpções:{json.dumps(q['options'])}\nResponda apenas o ID da correta."
                            resp = "".join(filter(str.isdigit, str(self.perguntar_gemini(prompt))))
                            if resp in q['options']:
                                respostas_ia[str(q['id'])] = {"question_id": q['id'], "question_type": "single", "answer": {k: (k == resp) for k in q['options']}}
                except: pass

                payload = {"status": "submitted", "answers": respostas_ia, "accessed_on": "room", "executed_on": p_target, "duration": 185}
                
                # PUT ou POST
                if a_id:
                    self.session.put(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer/{a_id}", json=payload, headers=headers)
                else:
                    self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                
                print(f"    [V] Tarefa {t_id} enviada.")
                time.sleep(1.5)
            return True
        except Exception as e:
            print(f"    [!] Erro ao processar tarefas: {e}")
            return False

# --- LOOP PRINCIPAL COM PROTEÇÃO ANTI-TRAVAMENTO ---
print(">>> BOT PK SCRIPTS ONLINE <<<")
while True:
    try:
        r_fila = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        fila = r_fila.json()
        
        if fila:
            for id_db, d in fila.items():
                ra_aluno = d.get('ra')
                print(f"\n[FILA] Processando RA: {ra_aluno}")
                
                bot = RoboSalaFinal(ra_aluno, d.get('digito'), d.get('uf'), d.get('senha'))
                
                # Tenta executar. Independente de dar erro de login ou não, 
                # vamos remover da fila para não travar o bot infinitamente.
                resultado = bot.resolver_tudo()
                
                if resultado:
                    print(f"[SUCESSO] RA {ra_aluno} concluído.")
                else:
                    print(f"[ERRO] RA {ra_aluno} ignorado (Login ou Dados Inválidos).")
                
                # DELETA SEMPRE para evitar o loop infinito
                requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                print(f"[LIMPEZA] Removido do Firebase.")
                
                time.sleep(2)
                break 
    except Exception as e:
        print(f"\r[!] Aguardando conexão ou fila vazia...", end="")
    
    time.sleep(5)
