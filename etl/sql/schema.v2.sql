-- View definitions
CREATE TABLE "view" (
    view_id INTEGER PRIMARY KEY,
    id VARCHAR NOT NULL UNIQUE,
    url_name VARCHAR NOT NULL UNIQUE,
    "name" VARCHAR NOT NULL,
    "source" VARCHAR NOT NULL
);

-- Filter groups linked to a view
CREATE TABLE view_filter_group (
    view_filter_group_id INTEGER PRIMARY KEY,
    view_id INTEGER NOT NULL,
    "id" VARCHAR NOT NULL,
    "label" VARCHAR NOT NULL,
    rank INTEGER NOT NULL,
    FOREIGN KEY (view_id) REFERENCES view(view_id),
    UNIQUE(view_id, "id")
);

-- Filter definitions linked to a view via a group
CREATE TABLE view_filter (
    view_filter_id INTEGER PRIMARY KEY,
    view_filter_group_id INTEGER NOT NULL,
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
    FOREIGN KEY (view_filter_group_id) REFERENCES view_filter_group(view_filter_group_id)
);

-- Pre-computed filter values (only populated for select_list type)
CREATE TABLE view_filter_value (
    view_filter_id INTEGER NOT NULL,
    "value" VARCHAR NOT NULL,
    "label" VARCHAR NOT NULL,
    FOREIGN KEY (view_filter_id) REFERENCES view_filter(view_filter_id),
    UNIQUE(view_filter_id, value, label)
);

-- Column metadata and view association (merged column_def + view_column)
CREATE TABLE view_column (
    view_column_id INTEGER PRIMARY KEY,
    view_id INTEGER NOT NULL,
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
    FOREIGN KEY (view_id) REFERENCES "view"(view_id),
    UNIQUE (view_id, "name")
);

CREATE TABLE IF NOT EXISTS view_column_link (
    view_id INTEGER NOT NULL,
    FOREIGN KEY (view_id) REFERENCES "view"(view_id)
);

-- Release metadata
CREATE TABLE IF NOT EXISTS "release" (
    release_label VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL
);

-- Convenience view: resolves view filters with their config
CREATE VIEW filter_config AS
SELECT
    v.view_id as view_dbid,
    v.id as view_id,
    v.url_name AS view_url_name,
    v."name" AS view_name,
    v."source" AS source,
    vfg."id" AS group_id,
    vfg."label" AS group_label,
    vfg.rank AS group_rank,
    vf.rank AS filter_rank,
    vf.view_filter_id,
    vf."id" AS filter_name,
    vf."label" AS filter_label,
    vf.filter_type,
    vf."min",
    vf."max",
    vf.extras,
    vf.regex
FROM view_filter vf
    JOIN view_filter_group vfg ON vf.view_filter_group_id = vfg.view_filter_group_id
    JOIN "view" v ON vfg.view_id = v.view_id
ORDER BY v.view_id, vfg.rank, vf.rank;

-- Convenience view: resolves view columns with their metadata
CREATE VIEW column_config AS
SELECT
    v.view_id,
    v.url_name AS view_url_name,
    v."name" AS view_name,
    v."source" AS source,
    vc.rank AS column_rank,
    vc.enable_by_default,
    vc.hidden,
    vc."name" AS column_name,
    vc."label" AS column_label,
    vc."type" AS column_type,
    vc.sortable,
    vc.url,
    vc."delimiter"
FROM view_column vc
    JOIN "view" v ON vc.view_id = v.view_id
ORDER BY v.view_id, vc.rank;

-- Config payload views -----------------------------------------
CREATE OR REPLACE VIEW filter_values_as_json AS
SELECT
{
  "label":label,
  "value":value
}::json as values_json,
view_filter_id
FROM view_filter_value;


CREATE OR REPLACE VIEW filters_as_json AS SELECT {
  "id":vf.id,
  "title":vf.title,
  "label":vf.label,
  "type":vf.filter_type,
  "example":vf.example,
  "min":vf.min,
  "max":vf.max,
  "regex":regexp_replace(vf.regex,'(\?[Pp]\<[a-zA-Z\_0-9\-]+\>)','','g'),
  "options":ARRAY(SELECT values_json FROM filter_values_as_json WHERE view_filter_id = vf.view_filter_id )
}::json as filter_json, view_filter_group_id from view_filter as vf;

CREATE OR REPLACE VIEW filter_groups_as_json AS SELECT {
  "id":vfg.id,
  "label":vfg.label,
  "filters":ARRAY(SELECT filter_json FROM filters_as_json where view_filter_group_id = vfg.view_filter_group_id)
}::json AS group_json,
vfg.view_id AS view_id
FROM view_filter_group AS vfg
ORDER BY vfg.rank ASC;

CREATE OR REPLACE VIEW columns_as_json AS SELECT 
{
"id":view_column_id,
"label":label,
"is_sortable":sortable,
"enable_by_default":enable_by_default, 
}::json as col_json,
view_id
FROM view_column
WHERE hidden=false
ORDER BY rank ASC;

CREATE OR REPLACE VIEW dataset_config AS
SELECT {
"columns":ARRAY(SELECT col_json FROM columns_as_json where view_id = view.view_id), 
"filter_groups":ARRAY(SELECT group_json FROM filter_groups_as_json where view_id = view.view_id)
}::json AS json_config,
view_id
FROM view;

-- records payload views -------------
CREATE OR REPLACE VIEW column_details AS SELECT
name,
{
  "id":view_column_id,
  "name":name,
  "style":type,
  "label":"label",
  "sortable":sortable
} as details FROM view_column order by rank;


-- Macros

--- Column id to name macros

---- column_map generated during ETL run
create macro column_mapper(ids) AS
(SELECT list_transform(ids, lambda c : column_map(c)))

--- Mask to column name macros
CREATE MACRO mask_set(i) AS floor(i / 28); -- used to generate bit mask set
CREATE MACRO col_mask(i)  AS (mask_set(i)::UINT32 << 28) + (1 << (i - (mask_set(i) * 28))::UINT32); -- convert a index into a mask
CREATE MACRO get_view_columns(view_source, target_mask) AS -- returns a list of columns based on a mask
(
  SELECT list(vc."name" ORDER BY vc.rank ASC) from view_column as vc JOIN "view" as v on v.view_id = vc.view_id
  where target_mask::UINT32 & vc.mask and v."source" = view_source
);
CREATE OR REPLACE MACRO get_view_default_columns(view_source) AS -- returns a list of default columns
(
  SELECT list(vc."name" ORDER BY vc.rank ASC) from view_column as vc JOIN "view" as v on v.view_id = vc.view_id
  where vc.enable_by_default and v."source" = view_source
);
CREATE OR REPLACE MACRO get_view_default_column_masks(view_source) AS -- returns a list of column masks
(
  SELECT list(vc.mask ORDER BY vc.rank ASC) from view_column as vc JOIN "view" as v on v.view_id = vc.view_id
  where vc.enable_by_default and v."source" = view_source
);

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