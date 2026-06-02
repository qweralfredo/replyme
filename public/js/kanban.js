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
                    <h2>${col.name}</h2>
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
                                text: `Item #${id} moved to ${newStatus}`,
                                duration: 3000,
                                style: { background: "var(--accent-low)" }
                            }).showToast();

                        } catch (err) {
                            console.error(err);
                            Toastify({
                                text: "Error moving card. Changes reverted.",
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
            
        } catch (err) {
            console.error(err);
            Toastify({
                text: "Failed to load board data",
                style: { background: "var(--accent-high)" }
            }).showToast();
        }
    }

    loadBoard();
});
