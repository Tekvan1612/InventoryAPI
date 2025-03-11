import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables!")

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")
