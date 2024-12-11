import datetime
import os
import sys
import openpyxl


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.pipeline.build_pipeline_db import db_post_build_pipeline , db_get_build_pipeline


if __name__ == "__main__":
    results=db_get_build_pipeline()
    folder = f"src\pipeline"
    headers =["Source_Project","Source_Pipeline_Name","Source_Pipeline_Id","File_Name","Source_Repo_Name", "Source_Repo_Branch","Target_Project", "Target_Pipeline_Name","Is_Classic", "Migration_Required","Status"]
    wb = openpyxl.Workbook()
    ws = wb.active
    # id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")   # Format as "HH-MM-SS"
    excel_name =f"{folder}\mapping_migration.xlsx"
    ws.append(headers)
    for result in results:
        data =[
              result.project_name,
              result.pipeline_name,
              result.pipeline_id,
              result.file_name,
              result.repository_name,
              result.repository_branch,
              result.project_name,
              result.pipeline_name,
              result.classic_pipeline,
              "yes",
              "Discovery Completed"
        ]
        ws.append(data)
    wb.save(excel_name)
