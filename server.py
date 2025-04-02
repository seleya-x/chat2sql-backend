#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Server script to handle SQL Query UI requests
"""

import os
import json
import subprocess
import pandas as pd
import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'sql_query_ui.html')

@app.route('/run-agent', methods=['POST'])
def run_agent():
    try:
        data = request.json
        query = data.get('query', '')
        
        # Print debug information
        print(f"Running agent_openrouter.py with query: {query}")
        
        # Run the agent_openrouter.py script with the query
        # Use the full path to the script and set the working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'agent_openrouter.py')
        cmd = ['python3', script_path, query]
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=script_dir  # Set the working directory to the script directory
        )
        
        # Print debug information about the result
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode != 0:
            return jsonify({
                'success': False, 
                'error': result.stderr,
                'command': ' '.join(cmd),
                'returncode': result.returncode
            }), 500
        
        # Read the generated SQL query
        sql_path = os.path.join(script_dir, 'sql_query.txt')
        with open(sql_path, 'r') as f:
            sql_query = f.read()
        
        return jsonify({
            'success': True, 
            'output': result.stdout,
            'sql_query': sql_query
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Exception: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_traceback
        }), 500

@app.route('/run-query', methods=['POST'])
def run_query():
    try:
        # Run run_specific_query.py with the correct path and working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'run_specific_query.py')
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            check=False,
            cwd=script_dir  # Set the working directory to the script directory
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False, 
                'error': result.stderr,
                'returncode': result.returncode
            }), 500
        
        # Read the results from the CSV file
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            results_path = os.path.join(script_dir, 'deal_extract_docs_results.csv')
            df = pd.read_csv(results_path)
            # Replace NaN values with empty strings
            df = df.fillna('')
            # Convert DataFrame to JSON
            results = df.to_dict(orient='records')
            return jsonify({
                'success': True, 
                'output': result.stdout,
                'results': results,
                'columns': df.columns.tolist()
            })
        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f"Error reading results: {str(e)}"
            }), 500
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Exception: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_traceback
        }), 500

@app.route('/get-sql', methods=['GET'])
def get_sql():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_path = os.path.join(script_dir, 'sql_query.txt')
        with open(sql_path, 'r') as file:
            sql_query = file.read()
        return sql_query
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return str(e), 500

@app.route('/new-query', methods=['POST'])
def new_query():
    try:
        data = request.json
        human_query = data.get('human_query', '')
        sql_query = data.get('sql_query', '')
        
        # Read current results if they exist
        results = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        results_path = os.path.join(script_dir, 'deal_extract_docs_results.csv')
        try:
            if os.path.exists(results_path):
                df = pd.read_csv(results_path)
                results = df.to_dict(orient='records')
        except Exception as e:
            print(f"Error reading results: {str(e)}")
        
        # Create history entry
        history_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'human_query': human_query,
            'sql_query': sql_query,
            'results': results
        }
        
        # Load existing history or create new
        history = []
        history_path = os.path.join(script_dir, 'chat_history.json')
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # If file exists but is invalid JSON, start fresh
                history = []
        
        # Add new entry to history
        history.append(history_entry)
        
        # Save updated history
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Clear current query and results
        sql_path = os.path.join(script_dir, 'sql_query.txt')
        with open(sql_path, 'w') as f:
            f.write('')
        
        # Create empty CSV with header
        if os.path.exists(results_path):
            with open(results_path, 'w') as f:
                f.write('deal_id,target,acquiror,announcement_date,target_advisor,acquiror_advisor\n')
        
        return jsonify({'success': True, 'message': 'Query saved to history and cleared'})
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Exception: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_traceback
        }), 500

@app.route('/get-history', methods=['GET'])
def get_history():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        history_path = os.path.join(script_dir, 'chat_history.json')
        print(f"Looking for history file at: {history_path}")
        
        if os.path.exists(history_path):
            print(f"History file found, size: {os.path.getsize(history_path)} bytes")
            with open(history_path, 'r') as f:
                history = json.load(f)
            print(f"Loaded {len(history)} history entries")
            return jsonify(history)
        else:
            print("History file not found, returning empty list")
            return jsonify([])
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error loading history: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500

@app.route('/delete-history-item', methods=['POST'])
def delete_history_item():
    try:
        data = request.json
        index = data.get('index')
        
        if index is None:
            return jsonify({'error': 'No index provided'}), 400
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        history_path = os.path.join(script_dir, 'chat_history.json')
        
        if not os.path.exists(history_path):
            return jsonify({'error': 'History file not found'}), 404
        
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        if index < 0 or index >= len(history):
            return jsonify({'error': f'Invalid index: {index}'}), 400
        
        # Remove the item at the specified index
        removed_item = history.pop(index)
        
        # Save the updated history
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Deleted history item at index {index}")
        return jsonify({'success': True, 'removed_item': removed_item})
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error deleting history item: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
