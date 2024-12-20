from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class TFVCFolderSecuritySourceDetails(Base):
    __tablename__ = 'db_devops_discovery_tfvc_files_folders_security'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    tfvc_files_folders_security_id = Column(Integer, primary_key=True, index=True)
    collection_name = Column(String(255),nullable=False, index=True)  
    project_name =  Column(String(255),nullable=False, index=True)  
    tfvc_name =Column(String(255),nullable=False, index=True)  
    tfvc_branch_name = Column(String(255),nullable=False, index=True)
    item_type = Column(String(255), nullable=False , index=True)
    item_name = Column(String(255), nullable=False, index=True)  
    permission_type = Column(String(255),nullable=False, index=True)  
    permission_name = Column(String(255),nullable=False, index=True)   
    access_type = Column(String(255),nullable=False, index=True)  
    access_level = Column(String(255),nullable=False, index=True)     
    


    def to_dict(self):
        return {
           "tfvc_files_folders_security_id" : self.tfvc_files_folders_security_id, 
            "collection_name" : self.collection_name  , 
            "project_name" : self.project_name, 
            "tfvc_name" : self.tfvc_name  , 
            "tfvc_branch_name": self.tfvc_branch_name  ,
            "item_type": self.item_type,
            "item_name": self.item_name, 
            "permission_type" : self.permission_name  , 
            "permission_name" : self.permission_name  , 
            "access_type" : self.access_type  , 
            "access_level": self.access_level 
            }

