import requests
import time
import io
import json
from ftplib import FTP

# ================= CONFIGURAÇÕES (PREENCHA AQUI) =================
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "0512pablo"

GEMINI_KEY = "AIzaSyCzUldmRFcer6FlHJTmD3mLSadgNF-4Sjk" # Consiga em: aistudio.google.com

class PKScriptSaaS:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36"

    def log_ftp(self, msg):
        """ Envia logs para o log.txt que aparece no seu iframe PHP """
        print(f"[LOG] {msg}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                linha = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
                ftp.storbinary('APPE log.txt', io.BytesIO(linha.encode('utf-8')))
        except Exception as e:
            print(f"Erro FTP Log: {e}")

    def perguntar_ao_gemini(self, titulo_tarefa):
        """ Resolve a questão usando a API do Gemini via HTTP (sem bibliotecas pesadas) """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = f"Você é um bot escolar. Resolva a tarefa: '{titulo_tarefa}'. Responda APENAS o número do índice da alternativa correta (0 para a primeira, 1 para a segunda, etc). Não escreva texto, apenas o número."
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, json=payload, timeout=10)
            resposta = res.json()['candidates'][0]['content']['parts'][0]['text']
            num = "".join(filter(str.isdigit, resposta))
            return int(num[0]) if num else 0
        except:
            return 0

    def login(self):
        # 1. Login SED
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h1 = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        res = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h1)
        
        if res.status_code != 200: return False
        
        # 2. Login CMSP
        token_sed = res.json().get("token")
        url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
        res_c = self.session.post(url_cmsp, json={"token": token_sed}, headers={"x-api-realm": "edusp"})
        
        if res_c.status_code == 200:
            self.auth_token = res_c.json().get("auth_token")
            return True
        return False

    def executar(self):
        self.log_ftp(f"Iniciando RA {self.ra_completo}...")
        if not self.login():
            self.log_ftp("Erro: RA ou Senha inválidos.")
            return

        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=15", headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            self.log_ftp(f"Total: {len(tarefas)} tarefas.")
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Tarefa')
                
                # IA entra em ação
                escolha = self.perguntar_ao_gemini(titulo)
                
                # Enviar resposta
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {"answers": {"0": escolha}, "last_question": True, "duration": 100}
                self.session.post(url_ans, json=payload, headers=headers)
                
                self.log_ftp(f"OK: {titulo[:15]}... (IA: {escolha})")
                time.sleep(1.5)
            self.log_ftp(">>> Processo concluído!")

def monitorar_ftp():
    print(">>> PK SCRIPT AGUARDANDO COMANDOS NO SITE <<<")
    while True:
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                r = io.BytesIO()
                ftp.retrbinary('RETR dados.txt', r.write)
                dados = r.getvalue().decode('utf-8').strip().split('\n')
                
                if dados and len(dados[0]) > 5:
                    linha = dados[-1] # Pega o último login
                    # Limpa o arquivo para o bot não repetir
                    ftp.storbinary('STORE dados.txt', io.BytesIO(b""))
                    
                    # Extrai dados do seu PHP: "RA: 123 | DIGITO: 1 | UF: SP | SENHA: 123"
                    p = {x.split(': ')[0].strip(): x.split(': ')[1].strip() for x in linha.split(' | ')}
                    
                    bot = PKScriptSaaS(p['RA'], p['DIGITO'], p['UF'], p['SENHA'])
                    bot.executar()
        except:
            pass
        time.sleep(10) # Verifica o site a cada 10 segundos

if __name__ == "__main__":
    monitorar_ftp()
