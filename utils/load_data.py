"""
Created by: EmelineDonovan
Date: 9/19/2024
Description:
"""
import requests
import pandas as pd
from pandas import json_normalize
import os
from datetime import datetime
import plotly.graph_objects as go

"""
Just in Case functions
"""
def else_authenticate(username, password):
    auth_url = 'https://app.visiblealpha.com/auth/'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = {'username': username, 'password': password}

    response = requests.post(auth_url, json=payload, headers=headers)

    try:
        jwt = response.json()['jwt']
        # update and return headers
        headers['Authorization'] = 'Bearer ' + jwt
        return headers

    except Exception as e:
        print('Review response for load_data.py authenticate function.')
        print('Status Code:', response.status_code, 'Text:', response.text)
        return response

def print_response(response) :
    if response.status_code == 500:
        print("API exception : " + response.text)
    if response.status_code == 401:
        print("User unauthorized : " + response.text)
    if response.status_code == 400:
        print("Bad request : " + response.text)


def else_pull_data(base_url, endpoint, headers):
    """

    This function sends a GET request to a specified API endpoint to retrieve metadata information for a given ticker.

    Args:
    cid (int): The id of the company you want to retrieve metadata for.
    Returns:
    pd.DataFrame or None: If successful, a DataFrame containing the requested metadata information is returned.
    If there is an issue with the API request or response, None is returned, and an error message is printed.
    """
    url = base_url + endpoint
    response = requests.get(url, headers=headers)

    try:
        if response.status_code == 200:
            #data = response.json()['data']
            data = json_normalize(response.json(), 'data')
            path = r''
            data.to_csv(path + endpoint.split('?')[0] + '.csv')
        else:
            print_response(response)
        print('data pulled')
        return data
    except Exception as e:
        print("Exception:" + str(e))
        print("Review response")
        return response


"""
Main Helper Functions
"""

def does_dataframe_exist(base_url, endpoint, headers):
    print('Checking if dataframe exists')
    path = r''
    just_endpoint = endpoint.split('?')[0]
    file_name = just_endpoint + '.csv'
    file_path = os.path.join(path, file_name)
    print(f'Checking path: {file_path}')

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df
    else:
        print(f'File not found. File path: {file_path}Pulling data...')
        response_df = else_pull_data(base_url, endpoint, headers)
        return response_df



def create_options_list(dataframe, value):
    dataframe.dropna(subset=['cname', 'bt', 'cid'], inplace=True)
    dataframe['cname'] = dataframe['cname'].str.lower()
    dataframe['cname'] = dataframe['cname'].str.title()
    list_of_dicts = [{'label': row[value] + ' EQUITY' + '  ---  ' + f'{row['cname']}', 'value': str(row['cid']).title()} for _, row in dataframe.iterrows()]
    return list_of_dicts


def generate_current_quarter_year():
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_year_string = str(current_year)

    if current_month in [1, 2, 3]:
        quarter = '1'
    elif current_month in [4, 5, 6]:
        quarter = '2'
    elif current_month in [7, 8, 9]:
        quarter = '3'
    elif current_month in [10, 11, 12]:
        quarter = '4'
    else:
        return 'Error with determining quarter'
    current_fiscal_quarter = quarter + 'QFY-' + current_year_string

    current_fiscal_year = 'FY-' + current_year_string
    return current_fiscal_quarter, current_fiscal_year


def generate_fiscal_quarters(start_year=2008, end_year=2034):
    """
    :param start_year:
    :param end_year:
    :return: The fiscal quarters of the date range in put in the format 1QFY-2008 (example)
    """
    quarters = []
    for year in range(start_year, end_year + 1):
        for q in range(1, 5):  # Loop through 1Q to 4Q
            quarters.append(f'{q}QFY-{year}')

    current_quarter, ___ = generate_current_quarter_year()

    return quarters, current_quarter


