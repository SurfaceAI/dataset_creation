create extension IF NOT EXISTS postgis_raster;
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

-- Add a spatial index for faster spatial queries
CREATE INDEX {raster_name}_gist
ON {raster_name}
USING gist (ST_ConvexHull(rast));

CREATE index if not exists node_tags_idx ON node_tags USING GIST(geom);


-- drop constraints that stop rasterization from working
ALTER TABLE {raster_name} DROP CONSTRAINT enforce_height_rast;
ALTER TABLE {raster_name} DROP CONSTRAINT enforce_nodata_values_rast;
ALTER TABLE {raster_name} DROP CONSTRAINT enforce_pixel_types_rast;
ALTER TABLE {raster_name} DROP CONSTRAINT enforce_width_rast;
ALTER TABLE {raster_name} DROP CONSTRAINT enforce_max_extent_rast;

UPDATE {raster_name} 
SET rast = (
    SELECT ST_Union(ST_AsRaster(node_tags.geom, rast::raster),'COUNT')
    FROM node_tags
    WHERE node_tags.surface = '{surface}'

    --WHERE ST_Intersects(st_transform(mapillaryimg_small.wkb_geometry , 3857), rast::geometry)
);

-- -- check stats
-- SELECT rid, (stats).*
-- FROM (SELECT rid, ST_SummaryStats(rast, 1) As stats
--     FROM dummy_rast) as foo ;
    
-- SELECT rid, ST_AsText(ST_Envelope(rast)) As envgeomwkt
-- FROM dummy_rast;
