javascript:(function(){
    if(document.getElementById('ai-extractor-v4')) {
        alert('Hunter V4 já está ativo!');
        return;
    }

    /* --- ESTILIZAÇÃO SUPERIOR --- */
    const style = document.createElement('style');
    style.innerHTML = `
        #ai-extractor-v4 { position: fixed; top: 5px; right: 5px; width: 340px; height: 500px; background: #000; color: #00ff41; font-family: 'Courier New', monospace; z-index: 2147483647; border: 1px solid #00ff41; border-radius: 4px; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0, 255, 65, 0.4); font-size: 11px; }
        #ai-header { padding: 10px; background: #111; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ff41; cursor: move; font-weight: bold; }
        #ai-log { flex: 1; overflow-y: auto; padding: 5px; background: #050505; }
        .log-line { border-bottom: 1px solid #111; padding: 4px 2px; word-break: break-all; line-height: 1.4; }
        .type-api { color: #ffff00; } 
        .type-auth { color: #ff00ff; font-weight: bold; background: rgba(255, 0, 255, 0.1); border-left: 3px solid #ff00ff; padding-left: 5px; margin: 2px 0; } 
        .type-sys { color: #00ffff; }
        .ai-footer { padding: 8px; background: #111; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; border-top: 1px solid #00ff41; }
        .ai-btn { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 6px; cursor: pointer; font-size: 9px; text-align: center; text-transform: uppercase; }
        .ai-btn:active { background: #00ff41; color: #000; }
        .minimized { height: 40px !important; width: 140px !important; overflow: hidden; }
    `;
    document.head.appendChild(style);

    const ui = document.createElement('div');
    ui.id = 'ai-extractor-v4';
    ui.innerHTML = `
        <div id="ai-header">
            <span>HUNTER_V4_PRO</span>
            <div style="display:flex; gap:10px;"><span id="ai-min" style="cursor:pointer;">[_]</span><span id="ai-close" style="cursor:pointer; color:red;">[X]</span></div>
        </div>
        <div id="ai-log"></div>
        <div class="ai-footer">
            <button class="ai-btn" id="ai-copy">DUMP JSON</button>
            <button class="ai-btn" id="ai-clear">LIMPAR</button>
            <button class="ai-btn" id="ai-info">DECODE JWT</button>
        </div>
    `;
    document.body.appendChild(ui);

    const logBox = document.getElementById('ai-log');
    let capturedData = { session: { cookies: document.cookie, storage: {...localStorage} }, network: [], tokens: [] };

    function writeLog(type, label, msg) {
        const entry = document.createElement('div');
        entry.className = `log-line type-${type}`;
        const time = new Date().toLocaleTimeString().split(' ')[0];
        entry.innerHTML = `[${time}] [${label}] ${msg}`;
        logBox.prepend(entry);
    }

    /* --- HUNTER ENGINE (INTERCEPTAÇÃO) --- */
    
    // Hook Fetch para pegar Headers de Autorização
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
        const url = args[0];
        const options = args[1] || {};
        
        writeLog('api', 'FETCH', url);

        // Tentar pescar Tokens nos Headers
        if (options.headers) {
            for (let h in options.headers) {
                if (h.toLowerCase().includes('auth') || h.toLowerCase().includes('token')) {
                    const tokenVal = options.headers[h];
                    writeLog('auth', 'TOKEN_FOUND', `${h}: ${tokenVal.substring(0, 30)}...`);
                    capturedData.tokens.push({ header: h, value: tokenVal, url });
                }
            }
        }
        return originalFetch(...args);
    };

    // Hook XHR
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        writeLog('api', 'XHR', `${method} -> ${url}`);
        capturedData.network.push({type: 'XHR', method, url, time: new Date()});
        return originalOpen.apply(this, arguments);
    };

    /* --- LOGICA DE BOTÕES --- */
    document.getElementById('ai-min').onclick = () => ui.classList.toggle('minimized');
    document.getElementById('ai-close').onclick = () => ui.remove();
    document.getElementById('ai-clear').onclick = () => { logBox.innerHTML = ''; capturedData.network = []; capturedData.tokens = []; };
    
    document.getElementById('ai-copy').onclick = () => {
        const fullDump = JSON.stringify(capturedData, null, 2);
        const el = document.createElement('textarea');
        el.value = fullDump; document.body.appendChild(el); el.select();
        document.execCommand('copy'); document.body.removeChild(el);
        alert('DUMP COMPLETO COPIADO!');
    };

    // Tenta decodificar o último token capturado (Base64)
    document.getElementById('ai-info').onclick = () => {
        if(capturedData.tokens.length === 0) return alert('Nenhum token capturado ainda.');
        const lastToken = capturedData.tokens[capturedData.tokens.length - 1].value;
        try {
            const payload = lastToken.split('.')[1];
            const decoded = atob(payload);
            writeLog('sys', 'JWT_DECODE', decoded);
            console.log("JWT Decodificado:", JSON.parse(decoded));
        } catch(e) { writeLog('sys', 'ERR', 'Token não é um JWT válido para decode.'); }
    };

    writeLog('sys', 'SYSTEM', 'Hunter V4 Online. Monitorando Headers...');
    
    /* Drag Touch Android */
    let active = false, currentY, initialY, yOffset = 0;
    ui.addEventListener("touchstart", (e) => { initialY = e.touches[0].clientY - yOffset; if (e.target.id === "ai-header") active = true; }, false);
    ui.addEventListener("touchmove", (e) => { if (active) { e.preventDefault(); currentY = e.touches[0].clientY - initialY; yOffset = currentY; ui.style.transform = `translate3d(0, ${currentY}px, 0)`; } }, false);
    ui.addEventListener("touchend", () => active = false, false);
})();
