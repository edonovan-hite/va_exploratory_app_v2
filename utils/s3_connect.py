# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 11:57:33 2023

Included a function called load_s3_params() that hard codes the key parameters for connecting to s3 including the 
bucket, region, and location of credentials associated with this user/machine.

@author: MaysaJarudi
"""

import os
import pandas as pd
import boto3
from io import StringIO
import datetime as dt
from io import BytesIO
import gzip
import json
import datetime as dt

def load_s3_params():
    """
    Bucket, region
    """
    bucket_name    = 's3quant'
    region_name    = 'us-east-2'
    
    return bucket_name, region_name

def list_folders_in_bucket(bucket_name):
    
    s3_client = boto3.client('s3')
    
    result = s3_client.list_objects(Bucket=bucket_name, Delimiter='/')
    
    folders = [prefix['Prefix'] for prefix in result.get('CommonPrefixes', [])]
    
    return folders

def list_folders_in_relative_s3_path(bucket_name, s3_path):
    """
    List folders within a specified S3 path relative to the bucket root.
    
    Args:
        bucket_name (str): The name of the S3 bucket.
        s3_path (str): Relative S3 path (e.g., 'model_runs_v2/output/').
        
    Returns:
        List[str]: List of folder paths within the specified S3 path.
    """
    
    # Ensure the path ends with a slash
    if not s3_path.endswith('/'):
        s3_path += '/'
    
    # List objects in the specified prefix
    s3_client = boto3.client('s3')
    result = s3_client.list_objects(Bucket=bucket_name, Prefix=s3_path, Delimiter='/')
    
    # Extract folders from CommonPrefixes
    folders = [prefix['Prefix'] for prefix in result.get('CommonPrefixes', [])]
    
    return folders

def list_files_in_s3_folder(bucket_name, folder_path):
    """
    List all files in the specified S3 folder.
    
    Args:
        bucket_name (str): Name of the S3 bucket.
        folder_path (str): Path to the folder in the bucket.
        
    Returns:
        List[str]: List of file paths (keys) in the folder.
    """
    
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
    
    # Extract file paths
    file_paths = [obj['Key'] for obj in response.get('Contents', []) if not obj['Key'].endswith('/')]
    
    return file_paths


def connect_to_s3_from_dash(region_name):
    """
    From Dash Enterprise server 

    Load credentials from credentials file and use that to connect to s3
    using boto3.resource
    
    Returns s3_resource
    """
    # Create the s3 resource session
    aws_access_key = os.environ.get('aws_access_key')
    aws_secret_key = os.environ.get('aws_secret_key')
    print('Aws access key: ', aws_access_key)
    print('Aws secret key: ', aws_secret_key)
    s3_resource = boto3.resource('s3', region_name=region_name,aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)

    return s3_resource


def connect_to_s3(path_to_credentials, credentials_filename, region_name):
    """
    Load credentials from credentials file and use that to connect to s3
    using boto3.resource
    
    Returns s3_resource
    """
    # Create the s3 resource session
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = path_to_credentials + credentials_filename
    s3_resource = boto3.resource('s3', region_name=region_name)
        
    return s3_resource

def connect_to_s3_from_databricks(region_name, aws_access_key_id, aws_secret_access_key):
    """
    Connects to S3 using credentials stored in Databricks Secrets.
    
    Args:
        region_name (str): AWS region.
        secret_scope (str): Databricks secret scope name (default: 'aws-scope').

    Returns:
        boto3 S3 resource object.
        
    NOTE - APRIL 2025
    Note you wuold run this in your notebook in Dbricks and feed to this function:

    aws_access_key_id     = dbutils.secrets.get(scope="aws", key="AWS_ACCESS_KEY_ID")
    aws_secret_access_key = dbutils.secrets.get(scope="aws", key="AWS_SECRET_ACCESS_KEY")            
    """
    

    # Create a session using the retrieved access keys
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name  # Specify the region you want to use
    )
    sts = session.client("sts")
    response = sts.assume_role(RoleArn="arn:aws:iam::287321004952:role/role_datascience-3",
                                RoleSessionName="S3_Search")
    
    #
    creds   = response["Credentials"]
    
    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=region_name
    )
            
    return s3_resource

def connect_to_s3_using_role(region_name, path_to_aws_cred, aws_cred_filename):
    """
    Connects to S3 using credentials stored in Databricks Secrets.
    
    Args:
        region_name (str): AWS region.
        secret_scope (str): Databricks secret scope name (default: 'aws-scope').

    Returns:
        boto3 S3 resource object.
    """
    # cred filename
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = path_to_aws_cred + aws_cred_filename
    session = boto3.Session(profile_name="data-science-3")
    sts = session.client("sts")
    response = sts.assume_role(RoleArn="arn:aws:iam::287321004952:role/role_datascience-3", RoleSessionName="test")
    
    new_session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                                aws_session_token=response['Credentials']['SessionToken'])
    s3_session = new_session.client("s3")
            
    return s3_session

def connect_to_s3_bucket(s3_resource, bucket_name):
    """
    Use the created s3_resource to connect to a particular bucket
    
    Function will try connecting to the bucket using try/except and will print
    a message if there is a problem
    
    s3_resource: s3_resource object created from connect_to_s3() function
    bucket_name: string, the name of the bucket you want to connect to
    
    Returns s3_bucket
    """
        
    # now connect to the bucket
    try:
        s3_bucket  = s3_resource.Bucket(bucket_name)
    except:
        print('Issue connecting to s3 bucket...')
        s3_bucket  = None
        
    return s3_bucket
    

def s3_file_exists(s3_bucket, path_to_s3, s3_filename):
    """
    Check whether a file exists in an S3 bucket.

    Returns True if the object exists and False otherwise.
    """

    s3_key = path_to_s3 + s3_filename

    try:
        s3_bucket.Object(s3_key).load()
        file_exists = True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            file_exists = False
        else:
            raise

    return file_exists

# def upload_df_to_s3(df, bucket_name, s3_resource, s3_bucket, path_to_s3, s3_filename, save_schema=False, schema_details=None, compress=False):
#     """
#     Function uploads a DataFrame directly to a specified S3 path as a CSV.
#     Arguments/inputs:
#     df: DataFrame to upload
#     bucket_name: string, name of the bucket you want to upload to
#     s3_resource: initiated s3 resource
#     s3_bucket: from connect_to_s3_bucket(), a boto3.resources.factory.s3.Bucket object
#     path_to_s3: string, separated by single forward slashes like this: folder1/folder2/folder3/, where you want
#     the file to go
#     s3_filename: the name you want for the file, including the file extension for example 'test.csv'
#     compress: defaults to False but if True then it'll save as a csv.gz

