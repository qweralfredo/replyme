const { test, describe } = require('node:test');
const assert = require('node:assert');
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

describe('Kanban Dashboard UI', () => {
    test('renders 4 required columns even without data', () => {
        // We simulate loading the index.html
        const htmlPath = path.resolve(__dirname, '../../public/index.html');
        // ST2.1 RED: File doesn't exist yet, should fail reading or finding columns
        
        try {
            const html = fs.readFileSync(htmlPath, 'utf8');
            const dom = new JSDOM(html);
            const document = dom.window.document;
            
            const columns = document.querySelectorAll('.kanban-column');
            assert.strictEqual(columns.length, 4, "Should have exactly 4 columns");
            
            const expectedIds = ['col-inbox', 'col-processing', 'col-review', 'col-done'];
            expectedIds.forEach(id => {
                assert.ok(document.getElementById(id), `Missing column with ID ${id}`);
            });
        } catch (e) {
            // Force fail if file doesn't exist or assertions fail
            assert.fail(e.message);
        }
    });
});
