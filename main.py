import requests
import time
import io
import json
from ftplib import FTP

# ================= CONFIGURAÇÕES =================
FTP_HOST = "ftpupload.net"
FTP_USER = "b6_41303686"
FTP_PASS = "SUA_SENHA_VPANEL"

GEMINI_KEY = "SUA_CHAVE_API_AQUI"

class PKScriptSaaS:
    def __init__(self, ra, digito, uf, senha):
        self.ra_completo = f"{ra}{digito}{uf}".upper()
        self.senha = senha
        self.session = requests.Session()
        self.auth_token = None
        self.ua = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36"

    def log_ftp(self, msg):
        print(f"[LOG] {msg}")
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                linha = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
                ftp.storbinary('APPE log.txt', io.BytesIO(linha.encode('utf-8')))
        except: pass

    def perguntar_ao_gemini(self, questao_texto):
        # CHAMADA DIRETA VIA HTTP (Não precisa de biblioteca especial)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {'Content-Type': 'application/json'}
        prompt = f"Resolva esta questão de múltipla escolha do CMSP. Responda APENAS o número do índice da alternativa (0 para a primeira, 1 para a segunda...). Questão: {questao_texto}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            res = requests.post(url, json=payload, headers=headers)
            data = res.json()
            resposta = data['candidates'][0]['content']['parts'][0]['text']
            # Extrai apenas o número
            res_clean = "".join(filter(str.isdigit, resposta))
            return res_clean[0] if res_clean else "0"
        except:
            return "0"

    def login(self):
        # Login SED
        url_sed = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi/credenciais/api/LoginCompletoToken"
        h1 = {"Ocp-Apim-Subscription-Key": "d701a2043aa24d7ebb37e9adf60d043b", "Content-Type": "application/json"}
        res = self.session.post(url_sed, json={"user": self.ra_completo, "senha": self.senha}, headers=h1)
        if res.status_code != 200: return False
        
        # Login CMSP
        token_sed = res.json().get("token")
        url_cmsp = "https://edusp-api.ip.tv/registration/edusp/token"
        res_c = self.session.post(url_cmsp, json={"token": token_sed}, headers={"Content-Type": "application/json", "x-api-realm": "edusp"})
        if res_c.status_code == 200:
            self.auth_token = res_c.json().get("auth_token")
            return True
        return False

    def executar(self):
        self.log_ftp(f"Iniciado para RA {self.ra_completo}")
        if not self.login():
            self.log_ftp("Erro: Login recusado.")
            return
        
        headers = {"x-api-key": self.auth_token, "x-api-realm": "edusp", "User-Agent": self.ua}
        res = self.session.get("https://edusp-api.ip.tv/tms/task/todo?limit=15", headers=headers)
        
        if res.status_code == 200:
            tarefas = res.json()
            for t in tarefas:
                t_id = t['id']
                titulo = t.get('title', 'Tarefa')
                idx_correta = self.perguntar_ao_gemini(titulo)
                
                url_ans = f"https://edusp-api.ip.tv/tms/task/{t_id}/answer"
                payload = {"answers": {"0": int(idx_correta)}, "last_question": True, "duration": 120}
                self.session.post(url_ans, json=payload, headers=headers)
                self.log_ftp(f"Feito: {titulo[:15]}... (IA: {idx_correta})")
                time.sleep(2)
            self.log_ftp("Concluído!")

def monitorar():
    print(">>> PK SCRIPT RODANDO (API DIRETA) <<<")
    while True:
        try:
            with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
                r = io.BytesIO()
                ftp.retrbinary('RETR dados.txt', r.write)
                conteudo = r.getvalue().decode('utf-8').strip().split('\n')
                if conteudo and conteudo[0] != "":
                    linha = conteudo[-1]
                    ftp.storbinary('STORE dados.txt', io.BytesIO(b"")) # Limpa
                    p = {x.split(': ')[0]: x.split(': ')[1] for x in linha.split(' | ')}
                    bot = PKScriptSaaS(p['RA'], p['DIGITO'], p['UF'], p['SENHA'])
                    bot.executar()
        except: pass
        time.sleep(10)

if __name__ == "__main__":
    monitorar()
