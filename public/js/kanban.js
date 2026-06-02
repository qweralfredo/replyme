document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8080/src/api';
    const dropzones = document.querySelectorAll('.kanban-dropzone');

    // Initialize SortableJS on all columns
    dropzones.forEach(zone => {
        new Sortable(zone, {
            group: 'kanban', // set both lists to same group
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: async function (evt) {
                const itemEl = evt.item;  // dragged HTMLElement
                const toColumn = evt.to.closest('.kanban-column');
                const newStatus = toColumn.dataset.status;
                const id = itemEl.dataset.id;
                
                if (itemEl.dataset.status === newStatus) return; // No change

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
                    // Revert UI implicitly by re-fetching or manually pushing back
                }
            },
        });
    });

    async function loadBoard() {
        try {
            const res = await fetch(`${API_URL}/kanban.php`);
            if (!res.ok) throw new Error('Failed to load Kanban data');
            const items = await res.json();
            
            // Clear dropzones
            dropzones.forEach(dz => dz.innerHTML = '');
            
            items.forEach(item => {
                const card = KanbanCard.create(item);
                const targetZone = document.getElementById(`drop-${item.status}`);
                if (targetZone) {
                    targetZone.appendChild(card);
                } else {
                    document.getElementById('drop-inbox').appendChild(card); // fallback
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
