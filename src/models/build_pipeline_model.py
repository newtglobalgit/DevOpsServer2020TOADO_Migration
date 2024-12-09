from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class BuildPipelineDetails(Base):
    __tablename__ = 'db_devops_discovery_pipelines_details'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    discovery_pipelines_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),nullable=False, index=True)
    collection_name =Column(String(255),nullable=False, index=True)
    pipeline_id = Column(Integer,nullable=False, index=True)
    pipeline_name = Column(String(255),nullable=False, index=True)
    last_updated_date = Column(String(255),nullable=False, index=True)
    file_name =Column(String(255),nullable=False, index=True)
    variables = Column(Integer,nullable=False, index=True)
    variable_groups = Column(Integer,nullable=False, index=True)
    repository_type = Column(String(255),nullable=False, index=True)
    repository_name =Column(String(255),nullable=False, index=True)
    repository_branch =Column(String(255),nullable=False, index=True)
    classic_pipeline =Column(String(255),nullable=False, index=True)
    agents = Column(String(255),nullable=False, index=True)
    phases =Column(String(255),nullable=False, index=True)                     
    execution_type = Column(String(255),nullable=False, index=True)     
    max_concurrency =Column(Integer,nullable=False, index=True)
    continue_on_error = Column(String(255),nullable=False, index=True)       
    builds = Column(Integer,nullable=False, index=True)
    artifacts = Column(String(255),nullable=False, index=True)     
    


    def to_dict(self):
        return {
           "discovery_build_pipeline_id": self.discovery_pipelines_id,
           "project_name" : self.project_name,
            "collection_name" : self.collection_name,
            "pipeline_id" :self.pipeline_id,
            "pipeline_name" : self.pipeline_name,
            "last_updated_date" :self.last_updated_date,
            "file_name" :self.file_name,
            "variables" : self.variables,
            "variable_groups" : self.variable_groups,
            "repository_type" : self.repository_type,
            "repository_name" : self.repository_name,
            "repository_branch" : self.repository_branch,
            "classic_pipeline" : self.classic_pipeline,
            "agents" : self.agents,
            "phases" : self.phases,                   
            "execution_type": self.execution_type ,   
            "max_concurrency" : self.max_concurrency,
            "continue_on_error" : self.continue_on_error,       
            "builds" : self.builds,
            "artifacts": self.artifacts
            }

