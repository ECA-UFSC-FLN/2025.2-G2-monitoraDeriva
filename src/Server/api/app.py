# app.py
from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import sql
import os
import time
from datetime import datetime

app = Flask(__name__)

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
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

@app.route('/location', methods=['POST'])
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
            INSERT INTO deriva_points (sender_id, timestamp, latitude, longitude, gps_module_id)
            VALUES (%s, %s, %s, %s, %s)
        ''')
        cur.execute(insert_query, (sender_id, datetime.fromtimestamp(timestamp), latitude, longitude, gps_module_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/', methods=['GET'])
def hello():
    return 'Olá, mundo!'

if __name__ == '__main__':
    app.run(debug=True)