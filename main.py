import requests
import time
import io
import os
from ftplib import FTP
from google import genai
from google.genai import types

# ================= CONFIGURAÇÕES =================
# FTP ByetHost
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

# Gemini API
GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk"
client_ai = genai.Client(api_key=GEMINI_KEY)

class PKScriptSaaS:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile"

    def log_ftp(self, msg):
        print(f"[LOG] {msg}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                linha = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
                ftp.storbinary('APPE log.txt', io.BytesIO(linha.encode('utf-8')))
        except: pass

    def login(self):
        # Passo 1: SED
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h1 = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        res = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h1)
        
        if res.status_code != 200: return False
        
        # Passo 2: CMSP
        token_sed = res.json().get("token")
        url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
        h2 = {"Content-Type": "application/json", "x-api-realm": "edusp"}
        res_c = self.session.post(url_cmsp, json={"token": token_sed}, headers=h2)
        
        if res_c.status_code == 200:
            self.auth_token = res_c.json().get("auth_token")
            return True
        return False

    def perguntar_ao_gemini(self, questao_texto):
        prompt = f"""
        Você é um assistente escolar. Resolva a seguinte questão de múltipla escolha.
        Responda APENAS com o ID da alternativa correta (ex: 0, 1, 2...).
        Questão: {questao_texto}
        """
        try:
            response = client_ai.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
                config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="HIGH"))
            )
            # Limpa a resposta para pegar apenas o número
            return response.text.strip()
        except:
            return "0" # Default para a primeira se falhar

    def executar(self):
        self.log_ftp(f"Iniciado para RA {self.ra_completo}")
        if not self.login():
            self.log_ftp("Erro: Login recusado.")
            return

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        # Pega tarefas pendentes (simplificado)
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=20", headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            self.log_ftp(f"{len(tarefas)} tarefas encontradas.")
            
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Sem título')
                
                # 1. Obter detalhes da questão (para o Gemini ler)
                # Nota: Em algumas versões da API, o conteúdo está em t['content']
                pergunta = f"Título: {titulo}" 
                
                # 2. Gemini resolve
                idx_correta = self.perguntar_ao_gemini(pergunta)
                
                # 3. Enviar resposta
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {
                    "answers": { "0": int(idx_correta) if idx_correta.isdigit() else 0 },
                    "last_question": True,
                    "duration": 120
                }
                
                self.session.post(url_ans, json=payload, headers=headers)
                self.log_ftp(f"Resolvida: {titulo[:15]}... (IA escolheu {idx_correta})")
                time.sleep(2)
            
            self.log_ftp("Concluído com sucesso!")

# --- LOOP DE MONITORAMENTO ---
def monitorar():
    print("PK SCRIPT ONLINE - AGUARDANDO LOGIN VIA SITE...")
    while True:
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                r = io.BytesIO()
                ftp.retrbinary('RETR dados.txt', r.write)
                dados = r.getvalue().decode('utf-8').strip().split('\n')
                
                if dados and dados[0] != "":
                    linha = dados[-1]
                    # Limpa o arquivo para o próximo
                    ftp.storbinary('STORE dados.txt', io.BytesIO(b""))
                    
                    # Parse
                    p = {x.split(': ')[0]: x.split(': ')[1] for x in linha.split(' | ')}
                    bot = PKScriptSaaS(p['RA'], p['DIGITO'], p['UF'], p['SENHA'])
                    bot.executar()
        except Exception as e:
            print(f"Erro no loop: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    monitorar()
