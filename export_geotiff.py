import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import database_credentials as db

## TODO: write entire script here

tag_counts_raster_path = 'data/unpaved_counts_germany.tif'
raster_name = "unpaved_rast"

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname=db.database,
    user=db.user,
    host=db.host,
)

# Specify the ID of the raster you want to export
raster_id = 1

# SQL query to export raster to GeoTIFF
sql_query = sql.SQL(f"""
    SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';

    SELECT ST_AsTIFF(rast) AS raster_data
    FROM {raster_name}
""")

# Execute the query
with conn.cursor(cursor_factory=DictCursor) as cursor:
    cursor.execute(sql_query, (raster_id,))
    result = cursor.fetchone()

# Save the GeoTIFF to a file
if result:
    raster_data = result['raster_data'].tobytes()
    with open(tag_counts_raster_path, 'wb') as tiff_file:
        tiff_file.write(raster_data)

# Close the database connection
conn.close()

