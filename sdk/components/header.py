from dash import html


def SedmaxHeader(title = 'Заголовок', logo = 'enpro', color = 'rgba(241,241,241,0.9)'):
    """Returns app header
    title = "Текст заголовка" (str),
    logo = 'enpro' или 'sedmax' (str),
    color = 'rgba(241,241,241,0.8)' (str rgb/rgba/hex)
    """


    header = html.Div([
        html.Span(className='helper'),
        html.Div(html.Img(src=f'assets/{logo}.png', className='logo'),
                 style={'width': '20%', 'opacity': 0.95, 'align-self': 'center'}),
        html.Div(html.B(title, style={'textAlign': 'center', 'color': color, 'font-size': 22}),
                 style={'width': '60%', 'text-align': 'center', 'vertical-align': 'middle', 'align-self': 'center'}),
        html.Div(style={'width': '20%', 'opacity': 0.9})
        ], className='header')

    return header