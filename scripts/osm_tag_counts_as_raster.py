import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

# setting path
import sys

sys.path.append("./")

# importing
import config
import constants as const
import database_credentials as db

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname=db.database,
    user=db.user,
    host=db.host,
)
with open(config.sql_script_osm_tags_to_raster_counts_path, "r") as file:
    query_template = file.read()

with conn.cursor(cursor_factory=DictCursor) as cursor:
    surfaces = [
        const.ASPHALT,
        const.CONCRETE,
        const.PAVING_STONES,
        const.SETT,
        const.UNPAVED,
    ]
    for surface in surfaces:
        raster_name = f"{surface}_rast"
        tag_counts_raster_path = f"data/tag_counts/{surface}_counts_germany.tif"

        # get raster based on template as table
        cursor.execute(sql.SQL(f"DROP TABLE IF EXISTS {raster_name};"))
        conn.commit()
        # TODO: currently, the password for the database needs to be entered manually (press enter if no password set)!
        os.system(
            f"raster2pgsql -I -C -s 3857  data/tag_counts/germany_tile_raster_template.tif  {raster_name} | psql  -d {db.database}  -W"
        )

        # run query for surface
        query = query_template.format(surface=surface, raster_name=raster_name)
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
            with open(tag_counts_raster_path, "wb") as tiff_file:
                tiff_file.write(raster_data)

# Close the database connection
conn.close()
