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
    document.querySelector('.kanban-board').addEventListener('click', (e) => {
        const card = e.target.closest('.kanban-card');
        if (!card) return;
        
        const data = card.aiData;
        if (!data) return;

        // ST3.1: Populate modal data
        inputId.value = data.id;
        inputCat.value = data.category || 'N/A';
        inputUrg.value = data.urgency || 'N/A';
        inputRes.value = data.ai_response || '';

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
                text: `Item #${id} response saved and marked Done!`,
                duration: 3000,
                style: { background: "var(--accent-low)" }
            }).showToast();

            modal.classList.add('hidden');
            
            // Reload window or trigger loadBoard from kanban.js
            setTimeout(() => window.location.reload(), 1000);

        } catch (err) {
            console.error(err);
            Toastify({
                text: "Failed to save AI response.",
                style: { background: "var(--accent-high)" }
            }).showToast();
        }
    });
});
