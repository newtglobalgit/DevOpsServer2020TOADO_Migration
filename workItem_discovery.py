import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import re
import html
import logging
from datetime import datetime
import getpass
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from utils.common import get_project_names, add_if_not_exists

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# Create a logger
logger = logging.getLogger()
# Set the log level
logger.setLevel(logging.INFO)
# File handler
file_handler = logging.FileHandler(os.path.join(log_dir, f'workitem_discovery_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'))
file_handler.setLevel(logging.INFO)
# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# Log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]


def make_api_request(url, pat, method='GET', data=None, timeout=50):
    """Reusable API request function with retry logic and timeout handling."""
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
    """Retrieve all work item IDs using pagination."""
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
    """Fetch work item details in chunks of 200 IDs."""
    all_work_item_details = []
    batch_size = 200
    
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
    comments_url = f'{base_url}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version=6.0-preview.3'
    logger.info(f"Fetching comments from URL: {comments_url}")
    return make_api_request(comments_url, pat)


def clean_html(raw_html):
    raw_html = html.unescape(raw_html)
    clean_text = re.sub(r'<a [^>]*>(.*?)</a>', r'\1', raw_html)
    clean_text = re.sub('<[^<]+?>', '', clean_text)
    return clean_text


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
        'Collection Name': collection_name,
        'Project Name': project_name,
        'ID': work_item['id'],
        'Work Item Name': fields.get('System.Title', ''),
        'Type': fields.get('System.WorkItemType', 'N/A'),
        'Description': description_text,
        'Assignee': assignee,
        'Created By': created_by,
        'Comment': comments_text,
        'Created Date': fields.get('System.CreatedDate', ''),
        'State': state,
        'Links': links_count,
        'Tags': tags
    }


def process_row(devops_server_url, project, token, api_version='6.0'):
    base_url = devops_server_url
    pat = token

    base_url_parts = base_url.split('/')
    collection_name = base_url_parts[3]  # Assuming collection name is the 4th part of the URL
    project_name = project

    logger.info(f'Read values from Excel:')
    logger.info(f'Server URL: {base_url}')
    logger.info(f'Project Name: {project}')
    logger.info(f'Collection Name: {collection_name}')

    work_item_details_list = []
    work_item_type_counts = {}

    work_item_ids = get_work_items_query(base_url, project, pat, api_version)
    if work_item_ids:
        details_response = get_work_item_details(base_url, project, work_item_ids, pat, api_version)
        if details_response:
            for work_item in details_response:
                comments = get_work_item_comments(base_url, project, work_item['id'], pat, api_version)
                info = extract_work_item_info(collection_name, project_name, work_item, comments)
                work_item_details_list.append(info)
                work_item_type = info['Type']
                if work_item_type in work_item_type_counts:
                    work_item_type_counts[work_item_type] += 1
                else:
                    work_item_type_counts[work_item_type] = 1
                logger.info(f'ID: {info["ID"]}')
                logger.info(f'Work Item Name: {info["Work Item Name"]}')
                logger.info(f'Type: {info["Type"]}')
                logger.info(f'Description: {info["Description"]}')
                logger.info(f'Assignee: {info["Assignee"]}')
                logger.info(f'Created By: {info["Created By"]}')
                logger.info(f'Comment: {info["Comment"]}')
                logger.info(f'Created Date: {info["Created Date"]}')
                logger.info(f'State: {info["State"]}')
                logger.info(f'Links: {info["Links"]}')
                logger.info(f'Tags: {info["Tags"]}')
                logger.info('---')

        return work_item_details_list, work_item_type_counts
    else:
        logger.error("Failed to retrieve work items query")
        return None, None


