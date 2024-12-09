# import ast
# import json
# import subprocess
# import pandas as pd
# import requests

# Azure DevOps details
# base_url = "https://dev.azure.com/PLMigration/"
# organization_project = "CatCore"
# project_id = "e3748b0f-42b0-4851-b073-2270061050f5"  # Replace with your project ID
# pipeline_id = 2  # Replace with your pipeline ID
# pat_token = "BqV9EbVuxxzXtmzEdtdTfevv1qZ3EQszfR410EtLL0TDvbwxMruhJQQJ99AKACAAAAAyb0Q7AAASAZDOBwc3"  # Replace with your PAT token





import requests
from requests.auth import HTTPBasicAuth
import json

# Replace these variables with your details
organization = 'http://172.191.4.85/DefaultCollection'  
project = 'CatCore'       
definition_id = 3       
pat = ''

# URL to get the pipeline definition
url = f"{organization}/{project}/_apis/build/definitions/{definition_id}?api-version=6.1-preview"
print(url)
# # Set up the authentication (Basic Auth with PAT)
auth = HTTPBasicAuth('', pat)

# Make the API request
response = requests.get(url, auth=auth)

# Check if the request was successful
if response.status_code == 200:
    # Save the response (JSON) to a file
    with open('pipeline_definition.json', 'w') as f:
        json.dump(response.json(), f, indent=4)
    print("Pipeline definition has been saved to 'pipeline_definition.json'")
else:
    print(f"Failed to fetch pipeline definition. Status code: {response.status_code}")
    print(response.text)












# import requests
# from requests.auth import HTTPBasicAuth
# import json
# import requests
# from requests.auth import HTTPBasicAuth
# import json

# Replace these variables with your details
# organization = 'PLMigration'    # Your Azure DevOps Cloud organization name (without https://dev.azure.com/)
# project = 'CatCore'             # Your project name in Azure DevOps Cloud
# pat = ''  # Your Personal Access Token (PAT) for Azure DevOps Cloud
# json_file = 'pipeline_definition.json'  # Path to the exported pipeline definition JSON

# # Read the exported pipeline definition JSON file
# with open(json_file, 'r') as file:
#     pipeline_definition = json.load(file)

# # URL to create a pipeline in Azure DevOps Cloud (Correct endpoint for creating a pipeline)
# url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines?api-version=6.0-preview.1"

# # Set up the authentication (Basic Auth with PAT)
# auth = HTTPBasicAuth('', pat)


# # Make the API request to create the pipeline
# response = requests.post(url, auth=auth, json=pipeline_definition)

# # Check if the request was successful
# if response.status_code == 200:
#     print("Pipeline has been successfully imported to Cloud ADO!")
# else:
#     print(f"Failed to import pipeline. Status code: {response.status_code}")
#     print(response.text)








# import requests
# from requests.auth import HTTPBasicAuth
# import base64
# import json

# # Azure DevOps details
# organization = "http://172.191.4.85/DefaultCollection"
# project = "CatCore"
# definition_id = "1"  
# api_version = "6.1-preview"
# json_file = 'release_definition.json' 

# # Personal Access Token (PAT)
# pat = ""  

# # Base URL for Azure DevOps REST API
# url = f"{organization}/{project}/_apis/release/definitions/{definition_id}?api-version={api_version}"

# # # Authentication header using the PAT
# auth = HTTPBasicAuth('', pat)

# # Make the API request to fetch the release pipeline definition
# response = requests.get(url, auth=auth)

# # Check if the request was successful
# if response.status_code == 200:
#     # If successful, get the response JSON
#     release_pipeline = response.json()

#     # Write the JSON content to the file
#     with open(json_file, 'w') as file:
#         json.dump(release_pipeline, file, indent=4)
    
#     print(f"Pipeline definition successfully exported to {json_file}")
# else:
#     # If the request failed, print the error message
#     print(f"Failed to fetch release pipeline. Status Code: {response.status_code}")
#     print(response.text)


















# import requests
# from requests.auth import HTTPBasicAuth
# import json

# # Azure DevOps details
# organization = "https://dev.azure.com/PLMigration"  
# project = "CatCore"  
# api_version = "7.2-preview.4"  
# json_file = 'release_definition.json'  # Path to the exported release pipeline JSON file

# # Personal Access Token (PAT)
# pat = ""  # Replace with your PAT

# # Base URL for Azure DevOps REST API to create the release pipeline
# url = f"{organization}/{project}/_apis/release/definitions?api-version={api_version}"

# # Authentication header using the PAT
# auth = HTTPBasicAuth('', pat)

# # Read the exported pipeline definition from the JSON file
# with open(json_file, 'r') as file:
#     pipeline_definition = json.load(file)

# # Make the API request to create the release pipeline using the JSON definition
# response = requests.post(url, auth=auth, json=pipeline_definition)

# # Print the raw response text for debugging
# print("Response status code:", response.status_code)
# # print("Response text:", response.text)

# # Check if the request was successful
# if response.status_code == 200 or response.status_code == 201:
#     # If successful, parse the JSON response and print it
#     created_pipeline = response.json()
#     print("Release pipeline created successfully:")
#     # print(json.dumps(created_pipeline, indent=4))
# else:
#     # If the request failed, print the error message
#     print(f"Failed to import release pipeline. Status Code: {response.status_code}")
#     # print(response.text)
