(async function() {
    // 1. Substitua pela sua chave real ou deixe o prompt
    const KEY = 'SUA_CHAVE_AQUI'; 

    // 2. Criar o painel visual
    const div = document.createElement('div');
    div.style = "position:fixed;top:10px;right:10px;width:300px;z-index:999999;background:#fff;color:#000;padding:15px;border-radius:10px;border:2px solid #4285f4;box-shadow:0 4px 15px #000;font-family:sans-serif";
    div.innerHTML = `<b>🤖 Gemini:</b><div id="g-res">Analisando questão...</div><button onclick="this.parentElement.remove()" style="width:100%;margin-top:10px">Fechar</button>`;
    document.body.appendChild(div);

    const res = document.getElementById('g-res');
    const promptTexto = "Resolva esta questão de forma curta:\n" + document.body.innerText.substring(0, 2500);

    try {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${KEY}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ contents: [{ parts: [{ text: promptTexto }] }] })
        });
        const data = await response.json();
        res.innerHTML = data.candidates[0].content.parts[0].text.replace(/\n/g, '<br>');
    } catch (e) {
        res.innerText = "Erro ao chamar a API. Verifique a chave.";
    }
})();