def generate_summary(writer, project_name, start_time, server_url):
    workbook = writer.book
    worksheet_summary = workbook.add_worksheet('Summary')
    header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#000080',
        'border': 1
    })
    regular_format = workbook.add_format({
        'border': 1
    })

    # Define wrap format to enable text wrapping
    wrap_format = workbook.add_format({
        'border': 1,
        'text_wrap': True  # Enable text wrapping
    })

    run_duration = datetime.now() - start_time
    hours, remainder = divmod(run_duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_run_duration = f"{int(hours)} hours, {int(minutes)} minutes, {seconds:.1f} seconds"

    # Determine organization or collection based on the server URL
    if "dev.azure.com" in server_url:
        org_or_collection = "organization"
        org_or_collection_name = server_url.split("/")[-1]  # Extract organization name from URL
    else:
        org_or_collection = "collection"
        org_or_collection_name = server_url.split('/')[-1]  # Extract collection name from URL

    summary_data = {
        'Report Title': f"Project {project_name} work items Report.",
        'Purpose of the report': f"This report provides a detailed view of the work items in project {project_name} of {org_or_collection} {org_or_collection_name}.",
        'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
        'Run Duration': formatted_run_duration,
        'Run By': getpass.getuser()
    }

    row = 0
    for key, value in summary_data.items():
        worksheet_summary.write(row, 0, key, header_format)
        # Apply wrap_format only for the "Purpose of the report" row
        if key == 'Purpose of the report':
            worksheet_summary.write(row, 1, value, wrap_format)
        else:
            worksheet_summary.write(row, 1, value, regular_format)
        
        row += 1

    worksheet_summary.set_column(0, 0, 26.71)
    worksheet_summary.set_column(1, 1, 81.87)
    for i in range(len(summary_data)):
        worksheet_summary.set_row(i, 30)

    worksheet_summary.hide_gridlines(2)


def set_column_widths(worksheet, df):
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = min(max(series.astype(str).map(len).max(), len(str(series.name))) + 2, 30)
        worksheet.set_column(idx, idx, max_len)


def generate_report(output_dir, project, work_item_details_list, work_item_type_counts, start_time,server_url ):
    report_df = pd.DataFrame(work_item_details_list)
    count_df = pd.DataFrame(list(work_item_type_counts.items()), columns=['Work Item Type', 'Count'])

    report_filename = os.path.join(output_dir, f'{project}_workItems_report.xlsx')
    with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
        # Generate Summary Sheet
        generate_summary(writer, project, start_time, server_url)
        
        workbook = writer.book
        header_format = workbook.add_format({
            'bg_color': '#000080',
            'font_color': 'white',
            'bold': True
        })
        right_align_format = workbook.add_format({'align': 'right', 'border': 1})
        
        # Write count_df with formatting
        count_df.to_excel(writer, sheet_name='Count', index=False)
        worksheet = writer.sheets['Count']
        for col_num, value in enumerate(count_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for row in range(1, len(count_df) + 1):
            for col in range(len(count_df.columns)):
                worksheet.write(row, col, count_df.iloc[row - 1, col], workbook.add_format({'border': 1}))
        worksheet.hide_gridlines(2)  # Hide gridlines
        set_column_widths(worksheet, count_df)
        
        # Write report_df with formatting
        report_df.to_excel(writer, sheet_name='work_items', index=False)
        worksheet = writer.sheets['work_items']
        for col_num, value in enumerate(report_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for row in range(1, len(report_df) + 1):
            for col in range(len(report_df.columns)):
                cell_value = report_df.iloc[row - 1, col]
                if col == report_df.columns.get_loc("Created Date"):  # Right-align date columns
                    worksheet.write(row, col, cell_value, right_align_format)
                else:
                    worksheet.write(row, col, cell_value, workbook.add_format({'border': 1}))
        worksheet.hide_gridlines(2)  # Hide gridlines
        set_column_widths(worksheet, report_df)
        
    logger.info(f'Report generated for {project}: {report_filename}')


def main():
    input_file = 'workitem_discovery_input_form.xlsx'
    try:
        run_id = str(int(datetime.now().strftime("%Y%m%d%H%M%S")))
        output_directory = os.path.join("Work Items", run_id)

        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        df = pd.read_excel(input_file)
        # Read the values from the Excel file and strip any leading/trailing spaces
        df['Server URL'] = df['Server URL'].str.strip().fillna('')
        df['Project Name'] = df['Project Name'].str.strip().fillna('')
        df['PAT'] = df['PAT'].str.strip().fillna('')

        # Form the input data in below format
        # Sample: { "server_url": { "pat": "123test_token", "projects": ['dev_server', 'qa_server'] }
        input_data = {}
        for index, row in df.iterrows():
            if pd.isna(row['Server URL']) or pd.isna(row['PAT']):
                logger.warning(f"Skipping row {int(index) + 1} due to missing data. ServerURL and PAT values are mandatory.")
                continue
            server_url = row['Server URL']
            proj_name = row['Project Name']
            ptoken = row['PAT']
            proj_names = []
            if not proj_name:
                proj_names = get_project_names(devops_server_url=server_url, pat=ptoken)
            if server_url not in input_data:
                input_data[server_url] = {}
                input_data[server_url]["pat"] = ptoken
                input_data[server_url]["projects"] = [proj_name] if proj_name else proj_names
            else:
                projects = input_data[server_url]["projects"]
                add_if_not_exists(projects, [proj_name] if proj_name else proj_names)
                input_data[server_url]["projects"] = projects

        for server_url in input_data:
            pat = input_data[server_url]["pat"]
            projects = input_data[server_url]["projects"]
            for project in projects:
                start_time = datetime.now()
                logger.info(f"Processing project {project}")
                try:
                    work_item_details_list, work_item_type_counts = process_row(server_url, project, pat)
                    if work_item_details_list and work_item_type_counts:
                        generate_report(output_directory, project.strip(), work_item_details_list, work_item_type_counts, start_time,server_url)
                    else:
                        logger.error(f"No work items found for project {project}")
                    # Clear the metadata
                    del work_item_details_list
                    del work_item_type_counts
                except Exception as e:
                    logger.error(f"Error occurred while processing project '{project}': {e}")
    except Exception as e:
        logger.error(f"Error occurred while processing input file '{input_file}': {e}")
        return


if __name__ == '__main__':
    main()

