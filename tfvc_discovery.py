import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import getpass
import time
import logging
from requests.exceptions import ConnectTimeout, HTTPError, RequestException
from utils.common import get_project_names, add_if_not_exists

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def make_request_with_retries(url, auth, max_retries=3, timeout=30):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting request to {url} (Attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, auth=auth, timeout=timeout)
            response.raise_for_status()
            logging.info("Request successful.")
            return response
        except ConnectTimeout:
            logging.warning(f"Attempt {attempt + 1} timed out. Retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
        except HTTPError as e:
            logging.error(f"HTTP error: {e}")
            break
        except RequestException as e:
            logging.error(f"General error: {e}")
            break
    logging.error(f"Failed to connect after {max_retries} attempts.")
    return None  # All attempts failed

def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]  # Excel sheet names can have a maximum of 31 characters

def get_pat_for_server(server_url, df):
    logging.info(f"Retrieving PAT for server URL: {server_url}")
    try:
        return df.loc[df['Server URL'] == server_url, 'PAT'].values[0]
    except IndexError:
        logging.warning(f"No PAT found for server URL: {server_url}")
        return None

def extract_organization_name(server_url):
    try:
        return server_url.split('/')[2]  # Assumes organization name is the third element in the URL
    except IndexError:
        logging.warning(f"Unable to extract organization name from URL: {server_url}")
        return "Unknown Organization"

def get_shelvesets_details(server_url, pat):
    url = f"{server_url}/_apis/tfvc/shelvesets?api-version=6.0"
    response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
    if response and response.status_code == 200:
        logging.info("Shelvesets details retrieved successfully.")
        return response.json().get('value', [])
    else:
        logging.error(f"Failed to retrieve shelvesets: {response.status_code} - {response.text if response else 'No response'}")
        return []

def get_changeset_details(server_url, project_name, changeset_id, pat):
    url = f"{server_url}/{project_name}/_apis/tfvc/changesets/{changeset_id}?api-version=6.0"
    response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
    if response and response.status_code == 200:
        logging.info(f"Changeset details retrieved for ID {changeset_id}")
        return response.json()
    else:
        logging.error(f"Failed to retrieve changeset {changeset_id} details.")
        return None

def get_changeset_changes(server_url, changeset_id, pat):
    url = f"{server_url}/_apis/tfvc/changesets/{changeset_id}/changes?api-version=6.0"
    response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
    if response and response.status_code == 200:
        logging.info(f"Changeset changes retrieved for ID {changeset_id}")
        return response.json()
    else:
        logging.error(f"Failed to retrieve changes for changeset {changeset_id}.")
        return None

def determine_file_type(item):
    if 'isFolder' in item:
        return 'Folder' if item['isFolder'] else 'File'
    if 'size' in item and item['size'] == 0:
        return 'Folder'
    return 'File'

def get_tfvc_branch_file_count(devops_server_url, project_name, branch_path, pat, exclude_paths=[]):
    items_api_url = f'{devops_server_url}/{project_name}/_apis/tfvc/items?scopePath={branch_path}&recursionLevel=full&api-version=6.0'
    items_response = make_request_with_retries(items_api_url, auth=HTTPBasicAuth('', pat))
    if items_response and items_response.status_code == 200:
        items = items_response.json().get('value', [])
        if exclude_paths:
            items = [item for item in items if not any(item['path'].startswith(excluded_path) for excluded_path in exclude_paths)]
        file_count = len([item for item in items if determine_file_type(item) in ['File', 'Folder']])
        logging.info(f"File count for branch '{branch_path}' is {file_count}")
        return file_count
    else:
        logging.error(f"Failed to retrieve items for branch '{branch_path}'.")
        return 0

def get_branch_file_details(devops_server_url, project_name, branch_path, pat, excluded_paths=[]):
    items_api_url = f'{devops_server_url}/{project_name}/_apis/tfvc/items?scopePath={branch_path}&recursionLevel=full&api-version=6.0'
    items_response = make_request_with_retries(items_api_url, auth=HTTPBasicAuth('', pat))
    if items_response and items_response.status_code == 200:
        items = items_response.json().get('value', [])
        filtered_items = [item for item in items if not any(item['path'].startswith(excluded_path) for excluded_path in excluded_paths)]
        logging.info(f"Retrieved {len(filtered_items)} items for branch '{branch_path}'")
        return filtered_items
    else:
        logging.error(f"Failed to retrieve items for branch '{branch_path}'.")
        return []

def get_latest_changeset_for_item(server_url, project_name, item_path, pat):
    changesets_url = f"{server_url}/{project_name}/_apis/tfvc/changesets?itemPath={item_path}&api-version=6.0"
    response = make_request_with_retries(changesets_url, auth=HTTPBasicAuth('', pat))
    if response and response.status_code == 200:
        changesets = response.json().get('value', [])
        if changesets:
            latest_changeset = changesets[0]
            logging.info(f"Latest changeset for '{item_path}' is {latest_changeset['changesetId']}")
            return latest_changeset['changesetId'], latest_changeset.get('comment', 'No comment'), \
                   latest_changeset['createdDate'], latest_changeset['author']['displayName']
    logging.warning(f"No changeset found for item '{item_path}'")
    return None, 'No comment', 'N/A', 'N/A'

def generate_excel_report(output_dir, server_url, pat, project, start_time):
    logging.info(f"Generating Excel report for project '{project}' at '{server_url}'")
    try:
        # [Omitted for brevity: Report generation logic with detailed logging]
        logging.info(f"Report generated and saved to {output_dir}")
    except Exception as e:
        logging.error(f"An error occurred while generating the report: {e}")

def main():
    input_file = 'tfvc_discovery_input_form.xlsx'
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    output_directory = os.path.join("TFVC", run_id)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        return
    except Exception as e:
        logging.error(f"An error occurred while reading the input file: {e}")
        return

    df['Server URL'] = df['Server URL'].str.strip().fillna('')
    df['Project Name'] = df['Project Name'].str.strip().fillna('')
    df['PAT'] = df['PAT'].str.strip().fillna('')

    input_data = {}
    for index, row in df.iterrows():
        if pd.isna(row['Server URL']) or pd.isna(row['PAT']):
            logging.warning(f"Skipping row {index + 1} due to missing data.")
            continue
        surl = row['Server URL']
        proj_name = row['Project Name']
        ptoken = row['PAT']
        proj_names = []
        if not proj_name:
            proj_names = get_project_names(devops_server_url=surl, pat=ptoken)
        if surl not in input_data:
            input_data[surl] = {"pat": ptoken, "projects": [proj_name] if proj_name else proj_names}
        else:
            add_if_not_exists(input_data[surl]["projects"], [proj_name] if proj_name else proj_names)

    for server_url, data in input_data.items():
        pat = data["pat"]
        projects = data["projects"]
        for project in projects:
            start_time = datetime.now()
            logging.info(f"Processing project {project} on server {server_url}")
            try:
                generate_excel_report(output_directory, server_url, pat, project, start_time)
            except Exception as e:
                logging.error(f"Failed to process project {project} on server {server_url}: {e}")

if __name__ == "__main__":
    main()
