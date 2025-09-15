import dash
from dash import html, dcc, callback, Input, Output
from dash.dependencies import Output, Input, State
from dash import callback_context
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import time
import random
import os
import urllib
import io
from base64 import b64encode
import json
from dotenv import load_dotenv

load_dotenv()

dash.register_page(__name__, path='/')

font_color = 'rgb(100,100,100)'

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'root')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def read_json(data):
    d = json.loads(data)
    return pd.DataFrame(d['data'],d['index'],d['columns'])

def get_data():
    return pd.read_sql('select * from deriva_points',engine,index_col='id')

def inicial_figure():
    fig = go.Figure()

    df = pd.DataFrame({key:[] for key in ['sender_id','timestamp','latitude','longitude','gps_module_id']})
    fig.add_trace(go.Scattermap(
        lon = df['longitude'],
        lat = df['latitude'],
        hoverinfo = 'lon+lat',
        text = df['gps_module_id'],
        mode = 'markers+lines',
        marker = dict(
            size = 10,
            color = f'rgb({random.randint(0,255)}, {random.randint(0,255)}, 0)',
        )))

    fig.update_layout(
        hovermode='closest',
        map=dict(
            bearing=0,
            center=go.layout.map.Center(
                lat=-28.5,
                lon=-48.5
            ),
            pitch=0,
            zoom=3
        ),
        showlegend = False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig

@callback(Output('data', 'data'),Output('mapa','figure'), Input('refresh', 'n_clicks'), State('data', 'data'),State('mapa','figure'))
def update_data(n_clicks, data, fig):
    alldf = get_data()
    print('Obtendo dados')
    fig = go.Figure()

    random.seed(0)
    for id in alldf['gps_module_id'].unique():
        df = alldf.loc[alldf['gps_module_id']==id]
        fig.add_trace(go.Scattermap(
            lon = df['longitude'],
            lat = df['latitude'],
            hoverinfo = 'lon+lat',
            text = df['gps_module_id'],
            mode = 'markers+lines',
            marker = dict(
                size = 10,
                color = f'rgb({random.randint(0,255)}, {random.randint(0,255)}, 0)',
            )))
    
    fig.update_layout(
        hovermode='closest',
        map=dict(
            bearing=0,
            center=go.layout.map.Center(
                lat=-28.5,
                lon=-48.5
            ),
            pitch=0,
            zoom=3
        ),
        showlegend = False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    data = alldf.to_json(orient='split')
    return data,fig

@callback(Output('baixar_mapa','href'),Input('mapa','figure'))
def create_html(figure):
    fig = go.Figure(figure)
    buffer = io.StringIO()
    fig.write_html(buffer)
    html_bytes = buffer.getvalue().encode()
    encoded = b64encode(html_bytes).decode()
    return "data:text/html;base64," + encoded

@callback(Output('baixar_dados','href'),Input('data','data'))
def create_csv(data):
    df = read_json(data)
    csv = df.to_csv(index = False)
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv)

@callback(Output('dashboard','style'),Output('fade2','style'),Output('dashButton','disabled'),Input('dashButton','n_clicks'),Input('closeDash','n_clicks'))
def show_dash(open,close):
    if open > close:
        return {'display':'block'},{'display':'block'},True
    return {'display': 'none'},{'display': 'none'},False

@callback(Output('info','style'),Output('fade','style'),Output('sobre','disabled'),Input('sobre','n_clicks'),Input('closeInfo','n_clicks'))
def show_info(open,close):
    if open > close:
        return {'display':'block'},{'display':'block'},True
    return {'display': 'none'},{'display': 'none'},False

@callback(Output('bargraph','figure'),Input('data','data'))
def build_graphs(data):
    df = read_json(data)
    fig = go.Figure()
    return fig

layout = html.Div([
    dcc.Store(id = 'data'),
    html.H1('Derivadores',
            style = {'font-family':'helvetica','background-color':'white','border-radius':'5px',
                        'padding':'10px','color':font_color,'margin':'10px','float':'left','font-size':'23px'},id = 'title'),
    html.Div([
        html.A(html.Button('Baixar Dados',className = 'menuButton'),id = 'baixar_dados',download = 'derivadores.csv'),html.Br(),
        html.A(html.Button('Baixar Mapa',className = 'menuButton'),id = 'baixar_mapa',download = 'derivadores.html'),html.Br(),
        html.A(html.Button('Dashboard',className = 'menuButton',id = 'dashButton',n_clicks = 0)),html.Br(),
        html.A(html.Button('Sobre',id = 'sobre',className = 'menuButton',n_clicks = 0))],
        style = {'position': 'fixed', 'top': '0', 'left': '0','margin-top':'75px','margin-left':'10px'}),
    dcc.Graph(
        id='mapa',
        figure = inicial_figure(),
        style = {'position': 'fixed', 'top': '0', 'left': '0','height': '100vh', 'width': '100vw', 'z-index': '-1'}
    ),
    html.Div(id = 'fade',className = 'fade'),
    html.Div([
        html.Button('X',id = 'closeInfo',n_clicks = 0,className = 'close'),
        html.Div([
            html.H2('Sobre o projeto'),
            html.P('Trajetórias de derivadores.'),
            html.P(['Criado por: Aruã Viggiano Souza, Gabriel Hessmann Ramos, Leonardo Coli de Aguiar e Matheus araujo langer']),
            html.P(['Código fonte: ',html.A('Github',href = 'https://github.com/ECA-UFSC-FLN/2025.2-G2-monitoraDeriva')])
        ],className = 'blocoTexto')],id = 'info'),
    html.Div(id = 'fade2',className = 'fade'),
    html.Div([
        html.Button('X',id = 'closeDash',n_clicks = 0,className = 'close'),
        html.Div([
            html.H2('Dashboard'),
            dcc.Graph(id = 'bargraph'),
        ],className = 'blocoDash')],id = 'dashboard'),
    html.Button('Atualizar Dados',id = 'refresh',className = 'menuButton',style = {'position': 'fixed', 'top':'93%','left':'1%'})
])