/**
 * Test script to verify that SQL queries are written exactly as provided to the sql_query.txt file
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Test queries with different formats and special characters
const testQueries = [
  // Simple query
  "SELECT * FROM users LIMIT 10;",
  
  // Query with multiple lines and indentation
  `SELECT 
    id, 
    name, 
    email
  FROM 
    users 
  WHERE 
    status = 'active'
  LIMIT 5;`,
  
  // Query with special characters
  "SELECT * FROM products WHERE name LIKE '%special & chars%' AND price > 100;",
  
  // Complex query with subqueries and joins
  `SELECT ds.deal_id AS DealID, ds.target_name AS Target, ds.acquiror_name AS Acquiror, ds.date_announced AS AnnouncementDate,
  ds.acquiror_parent_name AS acquiror_parent, ds.acquiror_ultimate_parent_name AS acquiror_ultimate_parent 
FROM deals_summary ds
WHERE ( LOWER(ds.acquiror_name) LIKE '%broadcom%' OR LOWER(ds.acquiror_parent_name) LIKE '%broadcom%' OR LOWER(ds.acquiror_ultimate_parent_name) LIKE '%broadcom%' ) 
  AND ds.date_announced >= '2015-01-01'
ORDER BY ds.date_announced DESC
LIMIT 10;`,

  // Query with HTML-like characters that might get encoded
  "SELECT * FROM table WHERE column < 10 AND column > 5;"
];

// Function to test writing a query and verifying it was written correctly
async function testQueryWrite(query) {
  console.log('----------------------------------------');
  console.log('TESTING QUERY:');
  console.log(query);
  
  try {
    // Call the API to write the query to the file
    const response = await axios.post('http://localhost:3001/api/write-sql-file', {
      query: query
    });
    
    // Check if the API call was successful
    if (!response.data.success) {
      console.error('API call failed:', response.data);
      return false;
    }
    
    // Read the file back to verify contents
    const sqlFilePath = path.join(__dirname, 'sql_query.txt');
    const fileContent = fs.readFileSync(sqlFilePath, 'utf8');
    
    // Compare original query with file content
    console.log('ORIGINAL LENGTH:', query.length);
    console.log('FILE LENGTH:', fileContent.length);
    
    // Check if they match
    const matches = query === fileContent;
    console.log('MATCHES:', matches);
    
    if (!matches) {
      console.log('ORIGINAL:');
      console.log(JSON.stringify(query));
      console.log('FILE CONTENT:');
      console.log(JSON.stringify(fileContent));
      console.log('DIFFERENCE:');
      
      // Log character by character comparison for the first difference
      for (let i = 0; i < Math.min(query.length, fileContent.length); i++) {
        if (query[i] !== fileContent[i]) {
          console.log(`Difference at position ${i}:`);
          console.log(`Original: "${query.charCodeAt(i)}" (${query[i]})`);
          console.log(`File: "${fileContent.charCodeAt(i)}" (${fileContent[i]})`);
          break;
        }
      }
    }
    
    return matches;
  } catch (error) {
    console.error('Error during test:', error.message);
    return false;
  }
}

// Main function to run all tests
async function runTests() {
  console.log('STARTING SQL WRITE TESTS');
  let passedTests = 0;
  
  for (let i = 0; i < testQueries.length; i++) {
    console.log(`\nTEST ${i+1}/${testQueries.length}`);
    const passed = await testQueryWrite(testQueries[i]);
    if (passed) {
      passedTests++;
    }
  }
  
  console.log('\n----------------------------------------');
  console.log(`TEST RESULTS: ${passedTests}/${testQueries.length} passed`);
}

// Run the tests
runTests().catch(console.error);
