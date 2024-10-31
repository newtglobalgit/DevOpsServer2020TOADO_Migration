import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import re
import html
import logging
from datetime import datetime
import getpass
from utils.common import get_project_names, add_project_if_not_exists

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]


def authenticate_and_get_projects(base_url, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    try:
        response = requests.get(f'{base_url}/_apis/projects?api-version={api_version}', auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to authenticate: {e}')
        return None


def get_work_items_query(base_url, project, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    query_url = f'{base_url}/{project}/_apis/wit/wiql?api-version={api_version}'
    query = {"query": "Select [System.Id] From WorkItems Where [System.TeamProject] = @project"}
    try:
        response = requests.post(query_url, json=query, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to retrieve work items: {e}')
        return None


def get_work_item_details(base_url, project, work_item_ids, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    work_item_url = f'{base_url}/{project}/_apis/wit/workitems?ids={",".join(map(str, work_item_ids))}&$expand=relations&api-version={api_version}'
    logging.info(f"Fetching work item details from URL: {work_item_url}")
    try:
        response = requests.get(work_item_url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to retrieve work item details: {e}')
        return None


def get_work_item_comments(base_url, project, work_item_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    comments_url = f'{base_url}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version=6.0-preview.3'
    logging.info(f"Fetching comments from URL: {comments_url}")
    try:
        response = requests.get(comments_url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to retrieve comments for work item ID {work_item_id}: {e}')
        return None


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
        'Links': links_count,  # Correctly count the links
        'Tags': tags
    }


def process_row(devops_server_url, project, token, api_version='6.0'):
    base_url = devops_server_url
    project = project
    pat = token

    base_url_parts = base_url.split('/')
    collection_name = base_url_parts[3]  # Assuming collection name is the 4th part of the URL
    project_name = project

    logging.info(f'Read values from Excel:')
    logging.info(f'Server URL: {base_url}')
    logging.info(f'Project Name: {project}')
    logging.info(f'Collection Name: {collection_name}')

    work_item_details_list = []
    work_item_type_counts = {}

    work_items_query = get_work_items_query(base_url, project, pat, api_version)
    if work_items_query:
        work_item_ids = [item['id'] for item in work_items_query['workItems']]
        details_response = get_work_item_details(base_url, project, work_item_ids, pat, api_version)
        if details_response:
            for work_item in details_response['value']:
                comments = get_work_item_comments(base_url, project, work_item['id'], pat, api_version)
                info = extract_work_item_info(collection_name, project_name, work_item, comments)
                work_item_details_list.append(info)
                work_item_type = info['Type']
                if work_item_type in work_item_type_counts:
                    work_item_type_counts[work_item_type] += 1
                else:
                    work_item_type_counts[work_item_type] = 1
                logging.info(f'ID: {info["ID"]}')
                logging.info(f'Work Item Name: {info["Work Item Name"]}')
                logging.info(f'Type: {info["Type"]}')
                logging.info(f'Description: {info["Description"]}')
                logging.info(f'Assignee: {info["Assignee"]}')
                logging.info(f'Created By: {info["Created By"]}')
                logging.info(f'Comment: {info["Comment"]}')
                logging.info(f'Created Date: {info["Created Date"]}')
                logging.info(f'State: {info["State"]}')
                logging.info(f'Links: {info["Links"]}')  # Updated log to show correct count of links
                logging.info(f'Tags: {info["Tags"]}')
                logging.info('---')

        return work_item_details_list, work_item_type_counts
    else:
        logging.error("Failed to retrieve work items query")
        return None, None


def generate_summary(writer, project_name, start_time):
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

    run_duration = datetime.now() - start_time
    hours, remainder = divmod(run_duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_run_duration = f"{int(hours)} hours, {int(minutes)} minutes, {seconds:.1f} seconds"

    summary_data = {
        'Report Title': f"Project {project_name} work items Report.",
        'Purpose of the report': f"This report provides a detailed view of the work items in project {project_name}.",
        'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
        'Run Duration': formatted_run_duration,
        'Run By': getpass.getuser()
    }

    row = 0
    for key, value in summary_data.items():
        worksheet_summary.write(row, 0, key, header_format)
        worksheet_summary.write(row, 1, value, regular_format)
        row += 1

    worksheet_summary.set_column(0, 0, 26.71)  # Adjust column A width
    worksheet_summary.set_column(1, 1, 81.87)  # Adjust column B width
    for i in range(len(summary_data)):
        worksheet_summary.set_row(i, 30)  # Adjust row height

    worksheet_summary.hide_gridlines(2)  # Hide gridlines


def set_column_widths(worksheet, df):
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = min(max(series.astype(str).map(len).max(), len(str(series.name))) + 2, 30)
        worksheet.set_column(idx, idx, max_len)


def generate_report(output_dir, project, work_item_details_list, work_item_type_counts, start_time):
    report_df = pd.DataFrame(work_item_details_list)
    count_df = pd.DataFrame(list(work_item_type_counts.items()), columns=['Work Item Type', 'Count'])

    report_filename = os.path.join(output_dir, f'{project}_workItems_report.xlsx')
    with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
        # Generate Summary Sheet
        generate_summary(writer, project, start_time)
        
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
                if col in [report_df.columns.get_loc("Created Date")]:  # Right-align date columns
                    worksheet.write(row, col, cell_value, right_align_format)
                else:
                    worksheet.write(row, col, cell_value, workbook.add_format({'border': 1}))
        worksheet.hide_gridlines(2)  # Hide gridlines
        set_column_widths(worksheet, report_df)
        
    logging.info(f'Report generated for {project}: {report_filename}')


def main():
    input_file = 'workitem_discovery_input_form.xlsx'
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
            logging.warning(f"Skipping row {index + 1} due to missing data. ServerURL and PAT values are mandatory.")
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
            add_project_if_not_exists(projects, [proj_name] if proj_name else proj_names)
            input_data[server_url]["projects"] = projects

    for server_url in input_data:
        pat = input_data[server_url]["pat"]
        projects = input_data[server_url]["projects"]
        for project in projects:
            start_time = datetime.now()
            logging.info(f"Processing project {project}")
            work_item_details_list, work_item_type_counts = process_row(server_url, project, pat)
            if work_item_details_list and work_item_type_counts:
                generate_report(output_directory, project.strip(), work_item_details_list, work_item_type_counts, start_time)
            else:
                logging.error(f"No work items found for project {project}")

            # Clear the metadata
            del work_item_details_list
            del work_item_type_counts


if __name__ == '__main__':
    main()
