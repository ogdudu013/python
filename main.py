import requests
import time

class TarefasBot:
    def __init__(self, ra, digito, senha):
        self.username = f"{ra}{digito}sp"
        self.senha = senha
        self.session = requests.Session()
        self.sub_key = "d701a2043aa24d7ebb37e9adf60d043b"
        self.token_sed = None
        self.token_iptv = None

    def login(self):
        # 1. Login na SED via o Proxy que você descobriu
        url = "https://taskitos.cupiditys.lol/p/https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        payload = {"user": self.username, "senha": self.senha}
        headers = {"ocp-apim-subscription-key": self.sub_key}
        
        response = self.session.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            self.token_sed = response.json().get("token")
            print(f"[*] Login SED Sucesso: {response.json()['DadosUsuario']['NAME']}")
            return True
        return False

    def get_iptv_token(self):
        # 2. Troca de Token para IP.TV
        url = "https://edusp-api.ip.tv/registration/edusp/token"
        payload = {"token": self.token_sed}
        headers = {"x-api-realm": "edusp", "x-api-platform": "webclient"}
        
        response = self.session.post(url, json=payload, headers=headers)
        self.token_iptv = response.json().get("auth_token")
        return self.token_iptv is not None

    def realizar_tarefas(self):
        # 3. Listar tarefas pendentes
        url_list = "https://edusp-api.ip.tv/tms/task/todo?limit=10"
        headers = {"Authorization": self.token_iptv, "x-api-realm": "edusp"}
        
        tarefas = self.session.get(url_list, headers=headers).json()
        
        for item in tarefas.get('items', []):
            print(f"[!] Resolvendo: {item['title']}")
            
            # 4. Enviar a resposta (O 'pulo do gato')
            # Geralmente é um POST para /answer com o ID da tarefa
            answer_url = f"https://edusp-api.ip.tv/tms/task/{item['id']}/answer"
            # O payload aqui depende de como a tarefa é estruturada (múltipla escolha, etc)
            # Exemplo genérico de conclusão:
            answer_payload = {"answers": {}, "last_question": True} 
            
            res = self.session.post(answer_url, json=answer_payload, headers=headers)
            if res.status_code == 200:
                print(f"[V] Tarefa concluída!")
            time.sleep(1) # Delay para não ser bloqueado por spam

# --- Execução ---
bot = TarefasBot("110877468", "4", "SuaSenhaAqui")
if bot.login():
    if bot.get_iptv_token():
        bot.realizar_tarefas()
