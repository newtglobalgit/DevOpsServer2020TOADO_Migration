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
from src.models.boards_work_item_model import  BoardsWorkItemDetails


def db_post_workitem(data):
    db = None  
    try:
        # Validate input
        project_name = data.get("project_name", "").strip()
        collection_name = data.get("collection_name", "").strip()
        workitem_type = data.get("workitem_type", "").strip()
        backlog = data.get("backlog", "").strip()
        tag = int(data.get("tag", 0)) if data.get("tag") else None
        total_count = int(data.get("total_count", 0))

        if not project_name or not collection_name:
            raise ValueError("Project name and collection name are required fields.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: project_name={project_name}, collection_name={collection_name}, "
            f"workitem_type={workitem_type}, backlog={backlog}, tag={tag}, total_count={total_count}"
        )

        # Create a new record
        new_record = BoardsWorkItemDetails(
            project_name=project_name,
            collection_name=collection_name,
            workitem_type=workitem_type,
            backlog=backlog,
            tag=tag,
            total_count=total_count,
        )

        # Insert into the database
        with SessionLocal() as db:
            db.add(new_record)
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the work item."
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

def db_get_workitem():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(BoardsWorkItemDetails).all()
            
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


# Main method to simulate data entry
def main():
    # Sample data to be inserted (you can adjust it as needed)
    data = {
        "project_name": "ProjectXYZ",
        "collection_name": "CollectionA",
        "workitem_type": "Bug",
        "backlog": "Sprint1",
        "tag": 123,
        "total_count": 10
    }

    # Call db_post_workitem function to insert data
    db_post_workitem(data)
    db_get_workitem()
    


# Entry point of the script
if __name__ == "__main__":
    main()