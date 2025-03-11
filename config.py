import os

DB_HOST = os.getenv('DB_HOST', 'host.docker.internal')  # Use host.docker.internal to refer to the host machine
DB_NAME = os.getenv('DB_NAME', 'wms')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'kvan')
