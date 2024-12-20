import os
import re
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import getpass
import time
from utils.common import get_project_names, add_if_not_exists
import logging


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# Create a logger
logger = logging.getLogger()
# Set the log level
logger.setLevel(logging.INFO)
# File handler
file_handler = logging.FileHandler(os.path.join(log_dir, f'tfvc_discovery_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'))
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


def modify_item_path(url):
    try:
        # Dictionary of replacements
        replacements = {
            '+': '%2B',
            '%24': '$',
            '&': '%26',
            ',': '%2C',
            # '/': '%2F',
            ':': '%3A',
            ';': '%3B',
            '=': '%3D',
            '?': '%3F',
            '@': '%40',
            ' ': '%20',
            '"': '%22',
            '<': '%3C',
            '>': '%3E',
            '#': '%23',
            # '%': '%25',
            '{': '%7B',
            '}': '%7D',
            '|': '%7C',
            '\\': '%5C',
            '^': '%5E',
            '[': '%5B',
            ']': '%5D',
            '`': '%60'
        }

        pattern = r"itemPath=(.+?)&api-version"
        match = re.search(pattern, url)
        
        if match:
            item_path = match.group(1)
            logger.info(f"Original item path: {item_path}")
            for char, replacement in replacements.items():
                item_path = item_path.replace(char, replacement)
            
            modified_url = url.replace(match.group(1), item_path)
            logger.info(f"Modified item path: {item_path}")
            return modified_url
        
        return url
    except Exception as e:
        logger.error(f"Failed to modify item path: {e}")
        return url


def make_request_with_retries(url, auth, max_retries=10, timeout=300):
    url = modify_item_path(url)
    print(url)
    logger.info(f"Making request to URL: {url}")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, auth=auth, timeout=timeout)
            if response.status_code == 200:
                logger.info(f"Request successful with status code: {response.status_code}")
                return response
            else:
                logger.warning(f"Attempt {attempt + 1}: Request timed out. Retrying...")
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Error during request: {e}")
            break
    logger.error(f"Failed to connect after {max_retries} attempts.")
    return None


# Function to sanitize Excel sheet names
def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]  # Excel sheet names can have a maximum of 31 characters


# Function to get the PAT for a server URL
def get_pat_for_server(server_url, df):
    try:
        return df.loc[df['Server URL'] == server_url, 'PAT'].values[0]
    except IndexError:
        logger.error(f"PAT not found for server URL: {server_url}")
        return None


# Function to get the organization name from the server URL
def extract_organization_name(server_url):
    return server_url.split('/')[2]  # Assumes the organization name is the third element in the URL


# Function to get shelvesets details
def get_shelvesets_details(server_url, pat):
    try:
        url = f"{server_url}/_apis/tfvc/shelvesets?api-version=6.0"
        response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
        return response.json().get('value', []) if response else []
    except Exception as e:
        logger.error(f"Failed to retrieve shelvesets: {e}")
        return []


# Function to get changeset details
def get_changeset_details(server_url, project_name, changeset_id, pat):
    try:
        url = f"{server_url}/{project_name}/_apis/tfvc/changesets/{changeset_id}?api-version=6.0"
        response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
        return response.json() if response else None
    except Exception as e:
        logger.error(f"Failed to retrieve changeset {changeset_id} details: {e}")
        return None


# Function to get changeset changes
def get_changeset_changes(server_url, changeset_id, pat):
    url = f"{server_url}/_apis/tfvc/changesets/{changeset_id}/changes?api-version=6.0"
    response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
    if response.status_code == 200:
        print(response.status_code)
        return response.json()
    else:
        print(f"Failed to retrieve changes for changeset {changeset_id}: {response.status_code} - {response.text}")
        return None


# Function to determine file type
def determine_file_type(item):
    if 'isFolder' in item:
        return 'Folder' if item['isFolder'] else 'File'
    if 'size' in item and item['size'] == 0:
        return 'Folder'
    return 'File'


