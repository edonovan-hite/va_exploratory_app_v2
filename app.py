""""
Created by: EmelineDonovan
Created on: 9/10/2024
Description: primary file to run VA Exploratory App
"""


"""
Imports and Variables
"""
import dash
from dash import dcc, html, no_update
from dash.dependencies import Input, Output
# from dash import no_update
import pandas as pd
import plotly.graph_objects as go
import os
from utils import load_data
from utils import va_api
import json
import dash_ag_grid as dag
import numbers
from dash.exceptions import PreventUpdate

# Comment out databricks
# from databricks.sdk.runtime import *

base_url = 'https://app.visiblealpha.com/api3/'
companies_endpoint = 'companies?stid=1' # Standard descriptive information for all companies covered in va universe
parameter_endpoint = 'parametermeta_cd' # All the parameters that can be pulled via companydata endpoint and which company they belong to
revisions_endpoint = 'revisions' # revisions info, corrections to previously reported financial metrics due to new info
company_data_endpoint = 'companydata' # financial metrics of a specific company


# i believe this is region name:
region_name = 'us-east-2'

"""
Pull relevant data
"""

# get VA credentials: F
va_username = os.environ.get('VA_USERNAME')
va_password = os.environ.get('VA_PASSWORD')
headers = va_api.authenticate(va_username, va_password) # get authenticated to access API data
os.environ['HEADERS'] = json.dumps(headers)

company_info_df = load_data.does_dataframe_exist(base_url, companies_endpoint, json.loads(os.environ.get('HEADERS'))) # check if df already exists, get df if not
company_list_dicts = load_data.create_options_list(company_info_df, 'cname') # create company drop-down menu
bt_ticker_list = load_data.create_options_list(company_info_df, 'bt') # create bloomberg ticket drop-down menu

# columns for parameter values + period-over-period change table
# pv_pop_table_columns = [{'name': 'Period', 'id': 'p'},
#                {'name': 'Value', 'id': 'value', 'type': 'numeric',
#                 'format': Format(group=Group.yes).scheme(Scheme.fixed).precision(2)},
#                # Claude added this formatting to create groups of three (like 12,500)
#                {'name': 'Change in Value', 'id': 'change', 'type': 'numeric',
#                 'format': Format(group=Group.yes).scheme(Scheme.fixed).precision(2)},
#                {'name': 'Percent Change', 'id': 'percent_change'},
#                {'name': 'Type', 'id': 'dt'},
#                {'name': 'Broker Count', 'id': 'b'}]

# pv_pop_grid_columns = [
#     {'field': 'p', 'headerName': 'Period',},
#     {'field': 'value', 'headerName': 'Average'},
#     {'field': 'change', 'headerName': 'PoP Change'},
#     {'field': 'percent_change', 'headerName': 'Percent'},
#     {'field': 'd', 'headerName': 'Median'},
#     {'field': 'x', 'headerName': 'Max'},
#     {'field': 'n', 'headerName': 'Min'},
#     {'field': 'dt', 'headerName': 'Type'},
#     {'field': 'b', 'headerName': 'Broker Count'},
# ]


revisions_columns = [{'field': 'r', 'headerName': 'Revision Date'},
                   {'field': 'v', 'headerName': 'Value'},
                   {'field': 'b', 'headerName': 'Broker Count',}]
#
# revisions_columns = [{'name': 'Revision Date', 'id': 'r'},
#                    {'name': 'Value', 'id': 'v', 'type':'numeric', 'format': Format(group=Group.yes).scheme(Scheme.fixed).precision(2)},
#                    {'name': 'Broker Count', 'id': 'b'}]
"""
Set up app and server
"""
# Create the Dash app
app = dash.Dash(__name__) # Create the dash app
server = app.server # Initiate the server


"""
App Layout
"""

