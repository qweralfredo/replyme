// Component to render a Kanban Card
class KanbanCard {
    static create(item) {
        const card = document.createElement('div');
        card.className = 'kanban-card';
        card.dataset.id = item.id;
        card.dataset.status = item.status;
        
        // Convert item details to string formats
        const urgencyClass = `urgency-${(item.urgency || 'low').toLowerCase()}`;
        const category = item.category || 'General';
        const aiResponse = item.ai_response || 'Pending AI processing...';

        card.innerHTML = `
            <div class="card-header">
                <span class="card-title">Email #${item.id}</span>
                <div class="urgency-indicator ${urgencyClass}" title="Urgency: ${item.urgency}"></div>
            </div>
            <div class="card-body">
                ${item.summary ? item.summary : 'No summary available.'}
            </div>
            <div class="card-footer">
                <span class="tag">${category}</span>
                <span>ID: ${item.id}</span>
            </div>
        `;
        
        // Keep actual raw response in a hidden property for the modal
        card.aiData = item;
        
        return card;
    }
}
