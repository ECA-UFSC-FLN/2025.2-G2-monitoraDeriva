import os
import dash
from dash import Dash

app = Dash(__name__, use_pages=True)
server = app.server

app.layout = dash.page_container

if __name__ == '__main__':
    app.run(debug=True)