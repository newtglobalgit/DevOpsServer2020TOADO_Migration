from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class ProjectMappingDetails(Base):
    __tablename__ = 'db_project_mapping'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    mapping_id = Column(Integer, primary_key=True, index=True)
    source_server_url = Column(String(255), nullable=False, index=True)
    source_project_name = Column(String(255), nullable=False, index=True)
    source_pat = Column(String(255), nullable=False, index=True)
    target_organization_url = Column(String(255), nullable=False, index=True) 
    target_project_name = Column(String(255), nullable=False, index=True)
    target_pat = Column(String(255), nullable=False, index=True)
    wiki = Column(String(255), nullable=False, index=True)
    workitem = Column(String(255), nullable=False, index=True)
    dashboard = Column(String(255), nullable=False, index=True)
    git = Column(String(255), nullable=False, index=True)
    devops_pat_token = Column(String(255), nullable=False, index=True)
    ado_pat_token = Column(String(255), nullable=False, index=True)
    test_plan = Column(String(255), nullable=False, index=True)
    wiki_security = Column(String(255), nullable=False, index=True)
    tfvc_security = Column(String(255), nullable=False, index=True)
    tfvc_files_folder_security = Column(String(255), nullable=False, index=True)

    

    

    def to_dict(self):
        return {
           "mappig_id" : self.mappig_id,
            "source_server_url" : self.source_server_url,
            "source_project_name" : self.source_project_name,
            "source_pat" : self.source_pat,
            "target_organization_url" : self.target_organization_url,
            "target_project_name" : self.target_project_name,
            "target_pat" : self.target_pat,
            "wiki" : self.wiki,
            "workitem" : self.workitem,
            "dashboard" : self.dashboard,
            "git" : self.git,
            "devops_pat_token" : self.devops_pat_token,
            "ado_pat_token" : self.ado_pat_token,
            "test_plan" : self.test_plan,
            "wiki_security" : self.wiki_security,
            "tfvc_security" : self.tfvc_security,
            "tfvc_files_folder_security" : self.tfvc_files_folder_security
            
        }
