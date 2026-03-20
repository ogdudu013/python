javascript:(function(){
    if(document.getElementById('ai-extractor-v3')) {
        alert('O extrator já está rodando!');
        return;
    }

    /* --- ESTILIZAÇÃO DO PAINEL --- */
    const style = document.createElement('style');
    style.innerHTML = `
        #ai-extractor-v3 { position: fixed; top: 5px; right: 5px; width: 330px; height: 480px; background: #000; color: #00ff41; font-family: 'Courier New', monospace; z-index: 2147483647; border: 1px solid #00ff41; border-radius: 4px; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0, 255, 65, 0.2); font-size: 11px; user-select: none; }
        #ai-header { padding: 10px; background: #111; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ff41; cursor: move; font-weight: bold; }
        #ai-log { flex: 1; overflow-y: auto; padding: 5px; background: #050505; scroll-behavior: smooth; }
        .log-line { border-bottom: 1px solid #111; padding: 4px 2px; word-break: break-all; }
        .type-api { color: #ffff00; } .type-auth { color: #ff00ff; font-weight: bold; } .type-sys { color: #00ffff; }
        .ai-footer { padding: 8px; background: #111; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; border-top: 1px solid #00ff41; }
        .ai-btn { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 5px; cursor: pointer; font-size: 10px; text-align: center; }
        .ai-btn:active { background: #00ff41; color: #000; }
        .minimized { height: 40px !important; width: 140px !important; overflow: hidden; }
    `;
    document.head.appendChild(style);

    /* --- ESTRUTURA HTML --- */
    const ui = document.createElement('div');
    ui.id = 'ai-extractor-v3';
    ui.innerHTML = `
        <div id="ai-header">
            <span>CORE_EXTRACTOR_V3</span>
            <div style="display:flex; gap:10px;">
                <span id="ai-min" style="cursor:pointer;">[ _ ]</span>
                <span id="ai-close" style="cursor:pointer; color:red;">[ X ]</span>
            </div>
        </div>
        <div id="ai-log"></div>
        <div class="ai-footer">
            <button class="ai-btn" id="ai-copy">COPIAR TUDO</button>
            <button class="ai-btn" id="ai-clear">LIMPAR</button>
            <button class="ai-btn" id="ai-info">STATUS</button>
        </div>
    `;
    document.body.appendChild(ui);

    const logBox = document.getElementById('ai-log');
    let capturedData = {
        session: { cookies: document.cookie, storage: {...localStorage} },
        network: []
    };

    function writeLog(type, label, msg) {
        const entry = document.createElement('div');
        entry.className = 'log-line';
        const time = new Date().toLocaleTimeString();
        entry.innerHTML = `[${time}] <span class="type-${type}">${label}</span>: ${msg}`;
        logBox.prepend(entry);
    }

    /* --- INTERCEPTAÇÃO REAL-TIME (HOOKS) --- */
    
    // Captura Fetch APIs
    const operFetch = window.fetch;
    window.fetch = async (...args) => {
        const url = args[0];
        writeLog('api', 'FETCH', url);
        capturedData.network.push({type: 'FETCH', url, time: new Date()});
        return operFetch(...args);
    };

    // Captura XHR (Ajax)
    const operOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        writeLog('api', 'XHR', `${method} -> ${url}`);
        capturedData.network.push({type: 'XHR', method, url, time: new Date()});
        return operOpen.apply(this, arguments);
    };

    /* --- BOTÕES E FUNÇÕES --- */
    
    document.getElementById('ai-min').onclick = () => ui.classList.toggle('minimized');
    document.getElementById('ai-close').onclick = () => { if(confirm('Fechar extrator?')) ui.remove(); };
    document.getElementById('ai-clear').onclick = () => { logBox.innerHTML = ''; capturedData.network = []; };
    
    document.getElementById('ai-copy').onclick = () => {
        capturedData.session.cookies = document.cookie; // Atualiza cookies no momento do copy
        const fullDump = JSON.stringify(capturedData, null, 2);
        const el = document.createElement('textarea');
        el.value = fullDump;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
        alert('DADOS COPIADOS!\n- Cookies\n- LocalStorage\n- Logs de Rede');
    };

    document.getElementById('ai-info').onclick = () => {
        writeLog('sys', 'INFO', `DOMínios: ${new Set(capturedData.network.map(n=>new URL(n.url).hostname)).size}`);
        writeLog('auth', 'COOKIE', `Size: ${document.cookie.length} chars`);
    };

    // Mensagem Inicial
    writeLog('sys', 'SYSTEM', 'Injetado com sucesso no Android.');
    writeLog('auth', 'LOCAL', Object.keys(localStorage).length + ' chaves encontradas.');

    /* --- MOVIMENTAÇÃO TOUCH (ANDROID) --- */
    let active = false, currentY, initialY, yOffset = 0;
    ui.addEventListener("touchstart", (e) => {
        initialY = e.touches[0].clientY - yOffset;
        if (e.target.id === "ai-header") active = true;
    }, false);
    ui.addEventListener("touchmove", (e) => {
        if (active) {
            e.preventDefault();
            currentY = e.touches[0].clientY - initialY;
            yOffset = currentY;
            ui.style.transform = `translate3d(0, ${currentY}px, 0)`;
        }
    }, false);
    ui.addEventListener("touchend", () => active = false, false);

})();