def generate_fiscal_years(start_year=2008, end_year=2034):
    """
    :param start_year:
    :param end_year:
    :return: The fiscal years of the date range in put in the format FY-2008 (example)
    """
    fiscal_years = []
    for year in range(start_year, end_year + 1):
        fiscal_years.append(f'FY-{year}')

    ___, current_year = generate_current_quarter_year()
    return fiscal_years, current_year


def create_error_graph():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[], y=[]))
    fig.update_layout(title="No data to display",
                      xaxis_title='No Data',
                      yaxis_title='No Data',
                      template="plotly_white")
    return fig



def handle_exception(e):
    e_type = type(e).__name__  # Get the exception type (e.g., 'ValueError')
    e_file = e.__traceback__.tb_frame.f_code.co_filename  # Get the filename
    e_line = e.__traceback__.tb_lineno  # Get the line number
    e_message = str(e)  # Get the exception message

    print(f'--Exception Message: {e_type}, {e_message}')
    print(f'--Exception Location: Line {e_line} in File {e_file}')
    return {}




# COMMENTED OUT:
# print('NA VALUES', dataframe.isna().sum())

# base_url = 'https://app.visiblealpha.com/api3/'
# companies_endpoint = 'companies?stid=1'
# parameter_endpoint = 'parametermeta_cd'
# revisions_endpoint = 'revisions'

# headers = authenticate('aummat@hitehedge.com', 'MobilityHIT3!')

#company_info_df = does_dataframe_exist(base_url, companies_endpoint, headers)


# period_dict = [
#     {'label': 'FY-2022', 'value': 'FY-2022'},
#     {'label': '1QFY-2023', 'value': '1QFY-2023'},
#     {'label': 'CY-2022', 'value': 'CY-2022'},
#     {'label': '1QCY-2023', 'value': ' 1QCY-2023'},
#     {'label': 'F-1', 'value': 'F-1'},
#     {'label': 'F0', 'value': 'F0'},
#     {'label': 'F1', 'value': 'F1'},
#     {'label': 'FQ-1', 'value': 'FQ-1'},
#     {'label': 'FQ0', 'value': 'FQ0'},
#     {'label': 'FQ1', 'value': 'FQ1'},
#     {'label': 'FH-1', 'value': 'FH-1'},
#     {'label': 'FH0', 'value': 'FH0'},
#     {'label': 'FH1', 'value': 'FH1'}
# ]










# COMMENTED OUT:


# Add a line trace
#         # fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines'))
#         fig.add_trace(go.Scatter())
#         fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
#         fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
#         fig.update_layout(
#                 plot_bgcolor='white',  # White background for the specific subplot
#                 paper_bgcolor='white',  # White around the plot
#             )
#         fig.add_annotation(
#                 text="No Revisions Data",  # Text to display
#                 xref="paper", yref="paper",
#                 x=0.5, y=0.5,  # Position the text in the center of subplot 2 (relative position)
#                 showarrow=False,  # No arrow with the annotation
#                 font=dict(size=25, color="purple"),  # Customize font size and color
#             )
#         return fig, [], []

