
drop table if exists mapillary_meta ;

CREATE TABLE mapillary_meta (
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
COPY mapillary_meta FROM '{}' DELIMITER ',' CSV HEADER;

ALTER TABLE mapillary_meta ADD COLUMN surface char(50);
ALTER TABLE mapillary_meta ADD COLUMN smoothness char(50);
ALTER TABLE mapillary_meta ADD COLUMN highway char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_surface char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_smoothness char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_right char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_right_surface char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_right_smoothness char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_left char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_left_surface char(50);
ALTER TABLE mapillary_meta ADD COLUMN cycleway_left_smoothness char(50);
ALTER TABLE mapillary_meta ADD COLUMN distance int;


-- Add a new geometry column
ALTER TABLE mapillary_meta ADD COLUMN geom geometry(Point, 4326);

-- Update the geometry column using lat and lon
UPDATE mapillary_meta SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);
