from flask import Flask, request, jsonify
import psycopg2
import json
import config  # Import the config module

app = Flask(__name__)


def get_db_connection():
    try:
        print(f"Connecting to database {config.DB_NAME} at {config.DB_HOST} with user {config.DB_USER}")
        conn = psycopg2.connect(
            host=config.DB_HOST,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        print("Database connection successful")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None


def call_postgresql_function(action, params):
    conn = get_db_connection()
    if conn is None:
        return None, {'message': 'Database connection failed', 'status': 0}

    try:
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
def get_job_details_with_barcodes(job_id):
    action = 'get_job_by_id'
    params = {'job_id': job_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200


@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    print(f"Received data: {data}")  # Log received data
    action = 'insert_scanned_info'
    result, response = call_postgresql_function(action, data)
    print(f"Result from PostgreSQL function: {result}")  # Log PostgreSQL function result

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Details not found', 'status': 0}), 404

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