app.layout = html.Div([
    html.H1("Explore Visible Alpha Data"), # Title
    html.H2('Select a company and explore its unique VA parameters'), # Subtitle

    # Four Dropdowns
    html.Div([
        html.Div([
            html.Label("Select a Bloomberg Ticker:"),  # Bloomberg Ticker Dropdown
            dcc.Dropdown(
                id='bt-dropdown',
                searchable=True,
                clearable=True,
                options=bt_ticker_list,
                value=bt_ticker_list[0]['value'],
                persistence=True,
                persistence_type="session",
            ),
        ], style={"display": "inline-block", "width": "20%", "padding":"10px"}),
        html.Div([
            html.Label("Quarterly or Annual Data:"),  # Quarter vs Annual Dropdown
            dcc.Dropdown(
                id='p-freq-dropdown',
                options=[{'label': 'Quarterly', 'value': 'Q'}, {'label': 'Annually', 'value': 'A'}],
                value='Q',
                persistence=True,
                persistence_type="session",
            ),
        ], style={"display": "inline-block", "width": "20%", "padding":"10px"}),
        html.Div([
            html.Label('Select Start Date:'),  # Start Date Parameters
            dcc.Dropdown(
                id='start-date-dropdown',
                placeholder="Select a start date",
                persistence=True,
                persistence_type="session",
            ),
        ], style={"display": "inline-block", "width": "20%", "padding":"10px"}),
        html.Div([
            html.Label('Select End Date:'),   # End Date Dropdown
            dcc.Dropdown(
                id='end-date-dropdown',
                placeholder="Select an end date",
                persistence=True,
                persistence_type="session",
            ),
        ], style={"display": "inline-block", "width": "20%", "padding":"10px"}),
    ]),
    html.Div(id='output-container'),

    # Table, Graph, Table Container
    html.Div(style={'display': 'flex', 'flex-wrap': 'nowrap', 'align-items': 'stretch', 'gap': '10px', 'height':'80vh'}, children=[

        # Parameter Table
        html.Div(style={'flex': '1 1 20%', 'box-sizing': 'border-box', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'display': 'flex', 'flex-direction': 'column', 'height': '100%'}, children=[
            html.H2('Parameter Table', style={'textAlign': 'center', 'flex': '0 0 auto'}),
            dag.AgGrid(
                id = 'data-table',
                columnDefs=[],
                rowData=[],
                columnSize='autoSize',
                dashGridOptions={
                    "enableCellTextSelection": True,
                    "ensureDomOrder": True,
                    "autoSizeStrategy": {"type": "fitCellContents"},
                    "suppressColumnVirtualisation": True,
                    "getRowId": {"function": "params.data.pid.toString()"}, # Maps pid to row id
                    'rowSelection': {'mode': 'singleRow'}}, # select a row
                defaultColDef={"cellStyle": {"textAlign": "left"}, "filter": True,  "wrapText": True, "autoHeight": True, 'floatingFilter':True, "floatingFilterComponentParams": {"placeholder": "Filter parameters..."},},
                style={'height':'100%'},
                selectedRows=[],
                        ),

                #          dash_table.DataTable(
                #              id='data-table',
                #              data=[],
                #              columns=[],
                #              filter_action="native",
                #              row_selectable='single',
                #              page_size = 8,
                #              selected_rows=[0],
                #              # dashGridOptions = {'rowSelection': {'mode': 'singleRow'}},
                #              # export_format='csv',
                #              # export_headers='display',
                #              style_table={'width': '100%', 'height': '80%', 'overflowY': 'scroll', 'overflowX': 'scroll'},
                #              style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto', 'padding': '4px'},
                # )
        ]),

        # Actuals vs Estimates Graph
        html.Div(style={'flex': '1 1 50%', 'min-width': '0', 'box-sizing': 'border-box', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'display':'flex', 'flex-direction':'column', 'height':'100%'}, children=[
            html.H2('Actuals & Estimates Graph', style={'textAlign': 'center'}),
            dcc.Graph(id='graph', style={'height':'100%', 'flex':'1 1 auto'}) # 'height':'1150px'
        ]),

        # Parameter Values and Period-over-Period Change Table
        html.Div(style={'flex': '1 1 30%', 'min-width': '0', 'box-sizing': 'border-box', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'display':'flex', 'flex-direction':'column', 'height':'100%'}, children=[
            html.H2('Parameter Values + period-over-period change Table', style={'textAlign': 'center', 'flex': '0 0 auto'}),

            # Parameter Values + p-o-p Grid
            dag.AgGrid(
                id='data-table-2',
                columnDefs=[],
                rowData=[],
                columnSize='autoSize',
                dashGridOptions={
                    "enableCellTextSelection": True,
                    "ensureDomOrder": True,
                    "autoSizeStrategy": {"type": "fitCellContents"},
                    "suppressColumnVirtualisation": True,
                },
                defaultColDef={"cellStyle": {"textAlign": "right"}, "resizable": True, "sortable": False, "filter": False, "wrapText": True,}, # "minWidth": 110, "maxWidth": 110, },
                style={'height':'100%'}, #'flex': '1 1 auto', 'minHeight': '0',}, # this width doesnt affect clumn sizes

            )
        ]),
    ]),
    
    # Revisions Data Dropdown
    html.Div([
        html.Div(style={'width': '50%', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'margin': '5px', }, children=[
            html.H2('Revisions Data'), 
            dcc.Dropdown(id='revisions-period-dropdown', options=[], value=[], multi=True, debounce=True, closeOnSelect=False,  persistence=True, persistence_type="session") # multi selection, updates when drop down closed
        ])
    ]),
    # Revision Data Graph + Table
    html.Div(style={'display': 'flex', 'flex-wrap': 'nowrap', 'height':'80vh'}, children=[

        # Revision Graph
        html.Div(style={'width': '65%', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'margin': '5px'}, children=[
            dcc.Graph('revisions-graph', style={'height':'100%'})
        ]),

        # Revision Table
        html.Div(style={'width': '35%', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'margin': '5px'}, children=[
            dag.AgGrid(
                id='revisions-table',
                columnDefs=[],
                rowData=[],
                columnSize='autoSize',
                 dashGridOptions={
                    "enableCellTextSelection": True,
                     "ensureDomOrder": True,
                     "autoSizeStrategy": {"type": "fitCellContents"},
                     "suppressColumnVirtualisation": True,
                 },
                defaultColDef={"cellStyle": {"textAlign": "right"},},
                style={'height': '100%'},  # this width doesn't affect clumn sizes

            )

            #
            # dash_table.DataTable(
            #     id='revisions-table',
            #     data=[],
            #     columns= revisions_columns,
            #     export_format='csv',
            #     export_headers='display'
            # )
        ])
    ]),

    # App Explanation
    html.Div([
        html.Div(style={'width': '100%', 'border': '1px solid #ddd', 'border-radius': '5px', 'padding': '10px', 'margin': '5px'}, children=[
            html.H4('Download Parameter Mapping for Energy & Autos Companies'),
            dcc.Location(id="url-1", refresh=True),
            html.A("Companies", id="link-download-1", href="#"),
            html.Br(),
            dcc.Location(id="url-2", refresh=True),
            html.A("Parameters", id="link-download-2", href="#"),
            html.H4('Summary:'),
            html.P("This exploratory app pulls data for a company's unique parameter with a Visible Alpha API call. First, select the company by its Bloomberg Ticker name in the first dropdown. Then, select whether you would like the data displayed to be annual or quarterly. Finally, select a start and end date."),
            html.P('Parameter Table: This table will load the unique parameter names and IDs associated with the selected company. The first company parameter is automatically selected and can be switched by clicking on the circle next to a different parameter. Search for parameter names or IDs by typing in the desired parameter in the "filter data" section of the table. This table can be exported as a csv by clicking the "Export" button.'),
            html.P('Actuals & Estimates Graph: This visualization will show the actuals and estimates data for the selected parameter. Selecting a date range that excludes estimates data will only show the plot containing actuals data, and vice versa. Selecting a date range where the start date is after the end date will result in no data being displayed.'),
            html.P('Parameter Values + period-over-period change Table: This table shows the periods (either fiscal quarters or years) available given the selected start and end date, the values associated with the period, the difference between a value and the value from the previous period, this change as a percent, and whether this value is an actual or an estimate. This table can be exported as a csv with the "Export" button.'),
            html.P('Revisions: Select a period to see the historical revisions for the parameter elected above.'),
            html.P('BROKER LIST: 86 Research, ABG Sundal Collier, Absa Group, Air Control Tower, Alantra Equities, Alembic Global, AlphaValue, Ambit Capital, Anchor Stockbrokers, Apalache Analisis, Apex Securities Bhd, Arete Research, Arqaam, Astris Advisory Japan, Ata Yatirim, Avior Capital, AXIA Ventures Group, Azabu Research, Baader Helvea, Bank Degroof Petercam N.V., Bank of America Securities, Bank of Montreal, Barclays, Barrenjoey, Barrington Research, Bell Potter Securities, Beltone Financial Holding, Berenberg Bank, Bestinver Securities, BNI Sekuritas, BNP Paribas Exane, BOCOM International, Bradesco BBI, BTG Pactual, BTIG, CaixaBank, Canaccord Genuity, Cantor Fitzgerald, Capital One, Carraighill Capital, Carter Bar Securities, CBRE, CCB International Securities, Centrum, CGS International Securities Hong Kong Limited, China Merchants Securities (Hong Kong), China Renaissance, Chronux Research, CI Capital, CIBC, Citi, CL King, CLSA, Colliers Securities LLC, Compass Point, Consumer Edge, Craigs Investment Partners, Credicorp Capital, D. A. Davidson, Daiwa Capital, DAM Capital Advisors Limited, Danske Bank, Data Based Analysis, Davy, DBS Vickers, Desjardins Securities, Deutsche Bank, Deutsche Numis, DNB Markets, Dowling & Partners, E&P Financial Group, Edgewater Research, EFG Hermes, Eight Capital, Equirus, EquitaSIM, Erste Group, Eurobank Equities, Euroxx Securities, Evercore ISI, FBN Quest, FBN Securities, First Shanghai Securities, Forsyth Barr, Freedom Capital Markets, Goldman Sachs, Goodbody, Gordon Haskett, Guggenheim Securities, H.C. Wainwright, Haitong, Hauck Aufhäuser Investment Banking, Hovde Group, HSBC, Huatai Securities Co. Ltd, Huber Research, ICBC International Research, LTD, ICICI Securities, IIFL, InCred Capital, ING Research, Insight Securities, Intermarket Securities, Intron Health, Investec Bank PLC, IPOPEMA Securities, Is Yatirim Menkul Degerler AS, Itau Securities, Janney, Jarden Securities, JB Capital, Jefferies, JM Financial, JMP Securities, Johnson Rice, Jones Trading, JS Global Capital, K. Liu & Co, KBC Securities, Keefe, Bruyette & Woods, Kempen, Kepler Cheuvreux, KeyBanc, KGI Securities, Kolytics, Kotak Securities, Ladenburg-Thalmann, Leerink Partners, LifeSci Capital, Loop Capital, Macquarie Group Limited, Marathon Capital Markets, LLC, Maxim Group, Maybank, Melius Research, Meristem Securities, Miranda Global Research, Mizuho Securities, Mizuho USA, Monness Crespi Hardt & Co., Morgan Stanley, Morgans, Morningstar, Motilal Oswal, MST Financial, National Bank Financial, Nedbank Ltd, Needham & Company, LLC, Nephron Research, New Street Research, NextGen Research, Nordea, Northcoast Research, Northland Capital Markets, Nuvama Wealth Management Limited, ODDO BHF, On Field Investment Research, Oppenheimer, Optima Bank, Ord Minnett, LTD, OxCap Analytics, Panmure Liberum, Pareto Securities, Peel Hunt, Periphery Research, Pickering Energy Partners, Piper Sandler, Pivotal Research, QNB Financial Services, QValue, R5 Capital, Raymond James, RBC Capital Markets, Redburn Atlantic, Regis Partners, ResearchGreece, Rosenblatt Securities, Roth MKM, Safra Securities, Samsung Securities, Sanford Bernstein, Santander, Scotia Capital Markets, Seaport Global Securities, LLC, SEB, Siebert Williams Shank, Singer Capital Markets, SMBC Nikko, SNB Capital, Soochow Securities International, Spark Capital, SPDB International Securities, SSI Securities, Stephens Inc, Stifel Nicolaus, Susquehanna Financial Group, Swiss Capital, TD Cowen, TD Securities, Telsey Advisory Group, Tera Yatirim, TH Data Capital, The Benchmark Company, Thompson Davis, Thompson Research Group, Tianfeng Securities, Topline Securities Ltd., TP ICAP Group, TPH&Co., Truist Securities, UBS, Unlu & Co, US Capital Advisors, US Tiger Securities, Vertical Research, Wedbush Securities, Wells Fargo, WestPark Capital, William Blair, Wilsons, Wood & Co, XP Securities, Yapı Kredi, Zelman & Associates, Zeus Capital, Alpha Finance Investment Services, Paradigm Capital Inc., Wolfe Research')
        ])
    ])
])


