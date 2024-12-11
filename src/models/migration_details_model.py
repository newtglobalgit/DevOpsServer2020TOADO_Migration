from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class MigrationDetails(Base):
    __tablename__ = 'db_devops_ado_project_migration_details'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    project_migration_id = Column(Integer, primary_key=True, index=True)
    source_server_url = Column(String(255),nullable=False, index=True)
    source_project_name =Column(String(255),nullable=False, index=True)
    source_pat = Column(Integer,nullable=False, index=True)
    target_organization_url = Column(String(255),nullable=False, index=True)
    target_project_name = Column(String(255),nullable=False, index=True)
    target_pat =Column(String(255),nullable=False, index=True)
    

    def to_dict(self):
        return {
           "devops_ado_migration_id": self.project_migration_id,
           "source_server_url" : self.source_server_url,
            "source_project_name" : self.source_project_name,
            "source_pat" :self.source_pat,
            "target_organization_url" : self.target_organization_url,
            "target_project_name" :self.target_project_name,
            "target_pat" :self.target_pat,
           
            }

