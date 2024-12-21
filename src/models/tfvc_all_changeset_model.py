from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base

class TfvcAllChangesetDetails(Base):
    __tablename__ = 'db_devops_discovery_changeset'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    changeset_id = Column(Integer, primary_key=True, index=True)
    collectionname = Column(String(255), nullable=False, index=True)
    projectname = Column(String(255), nullable=False, index=True)
    branchname = Column(String(255), nullable=False, index=True)
    changesetid= Column(Integer, nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    timedate = Column(TIMESTAMP, nullable=False, index=True)
    comment = Column(String(255), nullable=False, index=True)
    

    

    def to_dict(self):
        return {
            "changeset_id" : self.changeset_id,
            "collection_name" : self.collectionname,
            "project_name": self.projectname,
            "branchname" : self.branchname,
            "changesetid": self.changesetid,
            "author": self.author,
            "timedate": self.timedate,
            "comment": self.comment
            
        }
