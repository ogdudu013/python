Javascript:(function(){
    if(document.getElementById('omega-sniffer')) return alert('Sniffer Ativo!');

    const ui = document.createElement('div');
    ui.id = 'omega-sniffer';
    ui.style = 'position:fixed;top:0;right:0;width:350px;height:100%;background:#050505;color:#00ff00;z-index:999999;font-family:monospace;font-size:10px;border-left:1px solid #00ff00;display:flex;flex-direction:column;';
    ui.innerHTML = `
        <div style="background:#00ff00;color:#000;padding:5px;font-weight:bold;display:flex;justify-content:space-between">
            <span>OMEGA_SNIFFER_V5</span>
            <span onclick="this.parentElement.parentElement.remove()" style="cursor:pointer">[X]</span>
        </div>
        <div id="omg-log" style="flex:1;overflow-y:auto;padding:5px;"></div>
        <button id="omg-copy" style="background:#222;color:#00ff00;border:none;padding:10px;cursor:pointer;border-top:1px solid #00ff00">COPIAR TUDO (JSON)</button>
    `;
    document.body.appendChild(ui);

    const logBox = document.getElementById('omg-log');
    let masterData = { requests: [], storage: localStorage, cookies: document.cookie };

    function log(tag, data, color="#fff") {
        const div = document.createElement('div');
        div.style.borderBottom = '1px solid #222';
        div.style.padding = '5px 0';
        div.innerHTML = `<b style="color:${color}">[${tag}]</b> ${JSON.stringify(data).substring(0, 200)}...`;
        logBox.prepend(div);
    }

    /* Interceptador Bruto de Fetch */
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
        const url = args[0];
        const options = args[1] || {};
        const entry = { url, method: options.method || 'GET', headers: options.headers, body: options.body };
        
        masterData.requests.push(entry);
        log('FETCH', {url, method: entry.method}, "#ffff00");

        if (options.body) log('PAYLOAD', options.body, "#ff00ff");
        if (options.headers) log('HEADERS', options.headers, "#00ffff");

        return originalFetch(...args);
    };

    /* Interceptador Bruto de XHR (AJAX) */
    const send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        this.addEventListener('load', () => {
            log('XHR_RES', {url: this.responseURL, status: this.status}, "#00ff00");
            if(body) log('XHR_BODY', body, "#ff8800");
        });
        return send.apply(this, arguments);
    };

    document.getElementById('omg-copy').onclick = () => {
        const el = document.createElement('textarea');
        el.value = JSON.stringify(masterData, null, 2);
        document.body.appendChild(el); el.select();
        document.execCommand('copy'); el.remove();
        alert('LOG BRUTO COPIADO!');
    };

    log('SYSTEM', 'Monitoramento Total Ativado', '#fff');
})();


Coloque um botao minizar
