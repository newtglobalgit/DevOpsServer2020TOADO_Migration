from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class BoardsWorkItemDetails(Base):
    __tablename__ = 'db_discovery_boards_workitem_details'  # Match the SQL table name
    __table_args__ = {'schema': 'ado_to_ado'} 
    
    
    discovery_boards_workitem_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False, index=True)
    workitem_type = Column(String(255), nullable=False)
    backlog = Column(String(255), nullable=False)
    tag = Column(Integer, nullable=False)
    total_count = Column(Integer, nullable=False)
    


    def to_dict(self):
        return {
            "discovery_boards_workitem_id": self.discovery_boards_workitem_id,
            "project_name": self.project_name,
            "collection_name": self.collection_name,
            "workitem_type": self.workitem_type,
            "backlog": self.backlog,
            "tag": self.tag,
            "total_count": self.total_count
        }
