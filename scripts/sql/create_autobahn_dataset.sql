select * from ways where tags->'highway'='motorway';


select * from autobahn;

-- drop table if it exists
DROP TABLE IF EXISTS autobahn;

-- create table
CREATE TABLE autobahn(
  way_id bigint NOT NULL
);


-- add PostGIS geometry column
SELECT AddGeometryColumn('', 'autobahn', 'geom', 3035, 'GEOMETRY', 2);



-- add a linestring for every way (create a polyline)
INSERT INTO autobahn 
select id, (select st_transform(ST_LineFromMultiPoint( ST_Collect(nodes.geom)), 3035) from nodes 
left join way_nodes on nodes.id=way_nodes.node_id where way_nodes.way_id=ways.id ) FROM ways 
where ways.tags -> 'highway' = 'motorway';

-- add buffer of 10 meters --
update way_geometry 
set geom = ST_Buffer(geom, 10);
