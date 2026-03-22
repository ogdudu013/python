javascript:(function(){
    if(document.getElementById('omega-sniffer-v7')) return alert('Sniffer já ativo!');

    /* --- CRIAÇÃO DA INTERFACE --- */
    const ui = document.createElement('div');
    ui.id = 'omega-sniffer-v7';
    ui.style = 'position:fixed;top:50px;right:50px;width:420px;height:500px;background:rgba(10,10,10,0.98);color:#0f0;z-index:9999999;font-family:monospace;font-size:11px;border:1px solid #0f0;display:flex;flex-direction:column;box-shadow:0 0 20px #000;border-radius:5px;resize:both;overflow:hidden;';
    
    ui.innerHTML = `
        <div id="omg-drag" style="background:#0f0;color:#000;padding:10px;font-weight:bold;cursor:move;display:flex;justify-content:space-between;user-select:none;">
            <span>⚡ OMEGA_SNIFFER_V7_NATIVE</span>
            <div style="display:flex;gap:10px;">
                <span id="omg-min" style="cursor:pointer;padding:0 5px;border:1px solid #000;">_</span>
                <span id="omg-close" style="cursor:pointer;padding:0 5px;border:1px solid #000;">X</span>
            </div>
        </div>
        <div id="omg-content" style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
            <div id="omg-log" style="flex:1;overflow-y:auto;padding:10px;background:#000;scrollbar-width:thin;"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #333;">
                <button id="omg-copy" style="background:#111;color:#0ff;border:none;padding:12px;cursor:pointer;font-weight:bold;border-right:1px solid #333;">COPIAR LOGS (JSON)</button>
                <button id="omg-clear" style="background:#111;color:#f0f;border:none;padding:12px;cursor:pointer;font-weight:bold;">LIMPAR TUDO</button>
            </div>
        </div>
    `;
    document.body.appendChild(ui);

    const logBox = document.getElementById('omg-log');
    const content = document.getElementById('omg-content');
    const dragH = document.getElementById('omg-drag');
    let masterData = { requests: [], storage: {}, cookies: "", timestamp: new Date().toLocaleString() };

    /* --- FUNÇÃO DE LOG --- */
    const log = (tag, data, color="#fff") => {
        const div = document.createElement('div');
        div.style = 'border-bottom:1px solid #222;padding:5px 0;word-break:break-all;';
        div.innerHTML = `<b style="color:${color}">[${tag}]</b> ${typeof data === 'object' ? JSON.stringify(data) : data}`;
        logBox.prepend(div);
    };

    /* --- SISTEMA ARRASTÁVEL --- */
    let isDragging = false, offset = [0,0];
    dragH.onmousedown = (e) => {
        isDragging = true;
        offset = [ui.offsetLeft - e.clientX, ui.offsetTop - e.clientY];
    };
    document.addEventListener('mousemove', (e) => {
        if(!isDragging) return;
        ui.style.left = (e.clientX + offset[0]) + 'px';
        ui.style.top = (e.clientY + offset[1]) + 'px';
        ui.style.right = 'auto';
    });
    document.addEventListener('mouseup', () => isDragging = false);

    /* --- MINIMIZAR / FECHAR --- */
    document.getElementById('omg-min').onclick = () => {
        const isMin = content.style.display === 'none';
        content.style.display = isMin ? 'flex' : 'none';
        ui.style.height = isMin ? '500px' : '40px';
    };
    document.getElementById('omg-close').onclick = () => ui.remove();
    document.getElementById('omg-clear').onclick = () => { logBox.innerHTML = ''; masterData.requests = []; };

    /* --- EXTRAÇÃO PESADA (NETWORK SNIFFER) --- */
    // Interceptar FETCH
    const _fetch = window.fetch;
    window.fetch = async (...args) => {
        const url = args[0] instanceof Request ? args[0].url : args[0];
        log('FETCH_OUT', url.substring(0, 50), '#ffff00');
        try {
            const res = await _fetch(...args);
            const clone = res.clone();
            clone.text().then(t => masterData.requests.push({type:'FETCH', url, data: t.substring(0, 2000)}));
            return res;
        } catch(e) { return _fetch(...args); }
    };

    // Interceptar XHR
    const _send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        this.addEventListener('load', () => {
            log('XHR_DATA', this.responseURL.substring(0, 50), '#00ffff');
            masterData.requests.push({type:'XHR', url: this.responseURL, body, res: this.responseText.substring(0, 2000)});
        });
        return _send.apply(this, arguments);
    };

    /* --- MONITOR DE DADOS --- */
    setInterval(() => {
        masterData.storage = {...localStorage};
        masterData.cookies = document.cookie;
    }, 2000);

    /* --- BOTÃO COPIAR --- */
    document.getElementById('omg-copy').onclick = () => {
        const el = document.createElement('textarea');
        el.value = JSON.stringify(masterData, null, 2);
        document.body.appendChild(el); el.select();
        document.execCommand('copy'); el.remove();
        alert('DADOS COPIADOS!');
    };

    log('SYSTEM', 'V7 Ativado: Injeção Direta (Ignora CSP)', '#0f0');
})();
