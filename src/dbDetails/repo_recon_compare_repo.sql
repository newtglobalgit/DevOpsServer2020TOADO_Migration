CREATE OR REPLACE FUNCTION compare_repo_data(
    source_table TEXT,
    target_table TEXT,
    comparison_column TEXT,
    metric_name TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    source_count INT;
    target_count INT;
BEGIN
    -- Iterate through repositories in the source table
    FOR src_row IN 
        EXECUTE FORMAT(
            'SELECT DISTINCT collection_name, project_name, repository_name 
             FROM %I 
             WHERE migration_required = ''yes''', 
             source_table
        ) 
    LOOP
        -- Fetch count for the repository from source table
        EXECUTE FORMAT(
            'SELECT COUNT(DISTINCT %I) 
             FROM %I 
             WHERE collection_name = $1 AND project_name = $2 
               AND repository_name = $3',
            comparison_column, source_table
        )
        INTO source_count
        USING src_row.collection_name, src_row.project_name, src_row.repository_name;

        -- Fetch count for the repository from target table
        EXECUTE FORMAT(
            'SELECT COUNT(DISTINCT %I) 
             FROM %I 
             WHERE collection_name = $1 AND project_name = $2 
               AND repository_name = $3',
            comparison_column, target_table
        )
        INTO target_count
        USING src_row.collection_name, src_row.project_name, src_row.repository_name;

        -- Compare counts and log discrepancies
        IF source_count <> target_count THEN
            RAISE NOTICE 'Discrepancy in % between source and target: Project=% Repo=% Source=% Target=%', 
                         metric_name, src_row.project_name, src_row.repository_name, source_count, target_count;
        END IF;
    END LOOP;
END;
$$;
