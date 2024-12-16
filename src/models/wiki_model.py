from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class WikiDetails(Base):
    __tablename__ = 'db_devops_discovery_wiki_reports'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    wiki_reports_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(255), nullable=False, index=True)
    size_bytes = Column(Integer, nullable=False, index=True)
    last_modified = Column(TIMESTAMP, nullable=False, index=True)

    def to_dict(self):
        return {
            "wiki_reports_id": self.wiki_reports_id,
            "project_name": self.project_name,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "last_modified": self.last_modified
        }
