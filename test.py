import psycopg2
import json


def test_insert_scanned_info():
    conn = psycopg2.connect(
        host="host.docker.internal",
        dbname="wms",
        user="postgres",
        password="kvan"
    )
    cur = conn.cursor()

    action = 'insert_scanned_info'
    params = {
        "job_id": 5,
        "equipment_id": 18,
        "barcode": "1234555",
        "scan_date_time": "15-07-2024 10:38:00",
        "user_id": 1
    }

    try:
        cur.execute("SELECT test_insert_scanned_info(%s, %s::jsonb)", (action, json.dumps(params)))
        result = cur.fetchone()[0]
        conn.commit()  # Ensure commit is called to persist the changes
        print(f"Query result: {result}")
    except Exception as e:
        conn.rollback()
        print(f"Error executing query: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    test_insert_scanned_info()
