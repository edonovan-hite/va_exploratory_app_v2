"""
Created by: EmelineDonovan
Date: 10/8/2024
Description: Module for accessing VA API
"""

# imports:
import requests
import pandas as pd
from pandas import json_normalize
# from datetime import datetime

# url + used endpoints
visible_alpha_url = 'https://app.visiblealpha.com/api3/'
companies_endpoint = 'companies'
parameter_endpoint = 'parametermeta_cd'
company_data_endpoint = 'companydata'


def print_response(response):
    """
    Description: Prints out common response error codes and text
    """
    if response.status_code == 500:
        print("API exception : " + response.text)
    if response.status_code == 401:
        print("User unauthorized : " + response.text)
    if response.status_code == 400:
        print("Bad request : " + response.text)
    if response.status_code == 404:
        print('File not found : ' + response.text)
    else:
        print('API response error:', response.status_code, response.text)


def authenticate(user, passw):
    """
    Description: Authenticates access to the VA API
    :param user: the username for the VA API account
    :param passw: the password for the VA API account
    :return: authentication headers for the VA API account
    """
    auth_url = 'https://app.visiblealpha.com/auth/'
    auth_headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = {'username': user, 'password': passw}

    response = requests.post(auth_url, json=payload, headers=auth_headers)

    try:
        jwt = response.json()['jwt']
        # update and return headers
        auth_headers['Authorization'] = 'Bearer ' + jwt
        return auth_headers

    except Exception as e:
        print("Exception:" + str(e))
        print("Review response for authenticate")
        return print_response(response)


def pull_data(base_url, endpoint, endpoint_param_url, headers):
    """
    Description: Pulls and formats data from VA API
    This is the function that actually calls the API
    :param base_url: the base url for the VA API
    :param endpoint: the endpoint for the VA API
    :param headers: the headers for the VA API
    :return: formatted data from the VA API
    """
    url = base_url + endpoint + endpoint_param_url
    print('URL', url)
    response = requests.get(url, headers=headers)  # call the api

    try:
        if response.status_code == 200:
            data = json_normalize(response.json(), 'data')  # if api call goes through, return dataframe
        else:
            print_response(response)  # if api call does not go through, print what went wrong
            return
        print(f'Data was pulled from the VA API endpoint {endpoint}')
        return data
    except Exception as e:  # report any exceptions
        print("Exception:" + str(e))
        print("Review response for pull_data")
        return print_response(response)


def find_ticker(cname, bt, headers):
    """
    Description: Search for a ticker and its descriptive information
    Use when unsure about the VA name for a ticker + don't know the CID
    """
    # pull the companies data
    companies = pull_data(visible_alpha_url, companies_endpoint, '', headers)
    df = pd.DataFrame(companies)

    # filter tickers for the best match for either company name or bloomberg ticker
    filtered_df = df[(df['bt'].str.contains(bt, case=False)) | (df['cname'].str.contains(cname, case=False))]

    # if there's no matched, return no matches found, if there are, return a dataframe
    if filtered_df.empty:
        return print('No matches found')

    return print(filtered_df[['cid', 'cname', 'bt', 't']])


def get_ticker_params(base_url, endpoint, cid, params_list, headers):
    """
    Description: Retrieves parameters from VA API
    :param base_url: base url
    :param endpoint: the endpoint to access the parameters
    :param cid: the company id of the company whose parameters are to be retrieved
    :param params_list: words to pull specific parameters
    :param headers: authentication headers
    :return: a dictionary of available parameters and a dictionary of specific parameters based on params list
    """

    # pull in data for an individual company
    #new_endpoint = endpoint + f'?cid={cid}'
    parameters_df = pull_data(base_url, endpoint, f'?cid={cid}', headers)

    # make everything lowercase for ease of filtering
    parameters_df['pname'] = parameters_df['pname'].str.lower()
    # make a dictionary of available parameters and their respective ids
    parameter_dict = parameters_df.set_index('pid')['pname'].to_dict()

    # make filtered parameters dictionary to return in addition to parameters dict
    if not params_list:
        print('No specific parameters input')
        filtered_dict = {}
        return parameter_dict, filtered_dict
    else:
        print('Filtering based on input parameters:')
        pattern = '|'.join(params_list)
        filtered_df = parameters_df[parameters_df['pname'].str.contains(pattern, na=False)]
        filtered_dict = filtered_df.set_index('pid')['pname'].to_dict()
        if not filtered_dict:
            print('No parameter matches found')
            filtered_dict = {}
            return parameter_dict, filtered_dict
        else:
            return parameter_dict, filtered_dict


