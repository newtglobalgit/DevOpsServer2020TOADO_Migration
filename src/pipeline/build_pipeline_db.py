import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.exc import SQLAlchemyError


# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.build_pipeline_model import  BuildPipelineDetails


def db_post_build_pipeline(data):
    db = None  
    try:
        # Validate input
        discovery_pipelines_id =int(data.get("discovery_pipelines_id", 0))
        project_name = data.get("project_name","").strip()
        collection_name =data.get("collection_name","").strip()
        pipeline_id = int(data.get("pipeline_id", 0))
        pipeline_name = data.get("pipeline_name","").strip()
        last_updated_date = data.get("last_updated_date","").strip()
        file_name =data.get("file_name","").strip()
        variables = int(data.get("variables", 0))
        variable_groups = int(data.get("variable_groups", 0))
        repository_type = data.get("repository_type","").strip()
        repository_name =data.get("repository_name","").strip()
        repository_branch =data.get("repository_branch","").strip()
        classic_pipeline =data.get("classic_pipeline","").strip()
        agents = data.get("agents","").strip()
        phases =data.get("phases","").strip()                 
        execution_type = data.get("execution_type","").strip()  
        max_concurrency =int(data.get("max_concurrency", 0))
        continue_on_error =bool(data.get("continue_on_error")) if data.get("continue_on_error") else None
        builds = int(data.get("builds", 0))
        artifacts = data.get("artifacts","").strip()
        

        if not project_name or not collection_name:
            raise ValueError("Project name and collection name are required fields.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: project_name={project_name}, collection_name={collection_name}, "
           f"pipeline_id = {pipeline_id},
            pipeline_name = {pipeline_name},
            last_updated_date ={last_updated_date},
            file_name ={file_name},
            variables = {variables},
            variable_groups = {variable_groups},
            repository_type = {repository_type},
            repository_name ={repository_name},
            repository_branch ={repository_branch},
            classic_pipeline ={classic_pipeline},
            agents = {agents},
            phases = {phases},             
            execution_type = {execution_type},
            max_concurrency = {max_concurrency},
            continue_on_error = {continue_on_error},
            builds = {builds},
            artifacts ={artifacts}"
        )

        # Create a new record
        new_record = BuildPipelineDetails(
            project_name=project_name,
            pipeline_id = pipeline_id,
            pipeline_name = pipeline_name,
            last_updated_date =last_updated_date,
            file_name =file_name,
            variables = variables,
            variable_groups = variable_groups,
            repository_type = repository_type,
            repository_name =repository_name,
            repository_branch =repository_branch,
            classic_pipeline =classic_pipeline,
            agents = agents,
            phases = phases,             
            execution_type = execution_type,
            max_concurrency = max_concurrency,
            continue_on_error = continue_on_error,
            builds = builds,
            artifacts =artifacts
        )

        # Insert into the database
        with SessionLocal() as db:
            db.add(new_record)
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the build pipeline."
        logging.info(success_message)

    except ValueError as ve:
        # Handle input validation errors and log them
        error_message = f"Input validation failed: {str(ve)}"
        logging.error(error_message)

    except Exception as e:
        # Handle database or unexpected errors and log them
        error_message = f"Unexpected error occurred: {str(e)}"
        logging.error(error_message)

    finally:
        if db:
            db.close()  # Ensure the connection is closed

def db_get_build_pipeline():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(BuildPipelineDetails).all()
            
            if records:
                logging.info("Records retrieved successfully:")
                for record in records:
                    logging.info(record.to_dict())  
                return records
            else:
                # Log if no record found
                logging.info("No records found in the table.")
                return None
    except SQLAlchemyError as sae:
        # Handle database errors and log them
        error_message = f"Database error occurred: {str(sae)}"
        logging.error(error_message)
        return None
    except Exception as e:
        # Handle unexpected errors and log them
        error_message = f"Unexpected error occurred: {str(e)}"
        logging.error(error_message)
        return None

    finally:
        if db:
            db.close()  # Ensure the connection is closed


