(async function() {
    // Tenta pegar a chave de um prompt para não deixar exposta no GitHub
    // Ou substitua 'SUA_CHAVE' pela sua chave real se o repo for privado
    const API_KEY = window.GEMINI_KEY || prompt("Insira sua Gemini API Key:");
    if (!API_KEY) return;

    // Interface Visual
    const ui = document.createElement('div');
    ui.id = "gemini-ui";
    ui.style = "position:fixed;top:10px;right:10px;width:300px;z-index:999999;background:white;padding:15px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.2);font-family:sans-serif;border:2px solid #4285f4;color:black;";
    ui.innerHTML = `<b>🤖 Gemini Assistente</b><div id="gemini-res" style="margin-top:10px;font-size:13px;">Buscando questões...</div><button onclick="this.parentElement.remove()" style="width:100%;margin-top:10px;cursor:pointer">Fechar</button>`;
    document.body.appendChild(ui);

    const resDiv = document.getElementById('gemini-res');

    // Captura o texto da página (ajustado para focar em questões)
    const pageText = document.body.innerText.substring(0, 3000); 

    try {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{
                    parts: [{ text: "Analise a página e resolva as questões encontradas. Seja direto e indique apenas a alternativa correta ou a resposta curta:\n\n" + pageText }]
                }]
            })
        });

        const data = await response.json();
        
        if (data.error) {
            resDiv.innerHTML = `<span style="color:red">Erro: ${data.error.message}</span>`;
        } else {
            const answer = data.candidates[0].content.parts[0].text;
            resDiv.innerHTML = `<div style="background:#f0f7ff;padding:8px;border-radius:4px;">${answer.replace(/\n/g, '<br>')}</div>`;
        }
    } catch (err) {
        resDiv.innerHTML = "Erro ao conectar com a API.";
    }
})();
