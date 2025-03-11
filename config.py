import os
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Parse DATABASE_URL
url = urlparse(DATABASE_URL)

DB_NAME = url.path[1:]  # removes the leading '/'
USER = url.username
PASSWORD = url.password
HOST = url.hostname
PORT = url.port

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        sslmode='require'
    )

# Usage
try:
    conn = get_connection()
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")
