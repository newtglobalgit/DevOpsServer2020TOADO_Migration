from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class ReleasePipelineDetails(Base):
    __tablename__ = 'db_discovery_release_details'  # Match the SQL table name
    __table_args__ = {'schema': 'ado_to_ado'} 

    discovery_release_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),nullable=False, index=True)
    collection_name = Column(String(255),nullable=False, index=True)
    release_id	= Column(Integer,nullable=False, index=True)
    release_name= Column(String(255),nullable=False, index=True)
    created_date = Column(String(255),nullable=False, index=True)
    updated_date= Column(String(255),nullable=False, index=True)
    release_variable = Column(Integer,nullable=False, index=True)
    variable_groups	= Column(Integer,nullable=False, index=True)
    no_of_relaseses= Column(Integer,nullable=False, index=True)
    release_names = Column(String(255),nullable=False, index=True)
    artifacts	= Column(Integer,nullable=False, index=True)
    agents	= Column(String(255),nullable=False, index=True)
    parallel_execution_type = Column(String(255),nullable=False, index=True)
    max_agents	= Column(String(255),nullable=False, index=True)
    continueon_error = Column(String(255),nullable=False, index=True) 
    concurrency_count = Column(String(255),nullable=False, index=True)
    queuedepth_count = Column(String(255),nullable=False, index=True)


    def to_dict(self):
        return {
           "discovery_release_pipeline_id": self.discovery_release_id,
           "project_name" : self.project_name,
            "collection_name" : self.collection_name,
            "release_id"	: self.release_id,
            "release_name": self.release_name,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
            "release_variable" : self.release_variable,
            "variable_groups"	: self.variable_groups,
            "no_of_relaseses": self.no_of_relaseses,
            "release_names" : self.release_names,
            "artifacts"	: self.artifacts,
            "agents"	: self.agents,
            "parallel_execution_type" : self.parallel_execution_type,
            "max_agents": self.max_agents,
            "continueon_error" : self.continueon_error,
            "concurrency_count" : self.concurrency_count,
            "queuedepth_count" : self.queuedepth_count
            }

