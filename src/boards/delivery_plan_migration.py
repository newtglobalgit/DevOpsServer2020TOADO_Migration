import os
import re
import sys
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import getpass
import time
import logging
# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.boards.source_delivery_plan_db import db_post_delivery_plan , db_get_delivery_plan
from src.dbDetails.migration_details_db import db_get_migration_details


id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f'src\logs\logs_delivery_plan_migration_{id}'

# Clear the log file before starting a new run
with open(log_file, 'w'):
    pass

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_print(msg):
    logging.info(msg)
    print(msg)


def modify_item_path(url):
    try:
        # Dictionary of replacements
        replacements = {
            '+': '%2B', '%24': '$', '&': '%26', ',': '%2C', ':': '%3A',
            ';': '%3B', '=': '%3D', '?': '%3F', '@': '%40', ' ': '%20',
            '"': '%22', '<': '%3C', '>': '%3E', '#': '%23', '{': '%7B',
            '}': '%7D', '|': '%7C', '\\': '%5C', '^': '%5E', '[': '%5B',
            ']': '%5D', '`': '%60'
        }

        pattern = r"itemPath=(.+?)&api-version"
        match = re.search(pattern, url)
        
        if match:
            item_path = match.group(1)
            logging.info(f"Original item path: {item_path}")
            for char, replacement in replacements.items():
                item_path = item_path.replace(char, replacement)
            
            modified_url = url.replace(match.group(1), item_path)
            logging.info(f"Modified item path: {item_path}")
            return modified_url
        
        return url
    except Exception as e:
        logging.error(f"Failed to modify item path: {e}")
        return url


def make_request_with_retries(url, auth, max_retries=10, timeout=300):
    url = modify_item_path(url)
    print(url)
    logging.info(f"Making request to URL: {url}")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, auth=auth, timeout=timeout)
            if response.status_code == 200:
                logging.info(f"Request successful with status code: {response.status_code}")
                return response
            else:
                logging.warning(f"Attempt {attempt + 1}: Request timed out. Retrying...")
                time.sleep(2 ** attempt)
        except Exception as e:
            logging.error(f"Error during request: {e}")
            break
    logging.error(f"Failed to connect after {max_retries} attempts.")
    return None


def make_post_request(url, payload, auth):
    url = modify_item_path(url)
    print(url)
    logging.info(f"Making request to URL: {url}")
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url,headers=headers, json=payload, auth=auth)
        if response.status_code == 200:
            logging.info(f"Request successful with status code: {response.status_code}")
            logging.info(f"Delivery plan created successfully.")
            return response
    except Exception as e:
        logging.error(f"Error during request: {e}")

def make_put_request(url, payload, auth):
    url = modify_item_path(url)
    print(url)
    payload["revision"] = payload["revision"]+10000
    logging.info(f"Making request to URL: {url}")
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.put(url,headers=headers, json=payload, auth=auth)
        if response.status_code == 201:
            logging.info(f"Request successful with status code: {response.status_code}")
            logging.info(f"Delivery plan created successfully.")
            return response
    except Exception as e:
        logging.error(f"Error during request: {e}")

def main():

    try:
        results = db_get_migration_details()
    # Iterate over each row in the DataFrame
        for result in results:
            start_time = datetime.now()
            sourceUrl =  result.source_server_url
            sourceProjectName = result.source_project_name
            sourcePatToken = result.source_pat
            targetUrl = result.target_organization_url
            targetProjectName = result.target_project_name
            targetPatToken = result.target_pat
            get_delivery_plans_ids = f"{sourceUrl}/{sourceProjectName}/_apis/work/plans?api-version=6.0"

            delivery_plans_response = make_request_with_retries(get_delivery_plans_ids, auth=HTTPBasicAuth('', sourcePatToken))

            all_delivery_plans = delivery_plans_response.json()['value']

            for delivery_plans in all_delivery_plans:
                get_delivery_plans_details = f"{sourceUrl}/{sourceProjectName}/_apis/work/plans/{delivery_plans.get('id')}?api-version=6.0"

                delivery_plan_details_response = make_request_with_retries(get_delivery_plans_details, auth=HTTPBasicAuth('', sourcePatToken))

                create_delivery_plans = f"{targetUrl}/{targetProjectName}/_apis/work/plans/{delivery_plans.get('id')}?api-version=6.0"

                make_post_request(create_delivery_plans, delivery_plan_details_response.json(), auth=HTTPBasicAuth('', targetPatToken))

    except Exception as e:
        logging.error(f"Error occurred while processing input data from db': {e}")
        return



if __name__ == "__main__":
    main()