#     Example:
#     schema_details = {
#         "ticker_name": "Bloomberg syntax ex MTDR US EQUITY",
#         "data_completeness": "An indicator of how 'filled in' a unique month of data is, from 0% to 100%.",
#         "data_source": "The source of the data (e.g., Enverus Shaleprofile scrapes gas scrapes HITE models etc...)",
#         "date_associated": "The date associated with the data entry.",
#         "monthly_prod_kboeperday": "Monthly average production in thousands of barrels of oil equivalent per day.",
#         "state": "State where the well or asset is located.",
#         "qtr_date": "Quarterly date for data aggregation.",
#         "num_producing_wells": "Total number of producing wells at the given time.",
#     }

#     """
            
#     # check if the folder exists in the bucket
#     # objects = s3_bucket.objects.filter(Prefix=path_to_s3)

#     try:
        
#         # default is not compress
#         if compress==False:
#             # Convert DataFrame to CSV and upload to S3
#             csv_buffer = StringIO()
#             df.to_csv(csv_buffer, index=False)
#             s3_resource.Object(bucket_name, path_to_s3 + s3_filename).put(Body=csv_buffer.getvalue())
#             schema_filename = s3_filename.replace(".csv", "_schema.json")
            
#         else:
#             # Convert DataFrame to CSV string, encode, compress, and upload
#             csv_buffer = StringIO()
#             df.to_csv(csv_buffer, index=False)
#             csv_bytes = csv_buffer.getvalue().encode('utf-8')
#             gz_buffer = BytesIO()
#             with gzip.GzipFile(fileobj=gz_buffer, mode='wb') as gz_file:
#                 gz_file.write(csv_bytes)
#             # Ensure the buffer pointer is at the beginning
#             gz_buffer.seek(0)
#             s3_resource.Object(bucket_name, path_to_s3 + s3_filename).put(Body=gz_buffer.getvalue())    
#             schema_filename = s3_filename.replace(".csv.gz", "_schema.json")

#     except Exception as e:
#         print('Unable to write to s3: ', e)
#     # else:
#     #     print('Path does not exist in the s3 bucket! Check your path_to_s3 and make sure it is correct: '+path_to_s3+s3_filename)

#     if save_schema:
    
#         # NEW: Build schema JSON with dtypes and comments
#         schema_json = {
#             col: {
#                 "dtype": str(df[col].dtype),
#                 "comment": schema_details.get(col, "") if schema_details else ""
#             }
#             for col in df.columns
#         }
#         # Convert the schema to a JSON string and encode it to UTF-8 (no BOM)
#         json_str = json.dumps(schema_json, indent=4)
#         s3_resource.Object(bucket_name, path_to_s3 + schema_filename).put(Body=json_str.encode('utf-8'))
#         # print(f"Schema JSON saved to: s3://{bucket_name}/{path_to_s3}{schema_filename}")

#     return None


def upload_df_to_s3(df, bucket_name, s3_resource, s3_bucket, path_to_s3, s3_filename, save_schema=False, schema_details=None, compress=False):
    """
    New version with assistance from Claude to accomodate .parquet file
    Function uploads a DataFrame directly to a specified S3 path.
    Supports CSV, CSV.GZ, and parquet (detected from s3_filename extension).

    Args:
        df            : DataFrame to upload
        bucket_name   : string, name of the bucket
        s3_resource   : initiated s3 resource
        s3_bucket     : from connect_to_s3_bucket()
        path_to_s3    : string, folder path ending with '/' (e.g. 'folder1/folder2/')
        s3_filename   : filename including extension (e.g. 'data.csv', 'data.csv.gz', 'data.parquet')
        save_schema   : if True, saves a companion _schema.json (CSV only)
        schema_details: dict of column name to comment string
        compress      : if True and file is CSV, saves as csv.gz instead
    """

    objects = s3_bucket.objects.filter(Prefix=path_to_s3)
    if len(list(objects)) == 0:
        print('Path does not exist in the s3 bucket! Check your path_to_s3 and make sure it is correct: ' + path_to_s3 + ' ' + s3_filename)
        return None

    if s3_filename.endswith('.parquet'):
        buf = BytesIO()
        df.to_parquet(buf, index=False, compression='snappy')
        buf.seek(0)
        s3_resource.Object(bucket_name, path_to_s3 + s3_filename).put(Body=buf.getvalue())

    elif compress:
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        gz_buffer = BytesIO()
        with gzip.GzipFile(fileobj=gz_buffer, mode='wb') as gz_file:
            gz_file.write(csv_bytes)
        gz_buffer.seek(0)
        s3_resource.Object(bucket_name, path_to_s3 + s3_filename).put(Body=gz_buffer.getvalue())
        schema_filename = s3_filename.replace('.csv.gz', '_schema.json')

    else:
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        s3_resource.Object(bucket_name, path_to_s3 + s3_filename).put(Body=csv_buffer.getvalue())
        schema_filename = s3_filename.replace('.csv', '_schema.json')

    if save_schema and not s3_filename.endswith('.parquet'):
        schema_json = {
            col: {
                "dtype": str(df[col].dtype),
                "comment": schema_details.get(col, "") if schema_details else ""
            }
            for col in df.columns
        }
        json_str = json.dumps(schema_json, indent=4)
        s3_resource.Object(bucket_name, path_to_s3 + schema_filename).put(Body=json_str.encode('utf-8'))

    return None

