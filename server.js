
const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const app = express();
const port = 3001;

// Enable CORS for all routes
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).send('Agent server is running');
});

// API endpoint to execute Python agent
app.post('/api/agent', (req, res) => {
    const { query } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Query is required' });
    }

    // Escape quotes in the query to prevent command injection
    const sanitizedQuery = query.replace(/"/g, '\\"');

    // Execute the Python script with the query
    const command = `python agent_openrouter.py "${sanitizedQuery}"`;

    console.log(`Executing: ${command}`);

    exec(command, {
        cwd: '/app'
    }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Execution error: ${error}`);
            return res.status(500).json({ error: 'Failed to execute agent', details: stderr });
        }

        console.log(`Agent response: ${stdout}`);
        return res.status(200).json({ response: stdout });
    });
});

// API endpoint to execute a specific query
app.post('/api/execute-query', (req, res) => {
    const { query } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Query is required' });
    }

    // Save query to a temporary file
    const tempFilePath = path.join('/app/data', 'temp_query.sql');
    fs.writeFileSync(tempFilePath, query);

    // Execute the Python script with the query
    const command = `python run_specific_query.py`;

    console.log(`Executing specific query: ${query}`);

    exec(command, {
        cwd: '/app'
    }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Execution error: ${error}`);
            return res.status(500).json({ error: 'Failed to execute query', details: stderr });
        }

        // Try to read the CSV file
        try {
            const csvPath = path.join('/app/data', 'deal_extract_docs_results.csv');
            const csvContent = fs.readFileSync(csvPath, 'utf8');

            // Parse CSV data
            const rows = csvContent.split('\n');
            const headers = rows[0].split(',');
            const data = rows.slice(1)
                .filter(row => row.trim() !== '')
                .map(row => row.split(','));

            console.log(`Query executed and CSV data retrieved.`);
            return res.status(200).json({
                message: stdout,
                result: {
                    columns: headers,
                    data: data
                }
            });
        } catch (csvError) {
            console.error(`Error reading CSV: ${csvError}`);
            return res.status(200).json({
                message: stdout,
                result: null,
                error: 'Failed to read result data'
            });
        }
    });
});

// Start the server
app.listen(port, () => {
    console.log(`Agent server listening at http://localhost:${port}`);
});
