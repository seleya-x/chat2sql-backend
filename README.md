# PJT Chat2SQL Backend

## Overview

The Chat2SQL backend is a Node.js and Python-based application that powers the natural language to SQL conversion functionality. It integrates with OpenRouter API for AI-powered SQL generation and provides authentication and user management through Supabase.

## Features

- **Natural Language to SQL Conversion**: Converts plain English questions to SQL queries
- **SQL Query Execution**: Executes generated SQL queries against the target database
- **User Management API**: Endpoints for managing users and permissions
- **Authentication**: Secure API with Supabase integration for authentication
- **Database Schema Management**: Tools for extracting and managing database schema information

## Recent Updates

- **OpenRouter Integration**: Updated integration with OpenRouter for SQL generation
- **Admin API**: Enhanced admin functionality for user management
- **Security Improvements**: Added role-based authentication for admin routes

## Technology Stack

- **Server**: Node.js with Express
- **AI Integration**: OpenRouter API (o3-mini-high model)
- **Authentication**: Supabase Auth with Service Role access
- **Database**: MySQL/MariaDB compatibility for SQL execution

## Setup and Installation

### Prerequisites

- Node.js (v16+)
- Python 3.8+
- npm or yarn
- Access to a MySQL/MariaDB database (for SQL execution)
- OpenRouter API key
- Supabase project with service role key

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Database Configuration
DB_HOST=your-db-host.database.azure.com
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_PORT=3306
DB_NAME=your-db-name
DB_SSL=true
DB_SSL_VERIFY=false

# OpenRouter API Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_MODEL=o3-mini-high

# Server Configuration
FLASK_PORT=5002
FLASK_DEBUG=true
NODE_PORT=3001

# File Paths
SQL_QUERY_FILE=sql_query.txt
RESULTS_CSV_FILE=deal_extract_docs_results.csv
SCHEMA_FILE=database_schema_relationships_llm.json
HISTORY_FILE=chat_history.json

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Navigate to project directory
cd chat2sql-backend

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Start the server
node agent-server.js
```

The server will start on the port specified in your `.env` file (default: 3001).

## API Endpoints

### Chat API

- `POST /api/chat` - Process a chat message and generate SQL
- `POST /api/execute` - Execute a SQL query and return results
- `GET /api/schema` - Get the database schema

### Admin API

- `GET /api/admin/users` - List all users (admin only)
- `POST /api/admin/users` - Create a new user (admin only)
- `PUT /api/admin/users/:id` - Update a user (admin only)
- `DELETE /api/admin/users/:id` - Delete a user (admin only)

### Health Checks

- `GET /health` - Server health check

## Architecture

The backend consists of two main components:

1. **Node.js Server**: Handles API requests, authentication, and user management
2. **Python AI Module**: Processes natural language and generates SQL queries

The communication flow is as follows:

1. User sends a natural language question through the frontend
2. Node.js server authenticates the request and forwards it to the Python module
3. Python module uses OpenRouter API to convert the question to SQL
4. The SQL query is returned to the Node.js server
5. Node.js server executes the query against the target database
6. Results are returned to the frontend

## Security

- All API endpoints (except health checks) require authentication
- Admin endpoints require the user to have the `admin` role in their Supabase profile
- Database credentials are securely stored in environment variables
- OpenRouter API key is stored in environment variables and not exposed to clients