def get_schema_details_dict(df, databricks_table_name, s3_resource, s3_bucket, path_to_schema_s3, schema_filename_prefix):
    """
    This column does a few things!! 
    
    Given schema file name and path, and df and associated databricks table name in schema file:
        - Grab latest schema
        - Create a dict of col name & comment
        - Identify columns in schema and compare to columns in df and print warning if missing comments exist
    """
    latest_filename = get_latest_s3_filename(s3_bucket, path_to_s3=path_to_schema_s3, filename_prefix_str=schema_filename_prefix)
    schema_df = read_csv_from_s3(s3_resource, s3_bucket, path_to_schema_s3, s3_filename=latest_filename)
    
    # dictionary 
    schema_details_dict = dict(zip(schema_df[schema_df['table_name']==databricks_table_name]['column_name'],schema_df[schema_df['table_name']==databricks_table_name]['comment']))
    
    schema_col_list         = schema_df[schema_df['table_name']==databricks_table_name]['column_name'].tolist()
    uncommented_col_list    = list(set(df.columns)-set(schema_col_list))
    if len(uncommented_col_list)>0:
        print('Wait - you have columns in all_df that do NOT have comments for Databricks: ', uncommented_col_list)
            
    return schema_details_dict


def save_schema(df, schema_details, schema_filename, s3_resource, bucket_name, path_to_s3):
    """
    Takes a dataframe and saves out every dtype associated with the column along with any matching comments
    from the schema_details (a dict), saves this single JSON file to s3 with the desired schema_filename.
    Ideally schema_filename should match the associated CSV or CSV.GZ filelname as Databricks will look
    for a file and its associated schema which has the same name but just a _schema suffix and a different extension 
    (instead of a csv or csv.gz it'll lookf or a JSON)
     
     For example:
         s3_filename               = f"rig_excep_report_main_as_of_{dt.datetime.now().strftime('%Y%m%d')}.csv"
         schema_fiename            = f"rig_excep_report_main_as_of_{dt.datetime.now().strftime('%Y%m%d')}_schema.json"

                                                                                                 
     Function returns None
     """
    # NEW: Build schema JSON with dtypes and comments
    schema_json = {
        col: {
            "dtype": str(df[col].dtype),
            "comment": schema_details.get(col, "") if schema_details else ""
        }
        for col in df.columns
    }
    # Convert the schema to a JSON string and encode it to UTF-8 (no BOM)
    json_str = json.dumps(schema_json, indent=4)
    s3_resource.Object(bucket_name, path_to_s3 + schema_filename).put(Body=json_str.encode('utf-8'))
    # print(f"Schema JSON saved to: s3://{bucket_name}/{path_to_s3}{schema_filename}")
    
    return None

def get_latest_s3_filename_v0(region_name, bucket_name, path_to_s3, filename_prefix_str):
    """
    Finds the latest S3 filename in the specified path that matches the given filename prefix.
    The timestamp in the filename can include both date and time (e.g., YYYYMMDD or YYYYMMDDHHMMSS).
    
    Args:
        region_name (str): AWS region name.
        bucket_name (str): S3 bucket name.
        path_to_s3 (str): S3 path (prefix) where the files are located.
        filename_prefix_str (str): Prefix of the filename to search for (e.g., 'input_file_tils_as_of_').
    
    Returns:
        str: The latest S3 filename (e.g., 'input_file_tils_as_of_20250225143000.csv').
              Returns None if no matching files are found or if there's an issue.
              
    Returns latest_file as None if fails, otherwise a string! 
    """
    # Initialize
    # Extract timestamps from filenames and find the latest file
    latest_file      = None
    latest_timestamp = None

    # Initialize the S3 client
    s3_client = boto3.client('s3', region_name=region_name)
    
    # Ensure the path_to_s3 ends with a '/'
    if not path_to_s3.endswith('/'):
        path_to_s3 += '/'
    
    # List all files in the S3 directory
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=path_to_s3)
    except Exception as e:
        print(f"Error listing S3 objects: {e}")
        response = None

    # if resopnse... 
    if response:
        # Check if there are any files in the response
        if 'Contents' not in response:
            print("No files found in the specified S3 path.")
        
        # Filter files that contain the filename_prefix_str and end with ".csv" or ".csv.gz"
        # files = [obj['Key'] for obj in response['Contents'] 
        #         if filename_prefix_str in obj['Key'] and obj['Key'].endswith('.csv')]
        files = [obj['Key'] for obj in response['Contents'] 
         if filename_prefix_str in obj['Key'] and (obj['Key'].endswith('.csv') or obj['Key'].endswith('.csv.gz'))]
        
        if not files:
            print("No matching files found with the specified prefix.")
        
        
        for file in files:
            # Extract the filename without the path
            filename = file.split('/')[-1]
            
            # Extract the timestamp part of the filename
            if filename.endswith('.csv.gz'):
                timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv.gz')[0]
            else:
                timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]
        
            # timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]
            
            # Dynamically detect the timestamp format
            timestamp_format = None
            if len(timestamp_str) == 8:  # YYYYMMDD
                timestamp_format = '%Y%m%d'
            elif len(timestamp_str) == 14:  # YYYYMMDDHHMMSS
                timestamp_format = '%Y%m%d%H%M%S'
            else:
                print(f"Skipping file with invalid timestamp format: {filename}")
                continue  # Skip files with invalid timestamp formats
            
            try:
                timestamp = dt.datetime.strptime(timestamp_str, timestamp_format)
                
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_file = file
            except ValueError as e:
                print(f"Skipping file due to invalid timestamp: {filename}. Error: {e}")
                continue  # Skip files with invalid timestamps
    
    # FINALLY
    if latest_file:
        #print(f"Latest CSV file found: {latest_file}")
        latest_file = latest_file.split('/')[-1]  # Return only the filename (not the full path)
    else:
        print("No valid files found with a timestamp in the filename.")

    return latest_file    


