import os
import requests
import sys
from requests.auth import HTTPBasicAuth
import pandas as pd
import re
import html
import logging
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.boards.source_workitem_db import db_post_workitem
from src.dbDetails.db import get_db

log_dir = "workitem_logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(log_dir, f'workitem_discovery_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'))
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]

def extract_name(url):
    return url.split("/")[-1] 

def clean_html(raw_html):
    raw_html = html.unescape(raw_html)
    clean_text = re.sub(r'<a [^>]*>(.*?)</a>', r'\1', raw_html)
    clean_text = re.sub('<[^<]+?>', '', clean_text)
    return clean_text

def make_api_request(url, pat, method='GET', data=None, timeout=300):
    auth = HTTPBasicAuth('', pat)
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        if method == 'GET':
            response = session.get(url, auth=auth, timeout=timeout)
        elif method == 'POST':
            response = session.post(url, json=data, auth=auth, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out after {timeout} seconds for URL: {url}. Retrying if possible.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed API request to {url}: {e}')
        return None

def authenticate_and_get_projects(base_url, pat, api_version):
    projects_url = f'{base_url}/_apis/projects?api-version={api_version}'
    return make_api_request(projects_url, pat)

def get_work_items_query(base_url, project, pat, api_version, batch_size=50):
    query_url = f'{base_url}/{project}/_apis/wit/wiql?api-version={api_version}'
    query = {"query": "Select [System.Id] From WorkItems Where [System.TeamProject] = @project"}
    all_work_item_ids = []
    response = make_api_request(query_url, pat, method='POST', data=query)
    continuation_token = response.get('x-ms-continuationtoken', None)
    while response:
        work_items = response.get('workItems', [])
        all_work_item_ids.extend([item['id'] for item in work_items])
        if continuation_token:
            query_url = f'{base_url}/{project}/_apis/wit/wiql?continuationToken={continuation_token}&api-version={api_version}'
            response = make_api_request(query_url, pat)
            continuation_token = response.get('x-ms-continuationtoken', None)
        else:
            break
    logger.info(f"Total work item IDs retrieved: {len(all_work_item_ids)}")
    return all_work_item_ids

def get_work_item_details(base_url, project, work_item_ids, pat, api_version):
    all_work_item_details = []
    batch_size = 150
    for i in range(0, len(work_item_ids), batch_size):
        batch_ids = work_item_ids[i:i + batch_size]
        work_item_url = f'{base_url}/{project}/_apis/wit/workitems?ids={",".join(map(str, batch_ids))}&$expand=relations&api-version={api_version}'
        logger.info(f"Fetching work item details for batch from URL: {work_item_url}")
        response = make_api_request(work_item_url, pat)
        if response and 'value' in response:
            all_work_item_details.extend(response['value'])
        else:
            logger.warning(f"No data returned for work item batch starting at index {i}")
    return all_work_item_details

def get_work_item_comments(base_url, project, work_item_id, pat, api_version):
    comments_url = f'{base_url}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version={api_version}'
    logger.info(f"Fetching comments from URL: {comments_url}")
    response = make_api_request(comments_url, pat)    
    logger.info(f"Response received: {response}")    
    if isinstance(response, dict) and 'comments' in response:
        return response
    else:
        logger.warning(f"No 'comments' found for work item {work_item_id}. Returning empty list.")
        return {'comments': []}

def extract_work_item_info(collection_name, project_name, work_item, comments):
    fields = work_item['fields']
    state = fields.get('System.State', 'N/A')
    links = work_item.get('relations', [])
    links_count = len(links) if links else 0
    comments_text = 'No comments'
    if comments and 'comments' in comments:
        sorted_comments = sorted(comments['comments'], key=lambda x: x['createdDate'], reverse=True)
        comments_text = clean_html(sorted_comments[0]['text']) if sorted_comments else 'No comments'
    created_by_info = fields.get('System.CreatedBy', 'N/A')
    created_by = created_by_info['displayName'] if isinstance(created_by_info, dict) else created_by_info
    assignee_info = fields.get('System.AssignedTo', 'N/A')
    assignee = assignee_info['displayName'] if isinstance(assignee_info, dict) else assignee_info
    description_html = fields.get('System.Description', 'N/A')
    description_text = clean_html(description_html) if description_html != 'N/A' else 'N/A'
    tags = fields.get('System.Tags', 'N/A')

    return {
        'collection_name': collection_name,
        'project_name': project_name,
        'workitem_id': work_item['id'],
        'workitem_name': fields.get('System.Title', ''),
        'workitem_type': fields.get('System.WorkItemType', 'N/A'),
        'workitem_description': description_text,
        'workitem_assginee': assignee,
        'created_by': created_by,
        'created_date': fields.get('System.CreatedDate', ''),
        'workitem_comment': comments_text,
        'workitem_state': state,
        'workitem_links': links_count,
        'workitem_tags': tags
    }

def save_work_items_to_db(work_item_details_list):
    try:
        for work_item in work_item_details_list:
            db_post_workitem(work_item)  
        logger.info(f"Saved {len(work_item_details_list)} work items to the database.")
    except Exception as e:
        logger.error(f"Error while saving work items to the database: {e}")

def main():
    try:
        db_session = next(get_db())  
        query = text("SELECT source_server_url, source_project_name, source_pat FROM devops_to_ados.db_devops_ado_migration_details")
        migration_details = db_session.execute(query).fetchall()
        # Process each row
        for row in migration_details:
            source_server_url, source_project_name, source_pat = row
            collection_name=extract_name(source_server_url)
            if not source_server_url or not source_project_name or not source_pat:
                logger.warning("Missing essential fields. Skipping...")
                continue
            logger.info(f"Processing project {source_project_name} on server {source_server_url}")
            print("------------------------------------------------------------------------------")
            print(f"Processing project {source_project_name} in server {collection_name}")
            print("------------------------------------------------------------------------------")
            # Discover work items
            work_item_ids = get_work_items_query(source_server_url, source_project_name, source_pat, api_version='6.0')
            if work_item_ids:
                work_item_details_list = []
                work_items = get_work_item_details(source_server_url, source_project_name, work_item_ids, source_pat, api_version='6.0')
                for work_item in work_items:
                    comments = get_work_item_comments(source_server_url, source_project_name, work_item['id'], source_pat, api_version='6.0-preview.3')
                    work_item_details = extract_work_item_info(source_server_url, source_project_name, work_item, comments)
                    work_item_details_list.append(work_item_details)
                save_work_items_to_db(work_item_details_list)
            else:
                logger.warning(f"No work items found for project {source_project_name}")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if db_session:
            db_session.close() 

if __name__ == '__main__':
    main()