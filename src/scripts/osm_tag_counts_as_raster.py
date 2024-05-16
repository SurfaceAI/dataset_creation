import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))
sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))

import config as config
import database_credentials as db


def create_osm_tag_count_tif(surface, smoothness):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname=db.database,
        user=db.user,
        host=db.host,
    )
    with open(config.sql_script_osm_tags_to_raster_counts_path, "r") as file:
        query_template = file.read()

    with conn.cursor(cursor_factory=DictCursor) as cursor:
        raster_name = f"{surface}_{smoothness}_rast"

        # get raster based on template as table
        cursor.execute(sql.SQL(f"DROP TABLE IF EXISTS {raster_name};"))
        conn.commit()
        # TODO: currently, the password for the database needs to be entered manually (press enter if no password set)!
        os.system(
            f"raster2pgsql -I -C -s 3857  {config.germany_raster_template_path}  {raster_name} | psql  -d {db.database}  -W"
        )

        # run query for surface
        query = query_template.format(
            surface=surface, smoothness=smoothness, raster_name=raster_name
        )
        cursor.execute(sql.SQL(query))
        conn.commit()

        # export as geotiff
        # Specify the ID of the raster you want to export
        raster_id = 1

        # SQL query to export raster to GeoTIFF
        sql_query = sql.SQL(
            f"""
            SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';

            SELECT ST_AsTIFF(rast) AS raster_data
            FROM {raster_name}
        """
        )

        cursor.execute(sql_query, (raster_id,))
        conn.commit()
        result = cursor.fetchone()

        # Save the GeoTIFF to a file
        if result:
            raster_data = result["raster_data"].tobytes()
            with open(
                config.surf_smooth_tag_counts_path.format(surface, smoothness), "wb"
            ) as tiff_file:
                tiff_file.write(raster_data)

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    for surface in config.surfaces:
        for smoothness in config.surf_smooth_comb[surface]:
            create_osm_tag_count_tif(surface, smoothness)
