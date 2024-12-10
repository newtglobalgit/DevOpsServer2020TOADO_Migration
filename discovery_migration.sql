DROP SCHEMA IF EXISTS "devops_to_ados" CASCADE;
CREATE SCHEMA IF NOT EXISTS "devops_to_ados" AUTHORIZATION postgres;

SET search_path TO "devops_to_ados";

-- Drop tables for discovery for GIT
DROP TABLE IF EXISTS db_devops_discovery_git_project_projectdetails CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_project_root CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_project_repo CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_project_branches CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_project_workitems CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_project_pipelines CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_repo_sourcecode CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_repo_commits CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_git_repo_tags CASCADE;

-- Drop Tables for discovery for TFVC

DROP TABLE IF EXISTS db_devops_discovery_tfs_project_projectdetails CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_root CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_branches CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_workitems CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_boards CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_pipelines CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_sourcecode CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_commits CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_label CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_tfs_project_shelveset  CASCADE;

-- Other Tables
DROP TABLE IF EXISTS db_devops_discovery_overview_dashboard_details CASCADE;

DROP TABLE IF EXISTS db_devops_discovery_boards_workitem_details	CASCADE;  -- source table
DROP TABLE IF EXISTS db_ados_discovery_boards_workitem_details	CASCADE;    -- target

DROP TABLE IF EXISTS db_devops_discovery_user_details CASCADE;  --source table
DROP TABLE IF EXISTS db_ados_discovery_user_details CASCADE;  --target table


DROP TABLE IF EXISTS db_devops_discovery_release_details	CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_pipelines_details CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_wiki_reports CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_pull_requests CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_project_configuration_Iterations CASCADE;
DROP TABLE IF EXISTS db_devops_discovery_project_configuration_Areas CASCADE;

-- mapping trable for migration
DROP TABLE IF EXISTS db_devops_ado_project_migration_details CASCADE; -- for migration
DROP TABLE IF EXISTS db_devops_ado_repo_migration_details CASCADE; -- for migration

-- Table details for target --


-- Drop tables for target for GIT
DROP TABLE IF EXISTS db_ado_git_project_projectdetails CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_root CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_repo CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_branches CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_workitems CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_boards CASCADE;
DROP TABLE IF EXISTS db_ado_git_project_pipelines CASCADE;
DROP TABLE IF EXISTS db_ado_git_repo_sourcecode CASCADE;
DROP TABLE IF EXISTS db_ado_git_repo_commits CASCADE;
DROP TABLE IF EXISTS db_ado_git_repo_tags CASCADE;

-- Drop Tables for discovery for TFVC

DROP TABLE IF EXISTS db_ado_tfs_project_projectdetails CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_root CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_branches CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_workitems CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_boards CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_pipelines CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_sourcecode CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_commits CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_label CASCADE;
DROP TABLE IF EXISTS db_ado_tfs_project_shelveset  CASCADE;



CREATE TABLE db_devops_discovery_git_project_projectdetails( 
  project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
  collection_name VARCHAR(200) NOT NULL, 
  project_name VARCHAR(200) NOT NULL, 
  project_path_name VARCHAR(200), 
  branch_name VARCHAR(200), 
  file_count INTEGER, 
  sheet_name VARCHAR(200), 
  created_by VARCHAR(50), 
  updated_by VARCHAR(50), 
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, 
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP 
); 

-- Trigger for updated_at to mimic ON UPDATE CURRENT_TIMESTAMP on the table db_discovery_git_project_projectdetails 

CREATE OR REPLACE FUNCTION db_devops_discovery_git_project_projectdetails_update_updated_at() 
RETURNS TRIGGER AS $$ 
BEGIN 
  NEW.updated_at = CURRENT_TIMESTAMP; 
  RETURN NEW; 
END; 
$$ LANGUAGE plpgsql; 

  

