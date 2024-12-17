from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, Date
from sqlalchemy.sql import func
from src.dbDetails.db import Base



class SourceDeliveryPlanDetails(Base):
    __tablename__ = 'db_devops_discovery_delivery_plan'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    delivery_plan_sr_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),nullable=False, index=True)
    collection_name =Column(String(255),nullable=False, index=True)
    delivery_plan_id = Column(String(255),nullable=False, index=True)
    delivery_plan_revision = Column(String(255),nullable=False, index=True)
    delivery_plan_name = Column(String(255),nullable=False, index=True)
    delivery_plan_type =Column(String(255),nullable=False, index=True)
    delivery_plan_created_date = Column(Date,nullable=False, index=True)
    delivery_plan_created_by = Column(String(255),nullable=False, index=True)
    delivery_plan_modified_date = Column(Date,nullable=False, index=True)
    delivery_plan_modified_by =Column(String(255),nullable=False, index=True)
    discovery_run_duration =Column(String(255),nullable=False, index=True)
  
    def to_dict(self):
        return {
           "delivery_plan_sr_id": self.delivery_plan_sr_id,
           "project_name" : self.project_name,
            "collection_name" : self.collection_name,
            "delivery_plan_id" :self.delivery_plan_id,
            "delivery_plan_revision" : self.delivery_plan_revision,
            "delivery_plan_name" :self.delivery_plan_name,
            "delivery_plan_type" :self.delivery_plan_type,
            "delivery_plan_created_date" : self.delivery_plan_created_date,
            "delivery_plan_created_by" : self.delivery_plan_created_by,
            "delivery_plan_modified_date" : self.delivery_plan_modified_date,
            "delivery_plan_modified_by" : self.delivery_plan_modified_by,
            "discovery_run_duration" : self.discovery_run_duration
            }



class TargetDeliveryPlanDetails(Base):
    __tablename__ = 'db_ado_discovery_delivery_plan'  # Match the SQL table name
    __table_args__ = {'schema': 'devops_to_ados'} 
    
    delivery_plan_sr_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),nullable=False, index=True)
    collection_name =Column(String(255),nullable=False, index=True)
    delivery_plan_id = Column(String(255),nullable=False, index=True)
    delivery_plan_revision = Column(String(255),nullable=False, index=True)
    delivery_plan_name = Column(String(255),nullable=False, index=True)
    delivery_plan_type =Column(String(255),nullable=False, index=True)
    delivery_plan_created_date = Column(Date,nullable=False, index=True)
    delivery_plan_created_by = Column(String(255),nullable=False, index=True)
    delivery_plan_modified_date = Column(Date,nullable=False, index=True)
    delivery_plan_modified_by =Column(String(255),nullable=False, index=True)
    discovery_run_duration =Column(String(255),nullable=False, index=True)
  
    def to_dict(self):
        return {
           "discovery_delivery_plan_id": self.discovery_delivery_plan_id,
           "project_name" : self.project_name,
            "collection_name" : self.collection_name,
            "delivery_plan_id" :self.delivery_plan_id,
            "delivery_plan_revision" : self.delivery_plan_revision,
            "delivery_plan_name" :self.delivery_plan_name,
            "delivery_plan_type" :self.delivery_plan_type,
            "delivery_plan_created_date" : self.delivery_plan_created_date,
            "delivery_plan_created_by" : self.delivery_plan_created_by,
            "delivery_plan_modified_date" : self.delivery_plan_modified_date,
            "delivery_plan_modified_by" : self.delivery_plan_modified_by,
            "discovery_run_duration" : self.discovery_run_duration
            }
