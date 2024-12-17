import logging
import os
import re
import sys
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import getpass
import time
from urllib.parse import quote
# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.boards.source_delivery_plan_db import db_post_delivery_plan , db_get_delivery_plan
from src.dbDetails.migration_details_db import db_get_migration_details


# Setup logging
id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f'src\logs\logs_source_delivery_plan_{id}'

# Clear the log file before starting a new run
with open(log_file, 'w'):
    pass

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_print(msg):
    logging.info(msg)
    print(msg)


def encode_url_component(component):
    return quote(component, safe='/\\$')


def make_request_with_retries(url, auth, max_retries=10, timeout=300):
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


    

# Function to set column widths to fit the data
def set_column_widths(worksheet, dataframe):
    for idx, col in enumerate(dataframe.columns):
        max_len = min(max(dataframe[col].astype(str).map(len).max(), len(col)) + 2, 30)
        # Adding some padding and limiting to 30 characters
        worksheet.set_column(idx, idx, max_len)

def get_delivery_plan_details(dashboard_details_url, pat):
    logging.info(f"Fetching delivery plan details from: {dashboard_details_url}")
    response = make_request_with_retries(dashboard_details_url, auth=HTTPBasicAuth('', pat))
    if response and response.status_code == 200:
        try:
            dashboard_details = response.json()['value']  # Assuming the response contains a 'value' key
            logging.info(f"Successfully fetched delivery plan details: {len(dashboard_details)} items")
            return dashboard_details
        except KeyError:
            logging.error("The response did not contain 'value' key.")
        except ValueError:
            logging.error("Failed to decode JSON response.")
    else:
        logging.error(f"Failed to fetch dashboard details. Status code: {response.status_code if response else f'No response {response.json}'}")
    
    return {}


# Function to generate the Excel report
def generate_excel_report(report_directory, server_url, pat, project_name, start_time):
    try:
        branch_data = []
        all_delivery_plan_details = []

        collection_name = server_url.split('/')[-1]

        encoded_project=encode_url_component(project_name)
        delivery_plan_url = f"{server_url}/{encoded_project}/_apis/work/plans?api-version=6.0"
        print(f"Delivery plan URL: {delivery_plan_url}")


        delivery_plan_details =  get_delivery_plan_details(delivery_plan_url, pat)
        for delivery_plan_detail in delivery_plan_details:
            all_delivery_plan_details.append({
                'Collection Name': collection_name,
                'Project Name': project_name,
                'Delivery Plan Id': delivery_plan_detail.get('id', ''),
                'Delivery Plan Revision': delivery_plan_detail.get('revision', ''),
                'Delivery Plan Name': delivery_plan_detail.get('name', ''),
                'Delivery Plan Type': delivery_plan_detail.get('type', ''),
                'Delivery Plan Created Date': delivery_plan_detail.get('createdDate', ''),
                'Delivery Plan Created By': delivery_plan_detail.get('createdByIdentity', {}).get('displayName', 'Unknown'),
                'Delivery Plan Modified Date': delivery_plan_detail.get('modifiedDate', ''),
                'Delivery Plan Modified By': delivery_plan_detail.get('modifiedByIdentity', {}).get('displayName', 'Unknown'),
                'Run Duration': str(datetime.now() - start_time)
            })
        db_post_delivery_plan(all_delivery_plan_details)
        excel_output_path = os.path.join(report_directory, f"Source_{project_name}_{collection_name}_Delivery_Plan_discovery_report.xlsx")

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
                'border': 1, 'text_wrap': True
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
                'Purpose of the report': f"This report provides a summary and detailed view of Project {project_name} Delivery Plan.",
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


            if all_delivery_plan_details:
                all_delivery_plan_details_df = pd.DataFrame(all_delivery_plan_details)
                all_delivery_plan_details_df = all_delivery_plan_details_df[['Collection Name', 'Project Name', 'Delivery Plan Id', 'Delivery Plan Revision',
                                                'Delivery Plan Name', 'Delivery Plan Type', 'Delivery Plan Created Date', 'Delivery Plan Created By']]
                all_delivery_plan_details_df.to_excel(writer, sheet_name='Delivery_plan_detail', index=False)

            # Apply the header format to the shelvesets sheet
                all_delivery_plan_details_worksheet = writer.sheets['Delivery_plan_detail']
                all_delivery_plan_details_worksheet.hide_gridlines(2)  # Remove gridlines in the shelvesets sheet
                for col_num, value in enumerate(all_delivery_plan_details_df.columns.values):
                    all_delivery_plan_details_worksheet.write(0, col_num, value, header_format)

                # Set column widths to fit data in shelvesets sheet
                set_column_widths(all_delivery_plan_details_worksheet, all_delivery_plan_details_df)

            # Add borders and right-align numerical and date/time cells in the shelvesets sheet
                for row_num in range(1, len(all_delivery_plan_details_df) + 1):
                    for col_num, value in enumerate(all_delivery_plan_details_df.iloc[row_num - 1]):
                        if isinstance(value, (int, float)) or (isinstance(value, str) and 'T' in value and 'Z' in value):
                            all_delivery_plan_details_worksheet.write(row_num, col_num, value, right_align_format)
                        else:
                            all_delivery_plan_details_worksheet.write(row_num, col_num, value, regular_format)

        logging.info(f"Report saved to {excel_output_path}")
    except Exception as e:
        logging.error(f"Failed to generate Excel report for project '{project_name}': {e}")
    
def main():
    try:
        run_id = str(int(datetime.now().strftime("%Y%m%d%H%M%S")))
        report_directory = 'src\pipeline\output_folder'

        # Create output directory if it doesn't exist
        if not os.path.exists(report_directory):
            os.makedirs(report_directory)

        results =db_get_migration_details()
    # Iterate over each row in the DataFrame
        for result in results:
            start_time = datetime.now()
            try:
                # Generate the Excel report
                generate_excel_report(report_directory, result.source_server_url, result.source_pat, result.source_project_name, start_time)
            except Exception as e:
                logging.error(f"Error occurred while processing project '{result.source_project_name}': {e}")
    except Exception as e:
        logging.error(f"Error occurred while processing input data from db': {e}")
        return


if __name__ == "__main__":
    main()
