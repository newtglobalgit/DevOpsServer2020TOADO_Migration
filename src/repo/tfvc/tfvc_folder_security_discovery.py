import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.parse
import xlsxwriter
import pandas as pd
import sys
import os


folder_path = os.path.join("src","repo","tfvc")
file_name = f"tfvc_input.xlsx"
input_file = f"{folder_path}\\{file_name}"
input_data = pd.read_excel(input_file)

# Create Excel workbook for output
workbook = xlsxwriter.Workbook(f'{folder_path}\source_tfvc_folder_permissions.xlsx')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.repo.tfvc.tfvc_folder_security_source_discovery_db import  db_get_tfvc_folder_security, db_post_tfvc_folder_security
from src.dbDetails.db import clean_table

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
        # collection_id ="d664f669-94f1-447e-847f-aba3d0ba905f"
        url_  = f"{base_url}/_apis/projectCollections?api-version=6.0-preview"
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

def get_payload_1(ado_server_url , project_name, collection_id , descriptor , branch):
    collection_name = str(ado_server_url).split("/")[-1]
    payload = {
    "contributionIds": ["ms.vss-admin-web.security-view-permissions-data-provider"],
    "dataProviderContext": {
        "properties": {
            "subjectDescriptor": f"{descriptor}",
            "permissionSetId": "a39371cf-0841-4c16-bbd3-276e341bc052",
            "permissionSetToken": f"{branch}",
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


    return payload


def get_payload(ado_server_url ,project_name , collection_id, branch):
    collection_name = str(ado_server_url).split("/")[-1]
    return {
        "contributionIds": ["ms.vss-admin-web.security-view-members-data-provider"],
        "dataProviderContext": {
            "properties": {
                "permissionSetId": "a39371cf-0841-4c16-bbd3-276e341bc052",
                "permissionSetToken": f"{branch}",
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

def get_folder_details(ado_server_url , pat , project_name , branch):
    folder_paths = []
    url = f"{ado_server_url}/{project_name}/_apis/tfvc/items?scopePath={branch}&recursionLevel=full&api-version=6.0"
    response = requests.get(url , auth=HTTPBasicAuth("",pat))
    if response.status_code == 200:
        data = response.json()
        contents = data["value"]
        for content in contents:
            isFolder = content.get('isFolder', "")
            if isFolder == True:
                folder_paths.append(content.get("path",""))
    else:
        print(f"Failed to get folder paths")
    return folder_paths



    
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
        collection_name = str(ado_server_url).split("/")[-1]

        branch_list = [f"$/{project_name}"]
        branches_url = f"{ado_server_url}/{project_name}/_apis/tfvc/branches?api-version=6.0"
        branches_response = requests.get(branches_url , auth = HTTPBasicAuth("",pat))
        if branches_response.status_code == 200:
            data = branches_response.json()
            if data["count"] > 0:
                branches = data["value"]
                for branch in branches:
                    branch_list.append(branch.get("path",""))
            else:
                print(f"No branches in {project_name}")
        else:
            print(f"Error in fetching the branches data - {branches_response.status_code} {branches_response.text} ")
        for branch in branch_list:
            folder_paths =get_folder_details(ado_server_url , pat , project_name , branch)
            for folder_path_ in folder_paths:
                print(folder_path_)
                url = f"{ado_server_url}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview"    
                payload = get_payload(ado_server_url , project_name , collection_id, folder_path_)
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                response = requests.post(url,auth=HTTPBasicAuth("", pat) , headers=headers ,data=json.dumps(payload))
                if response.status_code == 200:
                    data = response.json()
                    detailed_data = data['dataProviders'].get("ms.vss-admin-web.security-view-members-data-provider","")
                    identities = detailed_data.get("identities","")
                    # Write TFID and Names in columns
                    col_counter =1
                    for identity in identities:
                        IdentityType = identity.get("subjectKind","")
                        displayName = identity.get("displayName", "")
                        descriptor = identity.get("descriptor", "")
                        worksheet.write(0, col_counter, displayName, bold_format)
                        col_widths[col_counter] = max(col_widths.get(col_counter, 0), len(displayName))

                        display_permissions_url = (
                            f"{ado_server_url}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview"
                        )
                        payload =get_payload_1(ado_server_url, project_name ,collection_id , descriptor, folder_path_)
                        response = requests.post(display_permissions_url,auth=HTTPBasicAuth("", pat) ,headers=headers ,data=json.dumps(payload))
                        if response.status_code == 200:
                            data = response.json()
                            detailed_data = data['dataProviders'].get("ms.vss-admin-web.security-view-permissions-data-provider","")
                            permissions = detailed_data.get("subjectPermissions", [])
                            for permission in permissions:
                                permission_displayName = permission.get("displayName", "")
                                permissionString = permission.get("permissionDisplayString", "")

                                if permission_displayName not in row_map:
                                    worksheet.write(row_counter, 0, permission_displayName)
                                    col_widths[0] = max(col_widths.get(0, 0), len(permission_displayName))
                                    row_map[permission_displayName] = row_counter
                                    row_counter += 1

                                worksheet.write(row_map[permission_displayName], col_counter, permissionString)
                                col_widths[col_counter] = max(col_widths.get(col_counter, 0), len(permissionString))

                                data ={
                                    "collection_name" : collection_name,
                                    "project_name" : project_name,
                                    "tfvc_name" : project_name,
                                    "tfvc_branch_name": branch,
                                    "item_type" : "Folder",
                                    "item_name" : folder_path_,
                                    "permission_type":IdentityType,
                                    "permission_name" : displayName,
                                    "access_type" : permission_displayName ,
                                    "access_level" : permissionString
                                }
                                db_post_tfvc_folder_security(data)
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
    # Read input data from Excel input file
    clean_table("devops_to_ados","db_devops_discovery_tfvc_files_folders_security","y")
    main()