def create_period_endpoint(period, from_period, to_period, p_frequency):
    """
    Description: processes the period input and creates the appropriate endpoint to be called by the api
    :param period:
    :param from_period:
    :param to_period:
    :param p_frequency:
    :return: the proper period input
    """
    if period is not None and (from_period is None and to_period is None):
        # print('filtering for one singular period')
        period_endpoint = f'&p={period}'
        return period_endpoint
    elif period is None and from_period is not None and to_period is not None:
        # print('filtering for a range of data')
        period_endpoint = f'&pfrom={from_period}' + f'&pto={to_period}' + f'&pfreq={p_frequency}'
        return period_endpoint
    elif period is None and from_period is None and to_period is None:
        # print('not filtering based on period inputs')
        return ''
    elif period is not None and from_period is not None or to_period is not None:
        raise ValueError('One period is selected as well as a range of periods. Resolve this discrepancy.')
    elif period is None and (from_period is None or to_period is None):
        raise ValueError('Missing a period range value')
    else:
        return print('Situation not accounted for in create_period_endpoint. Fix this')


def sort_periods(df):
    """
    Description: Sorts the dataframes by period in chronological order
    :param df:
    :return: sorted df
    """
    # clean the fiscal years and separate them into quarters and years for proper sorting
    df['quarter'] = df['p'].str[0]
    df['quarter'] = df['quarter'].replace('F', 5)
    df['year'] = df['p'].str[-4:]

    # ensure the values are integers for proper sorting
    df['quarter'] = df['quarter'].astype(int)
    df['year'] = df['year'].astype(int)

    # sort the dataframe
    df_sorted = df.sort_values(by=['year', 'quarter'])

    # Drop the 'Prefix' and 'Year' columns after sorting
    df_sorted = df_sorted.drop(columns=['quarter', 'year'])

    df_sorted = df_sorted.reset_index(drop=True)

    return df_sorted

def pull_va_data(headers, endpoint, cid, pid, value, period, from_period, to_period, period_frequency, ds_type):
    """
    Description: Pulls data from VA API
    :param cid: company id
    :param pid: parameter id
    :param value: 'A' for Actuals, 'E' for Estimates, 'None' or any other value for both
    :param period: a selected period
    :param from_period: first period in period range
    :param to_period: last period in period range
    :param period_frequency: 'ALL', 'A', 'H', 'Q' for All, Annual, Half Year, and Quarters
    :return: pulled data
    """

    # PERIOD INFO
    # print('PERIOD', period)
    # print('FROM PERIOD', from_period)
    # print('TO PERIOD', to_period)

    try:

        # handle the periods inputted:
        period_endpoint = create_period_endpoint(period, from_period, to_period, period_frequency)

        if ds_type is None:
            ds_type_e = ''
        else:
            ds_type_e =  f'&ds={ds_type}'

        # this is the url to be pulled from:
        data_endpoint = endpoint + f'?cid={cid}' + f'&pid={pid}' + ds_type_e + period_endpoint + '&statistics=true'
        print('data endpoint', data_endpoint)

        # use helper function to request data from API
        data = pull_data(visible_alpha_url, data_endpoint, '', headers)

        # if there is a range on inputs, sort the periods chronologically
        if period is None:
            data_sorted = sort_periods(data)
        else:
            data_sorted = data

        # if asking specifically for actuals or estimates, return as such, if not, return actuals and estimates
        if value == 'A' or value == 'E':
            result_df = data_sorted[data_sorted['dt'] == value]
            if result_df.empty:
                print('There are no values matching', value, 'for this dataset. Ensure that your selection of estimates/actuals matches the period you are calling.')
        else:
            result_df = data_sorted
        return result_df

    except Exception as e:
        print('Error in pull_va_data', e)
        raise