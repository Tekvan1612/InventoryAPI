from flask import Flask, request, jsonify
import psycopg2
import json
import os
import urllib.parse as urlparse
from datetime import datetime

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
        return jsonify({'message': 'Login successful', 'status': 1, 'user_id': result.get('user_id')}), 200
    else:
        return jsonify({'message': 'Invalid credentials', 'status': 0}), 401


@app.route('/jobs', methods=['GET'])
def get_jobs_delivery_challan():
    action = 'get_jobs'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    return jsonify({'jobs': result, 'status': 1}), 200

@app.route('/jobs/<int:temp_id>', methods=['GET'])
def get_job_details(temp_id):
    action = 'get_job_by_temp_id_with_details'
    params = {'temp_id': temp_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200


@app.route('/jobs/<int:temp_id>/<path:equipment_detail_id>', methods=['GET'])
def get_equipment_details(temp_id, equipment_detail_id):
    print(
        f"Fetching equipment details for temp_id: {temp_id}, equipment_detail_id: {equipment_detail_id}")  # Debugging line
    action = 'get_equipment_by_detail_id'  # New action for fetching equipment details
    params = {'temp_id': temp_id, 'equipment_detail_id': equipment_detail_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Equipment details not found', 'status': 0}), 404

    return jsonify({'equipment': result, 'status': 1}), 200

@app.route('/jobs_for_venue_out', methods=['GET'])
def get_jobs_for_venue_out():
    action = 'get_jobs_for_venue_out'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    return jsonify({'jobs': result, 'status': 1}), 200

@app.route('/venue/<int:temp_id>', methods=['GET'])
def get_job_details_for_venue(temp_id):
    action = 'get_job_by_temp_id_with_details_for_venue'
    params = {'temp_id': temp_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200

@app.route('/title/<int:temp_id>', methods=['GET'])
def get_job_details_for_scan_in(temp_id):
    action = 'get_job_by_temp_id_with_details_for_scan_in'
    params = {'temp_id': temp_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200

@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    print("Received data:", data)

    action = 'insert_scanned_info'
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT inventory_api(%s, %s::jsonb)", (action, json.dumps(data)))
        result_row = cursor.fetchone()
        conn.commit()
        print("Raw DB Response:", result_row)

        if result_row:
            result = result_row[0]
            print("Formatted Response:", result)  # Log output for debugging
            
            # 🟢 **Fix for Datetime Handling**
            if 'inserted_record' in result and isinstance(result['inserted_record'], dict):
                if 'scan_out_date_time' in result['inserted_record']:
                    scan_time = result['inserted_record']['scan_out_date_time']
                    if isinstance(scan_time, datetime):  
                        result['inserted_record']['scan_out_date_time'] = scan_time.strftime('%Y-%m-%d %H:%M:%S')

    except Exception as e:
        conn.rollback()
        error_message = str(e)
        print("🚨 Database Error:", error_message)  # Log the actual error
        return jsonify({'message': 'Database Error', 'error': error_message, 'status': 0}), 500
    finally:
        cursor.close()
        conn.close()

    # ✅ **Fixed Return Statement**
    return jsonify(result), 200 if result.get('status') == 1 else (jsonify(result), 400)

@app.route('/venue_out', methods=['POST'])
def venue_out():
    data = request.get_json()
    print("📥 Received data:", data)  # Debugging

    action = 'venue_out'
    
    # Ensure `user_id` is included in the request payload
    if 'user_id' not in data:
        return jsonify({'message': 'User ID is required', 'status': 0}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT inventory_api(%s, %s::jsonb)", (action, json.dumps(data)))
        result_row = cursor.fetchone()
        conn.commit()
        print("🛠️ Raw DB Response:", result_row)  # Debugging

        if result_row:
            result = result_row[0]
            print("📢 Formatted Response:", result)  # Debugging

            # 🟢 Fix for Datetime Handling
            if 'inserted_record' in result and isinstance(result['inserted_record'], dict):
                if 'venue_out_date' in result['inserted_record']:
                    venue_time = result['inserted_record']['venue_out_date']
                    if isinstance(venue_time, datetime):
                        result['inserted_record']['venue_out_date'] = venue_time.strftime('%Y-%m-%d %H:%M:%S')

    except Exception as e:
        conn.rollback()
        error_message = str(e)
        print("🚨 Database Error:", error_message)  # Log the actual error
        return jsonify({'message': 'Database Error', 'error': error_message, 'status': 0}), 500
    finally:
        cursor.close()
        conn.close()

    # ✅ Fixed Return Statement
    return jsonify(result), 200 if result.get('status') == 1 else (jsonify(result), 400)


@app.route('/scan_in', methods=['POST'])
def scan_in():
    data = request.get_json()
    print(f"Received data: {data}")
    action = 'global_scanned_in'
    result, response = call_postgresql_function(action, data)
    print(f"Result from PostgreSQL function: {result}")
    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Details not found', 'status': 0}), 404

    return jsonify(result), 200


@app.route('/title', methods=['GET'])
def get_title_delivery_challan():
    action = 'get_title'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    return jsonify({'jobs': result, 'status': 1}), 200


@app.route('/title/<int:temp_id>/<path:equipment_detail_id>', methods=['GET'])
def get_title_details_with_barcodes(temp_id, equipment_detail_id):
    action = 'get_title_by_id'
    params = {'temp_id': temp_id, 'equipment_detail_id': equipment_detail_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200


@app.route('/scan_in_title', methods=['POST'])
def scan_in_title():
    data = request.get_json()
    print(f"Received data: {data}")
    action = 'insert_scanned_in'

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        result, response = call_postgresql_function(action, data)
        print(f"Result from PostgreSQL function: {result}")

        if response['status'] == 0:
            conn.rollback()
            return jsonify(response), 500

        if not result:
            conn.rollback()
            return jsonify({'message': 'Details not found', 'status': 0}), 404

        conn.commit()
        return jsonify(result), 200

    except Exception as e:
        conn.rollback()
        error_message = str(e)
        print(f"Database Error: {error_message}")
        return jsonify({'message': 'Database Error', 'error': error_message, 'status': 0}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/crew/<int:temp_id>', methods=['GET'])
def get_crew_details(temp_id):
    action = 'get_crew'
    params = {'temp_id': temp_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Details not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200


@app.route('/crew', methods=['GET'])
def get_crew_details_with_id():
    action = 'get_crew_with_id'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    return jsonify({'jobs': result, 'status': 1}), 200


@app.route('/venue/<int:temp_id>/<path:equipment_detail_id>', methods=['GET'])
def get_details_for_venue_out_by_id(temp_id, equipment_detail_id):
    action = 'get_details_for_venue_out_by_id'
    params = {'temp_id': temp_id, 'equipment_detail_id': equipment_detail_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Job not found', 'status': 0}), 404

    return jsonify({'job': result, 'status': 1}), 200


@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    user_id = data.get('user_id')
    new_password = data.get('new_password')
    retype_new_password = data.get('retype_new_password')

    if not user_id or not new_password or not retype_new_password:
        return jsonify({"message": "Missing parameters", "status": 0}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed", "status": 0}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user_master WHERE status = TRUE AND user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "User not found", "status": 0}), 404

        current_password = result[0]

        if new_password != retype_new_password:
            return jsonify({"message": "Passwords do not match", "status": 0}), 400

        if new_password == current_password:
            return jsonify({"message": "Password already exists!!! Try a different password", "status": 0}), 400

        cursor.execute("UPDATE user_master SET password = %s WHERE status = TRUE AND user_id = %s",
                       (new_password, user_id))
        conn.commit()

        return jsonify({"message": "Password updated successfully", "status": 1}), 200
    except Exception as e:
        print(f"Error executing query: {e}")
        return jsonify({"message": "An error occurred", "status": 0}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/employee', methods=['GET'])
def get_employee_details():
    action = 'get_employee'
    result, response = call_postgresql_function(action, {})

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Employee not found', 'status': 0}), 404

    return jsonify({'Employee': result, 'status': 1}), 200


@app.route('/employee/<int:user_id>', methods=['GET'])
def get_employee_details_with_user_id(user_id):
    action = 'get_employee_by_user_id'
    params = {'user_id': user_id}
    result, response = call_postgresql_function(action, params)

    if response['status'] == 0:
        return jsonify(response), 500

    if not result:
        return jsonify({'message': 'Employee not found', 'status': 0}), 404

    return jsonify({'Employee': result, 'status': 1}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