"""
Callbacks + Functions
"""

@app.callback(
    Output('start-date-dropdown', 'options'),
    Output('start-date-dropdown', 'value'),
    Output('end-date-dropdown', 'options'),
    Output('end-date-dropdown', 'value'),
    Output('revisions-period-dropdown', 'options'),
    Output('revisions-period-dropdown', 'value'),
    Input('p-freq-dropdown', 'value'))

def create_period_dropdown_values(value):
    """
    Description: Fills the date dropdowns with relevant periods (quarters or years)

    Input: Selected period frequency (Quarters, Years) from "Quarterly or Annual" Data dropdown
    Output: Dropdown values for start date, end date, revisions period
    """

    # Quarters
    if value == 'Q':
        quarter_list, current_quarter = load_data.generate_fiscal_quarters() # get all relevant quarter names and current quarter
        quarter_options = [{'label': period, 'value': period} for period in quarter_list] # create dropdown menu base
        starting_date = current_quarter[:-4] + str(int(current_quarter[-4:]) - 4)  # establish default start date for dropdown menu
        ending_date = current_quarter[:-4] + str(int(current_quarter[-4:]) + 1) # establish default end date for dropdown menu

        return quarter_options, starting_date, quarter_options, ending_date, quarter_options, [current_quarter]
    # Years
    if value == 'A':
        year_list, current_year = load_data.generate_fiscal_years() # get all relevant year names and current year
        year_options = [{'label': period, 'value': period} for period in year_list] # create drop down menu base
        starting_year = current_year[:-4] + str(int(current_year[-4:]) - 4) # establish default start year for dropdown menu
        ending_year = current_year[:-4] + str(int(current_year[-4:]) + 1) # establish default end year for dropdown menu

        return year_options, starting_year, year_options, ending_year, year_options, [current_year]
    else:
        print('Error in create_period_dropdown_values')
        error_options = [{'label': 'error', 'value': 'error'}]
        error_date = 'error'

        return error_options, error_date, error_options, error_date, error_options, error_date