'''
# Callback to serve the PDF file for download
@app.callback(
    Output("url-1", "href"),
    Input("link-download-1", "n_clicks"), prevent_initial_call=True)
def serve_pdf(n_clicks_1):
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        bucket_name = 's3quant'
        # aws_access_key_id     = dbutils.secrets.get(scope="aws", key="AWS_ACCESS_KEY_ID")
        # aws_secret_access_key = dbutils.secrets.get(scope="aws", key="AWS_SECRET_ACCESS_KEY")

        # this is from Maysa's awesome s3 file right?
        s3_resource = s3_connect.connect_to_s3_from_databricks('us-east-2', aws_access_key, aws_secret_key) # switched to os variables
        s3_bucket = s3_connect.connect_to_s3_bucket(s3_resource, bucket_name)        
        s3_resource = boto3.resource('s3', region_name=region_name, aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)
        s3_client = s3_resource.meta.client  # This gets the client from the s3_resource object
        S3_KEY = 'visible_alpha/companies_reference.csv'
        # Generate a presigned URL for the S3 file
        presigned_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': 's3quant', 'Key': S3_KEY},
                                                         ExpiresIn=3600)  # URL expires in 1 hour
        return presigned_url

# Callback to serve the PDF file for download
@app.callback(
    Output("url-2", "href"),
    Input("link-download-2", "n_clicks"), prevent_initial_call=True)
def parameter_link(n_clicks_1):
        bucket_name = 's3quant'
        # aws_access_key_id     = dbutils.secrets.get(scope="aws", key="AWS_ACCESS_KEY_ID")
        # aws_secret_access_key = dbutils.secrets.get(scope="aws", key="AWS_SECRET_ACCESS_KEY")
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        s3_resource = s3_connect.connect_to_s3_from_databricks('us-east-2', aws_access_key, aws_secret_key) # switched to os variables
        s3_bucket = s3_connect.connect_to_s3_bucket(s3_resource, bucket_name)        
        s3_resource = boto3.resource('s3', region_name=region_name, aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)
        s3_client = s3_resource.meta.client  # This gets the client from the s3_resource object
        S3_KEY = 'visible_alpha/companies_reference.csv'
        # Generate a presigned URL for the S3 file
        presigned_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': 's3quant', 'Key': S3_KEY},
                                                         ExpiresIn=3600)  # URL expires in 1 hour
        # # Generate a presigned URL for the S3 file
        # presigned_url = s3_client.generate_presigned_url('get_object',
        #                                                  Params={'Bucket': 's3hitescratch', 'Key': S3_KEY},
        #                                                  ExpiresIn=3600)  # URL expires in 1 hour
        return presigned_url

'''

# quarter_options1 = va_api.generate_fiscal_quarters()
# quarter_options = [{'label': period, 'value': period} for period in quarter_options1]
# year_options = va_api.generate_fiscal_years()

# import plotly.express as px
# import matplotlib.pyplot as plt
# import seaborn as sns
# import plotly.tools as tls

# # Define the layout of the app
# app.layout = html.Div([
#     html.H1("Explore Visible Alpha Data"),
#     html.H2('Select a company and explore its unique VA parameters'),
#     html.Label("Select a Bloomberg Ticker:"),
#     dcc.Dropdown(
#         id='dropdown',
#         searchable=True,
#         clearable=True,
#         options=bt_ticker_list,
#         value=bt_ticker_list[0]['value']
#     ),
#     html.Label("Quarterly or Annual Data:"),
#     dcc.Dropdown(
#         id='p-freq-dropdown',
#         options=[{'label':'Quarterly', 'value':'Q'}, {'label':'Annually', 'value':'A'}],
#         value='Q'
#     ),
#     html.Label('Select Start Date:'),
#     dcc.Dropdown(
#         id='start-date-dropdown',
#         # options = [],
#         # value=quarter_options[0],
#         placeholder="Select a start date"
#     ),
#     html.Label('Select End Date:'),
#     dcc.Dropdown(
#         id='end-date-dropdown',
#         # options = [{'label': period, 'value': period} for period in quarter_options],
#         # value=quarter_options[-1],
#         placeholder="Select an end date"
#     ),
#     html.Div(id='output-container'),