CREATE TRIGGER db_devops_discovery_git_project_projectdetails_set_updated_at
BEFORE UPDATE ON db_devops_discovery_git_project_projectdetails 
FOR EACH ROW 
EXECUTE FUNCTION db_devops_discovery_git_project_projectdetails_update_updated_at(); 


CREATE TABLE db_devops_discovery_git_project_root(   
  project_root_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   
  root_folder VARCHAR(200) NOT NULL,   
  project_folder VARCHAR(200) NOT NULL,   
  file_name VARCHAR(200),   
  file_type VARCHAR(200),   
  file_size INTEGER,   
  file_path VARCHAR(200),   
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_devops_discovery_git_project_repo (  
  project_repo_id BIGINT PRIMARY KEY,  
  repo_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_devops_discovery_git_project_branches (  
  project_branch_id BIGINT PRIMARY KEY,  
  branch_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key for project
  repo_id BIGINT NOT NULL,  -- Add foreign key repo
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (repo_id) REFERENCES  db_devops_discovery_git_project_repo(project_repo_id) ON DELETE CASCADE
); 

CREATE TABLE db_devops_discovery_git_project_workitems (  
  project_workitems_id BIGINT PRIMARY KEY,  
  workitem_name VARCHAR(200) ,
  workitem_type VARCHAR(200) ,  
  project_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE
); 

CREATE TABLE db_devops_discovery_git_project_boards (  
  project_board_id BIGINT PRIMARY KEY,  
  workitem_id Integer ,  
  workitem_status VARCHAR(100),  
  project_id BIGINT ,
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (workitem_id) REFERENCES  db_devops_discovery_git_project_workitems(project_workitems_id) ON DELETE CASCADE
);

CREATE TABLE db_devops_discovery_git_project_pipelines (  
  project_pipeline_id BIGINT PRIMARY KEY,  
  environments VARCHAR(100) ,  
  releases VARCHAR(100),
  libraries VARCHAR(100),
  task_groups VARCHAR(100),
  deployment_groups VARCHAR(100),
  project_id BIGINT , -- Add foreign key project_id
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE
);

CREATE TABLE db_devops_discovery_git_repo_sourcecode (  
  source_code_id BIGINT PRIMARY KEY,  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  last_modified_time TIMESTAMPTZ, 
  author VARCHAR(100), 
  sourcecode_comments VARCHAR(300), 
  commit_id BIGINT,	 
  commit_count INTEGER, 
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  branch_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE ,
  FOREIGN KEY (repo_id) REFERENCES  db_devops_discovery_git_project_repo(project_repo_id) ON DELETE CASCADE,
  FOREIGN KEY (branch_id) REFERENCES  db_devops_discovery_git_project_branches(project_branch_id) ON DELETE CASCADE
); 

CREATE TABLE db_devops_discovery_git_repo_commits (  
  commits_id BIGINT PRIMARY KEY,     
  commit_name VARCHAR(200) NOT NULL,  
  collection_name VARCHAR(200),
  branch_id BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches   
  commit_message VARCHAR(200),  
  author VARCHAR(200), 
  commit_date TIMESTAMPTZ , 
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (repo_id) REFERENCES  db_devops_discovery_git_project_repo(project_repo_id) ON DELETE CASCADE ,
  FOREIGN KEY (branch_id) REFERENCES  db_devops_discovery_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 

 
CREATE TABLE db_devops_discovery_git_repo_tags (  
  tags_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,     
  tags_name VARCHAR(200) NOT NULL,  
  branch_id  BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches  
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (repo_id) REFERENCES  db_devops_discovery_git_project_repo(project_repo_id) ON DELETE CASCADE ,
  FOREIGN KEY (branch_id) REFERENCES  db_devops_discovery_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


------------------  For TFVC -----------------------------------

CREATE TABLE db_devops_discovery_tfs_project_projectdetails( 
  project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
  collection_name VARCHAR(200) NOT NULL, 
  project_name VARCHAR(200) NOT NULL, 
  project_path_name VARCHAR(200), 
  branch_name VARCHAR(200), 
  file_count INTEGER, 
  sheet_name VARCHAR(200), 
  created_by VARCHAR(50), 
  updated_by VARCHAR(50), 
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, 
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP 
); 


-- Trigger for updated_at to mimic ON UPDATE CURRENT_TIMESTAMP on the table db_tfs_project_projectdetails 

CREATE OR REPLACE FUNCTION db_devops_discovery_tfs_project_projectdetails_update_updated_at() 
RETURNS TRIGGER AS $$ 
BEGIN 
  NEW.updated_at = CURRENT_TIMESTAMP; 
  RETURN NEW; 
END; 
$$ LANGUAGE plpgsql; 

  

CREATE TRIGGER db_devops_discovery_tfs_project_projectdetails_set_updated_at
BEFORE UPDATE ON db_devops_discovery_tfs_project_projectdetails 
FOR EACH ROW 
EXECUTE FUNCTION db_devops_discovery_tfs_project_projectdetails_update_updated_at();

CREATE TABLE db_devops_discovery_tfs_project_root(   
  project_root_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   
  root_folder VARCHAR(200) NOT NULL,   
  project_folder VARCHAR(200) NOT NULL,   
  file_name VARCHAR(200),   
  file_type VARCHAR(200),   
  file_size INTEGER,   
  file_path VARCHAR(200),   
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE 
); 


CREATE TABLE db_devops_discovery_tfs_project_branches (  
  project_branch_id BIGINT PRIMARY KEY,  
  branch_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key for project
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE
  ); 

CREATE TABLE db_devops_discovery_tfs_project_workitems (  
  project_workitems_id BIGINT PRIMARY KEY,  
  workitem_name VARCHAR(200) ,
  workitem_type VARCHAR(200) ,  
  project_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE
); 


CREATE TABLE db_devops_discovery_tfs_project_boards (  
  project_board_id BIGINT PRIMARY KEY,  
  workitem_id Integer ,  
  workitem_status VARCHAR(100),  
  project_id BIGINT ,
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (workitem_id) REFERENCES  db_devops_discovery_tfs_project_workitems(project_workitems_id) ON DELETE CASCADE
);

CREATE TABLE db_devops_discovery_tfs_project_pipelines (  
  project_pipeline_id BIGINT PRIMARY KEY,  
  environments VARCHAR(100) ,  
  releases VARCHAR(100),
  libraries VARCHAR(100),
  task_groups VARCHAR(100),
  deployment_groups VARCHAR(100),
  project_id BIGINT , -- Add foreign key project_id
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE
);


CREATE TABLE db_devops_discovery_tfs_repo_sourcecode (  
  source_code_id BIGINT PRIMARY KEY,  
  collection_name VARCHAR(200) NOT NULL,   
  repository_name VARCHAR(200),  
  branch_name VARCHAR(200),  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  last_modified_time TIMESTAMPTZ, 
  author VARCHAR(100), 
  sourcecode_comments VARCHAR(300), 
  commit_id BIGINT,	 
  commit_count INTEGER, 
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_devops_discovery_tfs_repo_commits (  
  commits_id BIGINT PRIMARY KEY,     
  commit_name VARCHAR(200) NOT NULL,  
  collection_name VARCHAR(200),
  branch_id BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches   
  commit_message VARCHAR(200),  
  author VARCHAR(200), 
  commit_date TIMESTAMPTZ , 
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails  
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE,  
  FOREIGN KEY (branch_id) REFERENCES  db_devops_discovery_tfs_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


CREATE TABLE db_devops_discovery_tfs_project_label (  
  label_id BIGINT PRIMARY KEY,     
  label_name VARCHAR(200) NOT NULL,  
  branch_id  BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches  
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (branch_id) REFERENCES  db_devops_discovery_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


CREATE TABLE db_devops_discovery_tfs_project_shelveset (  
  shelveset_id BIGINT PRIMARY KEY,  
  collection_name VARCHAR(200) NOT NULL,  
  repository_name VARCHAR(200),  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  FOREIGN KEY (project_id) REFERENCES  db_devops_discovery_tfs_project_projectdetails(project_id) ON DELETE CASCADE  
);





CREATE TABLE db_ado_git_project_projectdetails( 
  project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
  collection_name VARCHAR(200) NOT NULL, 
  project_name VARCHAR(200) NOT NULL, 
  project_path_name VARCHAR(200), 
  branch_name VARCHAR(200), 
  file_count INTEGER, 
  sheet_name VARCHAR(200), 
  created_by VARCHAR(50), 
  updated_by VARCHAR(50), 
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, 
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP 
); 

-- Trigger for updated_at to mimic ON UPDATE CURRENT_TIMESTAMP on the table db_git_project_projectdetails 

CREATE OR REPLACE FUNCTION db_ado_git_project_projectdetails_update_updated_at() 
RETURNS TRIGGER AS $$ 
BEGIN 
  NEW.updated_at = CURRENT_TIMESTAMP; 
  RETURN NEW; 
END; 
$$ LANGUAGE plpgsql; 

  

CREATE TRIGGER db_ado_git_project_projectdetails_set_updated_at
BEFORE UPDATE ON db_ado_git_project_projectdetails 
FOR EACH ROW 
EXECUTE FUNCTION db_ado_git_project_projectdetails_update_updated_at(); 


CREATE TABLE db_ado_git_project_root(   
  project_root_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   
  root_folder VARCHAR(200) NOT NULL,   
  project_folder VARCHAR(200) NOT NULL,   
  file_name VARCHAR(200),   
  file_type VARCHAR(200),   
  file_size INTEGER,   
  file_path VARCHAR(200),   
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_ado_git_project_repo (  
  project_repo_id BIGINT PRIMARY KEY,  
  repo_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_ado_git_project_branches (  
  project_branch_id BIGINT PRIMARY KEY,  
  branch_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key for project
  repo_id BIGINT NOT NULL,  -- Add foreign key repo
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (repo_id) REFERENCES  db_ado_git_project_repo(project_repo_id) ON DELETE CASCADE
); 

CREATE TABLE db_ado_git_project_workitems (  
  project_workitems_id BIGINT PRIMARY KEY,  
  workitem_name VARCHAR(200) ,
  workitem_type VARCHAR(200) ,  
  project_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE
); 

CREATE TABLE db_ado_git_project_boards (  
  project_board_id BIGINT PRIMARY KEY,  
  workitem_id Integer ,  
  workitem_status VARCHAR(100),  
  project_id BIGINT ,
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (workitem_id) REFERENCES  db_ado_git_project_workitems(project_workitems_id) ON DELETE CASCADE
);

CREATE TABLE db_ado_git_project_pipelines (  
  project_pipeline_id BIGINT PRIMARY KEY,  
  environments VARCHAR(100) ,  
  releases VARCHAR(100),
  libraries VARCHAR(100),
  task_groups VARCHAR(100),
  deployment_groups VARCHAR(100),
  project_id BIGINT , -- Add foreign key project_id
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE
);

CREATE TABLE db_ado_git_repo_sourcecode (  
  source_code_id BIGINT PRIMARY KEY,  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  last_modified_time TIMESTAMPTZ, 
  author VARCHAR(100), 
  sourcecode_comments VARCHAR(300), 
  commit_id BIGINT,	 
  commit_count INTEGER, 
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  branch_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE ,
  FOREIGN KEY (repo_id) REFERENCES  db_ado_git_project_repo(project_repo_id) ON DELETE CASCADE,
  FOREIGN KEY (branch_id) REFERENCES  db_ado_git_project_branches(project_branch_id) ON DELETE CASCADE
); 

CREATE TABLE db_ado_git_repo_commits (  
  commits_id BIGINT PRIMARY KEY,     
  commit_name VARCHAR(200) NOT NULL,  
  collection_name VARCHAR(200),
  branch_id BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches   
  commit_message VARCHAR(200),  
  author VARCHAR(200), 
  commit_date TIMESTAMPTZ , 
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (repo_id) REFERENCES  db_ado_git_project_repo(project_repo_id) ON DELETE CASCADE ,
  FOREIGN KEY (branch_id) REFERENCES  db_ado_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 

 
CREATE TABLE db_ado_git_repo_tags (  
  tags_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,     
  tags_name VARCHAR(200) NOT NULL,  
  branch_id  BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches  
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  repo_id BIGINT NOT NULL,  -- Add foreign key column to repo table
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (repo_id) REFERENCES  db_ado_git_project_repo(project_repo_id) ON DELETE CASCADE ,
  FOREIGN KEY (branch_id) REFERENCES  db_ado_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


------------------  For TFVC -----------------------------------

CREATE TABLE db_ado_tfs_project_projectdetails( 
  project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
  collection_name VARCHAR(200) NOT NULL, 
  project_name VARCHAR(200) NOT NULL, 
  project_path_name VARCHAR(200), 
  branch_name VARCHAR(200), 
  file_count INTEGER, 
  sheet_name VARCHAR(200), 
  created_by VARCHAR(50), 
  updated_by VARCHAR(50), 
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, 
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP 
); 


-- Trigger for updated_at to mimic ON UPDATE CURRENT_TIMESTAMP on the table db_tfs_project_projectdetails 

CREATE OR REPLACE FUNCTION db_ado_tfs_project_projectdetails_update_updated_at() 
RETURNS TRIGGER AS $$ 
BEGIN 
  NEW.updated_at = CURRENT_TIMESTAMP; 
  RETURN NEW; 
END; 
$$ LANGUAGE plpgsql; 

  

CREATE TRIGGER db_ado_tfs_project_projectdetails_set_updated_at
BEFORE UPDATE ON db_ado_tfs_project_projectdetails 
FOR EACH ROW 
EXECUTE FUNCTION db_ado_tfs_project_projectdetails_update_updated_at();

CREATE TABLE db_ado_tfs_project_root(   
  project_root_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   
  root_folder VARCHAR(200) NOT NULL,   
  project_folder VARCHAR(200) NOT NULL,   
  file_name VARCHAR(200),   
  file_type VARCHAR(200),   
  file_size INTEGER,   
  file_path VARCHAR(200),   
  project_id BIGINT NOT NULL,  -- Add foreign key column 
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE 
); 


CREATE TABLE db_ado_tfs_project_branches (  
  project_branch_id BIGINT PRIMARY KEY,  
  branch_name VARCHAR(200) NOT NULL,  
  root_folder VARCHAR(200) NOT NULL,  
  file_name VARCHAR(200),  
  file_type VARCHAR(200),  
  file_size INTEGER,  
  file_path VARCHAR (200) Unique , 
  project_id BIGINT NOT NULL,  -- Add foreign key for project
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE
  ); 

CREATE TABLE db_ado_tfs_project_workitems (  
  project_workitems_id BIGINT PRIMARY KEY,  
  workitem_name VARCHAR(200) ,
  workitem_type VARCHAR(200) ,  
  project_id BIGINT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE
); 


CREATE TABLE db_ado_tfs_project_boards (  
  project_board_id BIGINT PRIMARY KEY,  
  workitem_id Integer ,  
  workitem_status VARCHAR(100),  
  project_id BIGINT ,
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE,
  FOREIGN KEY (workitem_id) REFERENCES  db_ado_tfs_project_workitems(project_workitems_id) ON DELETE CASCADE
);

CREATE TABLE db_ado_tfs_project_pipelines (  
  project_pipeline_id BIGINT PRIMARY KEY,  
  environments VARCHAR(100) ,  
  releases VARCHAR(100),
  libraries VARCHAR(100),
  task_groups VARCHAR(100),
  deployment_groups VARCHAR(100),
  project_id BIGINT , -- Add foreign key project_id
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE
);


CREATE TABLE db_ado_tfs_repo_sourcecode (  
  source_code_id BIGINT PRIMARY KEY,  
  collection_name VARCHAR(200) NOT NULL,   
  repository_name VARCHAR(200),  
  branch_name VARCHAR(200),  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  last_modified_time TIMESTAMPTZ, 
  author VARCHAR(100), 
  sourcecode_comments VARCHAR(300), 
  commit_id BIGINT,	 
  commit_count INTEGER, 
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE 
); 

CREATE TABLE db_ado_tfs_repo_commits (  
  commits_id BIGINT PRIMARY KEY,     
  commit_name VARCHAR(200) NOT NULL,  
  collection_name VARCHAR(200),
  branch_id BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches   
  commit_message VARCHAR(200),  
  author VARCHAR(200), 
  commit_date TIMESTAMPTZ , 
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails  
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE,  
  FOREIGN KEY (branch_id) REFERENCES  db_ado_tfs_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


CREATE TABLE db_ado_tfs_project_label (  
  label_id BIGINT PRIMARY KEY,     
  label_name VARCHAR(200) NOT NULL,  
  branch_id  BIGINT NOT NULL,  -- Add foreign key column to db_git_project_branches  
  project_id BIGINT NOT NULL,  -- Add foreign key column to db_project_projectdetails
  FOREIGN KEY (project_id) REFERENCES  db_ado_git_project_projectdetails(project_id) ON DELETE CASCADE, 
  FOREIGN KEY (branch_id) REFERENCES  db_ado_git_project_branches(project_branch_id) ON DELETE CASCADE 
 ); 


CREATE TABLE db_ado_tfs_project_shelveset (  
  shelveset_id BIGINT PRIMARY KEY,  
  collection_name VARCHAR(200) NOT NULL,  
  repository_name VARCHAR(200),  
  file_name VARCHAR(200), 
  file_type VARCHAR(200),  
  folder_level VARCHAR(200), 
  sourcecode_path VARCHAR(300),  
  sourcecode_size INTEGER,  
  project_id BIGINT NOT NULL,  -- Add foreign key column to projectsdetails table 
  FOREIGN KEY (project_id) REFERENCES  db_ado_tfs_project_projectdetails(project_id) ON DELETE CASCADE  
);




CREATE TABLE db_devops_discovery_overview_dashboard_details( 
  overview_dashboard_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
  collection_name VARCHAR(200) NOT NULL, 
  project_name VARCHAR(200) NOT NULL,
  project_dashboard_id VARCHAR(200) ,
  project_dashboard_name VARCHAR(200), 
  description VARCHAR(200), 
  refresh_interval INTEGER, 
  project_dashboard_position Integer, 
  e_tag VARCHAR(50), 
  group_id VARCHAR(100),
  owner_id VARCHAR(100),
  dashboard_scopr VARCHAR(50)
  ); 

CREATE TABLE db_devops_discovery_boards_workitem_details( 
	discovery_boards_workitem_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	collection_name varchar(100),
  project_name varchar(100),
  workitem_name varchar(50),
	workitem_type   varchar(50),
  workitem_description varchar(200),
  workitem_assignee varchar(100),
  created_by varchar(50),
  created_date TIMESTAMPTZ,
  workitem_comment varchar(200),
	workitem_state varchar(50),
  workitem_links integer,
	workitem_tags varchar(50),
	total_count		Integer
	);

CREATE TABLE db_ado_discovery_boards_workitem_details( 
	discovery_boards_workitem_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	collection_name varchar(100),
  project_name varchar(100),
  workitem_name varchar(50),
	workitem_type   varchar(50),
  workitem_description varchar(200),
  workitem_assignee varchar(100),
  created_by varchar(50),
  created_date TIMESTAMPTZ,
  workitem_comment varchar(200),
	workitem_state varchar(50),
  workitem_links integer,
	workitem_tags varchar(50),
	total_count		Integer
	);



CREATE TABLE db_devops_discovery_release_details( 
	discovery_release_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	project_name varchar(100),
	collection_name varchar(100),
	release_id	Integer,
	release_name	varchar(50),
	created_date 	TIMESTAMPTZ,
	updated_date	TIMESTAMPTZ,
	release_variable integer,
	variable_groups		integer,
    no_of_relaseses integer,
    release_names TEXT, 
	artifacts		integer,
	Agents			varchar(100),
	parallel_execution_type varchar(100),
	max_agents	varchar(100),
    continueon_error BOOLEAN,
    concurrency_count integer,
    queuedepth_count integer

);

CREATE TABLE db_devops_discovery_pipelines_details( 
    discovery_pipelines_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(100),
    collection_name VARCHAR(100),
    pipeline_id INTEGER,
    pipeline_name VARCHAR(50),
    last_updated_date TIMESTAMPTZ,
    file_name VARCHAR(100),
    variables INTEGER,
    variable_groups VARCHAR(200), 
    repository_type VARCHAR(100),
    repository_name VARCHAR(100),
    repository_branch VARCHAR(100),    
    classic_pipeline TEXT,
    agents VARCHAR(100),
    phases TEXT,                     
    execution_type VARCHAR(50),      
    max_concurrency INTEGER,
    continue_on_error BOOLEAN,       
    builds INTEGER,                  
    artifacts TEXT                   
);


 CREATE TABLE db_devops_discovery_wiki_reports (
 	discovery_wiki_reports_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	file_path varchar(100),
	file_size Integer,
	last_modified_date	TIMESTAMPTZ
 );
 
 CREATE TABLE db_devops_discovery_pull_requests(
	discovery_pull_requests_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title	varchar(100),
	pr_description varchar(100),
	status		varchar(50),
	creation_date TIMESTAMPTZ,
	created_by		varchar(100),
	source_ref_name	varchar(100),
	target_ref_name	varchar(100),
	merge_status	varchar(50),
	merge_id		varchar(100),
	last_merge_commit_id varchar(100),
	reviewers	varchar(100)
 );

CREATE TABLE db_devops_discovery_project_configuration_Iterations(
	discovery_project_configuration_Iterations_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	collection_name varchar(200),
	project_name varchar(200),
	iteration_path varchar(200),
	iteration_id Integer,
	iteration_identifier varchar(200),
	start_date TIMESTAMPTZ,
	end_date TIMESTAMPTZ
	);
	
CREATE TABLE db_devops_discovery_project_configuration_Areas(
	discovery_project_configuration_Areas_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	collection_name varchar(200),
	project_name varchar(200),
	areas_path varchar(200),
	areas varchar(200),
	areas_id Integer,
	areas_identifier varchar(200)
	);

CREATE TABLE db_devops_ado_project_migration_details(
	devops_ado_migration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	source_server_url varchar(200),
	source_project_name varchar(200),
	source_pat varchar(200),
  target_organization_url varchar(200),
	target_project_name varchar(200),
	target_pat varchar(200)
	);



CREATE TABLE db_devops_discovery_user_details (
    collection_name varchar(200) NOT NULL,
    project_name varchar(200) NOT NULL,
    group_name varchar(100) ,
    group_type varchar(50) ,
    user_name varchar(200),
    user_email varchar(100),
    user_type varchar(50)
);
 
CREATE TABLE db_ados_discovery_user_details (
    collection_name varchar(200) NOT NULL,
    project_name varchar(200) NOT NULL,
    group_name varchar(100) ,
    group_type varchar(50) ,
    user_name varchar(200),
    user_email varchar(100),
    user_type varchar(50)
);

 