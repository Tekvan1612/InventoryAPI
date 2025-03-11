from flask import Flask, request, jsonify
import psycopg2
import json
import os
import urllib.parse as urlparse

app = Flask(__name__)

def get_db_connection():
    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set!")

    url = urlparse.urlparse(DATABASE_URL)

    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode='require'
    )
    print("Database connection successful!")
    return conn

def call_postgresql_function(action, params):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT inventory_api(%s, %s::jsonb)", (action, json.dumps(params)))
        result = cur.fetchone()[0]
        cur.close()
        conn.close()
        return result, {'message': 'Query executed successfully', 'status': 1}
    except Exception as e:
        print(f"Error executing query: {e}")
        return None, {'message': 'Internal server error', 'status': 0}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    action = 'login'
    result, response = call_postgresql_function(action, data)

    if response['status'] == 0:
        return jsonify(response), 500

    if result and result['password'] == data.get('password'):
        return jsonify({'message': 'Login successful', 'status': 1}), 200
    else:
        return jsonify({'message': 'Invalid credentials', 'status': 0}), 401

@app.route('/jobs', methods=['GET'])
def get_jobs_delivery_challan():
    action = 'get_jobs'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    return jsonify({'jobs': result, 'status': 1}), 200

@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_by_id(job_id):
    data = call_inventory_api('get_job_by_temp_id_with_details', {'temp_id': job_id})
    return jsonify({'job': data, 'status': 1})


@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    print(f"Received data: {data}")  
    action = 'insert_scanned_info'
    result, response = call_postgresql_function(action, data)
    print(f"Result from PostgreSQL function: {result}")  

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Details not found', 'status': 0}), 404

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
