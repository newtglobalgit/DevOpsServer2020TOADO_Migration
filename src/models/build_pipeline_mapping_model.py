from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class BuildPipelineMappingDetails(Base):
    __tablename__ = 'db_devops_build_pipeline_mapping'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    mapping_pipelines_id = Column(Integer, primary_key=True, index=True)
    source_project_name = Column(String(255),nullable=False, index=True)
    source_pipeline_name = Column(String(255),nullable=False, index=True)
    source_pipeline_id = Column(String(255),nullable = False, index=True)
    source_file_name =Column(String(255),nullable=False, index=True)
    source_repository_name =Column(String(255),nullable=False, index=True)
    source_repository_branch =Column(String(255),nullable=False, index=True)
    target_project_name =Column(String(255),nullable=False, index=True)
    target_pipeline_name = Column(String(255),nullable=False, index=True)
    is_classic = Column(String(255),nullable=False, index=True)     
    migration_required =Column(String(255),nullable=False, index=True)
    status = Column(String(255),nullable=False, index=True)       
    
    


    def to_dict(self):
        return {
           "mapping_pipelines_id": self.mapping_pipelines_id,
           "source_project_name" : self.source_project_name,
            "source_pipeline_name" : self.source_pipeline_name,
            "source_pipeline_id": self.source_pipeline_id,
            "source_file_name" :self.source_file_name,
            "source_repository_name" : self.source_repository_name,
            "target_project_name" :self.target_project_name,
            "target_pipeline_name" :self.target_pipeline_name,
            "is_classic" : self.is_classic,
            "migration_required" : self.migration_required,
            "status" : self.status,
            }

