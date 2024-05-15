## create csv with number of mapillary images for each tile in given bounding box
import sys
import time
import concurrent.futures
import csv
import mercantile

# setting path
sys.path.append("./")

# importing
import config
import constants as const
import src.utils as utils

tiles = []

def counts_per_tile(tile):
    tile_no = tiles.index(tile)
    if tile_no % 10 == 0:
        print(f"current tile number {tile_no}")

    data = utils.get_tile_images(tile)
    return len(data["features"])

def mapillary_image_counts_per_tile(out_path, bbox, num_threads = 8):
    global tiles
    start = time.time()
    tiles = list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], config.zoom))

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Using executor.map to parallelize the function
        results = list(executor.map(counts_per_tile, tiles))

    with open(out_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["x", "y", "z", "lat", "lon", "image_count"])
        for i in range(0, len(tiles)):
            tile = tiles[i]
            image_count = results[i]
            lon, lat = utils.tile_center(tile.x, tile.y, config.zoom)
            csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon, image_count])

    end = time.time()
    print(f"{(end - start)/60} minutes")


if __name__ == "__main__":
    mapillary_image_counts_per_tile(config.germany_tiles_path, const.BBOX_GERMANY)

    # 21 minutes for 793 tiles
    # 7 minutes for 793 tiles with 4 threads
    # 293 minutes (ca. 5h) for Germany (235.478 tiles) with 8 threads
