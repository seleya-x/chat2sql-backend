const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const app = express();
const port = process.env.PORT || 3001;

// The root directory where Python agent files are located
const AGENT_ROOT_PATH = "./sql_with_table_schema-master";
const DEFAULT_AGENT_FILENAME = "agent_openrouter.py";
const SQL_QUERY_FILE = path.join(AGENT_ROOT_PATH, "sql_query.txt");
const QUERY_EXECUTOR_SCRIPT = path.join(AGENT_ROOT_PATH, "run_specific_query.py");
const QUERY_RESULTS_FILE = path.join(AGENT_ROOT_PATH, "deal_extract_docs_results.csv");

// Configure CORS to allow requests from anywhere (adjust for production)
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// Add health check endpoint
app.get('/health', (req, res) => {
    console.log('Health check request received');
    res.json({ status: 'online', message: 'Agent server is running' });
});

// New endpoint to save SQL to a file
app.post('/save-sql', (req, res) => {
    const { sql } = req.body;

    if (!sql) {
        console.error('SQL is required');
        return res.status(400).json({ message: 'SQL is required' });
    }

    console.log(`Saving SQL query to ${SQL_QUERY_FILE}`);

    try {
        // Check if the directory exists
        const dir = path.dirname(SQL_QUERY_FILE);
        if (!fs.existsSync(dir)) {
            console.log(`Creating directory: ${dir}`);
            fs.mkdirSync(dir, { recursive: true });
        }

        fs.writeFileSync(SQL_QUERY_FILE, sql, 'utf8');
        console.log('SQL saved successfully');
        return res.json({ message: 'SQL saved successfully' });
    } catch (error) {
        console.error(`Error saving SQL file: ${error.message}`);
        return res.status(500).json({ message: `Error: ${error.message}` });
    }
});

