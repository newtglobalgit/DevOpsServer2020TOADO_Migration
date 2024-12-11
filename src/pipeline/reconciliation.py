import os
import pandas as pd
import sys

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.pipeline.build_pipeline_target_db import db_post_build_pipeline_target , db_get_build_pipeline_target
from src.pipeline.build_pipeline_db import db_post_build_pipeline , db_get_build_pipeline

# Load source and target data from the database (assuming they return a list of objects)
source_df = db_get_build_pipeline()  # Assuming this returns a list of objects
target_df = db_get_build_pipeline_target()  # Assuming this returns a list of objects

# Columns to compare
compare_columns = ["project_name", "pipeline_name", "file_name", "variables", "variable_groups", "repository_name", "classic_pipeline"]

# Initialize the reconciliation DataFrame
recon_data = []

# Perform the comparison
for source_row in source_df:
    for target_row in target_df:
        # Compare Project and Name first
        if source_row.project_name == target_row.project_name and source_row.pipeline_name == target_row.pipeline_name:
            # Compare remaining columns, handling NaN values properly
            status = "Matched"
            for col in compare_columns:
                source_value = getattr(source_row, col, None) if pd.notna(getattr(source_row, col, None)) else ""
                target_value = getattr(target_row, col, None) if pd.notna(getattr(target_row, col, None)) else ""
                
                if source_value != target_value:
                    status = "Not Matched"
                    break

            # Append the results for matched rows
            recon_data.append({
                "Source Project": source_row.project_name,
                "Source Name": source_row.pipeline_name,
                "Source FileName": source_row.file_name,
                "Source Variables": source_row.variables,
                "Source Variable Groups": source_row.variable_groups,
                "Source Repository Name": source_row.repository_name,
                "Source Classic Pipeline": source_row.classic_pipeline,
                "Target Project": target_row.project_name,
                "Target Name": target_row.pipeline_name,
                "Target FileName": target_row.file_name,
                "Target Variables": target_row.variables,
                "Target Variable Groups": target_row.variable_groups,
                "Target Repository Name": target_row.repository_name,
                "Target Classic Pipeline": target_row.classic_pipeline,
                "Status": status
            })

# Create a DataFrame for the reconciliation
recon_df = pd.DataFrame(recon_data)

# Save the reconciliation DataFrame to Excel
folder_path = os.path.join("src", "pipeline", "output_folder")
recon_file = os.path.join(folder_path, "reconciliation.xlsx")
recon_df.to_excel(recon_file, index=False)

print(f"Reconciliation completed. File saved as {recon_file}.")
