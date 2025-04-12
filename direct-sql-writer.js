/**
 * Simple utility to directly write SQL query to the file
 * This bypasses all other processing
 */

const fs = require('fs');
const path = require('path');

// Path to the SQL query file
const sqlFilePath = path.join(__dirname, 'sql_query.txt');

// Function to write SQL to file
function writeSqlToFile(sql) {
  try {
    // Delete existing file if it exists
    if (fs.existsSync(sqlFilePath)) {
      fs.unlinkSync(sqlFilePath);
    }
    
    // Write SQL directly to file
    fs.writeFileSync(sqlFilePath, sql, 'utf8');
    
    // Read file back to verify
    const fileContent = fs.readFileSync(sqlFilePath, 'utf8');
    
    // Return comparison result
    return {
      success: fileContent === sql,
      fileContent,
      originalLength: sql.length,
      fileLength: fileContent.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Get SQL from command line arguments
const sql = process.argv[2];

if (!sql) {
  console.error('Error: No SQL provided');
  process.exit(1);
}

// Write to file and print result
const result = writeSqlToFile(sql);
console.log(JSON.stringify(result, null, 2));

if (result.success) {
  process.exit(0);
} else {
  process.exit(1);
}