#     ddk.Row(style={'display': 'flex', 'flex-wrap': 'nowrap'}, children=[
#         ddk.Card(style={'flex-grow': '1', 'width': '20%'}, children=[
#             html.H2('Parameter Table', style={'textAlign': 'center'}),
#             dash_table.DataTable(
#             id='data-table',
#             data=[],
#             columns=[],
#             filter_action="native",
#             row_selectable='single',
#             selected_rows=[0],
#             export_format='csv',  # Enable export to CSV
#             export_headers='display',
#             page_size=35,  # sets number of rows visible per page
#             style_table={'width': '100%', 'flex-grow': '0'},
#             style_cell={'textAlign':'left'},
#         )]),
#         ddk.Card(style={'flex-grow': '1', 'width': '60%'},  children=[
#             html.H2('Actuals + Estimates for Selected Parameter', style={'textAlign': 'center'}),
#             dcc.Graph(id='graph', style={'height':'1150px'})]),
#         ddk.Card(style={'width': '20%'}, children=[html.H2('Parameter Values + period-over-period change Table', style={'textAlign': 'center'}),
#         dash_table.DataTable(
#             id='data-table-2',
#             data=[],
#             columns=[],
#             page_size=35,  # sets number of rows visible per page
#             export_format='csv',  # Enable export to CSV
#             export_headers='display',
#             style_cell={'textAlign':'left'},
#             style_table={'width': '90%', 'flex-grow': '0'}
#         )]),
#     ]),
#     ddk.Row([ddk.Card(width=50, children=[html.H2('Revisions Data'), dcc.Dropdown(id='revisions-period-dropdown')])]),
#     ddk.Row(style={'display': 'flex', 'flex-wrap': 'nowrap'}, children=[ddk.Card(width=80, children=[dcc.Graph('revisions-graph',  style={'height':'1150px'})]),
#         ddk.Card(width=20, children=[
#             dash_table.DataTable(
#                 id='revisions-table',
#                 data=[],
#                 columns=[],
#                 page_size=35,
#                 export_format='csv',
#                 export_headers='display')])]),
#     ddk.Row([ddk.Card(width=50, children=[
#     html.H4('Download Parameter Mapping for Energy & Autos Companies'),
#     dcc.Location(id="url-1", refresh=True),
#     html.A("Companies", id="link-download-1", href="#"),
#     html.Br(),
#     dcc.Location(id="url-2", refresh=True),
#     html.A("Parameters", id="link-download-2", href="#"),
#     html.H4('Summary:'),
#     html.H4("This exploratory app pulls data for a company's unique parameter with a Visible Alpha API call. First, select the company by its Bloomberg Ticker name in the first dropdown. Then, select whether you would like the data displayed to be annual or quarterly. Finally, select a start and end date."),
#     html.H4('Parameter Table: This table will load the unique parameter names and IDs associated with the selected company. The first company parameter is automatically selected and can be switched by clicking on the circle next to a different parameter. Search for parameter names or IDs by typing in the desired parameter in the "filter data" section of the table. This table can be exported as a csv by clicking the "Export" button.'),
#     html.H4('Actuals + Estimates for Selected Parameter: This visualization will show the actuals and estimates data for the selected parameter. Selecting a date range that excludes estimates data will only show the plot containing actuals data, and vice versa. Selecting a date range where the start date is after the end date will result in no data being displayed.'),
#     html.H4('Parameter Values + period-over-period change Table: This table shows the periods (either fiscal quarters or years) available given the selected start and end date, the values associated with the period, the difference between a value and the value from the previous period, this change as a percent, and whether this value is an actual or an estimate. This table can be exported as a csv with the "Export" button.'),
#     html.H4('Revisions: Select a period to see the historical revisions for the parameter elected above.'),
#     html.H4('BROKER LIST: 86 Research, ABG Sundal Collier, Absa Group, Air Control Tower, Alantra Equities, Alembic Global, AlphaValue, Ambit Capital, Anchor Stockbrokers, Apalache Analisis, Apex Securities Bhd, Arete Research, Arqaam, Astris Advisory Japan, Ata Yatirim, Avior Capital, AXIA Ventures Group, Azabu Research, Baader Helvea, Bank Degroof Petercam N.V., Bank of America Securities, Bank of Montreal, Barclays, Barrenjoey, Barrington Research, Bell Potter Securities, Beltone Financial Holding, Berenberg Bank, Bestinver Securities, BNI Sekuritas, BNP Paribas Exane, BOCOM International, Bradesco BBI, BTG Pactual, BTIG, CaixaBank, Canaccord Genuity, Cantor Fitzgerald, Capital One, Carraighill Capital, Carter Bar Securities, CBRE, CCB International Securities, Centrum, CGS International Securities Hong Kong Limited, China Merchants Securities (Hong Kong), China Renaissance, Chronux Research, CI Capital, CIBC, Citi, CL King, CLSA, Colliers Securities LLC, Compass Point, Consumer Edge, Craigs Investment Partners, Credicorp Capital, D. A. Davidson, Daiwa Capital, DAM Capital Advisors Limited, Danske Bank, Data Based Analysis, Davy, DBS Vickers, Desjardins Securities, Deutsche Bank, Deutsche Numis, DNB Markets, Dowling & Partners, E&P Financial Group, Edgewater Research, EFG Hermes, Eight Capital, Equirus, EquitaSIM, Erste Group, Eurobank Equities, Euroxx Securities, Evercore ISI, FBN Quest, FBN Securities, First Shanghai Securities, Forsyth Barr, Freedom Capital Markets, Goldman Sachs, Goodbody, Gordon Haskett, Guggenheim Securities, H.C. Wainwright, Haitong, Hauck Aufhäuser Investment Banking, Hovde Group, HSBC, Huatai Securities Co. Ltd, Huber Research, ICBC International Research, LTD, ICICI Securities, IIFL, InCred Capital, ING Research, Insight Securities, Intermarket Securities, Intron Health, Investec Bank PLC, IPOPEMA Securities, Is Yatirim Menkul Degerler AS, Itau Securities, Janney, Jarden Securities, JB Capital, Jefferies, JM Financial, JMP Securities, Johnson Rice, Jones Trading, JS Global Capital, K. Liu & Co, KBC Securities, Keefe, Bruyette & Woods, Kempen, Kepler Cheuvreux, KeyBanc, KGI Securities, Kolytics, Kotak Securities, Ladenburg-Thalmann, Leerink Partners, LifeSci Capital, Loop Capital, Macquarie Group Limited, Marathon Capital Markets, LLC, Maxim Group, Maybank, Melius Research, Meristem Securities, Miranda Global Research, Mizuho Securities, Mizuho USA, Monness Crespi Hardt & Co., Morgan Stanley, Morgans, Morningstar, Motilal Oswal, MST Financial, National Bank Financial, Nedbank Ltd, Needham & Company, LLC, Nephron Research, New Street Research, NextGen Research, Nordea, Northcoast Research, Northland Capital Markets, Nuvama Wealth Management Limited, ODDO BHF, On Field Investment Research, Oppenheimer, Optima Bank, Ord Minnett, LTD, OxCap Analytics, Panmure Liberum, Pareto Securities, Peel Hunt, Periphery Research, Pickering Energy Partners, Piper Sandler, Pivotal Research, QNB Financial Services, QValue, R5 Capital, Raymond James, RBC Capital Markets, Redburn Atlantic, Regis Partners, ResearchGreece, Rosenblatt Securities, Roth MKM, Safra Securities, Samsung Securities, Sanford Bernstein, Santander, Scotia Capital Markets, Seaport Global Securities, LLC, SEB, Siebert Williams Shank, Singer Capital Markets, SMBC Nikko, SNB Capital, Soochow Securities International, Spark Capital, SPDB International Securities, SSI Securities, Stephens Inc, Stifel Nicolaus, Susquehanna Financial Group, Swiss Capital, TD Cowen, TD Securities, Telsey Advisory Group, Tera Yatirim, TH Data Capital, The Benchmark Company, Thompson Davis, Thompson Research Group, Tianfeng Securities, Topline Securities Ltd., TP ICAP Group, TPH&Co., Truist Securities, UBS, Unlu & Co, US Capital Advisors, US Tiger Securities, Vertical Research, Wedbush Securities, Wells Fargo, WestPark Capital, William Blair, Wilsons, Wood & Co, XP Securities, Yapı Kredi, Zelman & Associates, Zeus Capital, Alpha Finance Investment Services, Paradigm Capital Inc., Wolfe Research')])])
# ])



