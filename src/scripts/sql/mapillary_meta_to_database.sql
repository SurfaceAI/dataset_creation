
drop table if exists {table_name} ;

CREATE TABLE {table_name} (
	tile_id char(20),
    id bigint,
    sequence_id char(50),
    captured_at bigint,
    compass_angle double precision,
    is_pano bool,
    creator_id char(20),
    lon double precision,
    lat double precision
);

-- TODO: upload all mapillary metadata into  OSM ----
COPY {table_name} FROM '{absolute_path}' DELIMITER ',' CSV HEADER;

ALTER TABLE {table_name} ADD COLUMN surface char(50),
ADD COLUMN smoothness char(50),
ADD COLUMN highway char(50),
ADD COLUMN cycleway char(50),
ADD COLUMN cycleway_surface char(50),
ADD COLUMN cycleway_smoothness char(50),
ADD COLUMN cycleway_right char(50),
ADD COLUMN cycleway_right_surface char(50),
ADD COLUMN cycleway_right_smoothness char(50),
ADD COLUMN cycleway_left char(50),
ADD COLUMN cycleway_left_surface char(50),
ADD COLUMN cycleway_left_smoothness char(50),
ADD COLUMN cycleway_both char(50),
ADD COLUMN foot char(50),
ADD COLUMN distance int,
ADD COLUMN geom geometry(Point, 4326);

-- Update the geometry column using lat and lon
UPDATE {table_name} SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);

-- create index for faster intersections
CREATE INDEX {table_name}_idx ON {table_name} USING GIST(geom);
CREATE INDEX {table_name}_id_idx ON {table_name}(id);