// New endpoint to execute specific SQL query
app.post('/execute-sql', (req, res) => {
    const { sql } = req.body;

    // First save the SQL to file
    try {
        const dir = path.dirname(SQL_QUERY_FILE);
        if (!fs.existsSync(dir)) {
            console.log(`Creating directory: ${dir}`);
            fs.mkdirSync(dir, { recursive: true });
        }

        fs.writeFileSync(SQL_QUERY_FILE, sql, 'utf8');
        console.log('SQL saved to file before execution');
    } catch (error) {
        console.error(`Error saving SQL file before execution: ${error.message}`);
        return res.status(500).json({ message: `Error saving SQL: ${error.message}` });
    }

    console.log(`Executing SQL query using ${QUERY_EXECUTOR_SCRIPT}`);

    // Execute the Python script to run the SQL
    const command = `python "${QUERY_EXECUTOR_SCRIPT}"`;

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error}`);
            return res.status(500).json({ message: `Error: ${error.message}` });
        }

        if (stderr) {
            console.error(`Python script stderr: ${stderr}`);
            // Some scripts may output to stderr but still work correctly
            console.log(`Python script stdout: ${stdout}`);

            if (stdout) {
                return res.json({ result: stdout, warning: stderr });
            }
            return res.status(500).json({ message: `Error: ${stderr}` });
        }

        console.log(`Python script executed successfully`);

        // Try to read the results file
        try {
            if (fs.existsSync(QUERY_RESULTS_FILE)) {
                // Try to parse CSV file
                console.log(`Results file found at ${QUERY_RESULTS_FILE}`);
                const csvData = fs.readFileSync(QUERY_RESULTS_FILE, 'utf8');
                return res.json({
                    result: stdout,
                    message: 'SQL executed successfully'
                });
            } else {
                console.log('No results file found after execution');
                return res.json({
                    result: stdout,
                    message: 'SQL executed successfully, but no results file was found'
                });
            }
        } catch (fileError) {
            console.error(`Error reading results file: ${fileError.message}`);
            return res.json({
                result: stdout,
                message: 'SQL executed successfully, but error reading results file'
            });
        }
    });
});

// New endpoint to get CSV results
app.get('/get-csv-results', (req, res) => {
    console.log(`Fetching CSV results from ${QUERY_RESULTS_FILE}`);

    try {
        if (fs.existsSync(QUERY_RESULTS_FILE)) {
            const csvData = fs.readFileSync(QUERY_RESULTS_FILE, 'utf8');

            // Parse CSV data
            const rows = csvData.trim().split('\n');
            const headers = rows[0].split(',').map(header => header.trim());

            const data = rows.slice(1).map(row => {
                const values = row.split(',').map(value => value.trim());
                return values;
            });

            console.log(`CSV parsed successfully: ${headers.length} columns, ${data.length} rows`);
            return res.json({
                columns: headers,
                data: data
            });
        } else {
            console.error('No results file found');
            return res.status(404).json({ message: 'No results file found' });
        }
    } catch (error) {
        console.error(`Error reading CSV file: ${error.message}`);
        return res.status(500).json({ message: `Error: ${error.message}` });
    }
});

app.post('/execute-agent', (req, res) => {
    const { query, agentPath } = req.body;

    if (!query) {
        return res.status(400).json({ message: 'Query is required' });
    }

    // Determine agent path - use provided path or try to find it
    let finalAgentPath = agentPath;

    if (!finalAgentPath || !fs.existsSync(finalAgentPath)) {
        // Default path - combine the root path with the default filename
        const defaultPath = path.join(AGENT_ROOT_PATH, DEFAULT_AGENT_FILENAME);

        if (fs.existsSync(defaultPath)) {
            finalAgentPath = defaultPath;
        } else {
            // If default agent is not found, try to find any Python file in the directory
            console.log(`Looking for Python files in ${AGENT_ROOT_PATH}`);
            try {
                const files = fs.readdirSync(AGENT_ROOT_PATH);
                const pythonFiles = files.filter(file => file.endsWith('.py'));

                if (pythonFiles.length > 0) {
                    finalAgentPath = path.join(AGENT_ROOT_PATH, pythonFiles[0]);
                    console.log(`Found Python file: ${pythonFiles[0]}`);
                } else {
                    console.error('No Python files found in the specified directory.');
                    return res.status(404).json({
                        message: 'No Python agent files found in the specified directory.'
                    });
                }
            } catch (err) {
                console.error(`Error reading directory: ${err.message}`);
                return res.status(500).json({
                    message: `Error locating agent files: ${err.message}`
                });
            }
        }
    }

    console.log(`Executing agent with query: "${query}"`);
    console.log(`Agent path: ${finalAgentPath}`);

    // Execute the Python script with the query
    const command = `python "${finalAgentPath}" "${query}"`;

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error}`);
            return res.status(500).json({ message: `Error: ${error.message}` });
        }

        if (stderr) {
            console.error(`Python script stderr: ${stderr}`);
            // Some scripts may output to stderr but still work correctly
            console.log(`Python script stdout: ${stdout}`);
            // If stdout exists, we'll still return it along with the stderr
            if (stdout) {
                return res.json({ result: stdout, warning: stderr });
            }
            return res.status(500).json({ message: `Error: ${stderr}` });
        }

        console.log(`Python script result: ${stdout.substring(0, 100)}...`);
        // Return the stdout as the result
        return res.json({ result: stdout });
    });
});

// Handle options preflight requests for CORS
app.options('*', cors());

const serverInfo = `
=======================================================
🤖 AI Agent Server
=======================================================
Server is running at: http://localhost:${port}
Health check: http://localhost:${port}/health

To use this server:
1. Keep this terminal window open
2. The chat UI will automatically connect to this server

Python agent directory: ${AGENT_ROOT_PATH}
Default agent file: ${DEFAULT_AGENT_FILENAME}
SQL query file: ${SQL_QUERY_FILE}
Query executor script: ${QUERY_EXECUTOR_SCRIPT}
Query results file: ${QUERY_RESULTS_FILE}

To start the server, run: node agent-server.js
=======================================================
`;

app.listen(port, () => {
    console.log(serverInfo);
});