@app.callback(
    Output('output-container', 'children'),
    Input('bt-dropdown', 'value')
)
def update_selected_cid(value):
    """
    Description: Visualize the selected company ID on the dashboard.

    Input: Selected Company from "Select Bloomberg Ticker" dropdown menu.
    Output: Selected Company ID Text
    """
    return f'Selected company id: {value}'


@ app.callback(
    Output('data-table', 'rowData'),
    Output('data-table', 'columnDefs'),
    Output('data-table', 'selectedRows'),
    Input('bt-dropdown', 'value')
)
def display_parameters_data_table(value):
    """
    Description: Function to fill data table with parameter values.

    Input:
    Output: Relevant data, assosciated column names for 'Parameter Table'
    """

    # Establish columns we are filling in the table:
    param_column = [
        {'field': 'pname', 'headerName': 'Parameter Name', "maxWidth": 250, 'cellStyle': {'paddingLeft': '0px'}},
        {'field': 'pid', 'headerName': 'Parameter ID'},
    ]

    # Now pull the data for the table:
    try:
        df = va_api.pull_data(base_url, parameter_endpoint, f'?cid={value}', json.loads(os.environ.get('HEADERS'))) # pull all data from this endpoint

        df = df[['pid', 'pname']]
        df['pname'] = df['pname'].str.lower()
        data = df.to_dict('records')
        selected_row = {"ids": [str(data[0]["pid"])]} # get whatever the first PID is in the data and choose that row #[data[0]]
        print('AUTOMATIC selected row:', {"ids": [str(data[0]["pid"])]})
        return data, param_column, selected_row
    except Exception as e:
        print('Error in function display_parameters_data_table.')
        load_data.handle_exception(e)
        empty_data = [{'Period': 'Error', 'Value': 'Error', 'Change': 'Error', 'Percent Change': 'Error', 'Type': 'Error', 'Broker Count': 'Error'}]
        return empty_data, param_column, [empty_data[0]]


