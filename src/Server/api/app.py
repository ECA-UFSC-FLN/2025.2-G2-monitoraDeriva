import os
import bcrypt
import json
import requests
import math
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import jwt

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    "allow_headers": "*",
    "supports_credentials": True,
    "max_age": 86400
}})

DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_BASE_URL = os.getenv("API_BASE_URL")

conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASSWORD}'"
print("String de conexão com o PostgreSQL configurada.")

# --- GESTÃO DE AUTENTICAÇÃO (DECORATOR) ---

def token_required(f):
    """Decorator para proteger endpoints que exigem um token JWT."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({"error": "Formato de token inválido. Use 'Bearer <token>'."}), 401
        
        if not token:
            return jsonify({"error": "Token de autenticação em falta."}), 401
        
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "O seu token expirou. Por favor, faça login novamente."}), 401
        except Exception as e:
            print(f"Erro de token: {e}")
            return jsonify({"error": "Token inválido."}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# --- FUNÇÕES AUXILIARES ---

def send_telegram_message(chat_id: str, text: str, reply_markup=None):
    """Envia uma mensagem via bot do Telegram."""
    if not all([TELEGRAM_BOT_TOKEN, chat_id]):
        print("ERRO: Credenciais do Telegram não configuradas.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"Mensagem enviada para o Chat ID {chat_id}")
    except Exception as e:
        print(f"ERRO ao enviar mensagem via Telegram: {e}")

def check_for_alerts(data: dict):
    """Verifica os dados do derivador e envia alertas (Geofencing e Bateria)."""
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    battery = data.get('battery_level')
    alert_messages = []

    MAX_DISTANCE_KM = 40.0
    COASTLINE_LONGITUDE = -48.6 
    if latitude is not None and longitude is not None:
        lat_rad = math.radians(latitude)
        km_per_degree_lon = 111.32 * math.cos(lat_rad)
        distance_from_coast = abs(longitude - COASTLINE_LONGITUDE) * km_per_degree_lon
        if distance_from_coast > MAX_DISTANCE_KM:
            msg = (f"<b>ALERTA DE GEOFENCING:</b> Derivador '{data.get('gps_module_id')}' está a "
                   f"<b>{distance_from_coast:.2f} km</b> da costa (limite: {MAX_DISTANCE_KM} km).")
            alert_messages.append(msg)

    if battery is not None and battery < 20:
        msg = f"<b>ALERTA DE BATERIA BAIXA:</b> Derivador '{data.get('gps_module_id')}' está com <b>{battery}%</b> de bateria."
        alert_messages.append(msg)

    if alert_messages:
        full_alert = "\n\n".join(alert_messages)
        send_telegram_message(TELEGRAM_CHAT_ID, full_alert)

# --- ENDPOINTS DE AUTENTICAÇÃO E APROVAÇÃO ---

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.json
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                    (email, hashed_password.decode('utf-8'))
                )
                user_id = cur.fetchone()[0]
                conn.commit()
                approve_link = f"{API_BASE_URL}/auth/approve/{user_id}"
                deny_link = f"{API_BASE_URL}/auth/deny/{user_id}"
                message = f"<b>Nova solicitação de acesso</b>\n\n<b>Email:</b> {email}\n\nEscolha uma ação:"
                reply_markup = {"inline_keyboard": [[{"text": "✅ Aprovar", "url": approve_link}, {"text": "❌ Negar", "url": deny_link}]]}
                send_telegram_message(TELEGRAM_CHAT_ID, message, reply_markup)
                return jsonify({"message": "Pedido de registo enviado. Aguarde a aprovação do administrador."}), 201
    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "Este email já está registado."}), 409
    except Exception as e:
        print(f"ERRO no registo: {e}")
        return jsonify({"error": "Erro interno do servidor."}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():

    #apagar essa parte em produção
    token = jwt.encode({
                        'user_id': '0',
                        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({"message": "Login bem-sucedido.", "token": token}), 200

    data = request.json
    email, password = data.get('email'), data.get('password')
    try:
        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password_hash, is_approved FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    if not user['is_approved']:
                        user_id = user['id']
                        print(f"Tentativa de login por utilizador não aprovado: {email}. A reenviar notificação.")
                        approve_link = f"{API_BASE_URL}/auth/approve/{user_id}"
                        deny_link = f"{API_BASE_URL}/auth/deny/{user_id}"
                        message = (f"<b>LEMBRETE: Tentativa de login pendente</b>\n\n"
                                   f"O utilizador <b>{email}</b> tentou fazer login mas ainda não foi aprovado.\n\n"
                                   f"Escolha uma ação:")
                        reply_markup = {"inline_keyboard": [[{"text": "✅ Aprovar Agora", "url": approve_link}, {"text": "❌ Negar Acesso", "url": deny_link}]]}
                        send_telegram_message(TELEGRAM_CHAT_ID, message, reply_markup)
                        return jsonify({"error": "Sua conta ainda não foi aprovada por um administrador."}), 403
                    
                    token = jwt.encode({
                        'user_id': user['id'],
                        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
                    }, app.config['SECRET_KEY'], algorithm="HS256")
                    return jsonify({"message": "Login bem-sucedido.", "token": token}), 200
                return jsonify({"error": "Email ou senha inválidos."}), 401
    except Exception as e:
        print(f"ERRO no login: {e}")
        return jsonify({"error": "Erro interno do servidor."}), 500

@app.route('/api/auth/approve/<int:user_id>', methods=['GET'])
def approve_user_access(user_id):
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_approved = TRUE WHERE id = %s RETURNING email", (user_id,))
                result = cur.fetchone()
                conn.commit()
                if result:
                    user_email = result[0]
                    send_telegram_message(TELEGRAM_CHAT_ID, f"✅ O acesso para <b>{user_email}</b> foi <b>APROVADO</b>.")
                    return "<h1>Acesso APROVADO!</h1><p>O utilizador agora pode entrar no painel.</p>", 200
                return "<h1>Utilizador não encontrado.</h1>", 404
    except Exception as e:
        print(f"ERRO ao aprovar utilizador: {e}")
        return "<h1>Erro interno ao aprovar.</h1>", 500

@app.route('/api/auth/deny/<int:user_id>', methods=['GET'])
def deny_user_access(user_id):
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s AND is_approved = FALSE RETURNING email", (user_id,))
                result = cur.fetchone()
                conn.commit()
                if result:
                    user_email = result[0]
                    send_telegram_message(TELEGRAM_CHAT_ID, f"❌ O acesso para <b>{user_email}</b> foi <b>NEGADO</b> e a solicitação foi excluída.")
                    return "<h1>Acesso NEGADO!</h1><p>A solicitação do utilizador foi excluída.</p>", 200
                return "<h1>Utilizador não encontrado ou já aprovado.</h1>", 404
    except Exception as e:
        print(f"ERRO ao negar utilizador: {e}")
        return "<h1>Erro interno ao negar.</h1>", 500

# --- ENDPOINTS DE DADOS ---

@app.route('/api/location', methods=['GET'])
def receive_location_data():
    data = {
            "sender_id": request.args.get('sender_id', type=str),
            "timestamp": request.args.get('timestamp', type=int),
            "latitude": request.args.get('latitude', type=float),
            "longitude": request.args.get('longitude', type=float),
            "gps_module_id": request.args.get('gps_module_id', type=str),
            "battery_level": request.args.get('battery_level', type=int),
            "device_status": request.args.get('device_status', type=str)
        }
    required_fields = ['latitude', 'longitude', 'gps_module_id', 'timestamp']
    if not all(data[k] is not None for k in required_fields):
        return jsonify({"error": "Faltam campos obrigatórios nos dados de localização"}), 400
    try:
        timestamp = datetime.fromtimestamp(data["timestamp"])
    except Exception as e:
        return jsonify({"error": "Timestamp deve ser um número inteiro"}), 400
    record = {
        "sender_id": data.get("sender_id"),
        "timestamp": timestamp,
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "gps_module_id": data["gps_module_id"],
        "battery_level": data.get("battery_level"),
        "device_status": data.get("device_status")
    }
    
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO deriva_points (sender_id, timestamp, latitude, longitude, gps_module_id, battery_level, device_status)
                       VALUES (%(sender_id)s, %(timestamp)s, %(latitude)s, %(longitude)s, %(gps_module_id)s, %(battery_level)s, %(device_status)s)""",
                    record
                )
                conn.commit()
        check_for_alerts(data)
        return jsonify({"message": "Dados recebidos e guardados com sucesso"}), 201
    except Exception as e:
        print(f"ERRO ao inserir dados de localização: {e}")
        return jsonify({"error": f"Falha na inserção na base de dados: {e}"}), 500

@app.route('/api/data/derivadores', methods=['GET'])
@token_required
def get_derivadores_data():
    print("\n[API] Recebido pedido para /data/derivadores.")
    try:
        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM deriva_points ORDER BY timestamp DESC")
                results = cur.fetchall()
                print(f"[API] Encontrados {len(results)} registos na base de dados.")
                
                for row in results:
                    if 'timestamp' in row and isinstance(row['timestamp'], datetime):
                        row['timestamp'] = row['timestamp'].isoformat()
                
                print(f"[API] A enviar {len(results)} registos para o Dashboard.")
                return jsonify(results)
    except Exception as e:
        print(f"[API] ERRO ao obter dados da base de dados: {e}")
        return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500
    
@app.route('/api', methods=['GET'])
def teste():
    return 'Olá, mundo!'

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
