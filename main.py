import requests
import time
import json

# === CONFIGURAÇÕES ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila.json"
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKScriptBotUltra:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        # Targets base extraídos do seu log
        self.targets = ["r36cbf99f7e282664c-l", "rf5f73a6b29568391d-l", "1205", "1052", "1820", "764", "1834"]

    def perguntar_ia(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            return "0"

    def login(self):
        try:
            # 1. Login SED
            res_sed = self.session.post(
                "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                json={"user": self.ra_completo, "senha": self.senha}, 
                headers={"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json", "User-Agent": self.ua}
            )
            if res_sed.status_code != 200: return False
            token_sed = res_sed.json().get("token")

            # 2. Login CMSP (Obtendo Auth Token e Targets Dinâmicos)
            res_cmsp = self.session.post(
                "https://edusp-api.ip.tv/registration/edusp/token", 
                json={"token": token_sed}, 
                headers={"Content-Type": "application/json", "x-api-realm": "edusp", "x-api-platform": "webclient", "User-Agent": self.ua}
            )
            
            if res_cmsp.status_code == 200:
                dados = res_cmsp.json()
                self.auth_token = dados.get("auth_token")
                # Mescla os targets fixos com os que o aluno já tem
                novos_targets = dados.get("publication_targets", [])
                self.targets = list(set(self.targets + novos_targets))
                print(f"[V] Login realizado. {len(self.targets)} canais de tarefas mapeados.")
                return True
        except Exception as e:
            print(f"[X] Erro no login: {e}")
        return False

    def resolver_questoes(self, task_data):
        """Mapeia cada questão pelo ID real e gera a resposta via IA"""
        answers = {}
        questions = task_data.get('questions', [])
        
        for q in questions:
            q_id = str(q.get('id'))
            q_type = q.get('type')
            statement = q.get('statement', '')
            
            if q_type == 'info': continue # Pula slides informativos

            if q_type == 'single':
                # Múltipla Escolha: IA retorna apenas o índice (0, 1, 2...)
                prompt = f"Questão: {statement}. Responda apenas o número da alternativa correta (0, 1, 2, 3 ou 4)."
                resp = self.perguntar_ia(prompt)
                idx = "".join(filter(str.isdigit, resp))
                answers[q_id] = int(idx) if idx else 0
            
            elif q_type in ['text_ai', 'essay']:
                # Dissertativa: IA escreve o texto
                prompt = f"Escreva uma resposta curta e escolar para a questão: {statement}"
                answers[q_id] = self.perguntar_ia(prompt)
            
            elif q_type in ['cloud', 'fill-words', 'true-false']:
                # Outros tipos: Enviamos as opções padrão para validar
                if 'options' in q and 'words' in q['options']:
                    answers[q_id] = q['options']['words']
                else:
                    answers[q_id] = [0, 1]

        return answers

    def executar(self):
        if not self.login(): 
            print("[X] Falha na autenticação.")
            return False
        
        headers = {
            "x-api-key": self.auth_token, 
            "x-api-realm": "edusp", 
            "x-api-platform": "webclient", 
            "User-Agent": self.ua
        }

        # Busca a lista de tarefas pendentes
        params = [("limit", "100"), ("answer_statuses", "pending"), ("answer_statuses", "draft")]
        for t in self.targets: params.append(("publication_target", t))

        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            total = len(tarefas)
            print(f"[i] {total} tarefas encontradas no total.")
            
            for task in tarefas:
                t_id = task['id']
                titulo = task.get('title', 'Sem Título')
                
                # 1. Abre a tarefa para pegar os IDs das questões (Apply)
                try:
                    detalhes = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply", headers=headers).json()
                except:
                    print(f"[!] Erro ao abrir tarefa {t_id}. Pulando...")
                    continue

                print(f"\n[*] Resolvendo: {titulo}")
                respostas = self.resolver_questoes(detalhes)
                
                # 2. ESPERA OBRIGATÓRIA (Mínimo 3 minutos = 180 segundos)
                # Isso faz com que a SED valide a tarefa de verdade
                tempo_espera = 185 
                print(f"    [!] Aguardando {tempo_espera}s de tempo de segurança...")
                time.sleep(tempo_espera)
                
                # 3. Envia a resposta final
                payload = {
                    "answers": respostas, 
                    "last_question": True, 
                    "duration": tempo_espera
                }
                
                final = self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                
                if final.status_code == 200:
                    print(f"    [V] Concluída com Sucesso.")
                else:
                    print(f"    [X] Erro ao entregar: {final.status_code}")
                
            return True
        return False

# --- LOOP DE MONITORAMENTO FIREBASE ---
print(">>> PK SCRIPT ULTRA ATIVADO <<<")
print("Aguardando novas entradas na fila do Firebase...")

while True:
    try:
        response = requests.get(FIREBASE_URL, timeout=15)
        fila = response.json()
        
        if fila:
            # Pega o primeiro RA da fila
            id_db = list(fila.keys())[0]
            dados = fila[id_db]
            
            print(f"\n" + "="*40)
            print(f"[NOVO TRABALHO] RA: {dados['ra']}")
            
            bot = PKScriptBotUltra(dados['ra'], dados['digito'], dados['uf'], dados['senha'])
            bot.executar()
            
            # Remove da fila após terminar todas as tarefas do aluno
            requests.delete(f"https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila/{id_db}.json")
            print(f"[OK] RA {dados['ra']} finalizado e removido da fila.")
            print("="*40 + "\n")
            
    except Exception as e:
        print(f"[ERRO NO LOOP]: {e}")
        
    time.sleep(10) # Verifica a fila a cada 10 segundos