def time_series_chart_3(data, fig_title: str, cid):
    """
    Description: Creates the Actuals & Estimates Graph
    Input: data pulled from companydata endpoint, fig_title, maybe x/y-axis title, periodicity (Quarters, Annual)
    Output: A plotly Figure
    """
    try:
        fig = go.Figure()

        # print('time_series_chart3 data columns', data.columns)

        # Organize the data:
        data['index'] = data.index # data index
        data_actuals = data[data['dt'] == 'A'] # actuals data
        data_estimates = data[data['dt'] == 'E'] # estimates data

        # Now create traces on the plot:

        # Estimate Max
        fig.add_trace(
            go.Scatter(x=data_estimates['index'], y=data_estimates['x'], mode='lines', text=data_estimates['x'],
                       hovertemplate='<span style="color:rgb(204, 204, 204)"><b>Max</b></span><br><b>Period: </b>%{x}<br><b>Value: </b>%{y}<extra></extra>',
                       line=dict(color='rgb(204, 204, 204)', dash='dot'), name='Max/Min')
        )

        # Estimate Min
        fig.add_trace(
            go.Scatter(x=data_estimates['index'], y=data_estimates['n'], mode='lines', text=data_estimates['n'],
                        hovertemplate='<span style="color:rgb(204, 204, 204)"><b>Min</b></span><br><b>Period: </b>%{x}<br><b>Value: </b>%{y}<extra></extra>',
                        line=dict(color='rgb(204, 204, 204)', dash='dot'), name='Min', showlegend=False, fill="tonexty") # fills to the previous trace listed
        )

        # Actual Values
        fig.add_trace(
            go.Scatter(x=data_actuals['index'], y=data_actuals['v'], mode='lines+markers', text=data_actuals['b'],
                                 hovertemplate='<span style="color:blue"><b>Actuals</b></span><br><b>Period: </b>%{x}<br><b>Value: </b>%{y}<extra></extra>',
                                 name='Actuals',
                                 line=dict(color='blue')))


        # Estimate Medians
        fig.add_trace(
            go.Scatter(x=data_estimates['index'], y=data_estimates['d'], mode='lines', text=data_estimates['b'],
                       hovertemplate='<span style="color:orange"><b>Median</b></span><br><b>Period: </b>%{x}<br><b>Value: </b>%{y}<br><b>Broker Count:</b> %{text}<br><extra></extra>',
                       line=dict(color='orange', dash='dash'), name='Median')
        )

        # Estimate Values
        fig.add_trace(
            go.Scatter(x=data_estimates['index'], y=data_estimates['v'], mode='lines+markers', text=data_estimates['b'],
                       hovertemplate='<span style="color:red"><b>Estimates</b></span><br><b>Period:</b> %{x}<br><b>Value:</b> %{y}<br><b>Broker Count:</b> %{text}<br><extra></extra>', # extra removed the secondary trace block
                       line=dict(color='red'), name='Estimates',)
        )

        # Add vertical line indicating next earnings date
        # pull company earning date:

        # Update axes:
        fig.update_xaxes(tickvals=data['index'], ticktext=data['p'], tickangle=45)
        fig.update_yaxes(title_text='Value') # range=[min(data_1['v']), max(data_1['v']) * 1.07])

        # Update layout:
        fig.update_layout(title_text=f"{fig_title}",
                          title_x=0.5,
                          margin=dict(t=90),
                          legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="left",
                              x=0.01,
                              bgcolor='rgba(255, 255, 255, 0.50)',
                          ),
                          hoverlabel=dict(
                              bgcolor="white",
                              font_size=16,
                              font_family="Rockwell"
                          ),
                          )


        return fig

    except Exception as e:
        print(f'Error in function time_series_chart_3.')
        load_data.handle_exception(e)
        raise