def upload_file_to_s3(s3_resource, s3_bucket, bucket_name, path_to_local_file, local_filename, path_to_s3, s3_filename, save_with_todays_date=False):
    """
    
    Function uploads a file to a desired s3 bucket. It first makes sure to check
    that the file path actually exists in the s3 bucket by grabbing all the objects in that path
    and if the length of that list > 0 then we know the path exists, otherwise there is a
    problem and the function prints an error.
    
    Function uses s3_resource.meta.client.upload_file() to do the upload
    
    s3_resource: initiated s3 resource
    s3_bucket: from connect_to_s3_bucket()
    path_to_local_file: string, where the file lives locally (on your machine or directory, etc.)
    path_to_s3: string, separated by single forward slashes like this: folder1/folder2/folder3/, where you want
    the file to go
    s3_filename: the name you want for the file, including the file extension for example 'test.csv'
    
    Returns None
    """
    
    # check if the file path exists in the bucket 
    objects = s3_bucket.objects.filter(Prefix=path_to_s3)
    
    if len(list(objects)) > 0:
        # upload to s3
        try:
            # important! 
            if save_with_todays_date:
                base, extension = local_filename.rsplit('.', 1)
                s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}.{extension}"                
                
            s3_resource.meta.client.upload_file(Filename = path_to_local_file + local_filename,
                                                Bucket = bucket_name,
                                                Key = path_to_s3 + s3_filename)
        except Exception as e:
            print('!!! WARNING !!!! Error uploading to S3: ', e)
            print('For file: ', local_filename)
        
    else:
        print('Path does not exist in the s3 bucket! Check your path_to_s3 and make sure it is correct.')
    
    return None

def download_file_from_s3(s3_resource, s3_bucket, bucket_name, path_to_local_file, local_filename, path_to_s3, s3_filename):
    """
    Function downloads an object from s3 bucket. Similar to the upload_file_to_s3() function, this function
    checks to make sure the path exists in the s3 bucket, otherwise it prints an error
    
    s3_resource: initiated s3 resource
    s3_bucket: from connect_to_s3_bucket()
    path_to_local_file: string, where the file lives locally (on your machine or directory, etc.)
    path_to_s3: string, separated by single forward slashes like this: folder1/folder2/folder3/, where you want
    the file to go
    s3_filename: the name you want for the file, including the file extension for example 'test.csv'
    
    Returns None
    """
    
    # check if the file path exists in the bucket 
    objects = s3_bucket.objects.filter(Prefix=path_to_s3)
    
    if len(list(objects)) > 0:
        # upload to s3
        s3_resource.meta.client.download_file(Bucket = bucket_name, 
                                              Key = path_to_s3 + s3_filename,
                                              Filename = path_to_local_file + local_filename)
        
    else:
        print('Path does not exist in the s3 bucket! Check your path_to_s3 and make sure it is correct.')
    
    return None    

def write_files_in_folder_to_s3(path_to_local_file, local_file_list, path_to_s3, path_to_aws_cred, aws_cred_filename, save_with_todays_date=False):
    """
    Take all the files in a folder on a local drive and write them to a folder on s3
    """
    # s3
    
    for local_filename in local_file_list:
        
        s3_filename = local_filename
        
        try:
            # print(local_filename)
            # check file size
            # COMMENTED THIS OUT ON FEB 26 2025 - in the future we CANNOT overwrite files.
            # file_size_mb = os.path.getsize(path_to_local_file+local_filename)/1e6
            # do not save with individual date stamp if the file is bigger than 10MB, make it a monthly version instead
            # if file_size_mb > 10:
                # print('Larger than 10 MB, just saving for the month...')
            #     base, extension = local_filename.rsplit('.', 1)
            #     if save_with_todays_date:
            #         s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m')}.{extension}"
            # else:
                # otherwise yes create a date-stamp unique version! 
                # s3 filename is loca_filename plus todays date as just yyyy-mm
            if save_with_todays_date:
                base, extension = local_filename.rsplit('.', 1)
                s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}.{extension}"
            # proceed with writing 
            write_local_to_s3(path_to_aws_cred, aws_cred_filename, path_to_local_file, local_filename, path_to_s3, s3_filename)
            
        except Exception as e:
            print('!!! WARNING !!!! Error writing to S3: ', e)
            print('For file: ', local_filename)

    return None


