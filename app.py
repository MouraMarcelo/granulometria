import base64
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table

import pandas as pd
import plotly.express as px

df_example = pd.DataFrame({
    'Peneira': [4, 10, 20, '...'],
    'Abertura': [4.75, 2.00, 0.85, '...'],
    'Massa Retida': [0, 20, 40, '...']
})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

app.layout = html.Div([
    html.H1('Análise Granulométrica'),
    html.P('Desenvolvido por Marcelo Moura'),

    html.Hr(),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arraste e Solte ou ',
            html.A('Selecione o Arquivo',
                href='#',
                style={'color': '#0d6efd'}
            )
        ]),
        style={
            'width': '50%',
            'minWidth': '18rem',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),

    html.Details([
        html.Summary('Exemplo de Arquivo'),
        dbc.Row([
            dbc.Col(dash_table.DataTable(
                id='table',
                columns=[{'name': i, 'id': i} for i in df_example.columns],
                data=df_example.to_dict('records')
            ), sm=8, md=5, lg=4, style={'padding': '0.5rem'}),
            dbc.Col(html.Ul([
                html.Li('Os arquivos dever ter extensão .xls ou .csv'),
                html.Li('As três primeiras colunas devem conter os valuees da Peneira, Abertura e Massa Retida, mas não necessariamente com esses nomes'),
                html.Li('Pode ser utilizados ponto ou vírgula como separador decimal')
            ]), sm=8, md=5, lg=4, style={'padding': '0.5rem'})
        ])
    ]),
    
    html.Hr(),

    dbc.Row([
        dbc.Col(
            html.Div(id='output-data-upload', style={'minWidth': '37.5rem'}),
            sm=12, md=10, xl=8
        ),
        dbc.Col()
    ])
], style={'padding': '1rem'})


def manipulate_content(filename, df):
    df.columns = ['Peneira (mesh)', 'Abertura (mm)', 'Massa Retida (g)']
    total_refusal = [df['Massa Retida (g)'][0]]
    length = len(df)

    for value in range(1, length):
        n_value = total_refusal[value - 1] + df['Massa Retida (g)'][value]
        n_value = round(n_value, 2)
        total_refusal.append(n_value)

    weight = total_refusal[-1]

    filtered = []

    for value in range(length):
        n_value = (weight - total_refusal[value])/weight
        n_value = round(n_value, 2)
        filtered.append(n_value)

    df['Massa Acumulada (g)'] = total_refusal
    df['Porcentagem Passante (%)'] = [round((x * 100), 2) for x in filtered]

    fig = px.line(df, x='Abertura (mm)', y='Porcentagem Passante (%)',
        title=f'Curva de distribuição granulométrica - {filename}')

    fig['layout']['xaxis']['autorange'] = 'reversed'

    return html.Div([
        html.P(filename),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),

        dcc.Graph(
            id='graph',
            figure=fig
        )
    ])


def parse_contents(contents, filename, list_of_dates):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8'))
            )
        elif 'xls' in filename:
            
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'Ocorreu um erro ao processar este arquivo.'
        ])

    return manipulate_content(filename, df)

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server()