def create_change_table_data(df):
    """
    Obtains data for the parameter valuesa + period-over-period change table.
    """
    # Now get the data for the table:
    try:

        # print('df', df.head(), df.columns)

        # create PoP values
        df['pop_change'] = df['v'].diff(periods=1)  # one period back
        df['pop_percent_change'] = df['v'].pct_change(periods=1, fill_method=None) * 100

        # create YoY values
        df['yoy_change'] = df['v'].diff(periods=4) # four periods back
        df['yoy_percent_change'] = df['v'].pct_change(periods=4, fill_method=None) * 100

        # Formatting:
        df = df.round({'v': 2, 'd': 2, 'x': 2, 'n': 2, 'pop_change': 2, 'pop_percent_change': 2, 'yoy_change': 2,}) # rounding

        df['pop_percent_change'] = df['pop_percent_change'].map('{:.2f}%'.format, na_action='ignore') # adding percentages
        df['yoy_percent_change'] = df['yoy_percent_change'].map('{:.2f}%'.format,na_action='ignore')  # adding percentages

        df['b'] = pd.to_numeric(df['b'], errors='coerce').fillna(0).astype(int) # making broker count integers

        new_df = df[['p', 'v', 'pop_change', 'pop_percent_change', 'yoy_change', 'yoy_percent_change', 'dt', 'b', 'd', 'x', 'n']]
        new_df_transformed = new_df.map(lambda x: '{:,}'.format(x) if isinstance(x, numbers.Number) else x)

        # Final Data:
        data = new_df_transformed.to_dict('records')
        return data

    except Exception as e:
        print(f'Error in function create_change_table_data.')
        load_data.handle_exception(e)

        empty_data = [{'Period': 'Error', 'Value': 'Error', 'Change': 'Error', 'Percent Change': 'Error', 'Type': 'Error', 'Broker Count': 'Error'}]
        return empty_data

