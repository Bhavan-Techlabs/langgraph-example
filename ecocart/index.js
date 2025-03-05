const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');

// Create Express app
const app = express();
app.use(bodyParser.json());

// Sales persons list
const salesPersons = [
    { id: 1, name: 'Alice Johnson', email: 'alice@company.com' },
    { id: 2, name: 'Bob Smith', email: 'bob@company.com' },
    { id: 3, name: 'Charlie Brown', email: 'charlie@company.com' },
    { id: 4, name: 'Diana Prince', email: 'diana@company.com' }
];

// Initialize SQLite database
const db = new sqlite3.Database('./sales_leads.sqlite');

// Create tables
db.serialize(() => {
    // Sales Lead Assignments Table
    db.run(`CREATE TABLE IF NOT EXISTS lead_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT,
        assigned_person_id INTEGER,
        status TEXT DEFAULT 'PENDING',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Hubspot Ticket Mock Table
    db.run(`CREATE TABLE IF NOT EXISTS hubspot_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT,
        assigned_person_id INTEGER,
        ticket_status TEXT DEFAULT 'CREATED',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
});

// Endpoint to assign sales lead
app.get('/assign-lead/:lead_id', (req, res) => {
    const { lead_id } = req.params;

    if (!lead_id) {
        return res.status(400).json({ error: 'Lead ID is required' });
    }

    // Simple randomization to select sales person
    const selectedSalesPerson = salesPersons[Math.floor(Math.random() * salesPersons.length)];

    // Insert lead assignment record
    const stmt = db.prepare('INSERT INTO lead_assignments (lead_id, assigned_person_id) VALUES (?, ?)');
    stmt.run(lead_id, selectedSalesPerson.id, function(err) {
        if (err) {
            return res.status(500).json({ error: 'Failed to assign lead' });
        }

        res.json({
            message: 'Lead assigned successfully',
            assignment_id: this.lastID,
            sales_person: selectedSalesPerson
        });
    });
    stmt.finalize();
});

// Endpoint to confirm lead assignment
app.post('/confirm-lead', (req, res) => {
    const { lead_id, assigned_person_id } = req.body;

    if (!lead_id || !assigned_person_id) {
        return res.status(400).json({ error: 'Lead ID and Assigned Person ID are required' });
    }

    // Update lead assignment status
    const updateStmt = db.prepare(`
        UPDATE lead_assignments 
        SET status = 'ACCEPTED' 
        WHERE lead_id = ? AND assigned_person_id = ?
    `);
    
    updateStmt.run(lead_id, assigned_person_id, function(err) {
        if (err) {
            return res.status(500).json({ error: 'Failed to update lead assignment' });
        }

        // Mock Hubspot ticket creation
        const ticketStmt = db.prepare('INSERT INTO hubspot_tickets (lead_id, assigned_person_id) VALUES (?, ?)');
        ticketStmt.run(lead_id, assigned_person_id, function(ticketErr) {
            if (ticketErr) {
                return res.status(500).json({ error: 'Failed to create Hubspot ticket' });
            }

            res.json({
                message: 'Lead assignment confirmed and Hubspot ticket created',
                ticket_id: this.lastID
            });
        });
        ticketStmt.finalize();
    });
    updateStmt.finalize();
});

// Start the server
const PORT = process.env.PORT || 3500;
app.listen(PORT, () => {
    console.log(`Server running on url http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    db.close((err) => {
        if (err) {
            console.error(err.message);
        }
        console.log('Closed the database connection.');
        process.exit(0);
    });
});