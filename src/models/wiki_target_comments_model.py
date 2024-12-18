from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class WikiCommentDetails(Base):
    __tablename__ = 'db_ado_discovery_wiki_comments_reports'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    wiki_comments_reports_id = Column(Integer, primary_key=True, index=True)
    collection_name = Column(String(255), nullable=False, index=True)  # Assuming the collection name is stored in a separate table
    project_name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(255), nullable=False, index=True)
    comment_id = Column(Integer, nullable=False, index=True)
    comment_text = Column(String(255), nullable=False, index=True) 
    created_by = Column(String(255), nullable=False, index=True)
    created_date = Column(TIMESTAMP, nullable=False, index=True)

    def to_dict(self):
        return {
            "wiki_comments_reports_id": self.wiki_comments_reports_id,
            "collection_name" : self.collection_name,
            "project_name": self.project_name,
            "file_path": self.file_path,
            "comment_id" : self.comment_id,
            "comment_text": self.comment_text,
            "created_by": self.created_by,
            "created_date": self.created_date  # Convert the date to a string for consistency with other models
        }