@app.callback(
    Output('graph', 'figure'),
    Output('data-table-2', 'rowData'),
    Output('data-table-2', 'columnDefs'),
    # Output('data-table-2', 'columnSize'),
    Input('data-table', 'selectedRows'),
    Input('data-table', 'rowData'),
    Input('bt-dropdown', 'value'),
    Input('start-date-dropdown', 'value'),
    Input('end-date-dropdown', 'value'),
    Input('p-freq-dropdown', 'value')
)
def create_actuals_estimates_graph_data(selected_rows, table_data, drop_down_value, start_period, end_period, period_frequency):
    """
    Creates Actual + Estimates Graph and fills in the parameter period over period table.
    """
    # guard against proceeding with row id selection, wait for actual row data from the grid
    if not selected_rows or isinstance(selected_rows, dict):
        raise PreventUpdate

    print('CREATE ACTUALS ESTIMATES INPUT VALS')
    print('selected rows', selected_rows)
    print('drop down value', drop_down_value)
    print('start period', start_period)
    print('end period', end_period)
    print('period freq', period_frequency)

    # define columns:
    try:
        if period_frequency == 'Q':
            pv_pop_grid_columns = [
                {'field': 'p', 'headerName': 'Period', 'pinned': 'left', 'cellStyle': {'backgroundColor': '#ededed',  'paddingLeft': '0px'}},
                {'field': 'v', 'headerName': 'Average'},
                {'field': 'pop_change', 'headerName': 'PoP Change',},
                {'field': 'pop_percent_change', 'headerName': 'PoP % Change', },
                {'field': 'yoy_change', 'headerName': 'YoY Change',},
                {'field': 'yoy_percent_change', 'headerName': 'YoY % Change',},
                {'field': 'd', 'headerName': 'Median'},
                {'field': 'x', 'headerName': 'Max'},
                {'field': 'n', 'headerName': 'Min'},
                {'field': 'dt', 'headerName': 'Type', "headerTooltip": "A = Actuals, E = Estimates"},
                {'field': 'b', 'headerName': 'Broker Count'},
            ]
        elif period_frequency == 'A':
            pv_pop_grid_columns = [
                {'field': 'p', 'headerName': 'Period', 'pinned': 'left', 'cellStyle': {'backgroundColor': '#ededed'}},
                {'field': 'v', 'headerName': 'Average'},
                {'field': 'pop_change', 'headerName': 'PoP Change',},
                {'field': 'pop_percent_change', 'headerName': 'PoP % Change',},
                {'field': 'd', 'headerName': 'Median'},
                {'field': 'x', 'headerName': 'Max'},
                {'field': 'n', 'headerName': 'Min'},
                {'field': 'dt', 'headerName': 'Type', "headerTooltip": "A = Actuals, E = Estimates"},
                {'field': 'b', 'headerName': 'Broker Count'},
            ]

    # set up variables:
        #print('create_actuals_estimates_graph_data selected row', selected_rows)
        cid = drop_down_value
        pid = selected_rows[0]["pid"]
        pname = selected_rows[0]["pname"]

        # print('create actuals estiammtes graph', 'cid', cid, 'pid', pid, 'pname', pname)

        # Now pull VA data
        data_df = va_api.pull_data(base_url, company_data_endpoint, f'?cid={cid}&pid={pid}&pfrom={start_period}&pto={end_period}&pfreq={period_frequency}&statistics=true', json.loads(os.environ.get('HEADERS')))
        # print('pulled AE data', data_df.head())
        sort_df = va_api.sort_periods(data_df)
        result_df = sort_df.dropna(subset=['v'])
        # print('about to run create_change_table function with df', result_df.columns)
        data = create_change_table_data(result_df)
        #print('data resulting from create change table', data)
        fig = time_series_chart_3(result_df, f'Selected Parameter: {pname}', cid)

        return fig, data, pv_pop_grid_columns

    except Exception as e:
        print(f'Error in function create_actuals_estimates_graph_data.')
        load_data.handle_exception(e)
        error_data = create_change_table_data(pd.DataFrame())
        error_fig = load_data.create_error_graph()

        return error_fig, error_data, pv_pop_grid_columns



