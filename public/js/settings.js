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
                    <span><strong>${c.name}</strong> (${c.status_key}) ${c.rule_category ? `<br><small>Rules: [Cat: ${c.rule_category}, Urg: ${c.rule_urgency}]</small>` : ''}</span>
                    ${!c.is_system ? `<button class="btn-delete" data-key="${c.status_key}">🗑️</button>` : '<span>(System)</span>'}
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
});