#     try:
#     # Add first line
#     fig.add_trace(go.Scatter(x=data_estimates['index'], y=data_estimates['v'], mode='lines',  text=data_estimates['b'], hovertemplate='Broker Count: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>', name='Estimates',
#                              line=dict(color='red')), row=2, col=1)
#     # # for estimates subplot:
#     fig.update_xaxes(title_text=x_axis_title, tickvals=data_estimates.index, ticktext=data_estimates['p'], row=2,
#                      col=1)
#     fig.update_yaxes(title_text=y_axis_label, range=[min(data_estimates['v']), max(data_estimates['v']) * 1.07],
#                      row=2, col=1)

# except Exception as e:
#     print(f"Error in Subplot 2: {e}")
#     # Create a blank subplot and apply "plotly_white" manually to this subplot
#     fig.add_trace(go.Scatter(), row=2, col=1)

#     # Manually apply white background and remove axis lines for this specific subplot
#     fig.update_xaxes(showgrid=False, zeroline=False, visible=False, row=2, col=1)
#     fig.update_yaxes(showgrid=False, zeroline=False, visible=False, row=2, col=1)
#     fig.update_layout(
#         plot_bgcolor='white',  # White background for the specific subplot
#         paper_bgcolor='white',  # White around the plot
#     )
#     fig.add_annotation(
#         text="No Estimates Data",  # Text to display
#         xref="paper", yref="paper",
#         x=0.75, y=0.5,  # Position the text in the center of subplot 2 (relative position)
#         showarrow=False,  # No arrow with the annotation
#         font=dict(size=25, color="red"),  # Customize font size and color
#         row=2, col=1  # Apply to the specific subplot (1, 2)
#     )
#     #revisions_df['index'] = revisions_df.index
#     x_data = revisions_df['r']
#     y_data = revisions_df['v']
#     # print('REVISIONS', revisions_df)
#     # print('VALUES', revisions_df['v'])