def write_files_to_s3_compressed(local_file_path, local_file_list, s3_resource, bucket_name, s3_path):
    """
    Uploads a list of local CSV files to S3 as compressed gzip files.

    file_list: list of strings, full paths to the local CSV files to be uploaded
    s3_resource: boto3 resource object
    bucket_name: str, target S3 bucket name
    s3_path: str, S3 path to upload files (e.g., 'folder/subfolder/')
    """
    for file_name in local_file_list:
        # Extract filename from path
        s3_filename = f"{s3_path}{file_name}.gz"  # Add .gz extension for S3

        # Compress and upload file
        try:
            buffer = BytesIO()
            with open(local_file_path+file_name, 'rb') as f:
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                    gz_file.write(f.read())  # Read and compress raw file bytes
            buffer.seek(0)  # Reset buffer pointer

            # Upload compressed file to S3
            s3_resource.meta.client.upload_fileobj(
                Fileobj=buffer,
                Bucket=bucket_name,
                Key=s3_filename
            )
            print(f"Uploaded: {file_name} as {s3_filename}")
        except Exception as e:
            print(f"Error uploading {local_file_path}: {e}")

    return None


def write_file_to_s3_compressed(local_file_path, local_file_name, desired_file_name, s3_resource, bucket_name, s3_path):
    """
    Uploads a list of local CSV files to S3 as compressed gzip files.

    file_list: list of strings, full paths to the local CSV files to be uploaded
    s3_resource: boto3 resource object
    bucket_name: str, target S3 bucket name
    s3_path: str, S3 path to upload files (e.g., 'folder/subfolder/')
    """
    # Extract filename from path
    s3_filename = f"{s3_path}{desired_file_name}.gz"  # Add .gz extension for S3

    # Compress and upload file
    try:
        buffer = BytesIO()
        with open(local_file_path+local_file_name, 'rb') as f:
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                gz_file.write(f.read())  # Read and compress raw file bytes
        buffer.seek(0)  # Reset buffer pointer

        # Upload compressed file to S3
        s3_resource.meta.client.upload_fileobj(
            Fileobj=buffer,
            Bucket=bucket_name,
            Key=s3_filename
        )
        print(f"Uploaded: {desired_file_name} as {s3_filename}")
    except Exception as e:
        print(f"Error uploading {local_file_path}: {e}")

    return None


def write_local_to_s3(path_to_aws_cred, credentials_filename, path_to_local_file, local_filename, path_to_s3, s3_filename, save_with_todays_date=False):
    """   
    Take AWS credentials and load bucket name, region name and pass all that to s3_connect module along with the
    local file info (where it is saved, what its name is) and desired s3 info (where to save it on s3, what its name should be)
    
    Function does this and does not return anything. Returns None
    """
    bucket_name, region_name = load_s3_params()

    # connect
    s3_resource = connect_to_s3(path_to_aws_cred, credentials_filename, region_name)
    s3_bucket   = connect_to_s3_bucket(s3_resource, bucket_name)
    upload_file_to_s3(s3_resource, s3_bucket, bucket_name, path_to_local_file, local_filename, path_to_s3, s3_filename, save_with_todays_date)
    # print('Written to s3.')
    # check if it is there?
    # return success or fail flag?
    
    return None

def upload_df_to_s3_compressed(s3_resource, bucket_name, dataframe, path_to_s3, s3_filename, save_with_todays_date=False):
    """
    UUpload a df from memory to s3 as a compressed file
    Uploads a compressed DataFrame to a desired S3 bucket.

    s3_resource: initiated S3 resource
    s3_bucket: from connect_to_s3_bucket()
    bucket_name: string, S3 bucket name
    dataframe: pandas DataFrame to upload
    path_to_s3: string, S3 folder path (e.g., "folder1/folder2/")
    s3_filename: string, desired filename in S3 (e.g., "data.csv.gz")

    Returns None
    """
    # Create a buffer for the compressed file
    buffer = BytesIO()

    # Compress DataFrame content as bytes
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
        gz_file.write(dataframe.to_csv(index=False).encode('utf-8'))  # Encode to bytes
    buffer.seek(0)  # Reset buffer pointer to the beginning

    # Upload compressed buffer to S3
    try:

        if save_with_todays_date:
            base        = s3_filename.split('.csv.gz')[0]
            extension   = '.csv.gz'
            s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}{extension}"
        
        s3_resource.meta.client.upload_fileobj(
            Fileobj=buffer,
            Bucket=bucket_name,
            Key=f"{path_to_s3}{s3_filename}"
        )
        # print(f"File successfully uploaded to S3 as {s3_filename}")
    except Exception as e:
        print('!!! WARNING !!!! Error uploading to S3: ', e)

    return None

