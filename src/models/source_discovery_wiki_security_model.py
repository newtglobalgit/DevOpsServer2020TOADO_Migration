from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class WikiSecuritySourceDetails(Base):
    __tablename__ = 'db_devops_discovery_wiki_security'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    wiki_security_id = Column(Integer, primary_key=True, index=True)
    collection_name = Column(String(255),nullable=False, index=True)  
    project_name =  Column(String(255),nullable=False, index=True)  
    permission_type = Column(String(255),nullable=False, index=True)  
    permission_name = Column(String(255),nullable=False, index=True)   
    access_type = Column(String(255),nullable=False, index=True)  
    access_level = Column(String(255),nullable=False, index=True)  
     


    def to_dict(self):
        return {
           "wiki_security_id" : self.wiki_security_id, 
            "collection_name" : self.collection_name  , 
            "project_name" : self.project_name, 
            "permission_type" : self.permission_name  , 
            "permission_name" : self.permission_name  , 
            "access_type" : self.access_type  , 
            "access_level": self.access_level 
            }

