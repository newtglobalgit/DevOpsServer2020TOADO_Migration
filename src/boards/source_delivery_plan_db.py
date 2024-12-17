import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError


# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.delivery_plan_model import  SourceDeliveryPlanDetails


def db_post_delivery_plan(all_records):
    db = None  
    try:
        for data in all_records:
            collection_name = data.get("Collection Name", "")
            project_name = data.get("Project Name", "")
            delivery_plan_id = data.get("Delivery Plan Id","")
            delivery_plan_revision = data.get("Delivery Plan Revision","")
            delivery_plan_name =data.get("Delivery Plan Name","")
            delivery_plan_type = data.get("Delivery Plan Type",0)
            delivery_plan_created_date = data.get("Delivery Plan Created Date",0)
            delivery_plan_created_by = data.get("Delivery Plan Created By","")
            delivery_plan_modified_date =data.get("Delivery Plan Modified Date","")
            delivery_plan_modified_by =data.get("Delivery Plan Modified By","")
            discovery_run_duration =data.get("Run Duration","")

            if not project_name:
                raise ValueError("Project name and collection name are required fields.")

            # Log the data being inserted
            logging.info(
                f"Inserting record: \
                collection_name ={collection_name},\
                project_name={project_name},\
                delivery_plan_id={delivery_plan_id},\
                delivery_plan_revision={delivery_plan_revision},\
                delivery_plan_name={delivery_plan_name},\
                delivery_plan_type={delivery_plan_type},\
                delivery_plan_created_date={delivery_plan_created_date},\
                delivery_plan_created_by={delivery_plan_created_by},\
                delivery_plan_modified_date={delivery_plan_modified_date},\
                delivery_plan_modified_by={delivery_plan_modified_by},\
                run_duration={discovery_run_duration}"
                )


            # Create a new record
            new_record = SourceDeliveryPlanDetails(
                collection_name=collection_name,
                project_name=project_name,
                delivery_plan_id = delivery_plan_id,
                delivery_plan_revision =delivery_plan_revision,
                delivery_plan_name =delivery_plan_name,
                delivery_plan_type = delivery_plan_type,
                delivery_plan_created_date = delivery_plan_created_date,
                delivery_plan_created_by = delivery_plan_created_by,
                delivery_plan_modified_date =delivery_plan_modified_date,
                delivery_plan_modified_by =delivery_plan_modified_by,
                discovery_run_duration = discovery_run_duration,
            )

            # Insert into the database
            with SessionLocal() as db:
                query = db.add(new_record)
                
                db.commit()
        
            # Log success response
            success_message = "Record created successfully for Delivery Plans."
            logging.info(success_message)

    except ValueError as ve:
        # Handle input validation errors and log them
        error_message = f"Input validation failed: {str(ve)}"
        logging.error(error_message)

    except Exception as e:
        # Handle database or unexpected errors and log them
        print(str(e))
        error_message = f"Unexpected error occurred: {str(e)}"
        logging.error(error_message)

    finally:
        if db:
            db.close()  # Ensure the connection is closed

def db_get_delivery_plan():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(SourceDeliveryPlanDetails).all()
            
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
            db.close()