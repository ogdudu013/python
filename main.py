import requests

# Configurações extraídas dos seus headers
SUB_KEY = "d701a2043aa24d7ebb37e9adf60d043b"
BASE_URL = "https://sedintegracoes.educacao.sp.gov.br/saladofuturobffapi"

def executar_login_real(ra_completo, senha):
    session = requests.Session()
    
    # 1. Endpoint de Login que você capturou
    url_login = f"{BASE_URL}/credenciais/api/LoginCompletoToken"
    
    payload = {
        "user": ra_completo, # Ex: "1108774684SP"
        "senha": senha
    }
    
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": SUB_KEY,
        "Accept": "application/json, text/plain, */*"
    }

    print(f"[*] Tentando login para {ra_completo}...")
    response = session.post(url_login, json=payload, headers=headers)

    if response.status_code == 200:
        dados = response.json()
        token = dados.get("token")
        user_id = dados["DadosUsuario"]["CD_USUARIO"]
        print(f"[+] Sucesso! Token gerado para {dados['DadosUsuario']['NAME']}")
        
        # Agora podemos usar esse token para outras chamadas
        return session, token, user_id
    else:
        print(f"[!] Erro no login: {response.status_code}")
        return None, None, None

def listar_bimestres(session, token, escola_id):
    # Endpoint de Bimestres que aparece no seu log
    url = f"{BASE_URL}/apihubintegracoes/api/v2/Bimestre/ListarBimestres?escolaId={escola_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": SUB_KEY
    }
    
    res = session.get(url, headers=headers)
    if res.status_code == 200:
        bimestres = res.json().get("data", [])
        print(f"\n[i] Bimestres encontrados para a escola {escola_id}:")
        for b in bimestres:
            print(f" - Bimestre {b['NumeroBimestre']} (Início: {b['DataInicio'][:10]})")

# --- EXECUÇÃO ---
# Substitua pela sua senha real para testar localmente
RA_TESTE = "1108774684SP"
SENHA_TESTE = "Pp@12345678" 

sessao, meu_token, meu_id = executar_login_real(RA_TESTE, SENHA_TESTE)

if sessao:
    # Testando a listagem de bimestres com seu ID de escola real (12178)
    listar_bimestres(sessao, meu_token, 12178)
