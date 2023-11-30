----------------------------------------------
--- create temp table for way LINESTRINGS ---
----------------------------------------------


-------------- selection per tile -----------------


-- drop table if it exists
drop table if exists way_geometry;
drop table if exists way_nodes_selection;
drop table if exists node_selection;
drop table if exists ways_selection;


CREATE TABLE node_selection AS
SELECT * FROM nodes WHERE ST_Within(
        geom,
         ST_MakeEnvelope({}, {}, {}, {}, 4326)
    ); 
   
CREATE INDEX node_selection_idx ON node_selection USING GIST(geom);

create table way_nodes_selection as
select * from way_nodes 
JOIN node_selection ON way_nodes.node_id = node_selection.id;

CREATE INDEX way_nodes_selection_idx ON way_nodes_selection USING GIST(geom);

create table ways_selection as
select ways.* 
from ways
JOIN way_nodes_selection ON ways.id = way_nodes_selection.way_id;


create table way_geometry  as
select id, ways_selection.tags->'surface' as surface, 
ways_selection.tags ->'smoothness' as smoothness, 
ways_selection.tags -> 'highway' as highway,
ways_selection.tags -> 'cycleway' as cycleway,
ways_selection.tags -> 'cycleway:surface' as cycleway_surface,
ways_selection.tags -> 'cycleway:smoothness' as cycleway_smoothness,
ways_selection.tags -> 'cycleway:right' as cycleway_right,
ways_selection.tags -> 'cycleway:right:surface' as cycleway_right_surface,
ways_selection.tags -> 'cycleway:right:smoothness' as cycleway_right_smoothness,
ways_selection.tags -> 'cycleway:left' as cycleway_left,
ways_selection.tags -> 'cycleway:left:surface' as cycleway_left_surface,
ways_selection.tags -> 'cycleway:left:smoothness' as cycleway_left_smoothness,
(select st_transform(ST_LineFromMultiPoint( ST_Collect(ns.geom)), 3035)  AS geom
from node_selection as ns join way_nodes_selection on ns.id=way_nodes_selection.node_id where way_nodes_selection.way_id=ways_selection.id ) 
FROM ways_selection 
where ways_selection.tags -> 'highway' <> '' and 
(ways_selection.tags -> 'surface' <> '' or ways_selection.tags -> 'cycleway:surface' <> '' or ways_selection.tags -> 'cycleway:right:surface' <> '' or ways_selection.tags -> 'cycleway:left:surface' <> '') 
and (ways_selection.tags -> 'smoothness' <> '' or ways_selection.tags -> 'cycleway:smoothness' <> '' or ways_selection.tags -> 'cycleway:right:smoothness' <> '' or ways_selection.tags -> 'cycleway:left:smoothness' <> '');




-- create buffer of 5 meters -> now its polygons instead of linestrings --
update way_geometry 
set geom = ST_Buffer(geom, 5);


-------------- intersect with mapillary -----------------


-------- create subset for faster intersection ------------

drop table if exists mapillary_selection;

CREATE TABLE mapillary_selection AS
SELECT * FROM mapillary_meta 
--where captured_at > 1672527600000 -- filter images only from this year (2023) - still > 1 Mio

where  ST_Within(
        mapillary_meta.geom,
         ST_MakeEnvelope({}, {}, {}, {}, 4326)
    ); 

drop table if exists mapillary_selection_labeled;

-- create new table as this is faster than update --
 CREATE TABLE mapillary_selection_labeled AS (
  SELECT mp.id, wg.surface, wg.smoothness, wg.highway, wg.cycleway, wg.cycleway_surface, wg.cycleway_smoothness, wg.cycleway_right, wg.cycleway_right_surface, wg.cycleway_right_smoothness, wg.cycleway_left, wg.cycleway_left_surface, wg.cycleway_left_smoothness
  FROM mapillary_selection mp
  JOIN way_geometry wg ON ST_Within(st_transform(mp.geom, 3035), wg.geom)
);

UPDATE mapillary_meta
SET surface = mapillary_selection_labeled.surface,
smoothness = mapillary_selection_labeled.smoothness,
highway = mapillary_selection_labeled.highway,
cycleway = mapillary_selection_labeled.cycleway,
cycleway_surface = mapillary_selection_labeled.cycleway_surface,
cycleway_smoothness = mapillary_selection_labeled.cycleway_smoothness,
cycleway_right = mapillary_selection_labeled.cycleway_right,
cycleway_right_surface = mapillary_selection_labeled.cycleway_right_surface,
cycleway_right_smoothness = mapillary_selection_labeled.cycleway_right_smoothness,
cycleway_left = mapillary_selection_labeled.cycleway_left,
cycleway_left_surface = mapillary_selection_labeled.cycleway_left_surface,
cycleway_left_smoothness = mapillary_selection_labeled.cycleway_left_smoothness
FROM mapillary_selection_labeled
WHERE mapillary_meta.id = mapillary_selection_labeled.id;
