document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8080/src/api';
    const modal = document.getElementById('ai-modal');
    const closeBtn = document.getElementById('close-modal');
    const form = document.getElementById('review-form');
    
    // Form fields
    const inputId = document.getElementById('modal-card-id');
    const inputCat = document.getElementById('modal-category');
    const inputUrg = document.getElementById('modal-urgency');
    const inputRes = document.getElementById('modal-response');

    // ST3.3: Optimization - Use Event Delegation on the kanban board instead of loop attaching to cards
    document.querySelector('.kanban-board').addEventListener('click', async (e) => {
        const card = e.target.closest('.kanban-card');
        if (!card) return;
        
        const data = card.aiData;
        const item = card.aiData;
        if (!item) return;

        // ST3.1: Populate modal data
        inputId.value = item.id;
        inputCat.value = item.ai_category || 'N/A';
        inputUrg.value = item.ai_urgency || 'N/A';
        document.getElementById('modal-response').value = item.ai_response || '';
            
        // Fetch and render history
        const timeline = document.getElementById('history-timeline');
        timeline.innerHTML = '<li>Carregando histórico...</li>';
        
        try {
            const res = await fetch(`http://localhost:8080/src/api/history.php?email_id=${item.id}`);
            const history = await res.json();
            
            timeline.innerHTML = '';
            if (history.length === 0) {
                timeline.innerHTML = '<li>Nenhum histórico registrado ainda.</li>';
            } else {
                history.forEach(h => {
                    const li = document.createElement('li');
                    const date = new Date(h.created_at).toLocaleString();
                    
                    let text = h.action;
                    if (h.from_status && h.to_status) {
                        text += ` <br><small>(${h.from_status} ➔ ${h.to_status})</small>`;
                    } else if (h.to_status) {
                        text += ` <br><small>(➔ ${h.to_status})</small>`;
                    }
                    
                    li.innerHTML = `<span class="timeline-date">${date}</span> ${text}`;
                    timeline.appendChild(li);
                });
            }
        } catch (err) {
            timeline.innerHTML = '<li style="color:red">Falha ao carregar o histórico</li>';
        }

        modal.classList.remove('hidden');
    });

    closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    // ST3.2: Submit form and send PATCH to save ai_response and move to done
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const id = inputId.value;
        const newResponse = inputRes.value;

        try {
            const res = await fetch(`${API_URL}/work_item.php`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: parseInt(id),
                    ai_response: newResponse,
                    status: 'done' // "Approve & Mark Done"
                })
            });

            if (!res.ok) throw new Error('Failed to update response');

            Toastify({
                text: `Resposta do Item #${id} salva e marcada como Concluído!`,
                duration: 3000,
                style: { background: "var(--accent-low)" }
            }).showToast();

            modal.classList.add('hidden');
            
            // Reload window or trigger loadBoard from kanban.js
            setTimeout(() => window.location.reload(), 1000);

        } catch (err) {
            console.error(err);
            Toastify({
                text: "Falha ao salvar a resposta da IA.",
                style: { background: "var(--accent-high)" }
            }).showToast();
        }
    });

    // Email Viewer Modal Logic
    const viewerModal = document.getElementById('email-viewer-modal');
    const closeViewerBtn = document.getElementById('close-email-viewer');
    const iframe = document.getElementById('email-iframe');
    const btnViewEmail = document.getElementById('btn-view-email');
    
    let currentEmailData = null;

    document.querySelector('.kanban-board').addEventListener('click', (e) => {
        const card = e.target.closest('.kanban-card');
        if (card) {
            currentEmailData = card.aiData;
        }
    });

    btnViewEmail.addEventListener('click', () => {
        if (!currentEmailData) return;
        
        let htmlContent = currentEmailData.body_html;
        if (!htmlContent) {
            // Fallback for plain text emails
            htmlContent = `<div style="font-family: sans-serif; padding: 20px; color: #333; line-height: 1.5; white-space: pre-wrap;">${currentEmailData.body || 'No content available.'}</div>`;
        }
        
        iframe.srcdoc = htmlContent;
        viewerModal.classList.remove('hidden');
    });

    closeViewerBtn.addEventListener('click', () => {
        viewerModal.classList.add('hidden');
        iframe.srcdoc = ''; // clear to stop embedded media playing
    });

    viewerModal.addEventListener('click', (e) => {
        if (e.target === viewerModal) {
            viewerModal.classList.add('hidden');
            iframe.srcdoc = '';
        }
    });
});