#     # x_data = [1, 2, 3, 4, 5]
#     # y_data = [10, 11, 12, 13, 14]

#     # Create the figure
#     fig = go.Figure()

# # Add a line trace
#     fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines',  line_shape='hvh', connectgaps=True))
#     fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers',   marker=dict(color='red') ))
#     # ADD RED DOTS FOR EVERY DATAPOINT

#     return fig


'''
def time_series_chart2(data, fig_title: str, y_axis_label: str, periodicity):
    try:

        fig = make_subplots(rows=2, cols=1,  vertical_spacing=0.1, subplot_titles=['Actuals', 'Estimates'])


        data['index'] = data.index

        data_actuals = data[data['dt'] == 'A']
        data_estimates = data[data['dt'] == 'E']

        if periodicity == 'Q':
            x_axis_title = 'Quarters'
        elif periodicity == 'A':
            x_axis_title = 'Years'

        actuals_data_max = max(data_actuals['v'])
            # Determine the appropriate label based on the range
        if actuals_data_max >= 1e9:
            y_axis_label = "Billions"
        elif actuals_data_max >= 1e6:
            y_axis_label = "Millions"
        elif actuals_data_max >= 1e3:
            y_axis_label = "Thousands"
        else:
            y_axis_label = "Value"

        # try making the actuals subplot:
        try:
            fig.add_trace(go.Scatter(x=data_actuals['index'], y=data_actuals['v'], mode='lines', text=data_actuals['b'], hovertemplate='Broker Count: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>', name='Actuals',
                                     line=dict(color='blue')), row=1, col=1)
            fig.add_trace(go.Scatter(x=data_actuals['index'], y=data_actuals['v'], mode='markers', marker=dict(color='blue'), showlegend=False, text=data_actuals['b'], hovertemplate='Broker Count: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>'), row=1, col=1)

            # for actuals subplot:
            fig.update_xaxes(title_text=x_axis_title, tickvals=data_actuals.index, ticktext=data_actuals['p'], row=1,
                             col=1)
            fig.update_yaxes(title_text=y_axis_label, range=[min(data_actuals['v']), max(data_actuals['v']) * 1.07],
                             row=1, col=1)

        except Exception as e:
            print(f"Error in Subplot 1: {e}")
            # Create a blank subplot and apply "plotly_white" manually to this subplot
            fig.add_trace(go.Scatter(), row=1, col=1)

            # Manually apply white background and remove axis lines for this specific subplot
            fig.update_xaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
            fig.update_yaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
            fig.update_layout(
                plot_bgcolor='white',  # White background for the specific subplot
                paper_bgcolor='white',  # White around the plot
            )
            fig.add_annotation(
                text="No Acutals Data",  # Text to display
                xref="paper", yref="paper",
                x=0.75, y=0.5,  # Position the text in the center of subplot 2 (relative position)
                showarrow=False,  # No arrow with the annotation
                font=dict(size=25, color="blue"),  # Customize font size and color
                row=1, col=1  # Apply to the specific subplot (1, 2)
            )

        # try making the estimate subplot:
        try:
            # Add first line
            fig.add_trace(go.Scatter(x=data_estimates['index'], y=data_estimates['v'], mode='lines',  text=data_estimates['b'], hovertemplate='Broker Count: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>', name='Estimates',
                                     line=dict(color='red')), row=2, col=1)
            fig.add_trace(go.Scatter(x=data_estimates['index'], y=data_estimates['v'], mode='markers', marker=dict(color='red'), showlegend=False, text=data_estimates['b'], hovertemplate='Broker Count: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>'), row=2, col=1)
            # # for estimates subplot:
            fig.update_xaxes(title_text=x_axis_title, tickvals=data_estimates.index, ticktext=data_estimates['p'], row=2,
                             col=1)
            fig.update_yaxes(title_text=y_axis_label, range=[min(data_estimates['v']), max(data_estimates['v']) * 1.07],
                             row=2, col=1)

        except Exception as e:
            print(f"Error in Subplot 2: {e}")
            # Create a blank subplot and apply "plotly_white" manually to this subplot
            fig.add_trace(go.Scatter(), row=2, col=1)

            # Manually apply white background and remove axis lines for this specific subplot
            fig.update_xaxes(showgrid=False, zeroline=False, visible=False, row=2, col=1)
            fig.update_yaxes(showgrid=False, zeroline=False, visible=False, row=2, col=1)
            fig.update_layout(
                plot_bgcolor='white',  # White background for the specific subplot
                paper_bgcolor='white',  # White around the plot
            )
            fig.add_annotation(
                text="No Estimates Data",  # Text to display
                xref="paper", yref="paper",
                x=0.75, y=0.5,  # Position the text in the center of subplot 2 (relative position)
                showarrow=False,  # No arrow with the annotation
                font=dict(size=25, color="red"),  # Customize font size and color
                row=2, col=1  # Apply to the specific subplot (1, 2)
            )

        fig.update_layout(title_text=f"{fig_title}", title_x=0.5, margin=dict(t=90),)

        return fig

    except Exception as e:
        print(f'Error in the entire figure occured {e}')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[]))
        fig.update_layout(title="No data to display",
                          xaxis_title='No Data',
                          yaxis_title='No Data',
                          template="plotly_white")
        return fig

'''