@app.callback(
    Output('revisions-graph', 'figure'),
    Output('revisions-table', 'rowData'),
    Output('revisions-table', 'columnDefs'),
    Input('data-table', 'selectedRows'),
    Input('data-table', 'rowData'),
    Input('revisions-period-dropdown', 'value'),
    Input('bt-dropdown', 'value')
)
def create_revisions_graph(selected_rows, parameter_table_data, revisions_dropdown_value, cid):

    # guard against proceeding with row id selection, wait for actual row data from the grid
    if not selected_rows or isinstance(selected_rows, dict):
        raise PreventUpdate


    print('REVISIONS GRAPH INPUT VALUES:')
    print('selected_rows', selected_rows)
    print('revisions_dropdown_value', revisions_dropdown_value)
    print('cid', cid)

    try:

        # print('create_revisions_graph selected row', selected_rows)
        pid = selected_rows[0]["pid"]
        pname = selected_rows[0]["pname"]

        # 'revisions pid', pid, 'revisions pname', pname)

        fig = go.Figure()

        df_list = []

        for i, v in enumerate(revisions_dropdown_value):
            data_df = va_api.pull_data(base_url, revisions_endpoint, f'?cid={cid}&pid={pid}&ds=CD&p={v}&statistics=true', json.loads(os.environ.get('HEADERS')))
            if data_df.empty:
                continue
            revisions_df = data_df.dropna(subset=['v'])
            revisions_df = revisions_df.rename(columns={'r': 'Revision Date', 'p': 'Period', 'v':  f'Value', 'b':  'Broker Count'})
            df_list.append(revisions_df[['Revision Date', 'Period', f'Value', 'Broker Count']])
            fig.add_trace(go.Scatter(x=revisions_df['Revision Date'], y=revisions_df[f'Value'], mode='lines+markers',  line_shape='hvh', connectgaps=True, name=v,
                                     text=revisions_df['Broker Count'], hovertemplate=f'<b>{v}</b>' + '<br><b>Date: </b>%{x}<br><b>Value: </b>%{y}<br><b>Broker Count:</b> %{text}<br><extra></extra>')) #  line=dict(color='purple')


            # merge all dataframes in df_list
            value_df = pd.concat(df_list).sort_values(by='Revision Date', ascending=False)
                #reduce(lambda x, y: pd.concat(x, y), df_list)) # how='outer'

            #print('val df', value_df.head())
            # print('m -df.....')
            # m_df = revisions_df[['r', 'v', 'b']]
            # print('m_df', m_df.head(), m_df.columns)
            # print('about to merge')
            # m_df.merge(value_df, on='r', how='outer')
            # print('merge')

        # print('new value df;', value_df.head())

        fig.update_layout(
             title=f"Historical Revisions: {pname}",
             title_x=0.5, 
             margin=dict(t=90),
             xaxis_title='Revisions Dates',
             yaxis_title='Value',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor = 'rgba(255, 255, 255, 0.50)'),
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            ),
        )

        c_edate = company_info_df[company_info_df['cid'] == int(cid)]['need']
        # print(f'EDATE FOR {cid}', c_edate.iloc[0])

        fig.add_vline(
            x=c_edate.iloc[0],
            line_width=3,
            line_dash="dash",
            line_color="gray",
            name='Earnings Announcement',
        )

        # table data
        rounded_df = value_df.round(4)
        rounded_df_transformed = rounded_df.map(lambda x: '{:,}'.format(x) if isinstance(x,  numbers.Number) else x)
        rounded_df_transformed['Broker Count'] = pd.to_numeric(rounded_df_transformed['Broker Count'], errors='coerce').fillna(0).astype(int) # making broker count integers
        #rounded_df = rounded_df.select_dtypes(include=np.number).map('{:,}'.format) # add commas to numbers
        columndefs = [{"field": i} for i in value_df.columns]
        columndefs[0]["pinned"] = "left" # pin revisions date #  'cellStyle': {'backgroundColor': '#66c2a5'}
        columndefs[0]["cellStyle"] = {'backgroundColor': '#ededed', 'paddingLeft': '0px'} # "headerTooltip": "Broker Count"
        columndefs[-1]["headerTooltip"] = "Broker Count"
        data = rounded_df_transformed.to_dict('records')

        return fig, data, columndefs

    except Exception as e:
        print(f'Error in function create_revisions_graph.')
        load_data.handle_exception(e)
        error_data = [{'Revision Date': None, 'Value': None, 'Broker Count': None}]
        error_fig = load_data.create_error_graph()
        errorcols =  [{'field': 'Revision Date'}, {'field': 'Value'}, {'field': 'Broker Count'}]

        return error_fig, error_data, errorcols





# Run the app
if __name__ == '__main__':

    app.run(debug=True, dev_tools_hot_reload=True)
    # debugging is on, reloading is on,

