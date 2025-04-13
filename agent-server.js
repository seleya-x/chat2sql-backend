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
    cwd: '/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend' 
  }, (error, stdout, stderr) => {
    if (error) {
      console.error(`Execution error: ${error}`);
      return res.status(500).json({ error: 'Failed to execute agent', details: stderr });
    }
    
    console.log(`Agent response: ${stdout}`);
    return res.status(200).json({ response: stdout });
  });
});

// Helper function to ensure SQL query is properly formatted for execution
function cleanSqlQuery(sqlQuery) {
  if (!sqlQuery) return '';
  
  // Trim leading/trailing whitespace
  let cleanQuery = sqlQuery.trim();
  
  // Remove any HTML entities or formatting artifacts that might be present
  cleanQuery = cleanQuery.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  
  // Ensure SELECT keyword is uppercase (helps with detection)
  if (cleanQuery.toLowerCase().startsWith('select')) {
    const selectIndex = cleanQuery.toLowerCase().indexOf('select');
    cleanQuery = 'SELECT' + cleanQuery.substring(selectIndex + 6);
  }
  
  console.log('SQL query cleaned for execution');
  return cleanQuery;
}

// API endpoint to execute a specific query
app.post('/api/execute-query', (req, res) => {
  // Get the raw query from request body WITHOUT ANY PROCESSING
  let { query } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: 'Query is required' });
  }

  console.log('---------- RAW QUERY EXECUTION ----------');
  console.log('Original query as received from client:');
  console.log(query);
  
  // IMPORTANT: Write exactly what we received - no cleaning, no processing
  // Use the SQL_QUERY_FILE environment variable instead of hardcoding the filename
  const sqlQueryFile = process.env.SQL_QUERY_FILE || 'sql_query.txt';
  const tempFilePath = path.join(__dirname, sqlQueryFile);
  
  try {
    // Delete the file if it exists first
    if (fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
    
    // Write the EXACT query to file with no transformations
    fs.writeFileSync(tempFilePath, query);
    
    // Verify file was written correctly
    const writtenContent = fs.readFileSync(tempFilePath, 'utf8');
    
    // Log the SQL for debugging
    console.log(`SQL written to ${tempFilePath} (${writtenContent.length} chars)`);
    
    // Check for exact match
    if (writtenContent !== query) {
      console.error('CRITICAL ERROR: File content does not match the original query');
      console.error(`Original length: ${query.length}, file length: ${writtenContent.length}`);
      
      // Write to a diagnostic file to help debug
      fs.writeFileSync('sql_query_original.txt', query);
      fs.writeFileSync('sql_query_file.txt', writtenContent);
      
      console.error('Diagnostic files written for comparison');
    }
  } catch (writeError) {
    console.error(`Error writing SQL query to file: ${writeError}`);
    return res.status(500).json({ error: 'Failed to save query to file', details: writeError.message });
  }
  
  // Execute the Python script with the query
  const command = `python run_specific_query.py`;
  
  console.log(`Executing query with python script...`);
  
  exec(command, { 
    cwd: '/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend' 
  }, (error, stdout, stderr) => {
    if (error) {
      console.error(`Execution error: ${error}`);
      return res.status(500).json({ error: 'Failed to execute query', details: stderr });
    }
    
    // Try to read the CSV file
    try {
      const csvPath = path.join('/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend', 'deal_extract_docs_results.csv');
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

// API endpoint to directly write SQL to file
app.post('/api/write-sql-file', (req, res) => {
  const { query } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: 'Query is required', success: false });
  }

  console.log('\n-------- DIRECT SQL FILE WRITE --------');
  console.log('Writing SQL directly to file:', query);
  
  // Create the file path - absolute path to ensure reliability
  const sqlFilePath = path.join('/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend', 'sql_query.txt');
  
  try {
    // Delete the file if it exists
    if (fs.existsSync(sqlFilePath)) {
      fs.unlinkSync(sqlFilePath);
    }
    
    // Write the query directly to the file
    fs.writeFileSync(sqlFilePath, query, { encoding: 'utf8' });
    
    // Verify content was written correctly
    const writtenContent = fs.readFileSync(sqlFilePath, 'utf8');
    console.log('SQL query file created successfully with query:\n', writtenContent);
    
    return res.json({ success: true, message: 'SQL query written to file' });
  } catch (error) {
    console.error('Error writing SQL file:', error);
    return res.status(500).json({ error: 'Failed to write SQL file', success: false });
  }
});

// API endpoint to execute a query from the file
app.post('/api/execute-query-from-file', (req, res) => {
  console.log('\n-------- EXECUTING QUERY FROM FILE --------');
  
  // Path to the query file
  const sqlFilePath = path.join('/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend', 'sql_query.txt');
  
  // Check if the file exists
  if (!fs.existsSync(sqlFilePath)) {
    return res.status(400).json({ error: 'SQL query file not found' });
  }
  
  // Read the file content for logging
  try {
    const fileContent = fs.readFileSync(sqlFilePath, 'utf8');
    console.log('Executing query from file:\n', fileContent);
  } catch (error) {
    console.error('Error reading SQL file:', error);
  }
  
  // Execute the Python script
  const command = `python run_specific_query.py`;
  
  console.log('Executing Python script with SQL file...');
  
  exec(command, {
    cwd: '/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend'
  }, (error, stdout, stderr) => {
    if (error) {
      console.error(`Execution error: ${error}`);
      return res.status(500).json({ error: 'Failed to execute query', details: stderr });
    }
    
    // Try to read the CSV file
    try {
      const csvPath = path.join('/Users/buzzdog/Library/CloudStorage/OneDrive-Personal/Documents/Code/PJT/chat2sql-backend', 'deal_extract_docs_results.csv');
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