'''
def process_data(data):
        """
        Process and clean a DataFrame containing time-series data.

        Args:
        - data (pd.DataFrame): A DataFrame containing time-series data with columns 'r' for timestamps and 'v' for values.

        Returns:
        pd.DataFrame: A cleaned and processed DataFrame.
        """
        data['r'] = pd.to_datetime(data['r'])
        data.dropna(subset=['v'], inplace=True)
        data.sort_values(by=['r'], inplace=True)
        data.reset_index(drop=True, inplace=True)
        return data
'''

# print('pulling consensus data:')
# consensus_df = va_api.pull_data(base_url, company_consensus_endpoint, f'?cid={cid}&pid={pid}&statistics=true&ccd=true', headers)

# from plotly.subplots import make_subplots
# import boto3


# # actuals_data_max = max(data_actuals['v'])
#     # Determine the appropriate label based on the range
# if max(data_actuals['v']) >= 1e9:
#     y_axis_label = "Billions"
# elif max(data_actuals['v']) >= 1e6:
#     y_axis_label = "Millions"
# elif max(data_actuals['v']) >= 1e3:
#     y_axis_label = "Thousands"
# else:
#     y_axis_label = "Value"


#
# revisions_data_max = max(y_data)
#     # Determine the appropriate label based on the range
# if revisions_data_max >= 1e9:
#     y_axis_label = "Billions"
# elif revisions_data_max >= 1e6:
#     y_axis_label = "Millions"
# elif revisions_data_max >= 1e3:
#     y_axis_label = "Thousands"
# else:
#     y_axis_label = "Value"