def back_up_code_from_dash_server_to_s3(s3_resource, s3_bucket, bucket_name, path_to_s3):
    """
    Writes code files from Dash app to s3 folder, with each file getting the date stamp added like
    file_name_as_of_yyyymmdd.py. Hard tocded to back up code files in main app, pages folder, and utils folder.
    Assumes that there is a pages and utils folder in your app.

    Returns nothing.
    """
    main_code_list           = [f for f in os.listdir() if '.py' in f] 
    pages_code_list          = [f for f in os.listdir('pages') if '.py' in f] 
    utils_code_list          = [f for f in os.listdir('') if '.py' in f]
    
    
    for code_file in main_code_list:
        base, extension = code_file.rsplit('.', 1)
        s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}.{extension}"
        upload_file_to_s3(s3_resource, s3_bucket, bucket_name, '', code_file, path_to_s3, s3_filename)
    
    for code_file in pages_code_list:
        base, extension = code_file.rsplit('.', 1)
        s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}.{extension}"
        upload_file_to_s3(s3_resource, s3_bucket, bucket_name, 'pages/', code_file, path_to_s3+'pages/', s3_filename)
    
    for code_file in utils_code_list:
        base, extension = code_file.rsplit('.', 1)
        s3_filename = f"{base}_as_of_{dt.datetime.now().strftime('%Y%m%d')}.{extension}"
        upload_file_to_s3(s3_resource, s3_bucket, bucket_name, '/', code_file, path_to_s3 + 'utils/', s3_filename)
    
    print('Done backing up code to s3!')

    return None    

#
# def read_csv_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename):
#     """
#     Read file from s3, do not download it anywhere, just read it in as a pandas dataframe
#     12/30/24 added errors='replace' to enable still reading the CSV even if there are weird charcters in a text column
#     that are causing read issues.
#     """
#     df  = pd.DataFrame()
#     obj = None
#
#     try:
#         obj                = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
#         csv_content        = obj['Body'].read().decode('utf-8', errors='replace')
#         df                 = pd.read_csv(StringIO(csv_content))
#         last_modified_date = obj['LastModified']
#     except Exception as e:
#         print('Error reading in dataframe from s3 bucket, returning empty df!')
#         print('Error: ', e)
#         df = pd.DataFrame()
#     else:
#         print('Pulling file from s3, last modified: '+last_modified_date.strftime("%Y-%m-%d"))
#
#     return df

# def read_csv_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename):
#     """
#     Read file from s3, do not download it anywhere, just read it in as a pandas dataframe.
#     Supports both regular CSV and gzip-compressed CSV (.csv.gz).
#     12/30/24 added errors='replace' to enable still reading the CSV even if there are weird characters
#     in a text column that are causing read issues.
#     """
#     df = pd.DataFrame()
#     obj = None

#     try:
#         # Get the object from S3
#         obj = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
#         file_stream = obj['Body'].read()

#         # Check if the file is gzip-compressed
#         if s3_filename.endswith('.gz'):
#             with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
#                 df = pd.read_csv(gz_file, low_memory=False)
#         else:
#             csv_content = file_stream.decode('utf-8', errors='replace')
#             df = pd.read_csv(StringIO(csv_content), low_memory=False)

#         # Get last modified date
#         last_modified_date = obj['LastModified']
#     except Exception as e:
#         print('Error reading in dataframe from s3 bucket, returning empty df!')
#         print('Error: ', e)
#         df = pd.DataFrame()
#     else:
#         print('Pulling file from s3, last modified: ' + last_modified_date.strftime("%Y-%m-%d"))

#     return df

# def read_csv_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename, parse_dates=None, dtype=None, nrows=None):
#     """
#     Updated version Thurs 5/8 adding ability to set dtypes!
#     Read file from s3, do not download it anywhere, just read it in as a pandas dataframe.
#     Supports both regular CSV and gzip-compressed CSV (.csv.gz).
#     12/30/24 added errors='replace' to enable still reading the CSV even if there are weird characters
#     in a text column that are causing read issues.
#     """
#     df = pd.DataFrame()
#     obj = None

#     try:
#         # print('hi!')
#         # Get the object from S3
#         obj = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
#         file_stream = obj['Body'].read()

#         # Check if the file is gzip-compressed
#         if s3_filename.endswith('.gz'):
#             with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
#                 df = pd.read_csv(gz_file, low_memory=False,  parse_dates=parse_dates, dtype=dtype, nrows=nrows)
#         else:
#             csv_content = file_stream.decode('utf-8', errors='replace')
#             df = pd.read_csv(StringIO(csv_content), low_memory=False, parse_dates=parse_dates, dtype=dtype, nrows=nrows)
#             # print('dtypes: ',  df.dtypes)

#         # Get last modified date
#         last_modified_date = obj['LastModified']
#     except Exception as e:
#         print('Error reading in dataframe from s3 bucket, returning empty df!')
#         print('Error: ', e)
#         df = pd.DataFrame()
#     else:
#         print('Pulling file from s3, last modified: ' + last_modified_date.strftime("%Y-%m-%d"))

#     return df

# def read_csv_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename, parse_dates=None, dtype=None):
#     """
#     Updated version Thurs 5/8 adding ability to set dtypes!
#     Read file from s3, do not download it anywhere, just read it in as a pandas dataframe.
#     Supports both regular CSV and gzip-compressed CSV (.csv.gz).
#     12/30/24 added errors='replace' to enable still reading the CSV even if there are weird characters
#     in a text column that are causing read issues.
#     """
#     df = pd.DataFrame()
#     obj = None

#     try:
#         # print('hi!')
#         # Get the object from S3
#         obj = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
#         file_stream = obj['Body'].read()
#         #
#         # # Check if the file is gzip-compressed
#         # if s3_filename.endswith('.gz'):
#         #     with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
#         #         df = pd.read_csv(gz_file, low_memory=False,  parse_dates=parse_dates, dtype=dtype)
#         # else:
#         #     csv_content = file_stream.decode('utf-8', errors='replace')
#         #     df = pd.read_csv(StringIO(csv_content), low_memory=False, parse_dates=parse_dates, dtype=dtype)
#         #     # print('dtypes: ',  df.dtypes)
#         if s3_filename.endswith('.csv.gz'):
#             with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
#                 df = pd.read_csv(gz_file, low_memory=False, parse_dates=parse_dates, dtype=dtype)
#         # Added by MAysa on  Tues 7/15/25  to accomodate putting parquet files on s3
#         elif s3_filename.endswith('.parquet'):
#             df = pd.read_parquet(BytesIO(file_stream))
#         else:
#             csv_content = file_stream.decode('utf-8', errors='replace')
#             df = pd.read_csv(StringIO(csv_content), low_memory=False, parse_dates=parse_dates, dtype=dtype)

