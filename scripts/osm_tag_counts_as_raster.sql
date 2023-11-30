create extension postgis_raster;
SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';

/* 
 * Todo: filter nodes with tag surface or smoothness
 */
----------------------------------------------
--- create table of nodes with tag info ---
----------------------------------------------

-- drop table if it exists
DROP TABLE IF EXISTS node_tags;

-- create table
CREATE TABLE node_tags();

ALTER TABLE node_tags
ADD COLUMN IF NOT EXISTS way_id bigint NOT null,
ADD COLUMN IF NOT EXISTS surface char(100),
ADD COLUMN IF NOT EXISTS smoothness char(100);

-- add PostGIS geometry column
SELECT AddGeometryColumn('', 'node_tags', 'geom', 3857, 'GEOMETRY', 2);

-- add a linestring for every way (create a polyline)
INSERT INTO node_tags 
select ways.id,
ways.tags -> 'surface' as surface, 
ways.tags -> 'smoothness' as smoothness,
(select st_transform(nodes.geom, 3857) from nodes 
left join way_nodes on nodes.id=way_nodes.node_id where way_nodes.way_id=ways.id limit 1)
FROM ways
where ways.tags -> 'highway' <> '' and 
ways.tags -> 'surface' <> '' and
ways.tags -> 'smoothness' <> '';
-- takes 9 minutes for all of Germany (1 Mio tags)


----------------------------------------------
------------------ rasterize -----------------
----------------------------------------------

drop table dummy_rast ;

-- run in terminal: (to get dummy raster as table)
-- raster2pgsql -I -C -s 3857  germany_tile_raster_template.tif  dummy_rast | psql  -d osmGermany  -W


-- Add a spatial index for faster spatial queries
CREATE INDEX dummy_rast_gist
ON dummy_rast
USING gist (ST_ConvexHull(rast));

CREATE index if not exists node_tags_idx ON node_tags USING GIST(geom);


-- drop constraints that stop rasterization from working
ALTER TABLE dummy_rast DROP CONSTRAINT enforce_height_rast;
ALTER TABLE dummy_rast DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE dummy_rast DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE dummy_rast DROP CONSTRAINT enforce_width_rast;
ALTER TABLE dummy_rast DROP CONSTRAINT enforce_max_extent_rast;

UPDATE dummy_rast 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    --WHERE ST_Intersects(st_transform(mapillaryimg_small.wkb_geometry , 3857), rast::geometry)
);
-- rasterization of 90.000 points takes 30 seconds
-- rasterization of 1 Mio points takes 5 min


----------------- surface: asphalt ----------------------
-- TODO: rasterize by surface type
drop table asphalt_rast ;

-- run in terminal: (to get dummy raster as table)
-- raster2pgsql -I -C -s 3857  germany_tile_raster_template.tif  asphalt_rast | psql  -d osmGermany  -W


-- Add a spatial index for faster spatial queries
CREATE INDEX asphalt_rast_gist
ON asphalt_rast
USING gist (ST_ConvexHull(rast));

-- drop constraints that stop rasterization from working
ALTER TABLE asphalt_rast DROP CONSTRAINT enforce_height_rast;
ALTER TABLE asphalt_rast DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE asphalt_rast DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE asphalt_rast DROP CONSTRAINT enforce_width_rast;
ALTER TABLE asphalt_rast DROP CONSTRAINT enforce_max_extent_rast;

UPDATE asphalt_rast 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    where node_tags.surface = 'asphalt'
);

----------------- surface: paving stones ----------------------
-- TODO: rasterize by surface type
drop table pavstones_rast ;

-- run in terminal: (to get dummy raster as table)
-- raster2pgsql -I -C -s 3857  germany_tile_raster_template.tif  pavstones_rast | psql  -d osmGermany  -W


-- Add a spatial index for faster spatial queries
CREATE INDEX pavstones_rast_gist
ON pavstones_rast
USING gist (ST_ConvexHull(rast));

-- drop constraints that stop rasterization from working
ALTER TABLE pavstones_rast DROP CONSTRAINT enforce_height_rast;
ALTER TABLE pavstones_rast DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE pavstones_rast DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE pavstones_rast DROP CONSTRAINT enforce_width_rast;
ALTER TABLE pavstones_rast DROP CONSTRAINT enforce_max_extent_rast;

UPDATE pavstones_rast 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    where node_tags.surface = 'paving_stones'
);

----------------- surface: sett ----------------------
-- TODO: rasterize by surface type
drop table sett_rast ;

-- run in terminal: (to get dummy raster as table)
-- raster2pgsql -I -C -s 3857  germany_tile_raster_template.tif  asphalt_rast | psql  -d osmGermany  -W


-- Add a spatial index for faster spatial queries
CREATE INDEX sett_rast_gist
ON sett_rast
USING gist (ST_ConvexHull(rast));

-- drop constraints that stop rasterization from working
ALTER TABLE sett_rast DROP CONSTRAINT enforce_height_rast;
ALTER TABLE sett_rast DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE sett_rast DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE sett_rast DROP CONSTRAINT enforce_width_rast;
ALTER TABLE sett_rast DROP CONSTRAINT enforce_max_extent_rast;

UPDATE sett_rast 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    where node_tags.surface = 'sett' or node_tags.surface = 'cobblestone'
);


----------------- surface: unpaved ----------------------
-- TODO: rasterize by surface type
drop table unpaved_rast ;

-- run in terminal: (to get dummy raster as table)
-- raster2pgsql -I -C -s 3857  germany_tile_raster_template.tif  asphalt_rast | psql  -d osmGermany  -W


-- Add a spatial index for faster spatial queries
CREATE INDEX unpaved_rast_gist
ON unpaved_rast
USING gist (ST_ConvexHull(rast));

-- drop constraints that stop rasterization from working
ALTER TABLE unpaved_rast DROP CONSTRAINT enforce_height_rast;
ALTER TABLE unpaved_rast DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE unpaved_rast DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE unpaved_rast DROP CONSTRAINT enforce_width_rast;
ALTER TABLE unpaved_rast DROP CONSTRAINT enforce_max_extent_rast;

UPDATE unpaved_rast 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    WHERE node_tags.surface IN ('unpaved', 'compacted', 'gravel', 'ground', 'fine_gravel', 'dirt', 'grass')
   );



-- check stats
SELECT rid, (stats).*
FROM (SELECT rid, ST_SummaryStats(rast, 1) As stats
    FROM dummy_rast) as foo ;
    
SELECT rid, ST_AsText(ST_Envelope(rast)) As envgeomwkt
FROM dummy_rast;
