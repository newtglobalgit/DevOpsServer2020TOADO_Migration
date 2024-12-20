from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class TfvcRootDetails(Base):
    __tablename__ = 'db_devops_discovery_tfs_project_root'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    project_root_id = Column(Integer, primary_key=True, index=True)
    collection_name = Column(String(255), nullable=False, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    branch_name = Column(String(255), nullable=False, index=True)
    root_folder = Column(String(255), nullable=False, index=True)
    project_folder = Column(String(255), nullable=False, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    file_type = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=False, index=True)
    file_path = Column(String(255), nullable=False, index=True)

    

    def to_dict(self):
        return {
            "project_root_id": self.project_root_id_,
            "collection_name" : self.collection_name,
            "project_name": self.project_name,
            "branch_name": self.branch_name,
            "root_folder": self.root_folder,
            "project_folder": self.project_folder,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_path": self.file_path,
            
        }
