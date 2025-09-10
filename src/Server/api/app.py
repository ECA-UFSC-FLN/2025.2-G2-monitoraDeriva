# app.py
from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import sql
import os

app = Flask(__name__)

DB_HOST = 'localhost'
DB_NAME = os.getenv('POSTGRES_DB', 'derivadores')
DB_USER = os.getenv('POSTGRES_USER', 'root')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            sender_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            gps_module_id VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    sender_id = data.get('sender_id')
    timestamp = data.get('timestamp')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    gps_module_id = data.get('gps_module_id')

    if not all([sender_id, timestamp, latitude, longitude, gps_module_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        insert_query = sql.SQL('''
            INSERT INTO locations (sender_id, timestamp, latitude, longitude, gps_module_id)
            VALUES (%s, %s, %s, %s, %s)
        ''')
        cur.execute(insert_query, (sender_id, timestamp, latitude, longitude, gps_module_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Data inserted successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)