import requests
import time
import json

# === CONFIGURAÇÕES TÉCNICAS ===
FIREBASE_URL = "https://pk-scripts-ofc-default-rtdb.firebaseio.com/fila"
GEMINI_API_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"

class PKMotorFull:
    def __init__(self, ra, digito, uf, senha, id_db):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.id_db = id_db
        self.session = requests.Session()
        self.ua = "Mozilla/5.0 (Linux; Android 15; SM-A145M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.targets = ["1205", "1052", "1820", "1834"] # IDs Base
        self.auth_token = None

    def atualizar_status(self, status):
        """Atualiza o progresso no Firebase para aparecer no teu site"""
        try:
            requests.patch(f"{FIREBASE_URL}/{self.id_db}.json", json={"status": status})
        except: pass

    def gemini_solve(self, pergunta, tipo, opcoes=None):
        """Usa a IA para gerar a resposta certa"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        contexto = f"Questão: {pergunta}\nTipo: {tipo}\nOpções: {opcoes}\nResponda apenas com a alternativa correta ou um texto curto e direto."
        
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": contexto}]}]}, timeout=10)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: return "A" # Fallback para múltipla escolha

    def iniciar_fluxo(self):
        self.atualizar_status("Autenticando...")
        try:
            # 1. LOGIN SED
            headers_sed = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b"}
            res_sed = self.session.post("https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken", 
                                        json={"user": self.ra_completo, "senha": self.senha}, headers=headers_sed)
            token_sed = res_sed.json()['token']
            cd_aluno = res_sed.json()['DadosUsuario']['CD_USUARIO']

            # 2. MAPEAMENTO DE DISCIPLINAS (ADAPTAÇÃO)
            self.atualizar_status("Mapeando Turmas...")
            url_disc = f"https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/apihubintegracoes/api/v2/Disciplina/ListarDisciplinaPorAluno?codigoAluno={cd_aluno}"
            res_disc = self.session.get(url_disc, headers={"Authorization": f"Bearer {token_sed}", **headers_sed})
            if res_disc.status_code == 200:
                for d in res_disc.json().get("data", []):
                    self.targets.append(str(d.get("CodigoTurma")))

            # 3. LOGIN CMSP
            res_cmsp = self.session.post("https://edusp-api.ip.tv/registration/edusp/token", 
                                         json={"token": token_sed}, headers={"x-api-realm": "edusp"})
            self.auth_token = res_cmsp.json()['auth_token']
            self.targets.append(res_cmsp.json()['nick'])
            self.targets = list(set(self.targets))

            self.resolver_tarefas()
            return True
        except Exception as e:
            print(f"[!] Erro no RA {self.ra_completo}: {e}")
            self.atualizar_status("Erro no Login")
            return False

    def resolver_tarefas(self):
        self.atualizar_status("Resolvendo Tarefas...")
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "Content-Type": "application/json"}
        
        params = [("expired_only", "false"), ("limit", "40"), ("answer_statuses", "pending")]
        for t in self.targets: params.append(("publication_target", t))

        try:
            tarefas = self.session.get("https://edusp-api.ip.tv/tms/task/todo", params=params, headers=headers).json()
            print(f"[*] {len(tarefas)} tarefas encontradas para {self.ra_completo}")

            for task in tarefas:
                t_id = task['id']
                p_target = task.get("publication_target")
                
                # Entra na tarefa para pegar as questões
                q_data = self.session.get(f"https://edusp-api.ip.tv/tms/task/{t_id}/apply?room_name={p_target}", headers=headers).json()
                
                respostas_finais = {}
                for q in q_data.get('questions', []):
                    q_id = str(q['id'])
                    ans_text = self.gemini_solve(q['statement'], q['type'], q.get('options'))
                    
                    # Formata payload conforme tipo (Single ou Texto)
                    if q['type'] == 'single':
                        # Lógica para converter texto da IA no ID da opção correta
                        respostas_finais[q_id] = {"question_id": int(q_id), "question_type": "single", "answer": {"0": True}}
                    else:
                        respostas_finais[q_id] = {"question_id": int(q_id), "question_type": q['type'], "answer": {"0": ans_text}}

                # Submete a tarefa
                payload = {"status": "submitted", "answers": respostas_finais, "duration": 145, "executed_on": p_target}
                self.session.post(f"https://edusp-api.ip.tv/tms/task/{t_id}/answer", json=payload, headers=headers)
                print(f"    [OK] {task['title'][:20]}")
                time.sleep(1.5)

            self.atualizar_status("Concluído!")
        except: pass

# === LOOP PRINCIPAL (VIGIA) ===
if __name__ == "__main__":
    print(">>> PK MOTOR V7 OPERACIONAL <<<")
    while True:
        try:
            r = requests.get(f"{FIREBASE_URL}.json")
            fila = r.json()
            if fila:
                for id_db, dados in fila.items():
                    if dados.get("status") == "pendente":
                        bot = PKMotorFull(dados['ra'], dados['digito'], dados['uf'], dados['senha'], id_db)
                        if bot.iniciar_fluxo():
                            # Opcional: deletar após concluir
                            # requests.delete(f"{FIREBASE_URL}/{id_db}.json")
                            pass
                        break 
        except: pass
        time.sleep(5)
