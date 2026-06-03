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

                li.innerHTML = `
                    <span><strong>${mcp.name}</strong><br><small><a href="${mcp.url}" target="_blank" style="color:var(--accent-low)">${mcp.url}</a></small><br><span style="color:${statusColor}; font-size:0.8rem; font-weight:bold;">${statusText}</span></span>
                    <button class="btn-delete-mcp" data-id="${mcp.id}">🗑️</button>
                `;
                mcpList.appendChild(li);
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
            url: document.getElementById('mcp-url').value
        };

        await fetch(`${API_URL}/mcp_servers.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        newMcpForm.reset();
        loadMcpServers();
    });
});