# Function to get file count for a TFVC branch
def get_tfvc_branch_file_count(devops_server_url, project_name, branch_path, pat, exclude_paths=[]):
    try:
        items_api_url = f'{devops_server_url}/{project_name}/_apis/tfvc/items?scopePath={branch_path}&recursionLevel=full&api-version=6.0'
        items_response = make_request_with_retries(items_api_url, auth=HTTPBasicAuth('', pat))
        if items_response.status_code == 200:
            logger.info(f"Request successful with branch file status code: {items_response.status_code}")
            items = items_response.json()['value']
            if exclude_paths:
                items = [item for item in items if not any(item['path'].startswith(excluded_path) for excluded_path in exclude_paths)]
            return len([item for item in items if determine_file_type(item) in ['File', 'Folder']])
        else:
            logger.error(f"Failed to retrieve items for branch file'{branch_path}'. Status code: {items_response.status_code}")
            return 0
    except Exception as e:
        logger.error(f"Failed to retrieve items for branch file: {e}")
        return 0


def get_branch_file_details(devops_server_url, project_name, branch_path, pat, excluded_paths=[]):
    try: 
        items_api_url = f'{devops_server_url}/{project_name}/_apis/tfvc/items?scopePath={branch_path}&recursionLevel=full&api-version=6.0'
        items_response = make_request_with_retries(items_api_url, auth=HTTPBasicAuth('', pat))
        if items_response.status_code == 200:
            logger.info(f"Request successful with branch status code: {items_response.status_code}")
            items = items_response.json()['value']
            return [item for item in items if not any(item['path'].startswith(excluded_path) for excluded_path in excluded_paths)]
        else:
            logger.error(f"Failed to retrieve items for branch '{branch_path}'. Status code: {items_response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve items for branch: {e}")
        return []


def get_latest_changeset_for_item(server_url, project_name, item_path, pat):
    try: 
        changesets_url = f"{server_url}/{project_name}/_apis/tfvc/changesets?itemPath={item_path}&api-version=6.0"
        response = make_request_with_retries(changesets_url, auth=HTTPBasicAuth('', pat))
        if response.status_code == 200:
            logger.info(f"Request successful with changeset status code: {response.status_code}")
            changesets = response.json().get('value', [])
            if changesets:
                latest_changeset = changesets[0]
                return latest_changeset['changesetId'], latest_changeset.get('comment', 'No comment'), \
                    latest_changeset['createdDate'], latest_changeset['author']['displayName']
        return None, 'No comment', 'N/A', 'N/A'
    except Exception as e:
        logger.error(f"Failed to retrieve changeset for branch: {e}")
        return []
    

# Function to set column widths to fit the data
def set_column_widths(worksheet, dataframe):
    for idx, col in enumerate(dataframe.columns):
        max_len = min(max(dataframe[col].astype(str).map(len).max(), len(col)) + 2, 30)
        # Adding some padding and limiting to 30 characters
        worksheet.set_column(idx, idx, max_len)


