


import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.parse
import xlsxwriter
import pandas as pd
import sys
import os

# Read input data from Excel input file
input_file = 'wikis_input.xlsx'
input_data = pd.read_excel(input_file)

# Create Excel workbook for output
workbook = xlsxwriter.Workbook('source_wiki_permissions.xlsx')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.wiki.security.source_discovery_wiki_security_db import db_get_wiki_security  , db_post_wiki_security
from src.dbDetails.db import clean_table


def get_wiki_id(ado_server_url, project_name, pat):
    try:
        wiki_api_url = f"{ado_server_url}/{project_name}/_apis/wiki/wikis?api-version=6.0"
        response = requests.get(wiki_api_url, auth=HTTPBasicAuth("", pat))
        if response.status_code == 200:
            wikis = response.json().get("value", [])
            if wikis:
                return wikis[0].get("id", "")  # Return the first wiki ID found
            else:
                print(f"No wikis found for project {project_name}")
                return None
        else:
            print(f"Failed to fetch wikis for project {project_name}. HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching wiki ID: {e}")
        return None

def get_proj_details(ado_url, pat_token, proj_name):
    url = f"{ado_url}/_apis/projects/{proj_name}?api-version=6.1-preview"
    response = requests.get(url, auth=HTTPBasicAuth("", pat_token))
    if response.status_code == 200:
        proj_details = response.json()
        proj_id = proj_details.get('id', "")
        return proj_id

def get_explicit_identities(ado_server_url, project_name, pat, worksheet):
    row_map = {}
    row_counter = 1
    col_widths = {}

    try:
        # Set header with bold format
        bold_format = workbook.add_format({'bold': True})
        worksheet.write(0, 0, "Permissions", bold_format)
        collection_name = str(ado_server_url).split("/")[-1]
        permission_set_id = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        wiki_id = get_wiki_id(ado_server_url, project_name, pat)
        if not wiki_id:
            return

        proj_id = get_proj_details(ado_server_url, pat, project_name)
        read_identities_url = (
            f"{ado_server_url}/{proj_id}/_api/_security/ReadExplicitIdentitiesJson"
            f"?__v=5&permissionSetId={permission_set_id}"
            f"&permissionSetToken=repoV2%2F{proj_id}/{wiki_id}/"
        )

        response = requests.get(
            read_identities_url,
            auth=HTTPBasicAuth("", pat)
        )
        if response.status_code == 200:
            identities = response.json().get("identities", [])
            col_counter = 1

            # Write TFID and Names in columns
            for identity in identities:
                IdentityType = identity.get("IdentityType","")
                TeamFoundationId = identity.get("TeamFoundationId", "")
                name = identity.get("FriendlyDisplayName", "")
                if IdentityType == "user":
                    name = f"{name}(User)"
                worksheet.write(0, col_counter, name, bold_format)
                col_widths[col_counter] = max(col_widths.get(col_counter, 0), len(name))

                display_permissions_url = (
                    f"{ado_server_url}/{proj_id}/_api/_security/DisplayPermissions?__v=5&tfid="
                    f"{TeamFoundationId}"
                    f"&permissionSetId={permission_set_id}"
                    f"&permissionSetToken={urllib.parse.quote(f'repoV2/{proj_id}/{wiki_id}/')}"
                )

                # Send the request
                response = requests.get(
                    display_permissions_url,
                    auth=HTTPBasicAuth("", pat)
                )

                if response.status_code == 200:
                    data = response.json()
                    permissions = data.get("permissions", [])
                    for permission in permissions:
                        displayName = permission.get("displayName", "")
                        permissionString = permission.get("permissionDisplayString", "")

                        data ={
                            "collection_name" : collection_name,
                            "project_name" : project_name,
                            "permission_type" : IdentityType,
                            "permission_name" : displayName,
                            "access_type" : displayName ,
                            "access_level" : permissionString
                        }

                        if displayName not in row_map:
                            worksheet.write(row_counter, 0, displayName)
                            col_widths[0] = max(col_widths.get(0, 0), len(displayName))
                            row_map[displayName] = row_counter
                            row_counter += 1

                        worksheet.write(row_map[displayName], col_counter, permissionString)
                        col_widths[col_counter] = max(col_widths.get(col_counter, 0), len(permissionString))
                col_counter += 1

            # Set column widths
            for col, width in col_widths.items():
                worksheet.set_column(col, col, width + 2)  # Add padding
        else:
            print(f"Failed to fetch explicit identities. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"Error occurred while fetching explicit identities: {e}")

def main():
    for _, row in input_data.iterrows():
        ado_server_url = row['Source_URL']
        pat = row['Source_PAT']
        project_name = str(row['Source_Project']).strip()

        # Create a new sheet for each project
        worksheet = workbook.add_worksheet(project_name)  # Excel sheet name limit is 31 characters
        print(f"Processing permissions for Project: {project_name}")

        get_explicit_identities(ado_server_url, project_name, pat, worksheet)

    workbook.close()
    print("Permissions have been saved to 'wiki_permissions.xlsx'")

if __name__ == "__main__":
    clean_table()
    main()

