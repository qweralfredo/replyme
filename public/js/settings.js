document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8080/src/api';
    const settingsBtn = document.getElementById('open-settings');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettings = document.getElementById('close-settings');
    const newColForm = document.getElementById('new-column-form');
    const colsList = document.getElementById('settings-columns-list');

    settingsBtn.addEventListener('click', () => {
        loadSettingsColumns();
        settingsModal.classList.remove('hidden');
    });

    closeSettings.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
        window.location.reload(); // Reload to refresh kanban board
    });

    async function loadSettingsColumns() {
        try {
            const res = await fetch(`${API_URL}/columns.php`);
            const cols = await res.json();
            colsList.innerHTML = '';
            cols.forEach(c => {
                const li = document.createElement('li');
                li.style.marginBottom = '10px';
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.innerHTML = `
                    <span><strong>${c.name}</strong> (${c.status_key}) ${c.rule_category ? `<br><small>Regras: [Cat: ${c.rule_category}, Urg: ${c.rule_urgency}]</small>` : ''}</span>
                    ${!c.is_system ? `<button class="btn-delete" data-key="${c.status_key}">🗑️</button>` : '<span style="color:var(--text-muted); font-size:0.8rem;">(Sistema)</span>'}
                `;
                colsList.appendChild(li);
            });

            document.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const key = e.target.dataset.key;
                    await fetch(`${API_URL}/columns.php?status_key=${key}`, { method: 'DELETE' });
                    loadSettingsColumns();
                });
            });
        } catch (e) { console.error(e); }
    }

    newColForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('new-col-name').value,
            status_key: document.getElementById('new-col-key').value,
            rule_category: document.getElementById('new-col-category').value,
            rule_urgency: document.getElementById('new-col-urgency').value,
            position: 3 // Insert dynamically before Done (3 is review usually, so this inserts near middle)
        };

        await fetch(`${API_URL}/columns.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        newColForm.reset();
        loadSettingsColumns();
    });

    // --- MCP Settings Logic ---
    const mcpBtn = document.getElementById('open-mcp-settings');
    const mcpModal = document.getElementById('mcp-settings-modal');
    const closeMcpBtn = document.getElementById('close-mcp-settings');
    const newMcpForm = document.getElementById('new-mcp-form');
    const mcpList = document.getElementById('mcp-servers-list');

    mcpBtn.addEventListener('click', () => {
        loadMcpServers();
        mcpModal.classList.remove('hidden');
    });

    closeMcpBtn.addEventListener('click', () => {
        mcpModal.classList.add('hidden');
        // reload board just in case
        if (typeof window.loadBoard === 'function') {
            window.loadBoard();
        } else {
            window.location.reload();
        }
    });

    async function loadMcpServers() {
        try {
            const res = await fetch(`${API_URL}/mcp_servers.php`);
            const mcps = await res.json();
            mcpList.innerHTML = '';
            mcps.forEach(mcp => {
                const li = document.createElement('li');
                li.style.marginBottom = '10px';
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';
                
                let statusColor = 'var(--text-muted)';
                let statusText = 'Pendente';
                if(mcp.status === 'installed') { statusColor = 'var(--success)'; statusText = 'Instalado'; }
                if(mcp.status === 'failed') { statusColor = 'var(--accent-high)'; statusText = 'Falhou'; }
                if(mcp.status === 'testing') { statusColor = 'var(--accent-primary)'; statusText = 'Instalando...'; }

                let displayPath = mcp.url ? mcp.url : (mcp.inferred_command || 'Sem URL/Comando');
                li.innerHTML = `
                    <span><strong>${mcp.name}</strong><br><small><span style="color:var(--accent-low)">${displayPath}</span></small><br><span style="color:${statusColor}; font-size:0.8rem; font-weight:bold;">${statusText}</span></span>
                    <div>
                        <button class="btn-test-mcp" data-id="${mcp.id}" style="background: none; border: none; cursor: pointer; font-size: 1.2rem; margin-right: 5px;" title="Testar Servidor MCP">🧪</button>
                        <button class="btn-delete-mcp" data-id="${mcp.id}" style="background: none; border: none; cursor: pointer; font-size: 1.2rem;">🗑️</button>
                    </div>
                `;
                mcpList.appendChild(li);
            });

            document.querySelectorAll('.btn-test-mcp').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = e.target.dataset.id;
                    openMcpTestModal(id);
                });
            });

            document.querySelectorAll('.btn-delete-mcp').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.dataset.id;
                    await fetch(`${API_URL}/mcp_servers.php?id=${id}`, { method: 'DELETE' });
                    loadMcpServers();
                });
            });
        } catch (e) { console.error(e); }
    }

    newMcpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('mcp-name').value,
            url: document.getElementById('mcp-url').value,
            command: document.getElementById('mcp-command').value
        };

        if (!payload.url && !payload.command) {
            Toastify({ text: "Forneça uma URL ou um Comando Local.", backgroundColor: "var(--accent-high)" }).showToast();
            return;
        }

        await fetch(`${API_URL}/mcp_servers.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        newMcpForm.reset();
        loadMcpServers();
    });

    // --- Test MCP Logic ---
    let currentTestMcpId = null;
    const testModal = document.getElementById('test-mcp-modal');
    const testPrompt = document.getElementById('test-mcp-prompt');
    const testResult = document.getElementById('test-mcp-result');
    const btnRunTest = document.getElementById('btn-run-mcp-test');

    function openMcpTestModal(id) {
        currentTestMcpId = id;
        testPrompt.value = '';
        testResult.innerHTML = 'Aguardando teste...';
        testModal.classList.remove('hidden');
    }

    btnRunTest.addEventListener('click', async () => {
        if (!currentTestMcpId) return;
        const prompt = testPrompt.value.trim();
        if (!prompt) {
            Toastify({ text: "Escreva um prompt para testar.", backgroundColor: "var(--accent-high)" }).showToast();
            return;
        }

        testResult.innerHTML = '<span style="color: var(--accent-primary);">Iniciando agente... aguarde... (isso pode levar alguns segundos dependendo do prompt)</span>';
        btnRunTest.disabled = true;

        try {
            const res = await fetch(`${API_URL}/mcp_test.php`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mcp_id: currentTestMcpId, prompt: prompt })
            });
            const data = await res.json();
            
            if (data.error) {
                testResult.innerHTML = `<span style="color: var(--accent-high);">Erro: ${data.error}</span>`;
            } else if (data.result) {
                testResult.innerHTML = data.result.replace(/\n/g, '<br>');
            } else {
                testResult.innerHTML = 'Resposta inesperada: ' + JSON.stringify(data);
            }
        } catch (e) {
            testResult.innerHTML = `<span style="color: var(--accent-high);">Erro de rede: ${e.message}</span>`;
        } finally {
            btnRunTest.disabled = false;
        }
    });
});
