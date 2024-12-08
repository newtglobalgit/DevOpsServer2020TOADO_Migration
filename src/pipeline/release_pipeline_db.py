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
from src.models.release_pipeline_model import  ReleasePipelineDetails


def db_post_release_pipeline(data):
    db = None  
    try:
        # Validate input
        discovery_release_id = data.get("discovery_release_id",0)
        project_name = data.get("project_name","").strip()
        collection_name= data.get("collection_name","").strip()
        release_id	= int(data.get("release_id", 0))
        release_name= data.get("release_name","").strip()
        created_date = data.get("created_date","").strip()
        updated_date = data.get("updated_date","").strip()
        release_variable =int(data.get("release_variable", 0))
        variable_groups	= int(data.get("variable_groups", 0))
        no_of_relaseses=int(data.get("no_of_relaseses", 0))
        release_names = data.get("release_names","").strip()
        artifacts	=int(data.get("artifacts", 0))
        agents = data.get("agents","").strip()
        parallel_execution_type = data.get("parallel_execution_type","").strip()
        max_agents	= data.get("max_agents","").strip()
        continueon_error = bool(data.get("continueon_error")) if data.get("continueon_error") else None 
        concurrency_count = data.get("concurrency_count","").strip()
        queuedepth_count = data.get("queuedepth_count","").strip()
        

        if not project_name or not collection_name:
            raise ValueError("Project name and collection name are required fields.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: project_name={project_name}, collection_name={collection_name}, "
           f"project_name={project_name},
            release_id	= {release_id},
            release_name= {release_name},
            created_date = {created_date},
            updated_date = {updated_date},
            release_variable = {release_variable}, 
            variable_groups	= {variable_groups},
            no_of_relaseses= {no_of_relaseses},
            release_names = {release_names},
            artifacts	= {artifacts},
            agents = {agents},
            parallel_execution_type = {parallel_execution_type},
            max_agents	=  {max_agents},
            continueon_error = {continueon_error},
            concurrency_count = {concurrency_count},
            queuedepth_count = {queuedepth_count}"
        )

        # Create a new record
        new_record = ReleasePipelineDetails(
            project_name=project_name,
            release_id	= release_id,
            release_name= release_name,
            created_date = created_date,
            updated_date = updated_date,
            release_variable = release_variable, 
            variable_groups	= variable_groups,
            no_of_relaseses= no_of_relaseses,
            release_names = release_names,
            artifacts	= artifacts,
            agents = agents,
            parallel_execution_type = parallel_execution_type,
            max_agents	=  max_agents,
            continueon_error = continueon_error,
            concurrency_count = concurrency_count,
            queuedepth_count = queuedepth_count
        )

        # Insert into the database
        with SessionLocal() as db:
            db.add(new_record)
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the release pipeline."
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

def db_get_release_pipeline():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(ReleasePipelineDetails).all()
            
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


