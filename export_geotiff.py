import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname='osmBerlinNov23',
    user='alexandra',
    host='localhost',
)

# Specify the ID of the raster you want to export
raster_id = 1

# SQL query to export raster to GeoTIFF
sql_query = sql.SQL("""
    SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';

    SELECT ST_AsTIFF(rast) AS raster_data
    FROM dummy_rast
""")

# Execute the query
with conn.cursor(cursor_factory=DictCursor) as cursor:
    cursor.execute(sql_query, (raster_id,))
    result = cursor.fetchone()

# Save the GeoTIFF to a file
if result:
    raster_data = result['raster_data'].tobytes()
    with open('tag_counts.tif', 'wb') as tiff_file:
        tiff_file.write(raster_data)

# Close the database connection
conn.close()

