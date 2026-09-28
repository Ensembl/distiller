-- View definitions
CREATE TABLE "dataset" (
    id VARCHAR NOT NULL UNIQUE,
    url_name VARCHAR NOT NULL UNIQUE,
    "name" VARCHAR NOT NULL,
    "source" VARCHAR NOT NULL
);

-- Filter groups linked to a dataset
CREATE TABLE filter_group (
    filter_group_id INTEGER PRIMARY KEY,
    "id" VARCHAR NOT NULL,
    "label" VARCHAR NOT NULL,
    rank INTEGER NOT NULL,
    FOREIGN KEY (view_id) REFERENCES view(view_id),
    UNIQUE(view_id, "id")
);

-- Filter definitions linked to a view via a group
CREATE TABLE filter (
    filter_id INTEGER PRIMARY KEY,
    filter_group_id INTEGER NOT NULL,
    "id" VARCHAR NOT NULL,
    "title" VARCHAR NOT NULL,
    "example" VARCHAR,
    "label" VARCHAR,
    filter_type VARCHAR NOT NULL,
    rank INTEGER NOT NULL,
    "min" DOUBLE,
    "max" DOUBLE,
    extras JSON,
    regex VARCHAR,
    UNIQUE("id"),
    FOREIGN KEY (filter_group_id) REFERENCES filter_group(filter_group_id)
);

-- Pre-computed filter values (only populated for select_list type)
CREATE TABLE filter_value (
    filter_id INTEGER NOT NULL,
    "value" VARCHAR NOT NULL,
    "label" VARCHAR NOT NULL,
    FOREIGN KEY (filter_id) REFERENCES filter(filter_id),
    UNIQUE(filter_id, value, label)
);

-- Column metadata and view association (merged column_def + view_column)
CREATE TABLE column (
    column_id INTEGER PRIMARY KEY,
    "name" VARCHAR NOT NULL,
    "label" VARCHAR NOT NULL,
    "type" VARCHAR NOT NULL,
    sortable BOOLEAN NOT NULL DEFAULT true,
    url VARCHAR,
    "delimiter" VARCHAR,
    hidden BOOLEAN NOT NULL DEFAULT false,
    rank INTEGER NOT NULL,
    mask UINT32 NOT NULL,
    enable_by_default BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (column, "name")
);

--CREATE TABLE IF NOT EXISTS view_column_link (
--    view_id INTEGER NOT NULL,
--    FOREIGN KEY (view_id) REFERENCES "view"(view_id)
--);

-- Release metadata
CREATE TABLE IF NOT EXISTS "release" (
    release_label VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL
);

-- Convenience view: resolves view filters with their config
CREATE VIEW filter_config AS
SELECT
    fg."id" AS group_id,
    fg."label" AS group_label,
    fg.rank AS group_rank,
    f.rank AS filter_rank,
    f.filter_id,
    f."id" AS filter_name,
    f."label" AS filter_label,
    f.filter_type,
    f."min",
    f."max",
    f.extras,
    f.regex
FROM filter f
    JOIN filter_group fg ON f.filter_group_id = fg.filter_group_id
ORDER BY fg.rank, f.rank;

-- Convenience view: resolves view columns with their metadata
CREATE VIEW column_config AS
SELECT
    c.rank AS column_rank,
    c.enable_by_default,
    c.hidden,
    c."name" AS column_name,
    c."label" AS column_label,
    c."type" AS column_type,
    c.sortable,
    c.url,
    c."delimiter"
FROM column c
ORDER BY c.rank;

-- Config payload views -----------------------------------------
CREATE OR REPLACE VIEW filter_values_as_json AS
SELECT
{
  "label":label,
  "value":value
}::json as values_json,
filter_id
FROM filter_value;


CREATE OR REPLACE VIEW filters_as_json AS SELECT {
  "id":f.id,
  "title":f.title,
  "label":f.label,
  "type":f.filter_type,
  "example":f.example,
  "min":f.min,
  "max":f.max,
  "regex":regexp_replace(vf.regex,'(\?[Pp]\<[a-zA-Z\_0-9\-]+\>)','','g'),
  "options":ARRAY(SELECT values_json FROM filter_values_as_json WHERE filter_id = f.filter_id )
}::json as filter_json, filter_group_id from filter as f;

CREATE OR REPLACE VIEW filter_groups_as_json AS SELECT {
  "id":vfg.id,
  "label":vfg.label,
  "filters":ARRAY(SELECT filter_json FROM filters_as_json where filter_group_id = fg.filter_group_id)
}::json AS group_json,
fg.view_id AS view_id
FROM filter_group AS vfg
ORDER BY fg.rank ASC;

CREATE OR REPLACE VIEW columns_as_json AS SELECT 
{
"id":column_id,
"label":label,
"is_sortable":sortable,
"enable_by_default":enable_by_default, 
}::json as col_json,
view_id
FROM column
WHERE hidden=false
ORDER BY rank ASC;

CREATE OR REPLACE VIEW dataset_config AS
SELECT {
"columns":ARRAY(SELECT col_json FROM columns_as_json), 
"filter_groups":ARRAY(SELECT group_json FROM filter_groups_as_json)
}::json AS json_config;

-- records payload views -------------
CREATE OR REPLACE VIEW column_details AS SELECT
name,
{
  "id":column_id,
  "name":name,
  "style":type,
  "label":"label",
  "sortable":sortable
} as details FROM column order by rank;


-- Macros

--- Column id to name macros

---- column_map generated during ETL run

-- filter marcos
CREATE MACRO select_list_filter(table_name, column_name, in_list) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE COLUMNS(column_name) in in_list
);

CREATE OR REPLACE MACRO select_exact_filter(table_name, column_name, selected_value) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE COLUMNS(column_name) = selected_value
);

CREATE OR REPLACE MACRO select_prefix_filter(table_name, column_name, selected_value) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE COLUMNS(column_name) LIKE concat(selected_value,'%')
);

CREATE OR REPLACE MACRO range_filter(table_name, column_name, range_start, range_end) AS TABLE(
    SELECT *
    FROM query_table(table_name)
    WHERE COLUMNS(column_name)::int between range_start and range_end
);
