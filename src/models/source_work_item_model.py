from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class BoardsWorkItemDetails(Base):
    __tablename__ = 'db_devops_discovery_boards_workitem_details'
    __table_args__ = {'schema': 'devops_to_ados'}
    
    discovery_boards_workitem_id = Column(Integer, primary_key=True, index=True)
    collection_name = Column(String(255), nullable=False, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    workitem_id = Column(Integer, nullable=False, index=True)
    workitem_name = Column(String(255), nullable=False, index=True)
    workitem_type = Column(String(255), nullable=False, index=True)
    workitem_description = Column(String(200), nullable=True, index=True)
    workitem_assignee = Column(String(200), nullable=True, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    created_date = Column(String(255), nullable=False, index=True)
    workitem_comment = Column(String(255), nullable=True, index=True)
    workitem_state = Column(String(255), nullable=False,  index=True)
    workitem_links = Column(Integer, nullable=True, index=True)
    workitem_tags = Column(String(255), nullable=True, index=True)
    
    def to_dict(self):
        return {
            "discovery_boards_workitem_id": self.discovery_boards_workitem_id,
            "collection_name": self.collection_name,
            "project_name": self.project_name,
            "workitem_id": self.workitem_id,
            "workitem_name": self.workitem_name,
            "workitem_type": self.workitem_type,
            "workitem_description": self.workitem_description,
            "workitem_assignee": self.workitem_assignee,
            "created_by": self.created_by,
            "created_date": self.created_date,
            "workitem_comment": self.workitem_comment,
            "workitem_state": self.workitem_state,
            "workitem_links": self.workitem_links,
            "workitem_tags": self.workitem_tags
        }
