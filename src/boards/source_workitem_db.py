import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.source_work_item_model import BoardsWorkItemDetails

def db_post_workitem(data):
    try:
        collection_name = data.get("collection_name", "").strip()
        project_name = data.get("project_name", "").strip()
        workitem_id = int(data.get("workitem_id", 0))
        workitem_name = data.get("workitem_name", "").strip()
        workitem_type = data.get("workitem_type", "").strip()
        workitem_description = data.get("workitem_description", "").strip() or 'No description'
        workitem_assignee = data.get("workitem_assignee", "").strip() or 'No assignee'
        created_by = data.get("created_by", "").strip()
        created_date = data.get("created_date", "").strip()
        workitem_comment = data.get("workitem_comment", "").strip() or 'No comments'
        workitem_state = data.get("workitem_state", "").strip()
        workitem_links = int(data.get("workitem_links", 0)) if data.get("workitem_links", 0) else 0
        workitem_tags = data.get("workitem_tags", "").strip() or 'No tags'

        if not project_name or not collection_name:
            raise ValueError("Project name and collection name are required fields.")

        logging.info(f"Inserting record: project_name={project_name}, collection_name={collection_name}, "
                     f"workitem_id={workitem_id} workitem_name={workitem_name} workitem_type={workitem_type}, "
                     f"workitem_state={workitem_state}, workitem_tags={workitem_tags}")

        new_record = BoardsWorkItemDetails(
            project_name=project_name,
            collection_name=collection_name,
            workitem_id=workitem_id,
            workitem_name=workitem_name,
            workitem_type=workitem_type,
            workitem_description=workitem_description,
            workitem_assignee=workitem_assignee,
            created_by=created_by,
            created_date=created_date,
            workitem_comment=workitem_comment,
            workitem_state=workitem_state,
            workitem_links=workitem_links,
            workitem_tags=workitem_tags
        )

        with SessionLocal() as db:
            db.add(new_record)
            db.commit()

        logging.info("Record created successfully for the work item.")
    except ValueError as ve:
        logging.error(f"Input validation failed: {str(ve)}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")

def db_get_workitem():
    try:
        with SessionLocal() as db:
            records = db.query(BoardsWorkItemDetails).all()
            if records:
                logging.info("Records retrieved successfully:")
                for record in records:
                    logging.info(record.to_dict())  
                return records
            else:
                logging.info("No records found in the table.")
                return None
    except SQLAlchemyError as sae:
        logging.error(f"Database error occurred: {str(sae)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        return None
