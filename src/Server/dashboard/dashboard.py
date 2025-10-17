import dash
from dash import Dash, html, dcc
import os
from dotenv import load_dotenv

load_dotenv()

app = Dash(__name__, use_pages=True, assets_folder='assets')
server = app.server

app.layout = html.Div([
    dcc.Store(id='session-store', storage_type='session'),
    
    dcc.Location(id='url', refresh=True),

    dash.page_container
])

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=8050)
