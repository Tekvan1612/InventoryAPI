import os
import psycopg2
import urllib.parse as urlparse

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set!")

url = urlparse.urlparse(DATABASE_URL)

dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
        sslmode='require'
    )
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