# dash_table.DataTable(
#     id='data-table-2',
#     data=[],
#     columns= pv_pop_table_columns,
#     page_size=35,
#     export_format='csv',
#     export_headers='display',
#     # six columns in a narrow container: cap each cell and scroll
#     # horizontally inside the card rather than spilling out of it
#     style_cell={'textAlign': 'left', 'minWidth': '60px', 'width': '60px', 'maxWidth': '60px',
#                 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'padding': '4px'},
#     # let the long header labels wrap so they aren't clipped to ellipses
#     style_header={'whiteSpace': 'normal', 'height': 'auto'},
#     style_table={'width': '100%', 'height': '100%', 'overflowY': 'auto'}, # 'width': '100%'
#  )


# if period_frequency == 'Q':
#     pv_pop_grid_columns = [
#         {'field': 'p', 'colId': 'p_q', 'headerName': 'Period', 'pinned': 'left',
#          'cellStyle': {'backgroundColor': '#ededed', 'paddingLeft': '0px'}},
#         {'field': 'v', 'colId': 'v_q', 'headerName': 'Average'},
#         {'field': 'pop_change', 'colId': 'pop_change_q', 'headerName': 'PoP Change',
#          "headerTooltip": "Quarter over Quarter Value Change"},
#         {'field': 'pop_percent_change', 'colId': 'pop_percent_change_q', 'headerName': 'PoP % Change',
#          "headerTooltip": "Quarter over Quarter Percent Change"},
#         {'field': 'yoy_change', 'colId': 'yoy_change_q', 'headerName': 'YoY Change',
#          "headerTooltip": "Year over Year Value Change"},
#         {'field': 'yoy_percent_change', 'colId': 'yoy_percent_change_q', 'headerName': 'YoY % Change',
#          "headerTooltip": "Year over Year Percent Change"},
#         {'field': 'd', 'colId': 'd_q', 'headerName': 'Median'},
#         {'field': 'x', 'colId': 'x_q', 'headerName': 'Max'},
#         {'field': 'n', 'colId': 'n_q', 'headerName': 'Min'},
#         {'field': 'dt', 'colId': 'dt_q', 'headerName': 'Type', "headerTooltip": "A = Actuals, E = Estimates"},
#         {'field': 'b', 'colId': 'b_q', 'headerName': 'BC', "headerTooltip": "Broker Count"},
#     ]
# elif period_frequency == 'A':
#     pv_pop_grid_columns = [
#         {'field': 'p', 'colId': 'p_a', 'headerName': 'Period', 'pinned': 'left',
#          'cellStyle': {'backgroundColor': '#ededed'}},
#         {'field': 'v', 'colId': 'v_a', 'headerName': 'Average'},
#         {'field': 'pop_change', 'colId': 'pop_change_a', 'headerName': 'PoP Change',
#          "headerTooltip": "Year over Year Value Change"},
#         {'field': 'pop_percent_change', 'colId': 'pop_percent_change_a', 'headerName': 'PoP % Change',
#          "headerTooltip": "Year over Year Percent Change"},
#         {'field': 'd', 'colId': 'd_a', 'headerName': 'Median'},
#         {'field': 'x', 'colId': 'x_a', 'headerName': 'Max'},
#         {'field': 'n', 'colId': 'n_a', 'headerName': 'Min'},
#         {'field': 'dt', 'colId': 'dt_a', 'headerName': 'Type', "headerTooltip": "A = Actuals, E = Estimates"},
#         {'field': 'b', 'colId': 'b_a', 'headerName': 'BC', "headerTooltip": "Broker Count"},
#     ]

