copy (select id, sequence_id , creator_id, captured_at, is_pano, highway, surface, smoothness,
cycleway,cycleway_surface,cycleway_smoothness,cycleway_right,cycleway_right_surface,cycleway_right_smoothness,
cycleway_left,cycleway_left_surface,cycleway_left_smoothness
from mapillary_meta where highway != '') TO '{}' DELIMITER ',' CSV HEADER;