#         # Get last modified date
#         last_modified_date = obj['LastModified']
#     except Exception as e:
#         print('Error reading in dataframe from s3 bucket, returning empty df!')
#         print('Error: ', e)
#         df = pd.DataFrame()
#     else:
#         print('Pulling file from s3, last modified: ' + last_modified_date.strftime("%Y-%m-%d"))

#     return df


def read_csv_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename, parse_dates=None, dtype=None, print_modified_bool=False):
    """
    Updated Aug 2026 to add print_modified_bool
    Updated version Thurs 5/8 adding ability to set dtypes!
    Read file from s3, do not download it anywhere, just read it in as a pandas dataframe.
    Supports both regular CSV and gzip-compressed CSV (.csv.gz).
    12/30/24 added errors='replace' to enable still reading the CSV even if there are weird characters
    in a text column that are causing read issues.
    """
    df = pd.DataFrame()
    obj = None

    try:
        # print('hi!')
        # Get the object from S3
        obj = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
        file_stream = obj['Body'].read()
        #
        # # Check if the file is gzip-compressed
        # if s3_filename.endswith('.gz'):
        #     with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
        #         df = pd.read_csv(gz_file, low_memory=False,  parse_dates=parse_dates, dtype=dtype)
        # else:
        #     csv_content = file_stream.decode('utf-8', errors='replace')
        #     df = pd.read_csv(StringIO(csv_content), low_memory=False, parse_dates=parse_dates, dtype=dtype)
        #     # print('dtypes: ',  df.dtypes)
        if s3_filename.endswith('.csv.gz'):
            with gzip.GzipFile(fileobj=BytesIO(file_stream)) as gz_file:
                df = pd.read_csv(gz_file, low_memory=False, parse_dates=parse_dates, dtype=dtype)
        # Added by MAysa on  Tues 7/15/25  to accomodate putting parquet files on s3
        elif s3_filename.endswith('.parquet'):
            df = pd.read_parquet(BytesIO(file_stream))
        else:
            csv_content = file_stream.decode('utf-8', errors='replace')
            df = pd.read_csv(StringIO(csv_content), low_memory=False, parse_dates=parse_dates, dtype=dtype)

        # Get last modified date
        last_modified_date = obj['LastModified']
    except Exception as e:
        print('Error reading in dataframe from s3 bucket, returning empty df!')
        print('Error: ', e)
        df = pd.DataFrame()
    else:
        if print_modified_bool:
            print(f'Pulling {s3_filename} from s3, last modified: ' + last_modified_date.strftime("%Y-%m-%d"))

    return df


