javascript:(function(){
    if(document.getElementById('omega-sniffer')) return alert('Sniffer Ativo!');

    const ui = document.createElement('div');
    ui.id = 'omega-sniffer';
    ui.style = 'position:fixed;top:10px;right:10px;width:380px;height:500px;background:#050505;color:#00ff00;z-index:999999;font-family:monospace;font-size:11px;border:1px solid #00ff00;display:flex;flex-direction:column;box-shadow:0 0 15px #000;resize:both;overflow:hidden;';
    
    ui.innerHTML = `
        <div id="omg-header" style="background:#00ff00;color:#000;padding:8px;font-weight:bold;display:flex;justify-content:space-between;cursor:move;user-select:none;">
            <span>OMEGA_SNIFFER_V6_PRO</span>
            <div>
                <span id="omg-min" style="cursor:pointer;padding:0 5px;border:1px solid #000;">[ _ ]</span>
                <span id="omg-close" style="cursor:pointer;padding:0 5px;border:1px solid #000;margin-left:5px">[ X ]</span>
            </div>
        </div>
        <div id="omg-content" style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
            <div id="omg-log" style="flex:1;overflow-y:auto;padding:5px;background:#000;"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #00ff00;">
                <button id="omg-copy" style="background:#111;color:#0ff;border:none;padding:10px;cursor:pointer;border-right:1px solid #00ff00">COPIAR JSON</button>
                <button id="omg-clear" style="background:#111;color:#f0f;border:none;padding:10px;cursor:pointer">LIMPAR</button>
            </div>
        </div>
    `;
    document.body.appendChild(ui);

    const logBox = document.getElementById('omg-log');
    const content = document.getElementById('omg-content');
    const header = document.getElementById('omg-header');
    let masterData = { requests: [], storage: {}, cookies: document.cookie, timestamp: new Date().toISOString() };

    /* --- SISTEMA DE ARRASTAR --- */
    let isDragging = false, offset = [0,0];
    header.onmousedown = (e) => {
        isDragging = true;
        offset = [ui.offsetLeft - e.clientX, ui.offsetTop - e.clientY];
    };
    document.onmousemove = (e) => {
        if(isDragging) {
            ui.style.left = (e.clientX + offset[0]) + 'px';
            ui.style.top = (e.clientY + offset[1]) + 'px';
            ui.style.right = 'auto';
        }
    };
    document.onmouseup = () => isDragging = false;

    /* --- MINIMIZAR --- */
    document.getElementById('omg-min').onclick = () => {
        const isMin = ui.style.height === '35px';
        ui.style.height = isMin ? '500px' : '35px';
        content.style.display = isMin ? 'flex' : 'none';
    };
    document.getElementById('omg-close').onclick = () => ui.remove();
    document.getElementById('omg-clear').onclick = () => { logBox.innerHTML = ''; masterData.requests = []; };

    function log(tag, data, color="#fff") {
        const div = document.createElement('div');
        div.style.borderBottom = '1px solid #222';
        div.style.padding = '4px 0';
        div.style.wordBreak = 'break-all';
        div.innerHTML = `<b style="color:${color}">[${tag}]</b> ${typeof data === 'string' ? data : JSON.stringify(data)}`;
        logBox.prepend(div);
    }

    /* --- EXTRAÇÃO PESADA (FETCH & XHR) --- */
    const { fetch: origFetch } = window;
    window.fetch = async (...args) => {
        const response = await origFetch(...args);
        const clone = response.clone();
        const url = args[0] instanceof Request ? args[0].url : args[0];
        
        clone.text().then(text => {
            const entry = { type: 'FETCH', url, status: response.status, body: text.substring(0, 1000) };
            masterData.requests.push(entry);
            log('FETCH_OUT', {url, status: response.status}, "#ffff00");
        });
        return response;
    };

    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        this.addEventListener('load', () => {
            log('XHR_DATA', {url: this.responseURL, res: this.responseText.substring(0, 100)}, "#00ffff");
            masterData.requests.push({type:'XHR', url: this.responseURL, resp: this.responseText});
        });
        return origSend.apply(this, arguments);
    };

    /* --- MONITOR DE STORAGE --- */
    setInterval(() => {
        masterData.storage = {...localStorage};
        masterData.cookies = document.cookie;
    }, 2000);

    document.getElementById('omg-copy').onclick = () => {
        const textArea = document.createElement("textarea");
        textArea.value = JSON.stringify(masterData, null, 4);
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
        alert('DATA EXTRAÍDA COM SUCESSO!');
    };

    log('SYSTEM', 'Sniffer V6 High-Extraction Ativo', '#00ff00');
})();
