import pandas as pd
import json
import subprocess
import os

def read_excel_and_execute(input_excel, json_template_path):
    # Load the Excel file
    file = pd.read_excel(input_excel)
    file.columns = file.columns.str.strip()

    # Load the JSON template once
    with open(json_template_path, 'r') as json_file:
        json_template = json.load(json_file)

    # Set the correct absolute path for the temporary JSON file
    base_dir = os.path.abspath(os.path.dirname(json_template_path))  # Absolute directory of the template
    temp_json_path = os.path.join(base_dir, "temp_workitem_migration.json")

    for index, row in file.iterrows():
        try:
            # Extract values from the Excel row and handle missing/non-string values
            src_url = str(row.get('Source Server URL', '')).strip()
            src_project = str(row.get('Source Project Name', '')).strip()
            src_pat = str(row.get('Source PAT', '')).strip()
            trg_url = str(row.get('Target Organization URL', '')).strip()
            trg_project = row.get('Target Project Name')
            trg_pat = str(row.get('Target PAT', '')).strip()

            # Handle missing Target Project Name
            if pd.isna(trg_project) or not str(trg_project).strip():
                trg_project = src_project  
            trg_project = str(trg_project).strip() 

            # Update the JSON template dynamically
            json_data = json_template.copy()  # Work with a copy
            json_data["MigrationTools"]["Endpoints"]["Source"]["Collection"] = src_url
            json_data["MigrationTools"]["Endpoints"]["Source"]["Project"] = src_project
            json_data["MigrationTools"]["Endpoints"]["Source"]["Authentication"]["AccessToken"] = src_pat

            json_data["MigrationTools"]["Endpoints"]["Target"]["Collection"] = trg_url
            json_data["MigrationTools"]["Endpoints"]["Target"]["Project"] = trg_project
            json_data["MigrationTools"]["Endpoints"]["Target"]["Authentication"]["AccessToken"] = trg_pat

            # Write the updated JSON to the temporary file
            with open(temp_json_path, 'w') as temp_file:
                json.dump(json_data, temp_file, indent=4)

            # Execute the migration tool with the temporary JSON
            command = [os.path.join(base_dir, "devopsmigration.exe"), "execute", "-c", temp_json_path]
            result = subprocess.run(command, capture_output=True, text=True)

            # Handle the tool's execution result
            if result.returncode == 0:
                print(f"Execution successful for row {index+1}")
                print(result.stdout)
            else:
                print(f"Execution failed for row {index+1}")
                print(result.stderr)

            # Cleanup the temporary JSON file
            os.remove(temp_json_path)

        except Exception as e:
            print(f"An error occurred on row {index+1}: {e}")

# File paths
input_excel = r"migration_input.xlsx"
json_template_path = r"MigrationTools-16.0.5\latest.json"

# Run the function
read_excel_and_execute(input_excel, json_template_path)
