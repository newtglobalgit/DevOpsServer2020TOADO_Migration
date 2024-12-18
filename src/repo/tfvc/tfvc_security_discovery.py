import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.parse
import xlsxwriter
import pandas as pd

# Read input data from Excel input file
input_file = 'tfvc_input.xlsx'
input_data = pd.read_excel(input_file)

# Create Excel workbook for output
workbook = xlsxwriter.Workbook('source_tfvc_permissions.xlsx')

def get_proj_details(ado_server_url , pat , project):
    collection_id=""
    proj_id=""
    url = f"{ado_server_url}/_apis/projects/{project}?api-version=6.1-preview"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat}'
    }
    response = requests.get(url,auth=HTTPBasicAuth("",pat))
    if response.status_code == 200:
        proj_details = response.json()
        proj_id = proj_details.get('id', "")
        collection_name = str(ado_server_url).split("/")[-1]
        base_url = "/".join(ado_server_url.split("/")[:3])
        url_  = f"{base_url}/_apis/projectCollections?api-version=6.0"
        response = requests.get(url_ , headers=headers , verify=False)
        if response.status_code == 200:
            data = response.json()
            if data['count'] > 0:
                collections =data['values']
                for collection in collections:
                    if collection.get("name") == collection_name:
                        collection_id = collection_id.get("id","")   
        return proj_id , collection_id
    else:
        print(f"Failed to retrieve build definitions. Status code: {response.status_code}")
        return None

def get_payload(ado_server_url , project_name, collection_id , collection_name ):
    payload = {
    "contributionIds": ["ms.vss-admin-web.security-view-permissions-data-provider"],
    "dataProviderContext": {
        "properties": {
            "subjectDescriptor": "vssgp.Uy0xLTktMTU1MTM3NDI0NS0yOTMxNDg0MzU1LTEyOTM0MjA4NzItMjY0Njg4MjI2My02MTA0Mzg2MS0xLTE1MTUyMzg4MjYtMTYwMjE2MTczOC0yNjIyNzc0MTQwLTMwNTM0MzUxMjY",
            "permissionSetId": "a39371cf-0841-4c16-bbd3-276e341bc052",
            "permissionSetToken": f"$/{project_name}",
            "accountName": f"[{project_name}]\\Contributors",
            "sourcePage": {
                "url": f"{ado_server_url}/{project_name}/_settings/repositories?repo=tfvc&_a=permissionsMid",
                "routeId": "ms.vss-admin-web.project-admin-hub-route",
                "routeValues": {
                    "project": project_name,
                    "adminPivot": "repositories",
                    "controller": "ContributedPage",
                    "action": "Execute",
                    "serviceHost": f"{collection_id} ({collection_name})"
                }
            }
        }
    }
    }

    # Convert to JSON formatted string
    payload_json = json.dumps(payload, indent=4)
    print(payload_json)


def get_payload(ado_server_url ,project_name , collection_id):
    collection_name = str(ado_server_url).split("/")[-1]
    return {
        "contributionIds": ["ms.vss-admin-web.security-view-members-data-provider"],
        "dataProviderContext": {
            "properties": {
                "permissionSetId": "a39371cf-0841-4c16-bbd3-276e341bc052",
                "permissionSetToken": f"$/ {project_name}",
                "sourcePage": {
                    "url": f"{ado_server_url}/{project_name}/_settings/repositories?repo=tfvc&_a=permissionsMid",
                    "routeId": "ms.vss-admin-web.project-admin-hub-route",
                    "routeValues": {
                        "project": project_name,
                        "adminPivot": "repositories",
                        "controller": "ContributedPage",
                        "action": "Execute",
                        "serviceHost": f"{collection_id} ({collection_name})"
                    }
                }
            }
        }
    }

    
def get_explicit_identities(ado_server_url, project_name, pat, worksheet):
    row_map = {}
    row_counter = 1
    col_widths = {}

    try:
        # Set header with bold format
        bold_format = workbook.add_format({'bold': True})
        worksheet.write(0, 0, "Permissions", bold_format)

        permission_set_id = "a39371cf-0841-4c16-bbd3-276e341bc052"
        proj_id , collection_id = get_proj_details(ado_server_url, pat, project_name)
        
        url = f"{ado_server_url}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview"
        payload = get_payload(ado_server_url , project_name , collection_id)
        response = requests.get(url,auth=HTTPBasicAuth("", pat) , data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            detailed_data = data['dataProviders'].get("ms.vss-admin-web.security-view-members-data-provider","")
            identities = detailed_data.get("identities","")
            

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
    main()