# Function to generate the Excel report
def generate_excel_report(output_dir, server_url, pat, project, start_time):
    try:
        project_name = project
        server_url = server_url
        pat = pat

        branch_data = []
        all_branch_file_details = {}
        all_files_data = []
        all_changesets_data = []
        all_shelvesets_data = []

        collection_name = server_url.split('/')[-1]
        organization_name = extract_organization_name(server_url)
        tfvc_changesets_url = f"{server_url}/{project_name}/_apis/tfvc/changesets?api-version=6.0&$top=10000"
        print(f"TFVC Changesets URL: {tfvc_changesets_url}")

        params = {
            'api-version': '6.0',
            'maxCommentLength': 255,
            '$top': 100,
            '$orderby': 'createdDate desc'
        }

        tfvc_check_api_url = f'{server_url}/{project_name}/_apis/tfvc/branches?api-version=6.0'
        tfvc_response = make_request_with_retries(tfvc_check_api_url, auth=HTTPBasicAuth('', pat))
        if tfvc_response.status_code == 200:
            try:
                tfvc_branches = tfvc_response.json()['value']
                print(f"TFVC branches for project '{project_name}': {tfvc_branches}")  # Debugging output
                root_path = f"$/{project_name}"
                branch_paths = [tfvc_branch.get('path', 'Unnamed Branch') for tfvc_branch in tfvc_branches]
                root_file_count = get_tfvc_branch_file_count(server_url, project_name, root_path, pat, exclude_paths=branch_paths)
                branch_data.append({
                    'Collection Name': collection_name,
                    'Project Name': project_name,
                    'Repository Name': 'TFVC',
                    'Branch Name': sanitize_sheet_name(f"{project_name} [root]"),
                    'File count': root_file_count
                })
                root_file_details = get_branch_file_details(server_url, project_name, root_path, pat, excluded_paths=branch_paths)
                all_branch_file_details[sanitize_sheet_name(f"{project_name} [root]")] = root_file_details
                all_files_data.extend(root_file_details)

                if tfvc_branches:
                    for tfvc_branch in tfvc_branches:
                        branch_path = tfvc_branch.get('path', 'Unnamed Branch')
                        branch_name = branch_path.split('/')[-1]
                        branch_file_count = get_tfvc_branch_file_count(server_url, project_name, branch_path, pat)
                        branch_data.append({
                            'Collection Name': collection_name,
                            'Project Name': project_name,
                            'Repository Name': 'TFVC',
                            'Branch Name': sanitize_sheet_name(branch_name),
                            'File count': branch_file_count
                        })
                        branch_file_details = get_branch_file_details(server_url, project_name, branch_path, pat)
                        all_branch_file_details[sanitize_sheet_name(branch_name)] = branch_file_details
                        all_files_data.extend(branch_file_details)
            except (ValueError, KeyError) as e:
                logger.error(f"  Error parsing JSON response for TFVC in project '{project_name}':", e)
        else:
            logger.error(f"  Failed to retrieve TFVC branches for project '{project_name}'. Status code: {tfvc_response.status_code}")

        # Fetch all changesets
        changeset_response = make_request_with_retries(tfvc_changesets_url, auth=HTTPBasicAuth('', pat))
        if changeset_response.status_code == 200:
            logger.info(f"Changeset status code -{changeset_response.status_code}")
            changesets = changeset_response.json()['value']
            for changeset in changesets:
                all_changesets_data.append({
                    'Collection Name': collection_name,
                    'Project Name': project_name,
                    'Changeset ID': changeset['changesetId'],
                    'Author': changeset['author']['displayName'],
                    'Time Date': changeset['createdDate'],
                    'Comment': changeset.get('comment', 'No comment')
                })
        else:
            logger.error(f"  Failed to retrieve changesets for project '{project_name}'. Status code: {changeset_response.status_code}")

        # Fetch all shelvesets
        shelvesets = get_shelvesets_details(server_url, pat)
        for shelveset in shelvesets:
            shelveset_name, shelveset_id = shelveset['id'].split(';', 1)
            all_shelvesets_data.append({
                'Collection Name': collection_name,
                'Project Name': project_name,
                'Shelveset Name': shelveset_name,
                'Shelveset ID': shelveset_id,
                'Author': shelveset['owner']['displayName'],
                'Created Date': shelveset['createdDate'],
                'Comment': shelveset.get('comment', 'No comment')
            })

        df_tfvc_summary = pd.DataFrame(branch_data)
        # Define the Excel file name and path with project name, collection name
        excel_output_path = os.path.join(output_dir, f"{project_name}_{collection_name}_tfvc_discovery_report.xlsx")

        with pd.ExcelWriter(excel_output_path, engine='xlsxwriter') as writer:
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
            right_align_format = workbook.add_format({
                'border': 1,
                'align': 'right'
            })

            # Remove gridlines in the Summary sheet
            worksheet_summary.hide_gridlines(2)

            # Calculate run duration
            run_duration = datetime.now() - start_time
            hours, remainder = divmod(run_duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_run_duration = f"{int(hours)} hours, {int(minutes)} minutes, {seconds:.1f} seconds"

            summary_data = {
                'Report Title': f"Project {project_name} TFVC Report.",
                'Purpose of the report': f"This report provides a summary and detailed view of the TFVC in project {project_name}.",
                'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
                'Run Duration': formatted_run_duration,
                'Run By': getpass.getuser()
            }

            row = 0
            for key, value in summary_data.items():
                worksheet_summary.write(row, 0, key, header_format)
                worksheet_summary.write(row, 1, value, regular_format)
                row += 1

            for i in range(len(summary_data)):
                worksheet_summary.set_column(0, 0, 25.71)  # Adjust column A width
                worksheet_summary.set_column(1, 1, 76.87)  # Adjust column B width
                worksheet_summary.set_row(i, 30)  # Adjust row height

            df_tfvc_summary.to_excel(writer, sheet_name='TFVC', index=False)
            workbook = writer.book

            # Apply the header format to the TFVC sheet
            tfvc_worksheet = writer.sheets['TFVC']
            tfvc_worksheet.hide_gridlines(2)  # Remove gridlines in the TFVC sheet
            for col_num, value in enumerate(df_tfvc_summary.columns.values):
                tfvc_worksheet.write(0, col_num, value, header_format)

            set_column_widths(tfvc_worksheet, df_tfvc_summary)  # Adjust column widths for TFVC sheet

            # Add borders and right-align numerical and date/time cells in the TFVC sheet
            for row_num in range(1, len(df_tfvc_summary) + 1):
                for col_num, value in enumerate(df_tfvc_summary.iloc[row_num - 1]):
                    if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                        tfvc_worksheet.write(row_num, col_num, value, right_align_format)
                    else:
                        tfvc_worksheet.write(row_num, col_num, value, regular_format)

            all_files_data_df = []
            for branch_name, branch_file_details in all_branch_file_details.items():
                branch_file_data = []
                for item in branch_file_details:
                    if item['path'] != f'$/{project_name}':
                        changeset_id, comment, last_modified, author = get_latest_changeset_for_item(
                            server_url, project_name, item['path'], pat)
                        item_data = {
                            'Root Folder': project_name,
                            'Project Folder': '/'.join(item['path'].split('/')[2:-1]),
                            'File Name': item['path'].rsplit('/', 1)[-1],
                            'File Type': determine_file_type(item),
                            'File Size (bytes)': item.get('size', 'N/A'),
                            'File Path': item['path'],
                            'Last modified (time&date)': last_modified,
                            'Author': author,
                            'Comment': comment,
                            'Changeset ID': changeset_id
                        }
                        branch_file_data.append(item_data)
                        all_files_data_df.append(item_data)

                branch_df = pd.DataFrame(branch_file_data)
                branch_df = branch_df[['Root Folder', 'Project Folder', 'File Name', 'File Type', 'File Size (bytes)',
                                    'File Path', 'Last modified (time&date)', 'Author', 'Comment', 'Changeset ID']]
                branch_df.to_excel(writer, sheet_name=sanitize_sheet_name(branch_name), index=False)

                # Apply the header format to each branch sheet
                branch_worksheet = writer.sheets[sanitize_sheet_name(branch_name)]
                branch_worksheet.hide_gridlines(2)  # Remove gridlines in the branch sheet
                for col_num, value in enumerate(branch_df.columns.values):
                    branch_worksheet.write(0, col_num, value, header_format)

                # Set column widths to fit data in branch sheet
                set_column_widths(branch_worksheet, branch_df)

                # Add borders and right-align numerical and date/time cells in the branch sheet
                for row_num in range(1, len(branch_df) + 1):
                    for col_num, value in enumerate(branch_df.iloc[row_num - 1]):
                        if not value:
                            value = 'NULL'
                        if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                            branch_worksheet.write(row_num, col_num, value, right_align_format)
                        else:
                            branch_worksheet.write(row_num, col_num, value, regular_format)

            all_files_df = pd.DataFrame(all_files_data_df)
            all_files_df = all_files_df[['Root Folder', 'Project Folder', 'File Name', 'File Type', 'File Size (bytes)',
                                        'File Path', 'Last modified (time&date)', 'Author', 'Comment', 'Changeset ID']]
            all_files_df.to_excel(writer, sheet_name='all_files', index=False)

            # Apply the header format to the all_files sheet
            all_files_worksheet = writer.sheets['all_files']
            all_files_worksheet.hide_gridlines(2)  # Remove gridlines in the all_files sheet
            for col_num, value in enumerate(all_files_df.columns.values):
                all_files_worksheet.write(0, col_num, value, header_format)

            # Set column widths to fit data in all_files sheet
            set_column_widths(all_files_worksheet, all_files_df)

            # Add borders and right-align numerical and date/time cells in the all_files sheet
            for row_num in range(1, len(all_files_df) + 1):
                for col_num, value in enumerate(all_files_df.iloc[row_num - 1]):
                    if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                        all_files_worksheet.write(row_num, col_num, value, right_align_format)
                    else:
                        all_files_worksheet.write(row_num, col_num, value, regular_format)

            all_changesets_df = pd.DataFrame(all_changesets_data)
            all_changesets_df = all_changesets_df[['Collection Name', 'Project Name', 'Changeset ID', 'Author',
                                                'Time Date', 'Comment']]
            all_changesets_df.to_excel(writer, sheet_name='all_changesets', index=False)

            # Apply the header format to the all_changesets sheet
            all_changesets_worksheet = writer.sheets['all_changesets']
            all_changesets_worksheet.hide_gridlines(2)  # Remove gridlines in the all_changesets sheet
            for col_num, value in enumerate(all_changesets_df.columns.values):
                all_changesets_worksheet.write(0, col_num, value, header_format)

            # Set column widths to fit data in all_changesets sheet
            set_column_widths(all_changesets_worksheet, all_changesets_df)

            # Add borders and right-align numerical and date/time cells in the all_changesets sheet
            for row_num in range(1, len(all_changesets_df) + 1):
                for col_num, value in enumerate(all_changesets_df.iloc[row_num - 1]):
                    if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                        all_changesets_worksheet.write(row_num, col_num, value, right_align_format)
                    else:
                        all_changesets_worksheet.write(row_num, col_num, value, regular_format)

            all_shelvesets_df = pd.DataFrame(all_shelvesets_data)
            all_shelvesets_df = all_shelvesets_df[['Collection Name', 'Project Name', 'Shelveset Name', 'Shelveset ID',
                                                'Author', 'Created Date', 'Comment']]
            all_shelvesets_df.to_excel(writer, sheet_name='shelvesets', index=False)

            # Apply the header format to the shelvesets sheet
            all_shelvesets_worksheet = writer.sheets['shelvesets']
            all_shelvesets_worksheet.hide_gridlines(2)  # Remove gridlines in the shelvesets sheet
            for col_num, value in enumerate(all_shelvesets_df.columns.values):
                all_shelvesets_worksheet.write(0, col_num, value, header_format)

            # Set column widths to fit data in shelvesets sheet
            set_column_widths(all_shelvesets_worksheet, all_shelvesets_df)

            # Add borders and right-align numerical and date/time cells in the shelvesets sheet
            for row_num in range(1, len(all_shelvesets_df) + 1):
                for col_num, value in enumerate(all_shelvesets_df.iloc[row_num - 1]):
                    if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                        all_shelvesets_worksheet.write(row_num, col_num, value, right_align_format)
                    else:
                        all_shelvesets_worksheet.write(row_num, col_num, value, regular_format)

        logger.info(f"Report saved to {excel_output_path}")
    except Exception as e:
        logger.error(f"Failed to generate Excel report for project '{project}': {e}")
    

def main():
    input_file = 'tfvc_discovery_input_form.xlsx'
    try:
        run_id = str(int(datetime.now().strftime("%Y%m%d%H%M%S")))
        output_directory = os.path.join("TFVC", run_id)

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
                print(f"Skipping row {int(index) + 1} due to missing data. ServerURL and PAT values are mandatory.")
                continue
            surl = row['Server URL']
            proj_name = row['Project Name']
            ptoken = row['PAT']
            proj_names = []
            if not proj_name:
                proj_names = get_project_names(devops_server_url=surl, pat=ptoken)
            if surl not in input_data:
                input_data[surl] = {}
                input_data[surl]["pat"] = ptoken
                input_data[surl]["projects"] = [proj_name] if proj_name else proj_names
            else:
                projects = input_data[surl]["projects"]
                add_if_not_exists(projects, [proj_name] if proj_name else proj_names)
                input_data[surl]["projects"] = projects

        for server_url in input_data:
            pat = input_data[server_url]["pat"]
            projects = input_data[server_url]["projects"]
            for project in projects:
                start_time = datetime.now()
                print(f"Processing project {project}")
                try:
                    # Generate the Excel report
                    generate_excel_report(output_directory, server_url, pat, project, start_time)
                except Exception as e:
                    logger.error(f"Error occurred while processing project '{project}': {e}")
    except Exception as e:
        logger.error(f"Error occurred while processing input file '{input_file}': {e}")
        return


if __name__ == "__main__":
    main()

