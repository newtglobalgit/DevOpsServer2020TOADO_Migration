import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
#from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base



# Configure logging
logging.basicConfig(
    filename="database_operations.log",  # Log file name
    level=logging.INFO,                 # Logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Log initialization message
logging.info("Logging configuration initialized in db.py.")

# Update DATABASE_URL for PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:Romys%40123@172.191.4.85:5432/newt_devops_to_ado"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Set the schema for the session
def set_search_path(db_session):
    db_session.execute(text("SET search_path TO ado_to_ado"))

# Create a SessionLocal class to be used as a factory for session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for DB session with schema setup
def get_db():
    db = SessionLocal()
    try:
        set_search_path(db)  # Ensure the schema is set for every session
        yield db
    finally:
        db.close()

# Base model
Base = declarative_base()

# Export logger
logger = logging.getLogger(__name__)

# Check connection
def check_db():
    try:
        # Attempt to create a connection and execute a simple query
        with engine.connect() as connection:
            connection.execute(text("SET search_path TO ado_to_ado"))
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

if __name__ == "__main__":
    if check_db():
        print("Database connection successful!")
    else:
        print("Failed to connect to the database.")
