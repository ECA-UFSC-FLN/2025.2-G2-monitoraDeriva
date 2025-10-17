# pages/login.py --- Página de Login e Registo 
from dash import html, dcc, callback, Input, Output, State, no_update
import dash
import requests
import os

dash.register_page(__name__, path='/login')
API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

# --- Layout da Página ---
layout = html.Div(className='login-container', children=[
    html.Div(className='login-box', children=[
        html.H2('Acesso ao Painel'),
        dcc.Input(id='email-input', type='email', placeholder='Email', className='login-input'),
        dcc.Input(id='password-input', type='password', placeholder='Senha', className='login-input'),
        html.Button('Entrar', id='login-button', className='login-button'),
        html.Button('Registar', id='register-button', className='login-button secondary'),
        html.Div(id='auth-message', style={'marginTop': '15px', 'color': 'red'})
    ])
])

# --- Callbacks ---

# Callback de segurança: se o utilizador já está autenticado, redireciona para o mapa.
@callback(
    Output('url', 'href', allow_duplicate=True),
    Input('url', 'pathname'), # É acionada na carga da página
    State('session-store', 'data'),
    prevent_initial_call=True
)
def check_login_status(pathname, session_data):
    if pathname == '/login':
        if session_data and 'token' in session_data:
            return '/'
    return dash.no_update

# Callback principal para registo e login
@callback(
    Output('url', 'href', allow_duplicate=True),
    Output('auth-message', 'children'),
    Output('session-store', 'data'),
    Input('login-button', 'n_clicks'),
    Input('register-button', 'n_clicks'),
    State('email-input', 'value'),
    State('password-input', 'value'),
    prevent_initial_call=True
)
def handle_authentication(login_clicks, register_clicks, email, password):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, "", no_update
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if not email or not password:
        return no_update, "Por favor, preencha o email e a senha.", no_update

    endpoint = ""
    if button_id == 'login-button':
        endpoint = '/auth/login'
    elif button_id == 'register-button':
        endpoint = '/auth/register'
    
    payload = {'email': email, 'password': password}
    
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10)
        response_data = response.json()

        if response.status_code == 200: # Login bem-sucedido
            token = response_data.get('token')
            if token:
                # Guarda o token na sessão e redireciona para o mapa
                return '/', "", {'token': token}
            else:
                return no_update, "Erro de login: token não recebido.", no_update
        
        elif response.status_code == 201: # Registo bem-sucedido
            return no_update, "Pedido de registo enviado. Aguarde a aprovação do administrador.", no_update
        else:
            # Mostra a mensagem de erro da API (ex: "Conta não aprovada")
            error_message = response_data.get('error', 'Ocorreu um erro desconhecido.')
            return no_update, error_message, no_update
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a API: {e}")
        return no_update, "Não foi possível conectar ao servidor.", no_update

