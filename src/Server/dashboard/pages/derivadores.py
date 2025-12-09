# pages/derivadores.py --- Página Final e Completa do Mapa com Layout e Callbacks Corrigidos
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import os
import random
import urllib.parse
import io
from base64 import b64encode

API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000/api")
dash.register_page(__name__, path='/')

def create_initial_figure():
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(center=go.layout.mapbox.Center(lat=-27.59, lon=-48.54), zoom=7),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig

layout = html.Div(className='app-container', children=[

    # 1. Memória do estado da sidebar
    dcc.Store(id='side_click', data=True),

    # 2. Botão Toggle
    html.Button('☰', id='btn_sidebar', n_clicks=0, style={
        'position': 'fixed', 'top': '10px', 'left': '10px', 'zIndex': 1100,
        'fontSize': '20px', 'backgroundColor': 'white', 'border': 'none', 
        'cursor': 'pointer', 'padding': '5px 10px', 'borderRadius': '5px', 
        'boxShadow': '0px 2px 5px rgba(0,0,0,0.2)'
    }),

    # 3. Sidebar NOVA (Com ID)
    html.Div(id='sidebar', className="sidebar", children=[
        html.H2('Derivadores', style={'textAlign': 'center', 'color': '#333', 'marginTop': '40px'}), 
        html.Hr(),
        html.Button('Logout', id='logout-button', className='sidebar-button'),
        html.Button('Atualizar Dados', id='refresh-button', className='sidebar-button'),
        html.A(html.Button('Baixar Dados (.csv)', className='sidebar-button'), id='download-data-link', download='dados_derivadores.csv'),
        html.A(html.Button('Baixar Mapa (.html)', className='sidebar-button'), id='download-map-link', download='mapa_derivadores.html'),
        html.Button('Dashboard', id='dashboard-button', className='sidebar-button', n_clicks=0),
        html.Button('Sobre', id='about-button', className='sidebar-button', n_clicks=0),
    ]),

    # 4. Content NOVO (Com ID e contendo o mapa)
    html.Div(id='page-content', className="content", children=[
        dcc.Graph(id='mapa', figure=create_initial_figure(), style={'height': '100vh'})
    ]),

    # 5. Popups e Utilitários (Isso fica igual)
    html.Div(id='fade-about', className='fade'),
    html.Div(id='fade-dashboard', className='fade'),
    
    html.Div(className='popup', id='about-popup', children=[
        html.Button('X', id='close-about', n_clicks=0, className='close'),
        html.H2('Sobre o Projeto'),
        html.P('Visualização em tempo real das trajetórias de derivadores oceanográficos.'),
        html.P('Criado por: Aruã Viggiano Souza, Gabriel Hessmann Ramos, Leonardo Coli de Aguiar e Matheus Araujo Langer'),
        html.P(['Código fonte: ', html.A('GitHub', href='https://github.com/ECA-UFSC-FLN/2025.2-G2-monitoraDeriva', target='_blank')])
    ]),
    
    html.Div(className='popup', id='dashboard-popup', children=[
        html.Button('X', id='close-dashboard', n_clicks=0, className='close'),
        html.H2('Dashboard de Status'),
        dcc.Graph(id='battery-graph'),
    ]),

    dcc.Store(id='data-store'),
])

# --- Callbacks ---

# Callback de Segurança: Verifica a sessão na carga da página e após o logout.
@callback(
    Output('url', 'href', allow_duplicate=True),
    [Input('url', 'pathname'),
    Input('session-store', 'data')], 
    prevent_initial_call=True
)
def protect_derivadores_page(pathname, session_data):
    if pathname == '/':
        if not session_data or 'token' not in session_data:
            return '/login'
    return dash.no_update
#@callback(
#    Output('url', 'href', allow_duplicate=True),
#    Input('session-store', 'data'),
#    prevent_initial_call=True
#)
#def security_redirect(session_data):
#    if not session_data or 'token' not in session_data:
#        # Se não houver token (ex: após logout), força o redirecionamento.
#        return '/login'
#    return no_update


