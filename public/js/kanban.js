document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8080/src/api';
    const boardContainer = document.getElementById('kanban-board-container');
    let dropzones = [];

    async function loadBoard() {
        try {
            // 1. Fetch Dynamic Columns
            const colsRes = await fetch(`${API_URL}/columns.php`);
            if (!colsRes.ok) throw new Error('Failed to load columns');
            const columns = await colsRes.json();
            
            // 2. Render Columns
            boardContainer.innerHTML = '';
            columns.forEach(col => {
                const section = document.createElement('section');
                section.className = 'kanban-column';
                if(col.status_key === 'to_send') section.classList.add('column-to-send');
                section.id = `col-${col.status_key}`;
                section.dataset.status = col.status_key;
                
                section.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px;">
                        <h2 style="margin: 0;">${col.name}</h2>
                        <button class="btn-assign-mcp" data-col="${col.status_key}" data-name="${col.name}" style="background:none; border:none; cursor:pointer; font-size:1.2rem;" title="Atribuir MCPs a esta coluna">⚙️</button>
                    </div>
                    <div class="kanban-dropzone" id="drop-${col.status_key}"></div>
                `;
                boardContainer.appendChild(section);
            });

            // 3. Initialize SortableJS
            dropzones = document.querySelectorAll('.kanban-dropzone');
            dropzones.forEach(zone => {
                new Sortable(zone, {
                    group: 'kanban',
                    animation: 150,
                    ghostClass: 'sortable-ghost',
                    onEnd: async function (evt) {
                        const itemEl = evt.item;
                        const toColumn = evt.to.closest('.kanban-column');
                        const newStatus = toColumn.dataset.status;
                        const id = itemEl.dataset.id;
                        
                        if (itemEl.dataset.status === newStatus) return;

                        itemEl.dataset.status = newStatus;
                        
                        try {
                            const response = await fetch(`${API_URL}/work_item.php`, {
                                method: 'PATCH',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ id: parseInt(id), status: newStatus })
                            });
                            
                            if (!response.ok) throw new Error('API update failed');
                            
                            Toastify({
                                text: `Item #${id} movido para ${newStatus}`,
                                duration: 3000,
                                style: { background: "var(--accent-low)" }
                            }).showToast();

                        } catch (err) {
                            console.error(err);
                            Toastify({
                                text: "Erro ao mover o card. Alterações revertidas.",
                                duration: 3000,
                                style: { background: "var(--accent-high)" }
                            }).showToast();
                        }
                    },
                });
            });

            // 4. Fetch Emails and Populate
            const res = await fetch(`${API_URL}/kanban.php`);
            if (!res.ok) throw new Error('Failed to load Kanban data');
            const items = await res.json();
            
            items.forEach(item => {
                // Don't show sent emails on board to avoid clutter
                if (item.status === 'sent') return; 
                
                const card = KanbanCard.create(item);
                const targetZone = document.getElementById(`drop-${item.status}`);
                if (targetZone) {
                    targetZone.appendChild(card);
                } else {
                    const inbox = document.getElementById('drop-inbox');
                    if (inbox) inbox.appendChild(card);
                }
            });
            
            // 5. Gear Icons Events
            document.querySelectorAll('.btn-assign-mcp').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const colKey = e.currentTarget.dataset.col;
                    const colName = e.currentTarget.dataset.name;
                    
                    document.getElementById('assign-col-name').innerText = colName;
                    document.getElementById('assign-status-key').value = colKey;
                    
                    // Find column data to pre-fill
                    const colData = columns.find(c => c.status_key === colKey);
                    let assigned = [];
                    try { assigned = JSON.parse(colData.mcp_servers || '[]'); } catch(e){}
                    
                    // Fetch MCPs
                    const res = await fetch(`${API_URL}/mcp_servers.php`);
                    const mcps = await res.json();
                    
                    const listContainer = document.getElementById('mcp-checkbox-list');
                    listContainer.innerHTML = '';
                    
                    let commonPrompt = '';
                    mcps.forEach(mcp => {
                        const isChecked = assigned.find(a => a.mcp_id == mcp.id);
                        if(isChecked) commonPrompt = isChecked.prompt;
                        
                        const div = document.createElement('div');
                        div.innerHTML = `
                            <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                                <input type="checkbox" name="mcp_selection" value="${mcp.id}" ${isChecked ? 'checked' : ''}>
                                <strong>${mcp.name}</strong> <small style="color:var(--text-muted)">(${mcp.status})</small>
                            </label>
                        `;
                        listContainer.appendChild(div);
                    });
                    
                    document.getElementById('mcp-prompt').value = commonPrompt;
                    document.getElementById('assign-mcp-modal').classList.remove('hidden');
                });
            });
            
        } catch (err) {
            console.error(err);
            Toastify({
                text: "Falha ao carregar os dados do quadro",
                style: { background: "var(--accent-high)" }
            }).showToast();
        }
    }

    loadBoard();

    document.getElementById('close-assign-mcp').addEventListener('click', () => {
        document.getElementById('assign-mcp-modal').classList.add('hidden');
    });

    document.getElementById('assign-mcp-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const colKey = document.getElementById('assign-status-key').value;
        const promptText = document.getElementById('mcp-prompt').value;
        
        const selectedIds = Array.from(document.querySelectorAll('input[name="mcp_selection"]:checked')).map(cb => parseInt(cb.value));
        const payloadArray = selectedIds.map(id => ({
            mcp_id: id,
            prompt: promptText
        }));
        
        try {
            await fetch(`${API_URL}/columns.php`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status_key: colKey,
                    mcp_servers: JSON.stringify(payloadArray)
                })
            });
            
            document.getElementById('assign-mcp-modal').classList.add('hidden');
            Toastify({ text: "Atribuição salva", style: { background: "var(--success)" } }).showToast();
            loadBoard();
        } catch(err) {
            console.error(err);
        }
    });
});
