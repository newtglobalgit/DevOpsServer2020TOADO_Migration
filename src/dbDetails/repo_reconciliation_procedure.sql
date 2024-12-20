CREATE OR REPLACE PROCEDURE execute_reconciliation(
    IN reconciliation_item TEXT, 
    OUT output_data JSON
)
LANGUAGE plpgsql
AS $$
DECLARE
    -- Cursors for mapping and discovery tables
    src_cursor CURSOR FOR SELECT source_project_name, source_repo_name, source_branch_name 
                          FROM devops_to_ados.db_repo_mapping
                          ORDER BY source_project_name, source_repo_name, source_branch_name;

    tgt_cursor CURSOR FOR SELECT target_project_name, target_repo_name, target_branch_name 
                          FROM devops_to_ados.db_repo_mapping
                          ORDER BY target_project_name, target_repo_name, target_branch_name;

    -- Cursors for discovery and reconciliation steps
    source_discovery_cursor CURSOR FOR
        SELECT collection_name, project_name, repository_name, branch_name
        FROM devops_to_ados.db_devops_discovery_git_repo_sourcecode
        WHERE migration_required = 'yes'
        ORDER BY collection_name, project_name, repository_name, branch_name;

    target_discovery_cursor CURSOR FOR
        SELECT collection_name, project_name, repository_name, branch_name
        FROM devops_to_ados.db_ado_discovery_git_repo_sourcecode
        WHERE migration_required = 'yes'
        ORDER BY collection_name, project_name, repository_name, branch_name;

    -- Variables to store row data and output JSON
    src_row RECORD;
    tgt_row RECORD;
    valid_data JSONB := '[]'::JSONB;

    -- Error Handling Variables
    no_data_found BOOLEAN := FALSE;
    err_mesg TEXT := '';

    -- Temporary Variables
    source_exists BOOLEAN := FALSE;
    target_exists BOOLEAN := FALSE;

BEGIN
    -- Step 0: Validate reconciliation item
    IF reconciliation_item <> 'REPO_RECONCILITION' THEN
        RAISE EXCEPTION 'Unknown reconciliation item: %', reconciliation_item;
    END IF;

    -- Step 1: Process source and target mappings
    OPEN src_cursor;
    OPEN tgt_cursor;

    LOOP
        FETCH src_cursor INTO src_row;
        FETCH tgt_cursor INTO tgt_row;
        EXIT WHEN NOT FOUND;

        -- Check if data exists in discovery tables
        SELECT EXISTS (
            SELECT 1 
            FROM devops_to_ados.db_devops_discovery_git_repo_sourcecode
            WHERE project_name = src_row.source_project_name 
              AND repository_name = src_row.source_repo_name 
              AND branch_name = src_row.source_branch_name
        ) INTO source_exists;

        SELECT EXISTS (
            SELECT 1 
            FROM devops_to_ados.db_ado_discovery_git_repo_sourcecode
            WHERE project_name = tgt_row.target_project_name 
              AND repository_name = tgt_row.target_repo_name 
              AND branch_name = tgt_row.target_branch_name
        ) INTO target_exists;

        -- If both source and target exist, add to valid data
        IF source_exists AND target_exists THEN
            valid_data := jsonb_insert(
                valid_data,
                '{-1}',
                jsonb_build_object(
                    'source_project', src_row.source_project_name,
                    'source_repo', src_row.source_repo_name,
                    'source_branch', src_row.source_branch_name,
                    'target_project', tgt_row.target_project_name,
                    'target_repo', tgt_row.target_repo_name,
                    'target_branch', tgt_row.target_branch_name
                )
            );
        END IF;
    END LOOP;

    CLOSE src_cursor;
    CLOSE tgt_cursor;

    -- Step 2: Compare item size branch-wise
    PERFORM compare_branch_data(
        'devops_to_ados.db_devops_discovery_git_repo_sourcecode',
        'devops_to_ados.db_ado_discovery_git_repo_sourcecode',
        'item_size',
        'total_size'
    );

    

    -- Step 3: Compare commit counts branch-wise
    PERFORM compare_branch_data(
        'devops_to_ados.db_devops_discovery_git_repo_commits',
        'devops_to_ados.db_ado_discovery_git_repo_commits',
        'commit_id',
        'commit_count'
    );

    -- Step 4: Compare tag counts repository-wise
    PERFORM compare_repo_data(
        'devops_to_ados.db_devops_discovery_git_repo_tags',
        'devops_to_ados.db_ado_discovery_git_repo_tags',
        'tag_id',
        'tag_count'
    );

    -- Final Output
    IF valid_data = '[]'::JSONB THEN
        output_data := jsonb_build_object(
            'status', 'FAILED',
            'message', 'No valid mappings found for reconciliation.'
        );
    ELSE
        output_data := jsonb_build_object(
            'status', 'SUCCESS',
            'valid_data', valid_data
        );
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'An error occurred: %', SQLERRM;
        output_data := jsonb_build_object(
            'status', 'FAILED',
            'error', SQLERRM
        );
END;
$$;