@callback(
    Output('session-store', 'clear_data'),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks and n_clicks > 0:
        return True
    return False

# Callback Principal: Carrega os dados para o mapa.
@callback(
    Output('data-store', 'data'),
    Output('mapa', 'figure'),
    [Input('url', 'pathname'), Input('refresh-button', 'n_clicks')],
    State('session-store', 'data')
)
def update_data_and_map(pathname, n_clicks, session_data):
    if pathname != '/' or not session_data or 'token' not in session_data:
        return no_update, create_initial_figure()

    token = session_data['token']
    headers = {'Authorization': f'Bearer {token}'}

    try:
        response = requests.get(f"{API_URL}/data/derivadores", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return pd.DataFrame().to_json(orient='split'), create_initial_figure()
        
    if df.empty:
        return df.to_json(orient='split'), create_initial_figure()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    drifter_ids = sorted(df['gps_module_id'].unique()) # Ordena para garantir consistência

    # Uma paleta de cores predefinida e visualmente distinta
    color_palette = [
        '#1f77b4',  # azul
        '#ff7f0e',  # laranja
        '#2ca02c',  # verde
        '#d62728',  # vermelho
        '#9467bd',  # roxo
        '#8c564b',  # castanho
        '#e377c2',  # rosa
        '#7f7f7f',  # cinza
        '#bcbd22',  # verde-oliva
        '#17becf'   # ciano
    ]
    
    # Mapeia cada ID a uma cor da paleta de forma consistente
    colors = {id: color_palette[i % len(color_palette)] for i, id in enumerate(drifter_ids)}

    for drifter_id in drifter_ids:
        drifter_df = df[df['gps_module_id'] == drifter_id].sort_values(by='timestamp')
        drifter_df['hover_text'] = drifter_df.apply(
            lambda row: f"<b>Derivador: {row['gps_module_id']}</b><br>Hora: {pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M')}<br>Bateria: {row.get('battery_level', 'N/A')}%<br>Status: {row.get('device_status', 'N/A')}", axis=1
        )
        fig.add_trace(go.Scattermapbox(
            lon=drifter_df['longitude'], lat=drifter_df['latitude'], mode='markers+lines',
            marker=dict(size=8, color=colors[drifter_id], opacity=0.7),
            line=dict(width=2, color=colors[drifter_id]),
            name=str(drifter_id), hoverinfo='text', text=drifter_df['hover_text']
        ))

        if not drifter_df.empty:
            last_pos = drifter_df.iloc[-1]
            
            fig.add_trace(go.Scattermapbox(
                lon=[last_pos['longitude']], lat=[last_pos['latitude']], mode='markers',
                marker=dict(size=16, color=colors[drifter_id], opacity=1,),

                text=[f"📍 <b>ATUAL</b><br>{last_pos['hover_text']}"],
                hoverinfo='text',
                name=f"{drifter_id} (Atual)", 
                showlegend=False 
            ))

    fig.update_layout(
        mapbox_style="open-street-map",
        legend=dict(x=0.05, y=0.95, bgcolor='rgba(255,255,255,0.7)'),
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(center=go.layout.mapbox.Center(lat=df['latitude'].mean(), lon=df['longitude'].mean()), zoom=7)
    )
    
    return df.to_json(date_format='iso', orient='split'), fig

# Callbacks para Popups e Downloads
@callback(
    Output('about-popup', 'style'),
    Output('fade-about', 'style'),
    Input('about-button', 'n_clicks'),
    Input('close-about', 'n_clicks'),
)
def toggle_about_popup(open_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'close-about.n_clicks':
        return {'display': 'none'}, {'display': 'none'}
    return {'display': 'block'}, {'display': 'block'}

@callback(
    Output('dashboard-popup', 'style'),
    Output('fade-dashboard', 'style'),
    Input('dashboard-button', 'n_clicks'),
    Input('close-dashboard', 'n_clicks'),
)
def toggle_dashboard_popup(open_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'close-dashboard.n_clicks':
        return {'display': 'none'}, {'display': 'none'}
    return {'display': 'block'}, {'display': 'block'}

@callback(
    Output('battery-graph', 'figure'),
    Input('data-store', 'data')
)
def update_battery_graph(data_json):
    if not data_json:
        return go.Figure().update_layout(title="Sem dados disponíveis")

    df = pd.read_json(data_json, orient='split')
    if df.empty or 'battery_level' not in df.columns:
        return go.Figure().update_layout(title="Sem dados de bateria")
        
    latest_df = df.sort_values('timestamp').groupby('gps_module_id').tail(1)

    fig = px.bar(
        latest_df, x='gps_module_id', y='battery_level',
        title='Níveis de Bateria Mais Recentes',
        labels={'gps_module_id': 'ID do Derivador', 'battery_level': 'Bateria (%)'},
        color='gps_module_id', text='battery_level'
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_range=[0,110])
    return fig

@callback(
    Output('download-map-link', 'href'),
    Input('mapa', 'figure'),
    prevent_initial_call=True
)
def generate_map_download_link(fig_data):
    if not fig_data:
        return ""
    fig = go.Figure(fig_data)
    buffer = io.StringIO()
    fig.write_html(buffer)
    html_bytes = buffer.getvalue().encode()
    encoded = b64encode(html_bytes).decode()
    return "data:text/html;base64," + encoded

@callback(
    Output('download-data-link', 'href'),
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def generate_data_download_link(data_json):
    if not data_json:
        return ""
    df = pd.read_json(data_json, orient='split')
    csv_string = df.to_csv(index=False, encoding='utf-8')
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

@callback(
    [Output('sidebar', 'style'),
     Output('page-content', 'style'),
     Output('side_click', 'data')],
    Input('btn_sidebar', 'n_clicks'),
    State('side_click', 'data')
)
def toggle_sidebar(n, is_open):
    if n:
        is_open = not is_open
    
    SIDEBAR_WIDTH = "250px" 
    
    if is_open:
        sidebar_style = {
            'marginLeft': '0', 
            'transition': 'margin-left 0.3s ease-in-out',
            'position': 'fixed', 'top': 0, 'left': 0, 'bottom': 0, 'width': SIDEBAR_WIDTH, 'padding': '2rem 1rem', 'backgroundColor': '#f8f9fa'
        }
        content_style = {
            'marginLeft': SIDEBAR_WIDTH, 
            'transition': 'margin-left 0.3s ease-in-out'
        }
    else:
        sidebar_style = {
            'marginLeft': f'-{SIDEBAR_WIDTH}', 
            'transition': 'margin-left 0.3s ease-in-out',
            'position': 'fixed', 'top': 0, 'left': 0, 'bottom': 0, 'width': SIDEBAR_WIDTH, 'padding': '2rem 1rem', 'backgroundColor': '#f8f9fa'
        }
        content_style = {
            'marginLeft': '0', 
            'transition': 'margin-left 0.3s ease-in-out'
        }
        
    return sidebar_style, content_style, is_open