def read_text_file_from_s3(s3_resource, s3_bucket, path_to_s3, s3_filename):
    """
    Read text file from s3, do not download it anywhere, just read it in as text
    If there is an exception raised when trying to read from s3, that is handled by the app by going
    to the cache backup folder (see app.py)
    """
    try:
        obj = s3_resource.Object(s3_bucket.name, path_to_s3 + s3_filename).get()
        result = obj['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error reading text file from S3: {str(e)}")
        result = ""  # Return empty string on error (matches your CSV function behavior)

    return result
    




def create_new_folder(s3_bucket, path_to_s3, folder_name):
    """
    Creating a folder on an s3 bucket is similar to putting any other object in an s3
    bucket.
    
    path_to_s3: where to put the folder, should end with a forward slash
    folder_name: the name of the folder
    
    Returns None
    """
    path_to_submit = path_to_s3 + folder_name + '/'
    s3_bucket.put_object(Key=(path_to_submit))

    return None



# def get_latest_s3_filename(s3_bucket, path_to_s3, filename_prefix_str):
#     """
#     Updated 2/27/25 to be able to useu s3_bucket instead of s3 client
    
#     Finds the latest S3 filename in the specified path that matches the given filename prefix.
#     The timestamp in the filename can include both date and time (e.g., YYYYMMDD or YYYYMMDDHHMMSS).
    
#     Args:
#         region_name (str): AWS region name.
#         bucket_name (str): S3 bucket name.
#         path_to_s3 (str): S3 path (prefix) where the files are located.
#         filename_prefix_str (str): Prefix of the filename to search for (e.g., 'input_file_tils_as_of_').
    
#     Returns:
#         str: The latest S3 filename (e.g., 'input_file_tils_as_of_20250225143000.csv').
#               Returns None if no matching files are found or if there's an issue.
              
#     Returns latest_file as None if fails, otherwise a string! 
#     """
#     # Initialize
#     # Extract timestamps from filenames and find the latest file
#     latest_file      = None
#     latest_timestamp = None
    
#     # Ensure the path_to_s3 ends with a '/'
#     if not path_to_s3.endswith('/'):
#         path_to_s3 += '/'
    
#     # List all files in the S3 directory
#     try:
#         files = [obj.key for obj in s3_bucket.objects.filter(Prefix=path_to_s3)]
#     except Exception as e:
#         print(f"Error listing S3 objects: {e}")
#         files = None

#     # if resopnse... 
#     if files:        

#         # Filter files that contain the filename_prefix_str and end with ".csv" or ".csv.gz"
#         files = [f for f in files 
#                 if filename_prefix_str in f and (f.endswith('.csv') or f.endswith('.csv.gz'))]

#         if not files:
#             print("No matching files found with the specified prefix.")
                
#         for file in files:
#             # Extract the filename without the path
#             filename = file.split('/')[-1]
            
#             # Extract the timestamp part of the filename
#             if filename.endswith('.csv.gz'):
#                 timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv.gz')[0]
#             else:
#                 timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]
        
#             # timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]
#             # Dynamically detect the timestamp format
#             timestamp_format = None
#             if len(timestamp_str) == 8 and timestamp_str.isdigit():  # YYYYMMDD
#                 timestamp_format = '%Y%m%d'
#             elif len(timestamp_str) == 14 and timestamp_str.isdigit():  # YYYYMMDDHHMMSS
#                 timestamp_format = '%Y%m%d%H%M%S'
#             elif len(timestamp_str) == 10 and '-' in timestamp_str:  # YYYY-MM-DD
#                 timestamp_format = '%Y-%m-%d'
#             else:
#                 print(f"Skipping file with invalid timestamp format: {filename}")
#                 continue  # Skip files with invalid timestamp formats
            
#             try:
#                 timestamp = dt.datetime.strptime(timestamp_str, timestamp_format)
                
#                 if latest_timestamp is None or timestamp > latest_timestamp:
#                     latest_timestamp = timestamp
#                     latest_file = file
#             except ValueError as e:
#                 print(f"Skipping file due to invalid timestamp: {filename}. Error: {e}")
#                 continue  # Skip files with invalid timestamps

#     else:
#         print("No files found in the specified S3 path.")

#     # FINALLY
#     if latest_file:
#         # print(f"Latest CSV file found: {latest_file}")
#         latest_file = latest_file.split('/')[-1]  # Return only the filename (not the full path)
#     else:
#         print("No valid files found with a timestamp in the filename.")

#     return latest_file    

def get_latest_s3_filename(s3_bucket, path_to_s3, filename_prefix_str):
    """
    Updated 2/27/25 to be able to useu s3_bucket instead of s3 client
    
    Finds the latest S3 filename in the specified path that matches the given filename prefix.
    The timestamp in the filename can include both date and time (e.g., YYYYMMDD or YYYYMMDDHHMMSS).
    
    Args:
        region_name (str): AWS region name.
        bucket_name (str): S3 bucket name.
        path_to_s3 (str): S3 path (prefix) where the files are located.
        filename_prefix_str (str): Prefix of the filename to search for (e.g., 'input_file_tils_as_of_').
    
    Returns:
        str: The latest S3 filename (e.g., 'input_file_tils_as_of_20250225143000.csv').
              Returns None if no matching files are found or if there's an issue.
              
    Returns latest_file as None if fails, otherwise a string! 
    """
    # Initialize
    # Extract timestamps from filenames and find the latest file
    latest_file      = None
    latest_timestamp = None
    
    # Ensure the path_to_s3 ends with a '/'
    if not path_to_s3.endswith('/'):
        path_to_s3 += '/'
    
    # List all files in the S3 directory
    try:
        files = [obj.key for obj in s3_bucket.objects.filter(Prefix=path_to_s3)]
    except Exception as e:
        print(f"Error listing S3 objects: {e}")
        files = None

    # if resopnse... 
    if files:        

        # Filter files that contain the filename_prefix_str and end with ".csv" or ".csv.gz"
        files = [f for f in files 
                if filename_prefix_str in f and (f.endswith('.csv') or f.endswith('.csv.gz') or f.endswith('.txt'))]

        if not files:
            print("No matching files found with the specified prefix.")
                
        for file in files:
            # Extract the filename without the path
            filename = file.split('/')[-1]
            
            # Extract the timestamp part of the filename
            if filename.endswith('.csv.gz'):
                timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv.gz')[0]
            elif filename.endswith('.txt'):
                timestamp_str = filename.split(filename_prefix_str)[-1].split('.txt')[0]
            else:
                timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]

            # clear out any underscores
            timestamp_str = timestamp_str.replace('_','')
        
            # timestamp_str = filename.split(filename_prefix_str)[-1].split('.csv')[0]
            # Dynamically detect the timestamp format
            timestamp_format = None
            if len(timestamp_str) == 8 and timestamp_str.isdigit():  # YYYYMMDD
                timestamp_format = '%Y%m%d'
            elif len(timestamp_str) == 14 and timestamp_str.isdigit():  # YYYYMMDDHHMMSS
                timestamp_format = '%Y%m%d%H%M%S'
            elif len(timestamp_str) == 10 and '-' in timestamp_str:  # YYYY-MM-DD
                timestamp_format = '%Y-%m-%d'
            else:
                print(f"Skipping file with invalid timestamp format: {filename}")
                continue  # Skip files with invalid timestamp formats
            
            try:
                timestamp = dt.datetime.strptime(timestamp_str, timestamp_format)
                
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_file = file
            except ValueError as e:
                print(f"Skipping file due to invalid timestamp: {filename}. Error: {e}")
                continue  # Skip files with invalid timestamps

    else:
        print("No files found in the specified S3 path.")

    # FINALLY
    if latest_file:
        # print(f"Latest CSV file found: {latest_file}")
        latest_file = latest_file.split('/')[-1]  # Return only the filename (not the full path)
    else:
        print("No valid files found with a timestamp in the filename.")

    return latest_file    


