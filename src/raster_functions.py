from PIL import Image
import numpy as np
import mercantile

import rasterio
from rasterio.transform import from_origin
from rasterio.features import rasterize
import rasterstats

import pandas as pd
import geopandas as gpd

import config


def read_raster(raster_path):
    """read raster image from path and return values as numpy array

    Args:
        raster_path (str): path to raster image

    Returns:
        np.array: raster values as numpy array
    """
    # Open image
    im = Image.open(raster_path)
    return np.array(im)


def create_raster(
    xmin, xmax, ymin, ymax, crs, output_path, nrows=False, ncols=False, resolution=False
):
    """create raster based on bounding box coordinates, crs, output_path, and either nrows, ncols, or resolution.
    Args:
        xmin (float): xmin coordinate of bounding box (in given CRS)
        xmax (float): xmax coordinate of bounding box (in given CRS)
        ymin (float): ymin coordinate of bounding box (in given CRS)
        ymax (float): ymax coordinate of bounding box (in given CRS)
        crs (str): crs of target raster in format 'epsg:xxxx'
        output_path (str): path to save raster to
        nrows (int, optional): number of rows of target raster. Defaults to False.
        ncols (int, optional): number of columns of target raster. Defaults to False.
        resolution (int, optional): resolution in unit of target CRS. Either use resolution OR nrows&ncols. Defaults to False.
    """

    if nrows and ncols:
        # Calculate cell size
        cell_size_x = (xmax - xmin) / ncols
        cell_size_y = (ymax - ymin) / nrows

        # Define transform
        transform = from_origin(xmin, ymax, cell_size_x, cell_size_y)

    elif resolution:
        # Calculate number of columns and rows
        ncols = int((xmax - xmin) / resolution)
        nrows = int((ymax - ymin) / resolution)

        # Define transform
        transform = from_origin(xmin, ymax, resolution, resolution)

    if nrows and ncols:
        # Create raster
        dsw = rasterio.open(
            output_path,
            "w",
            driver="GTiff",
            height=nrows,
            width=ncols,
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
        )
        dsw.close()
    else:
        print("either nrows and ncols or resolution must be specified")


def raster_to_tiledf(raster_path):
    """Return a dataframe from a raster image. Currently 'osmtag_count' is the hardcoded raster layer name.

    Args:
        raster_path (str): path to raster image

    Returns:
        df: dataframe with columns x, y, and osmtag_count (value of raster)
    """
    with rasterio.open(raster_path) as src:
        # Read raster values
        band1 = src.read(1)
        height = band1.shape[0]
        width = band1.shape[1]
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        xs, ys = rasterio.transform.xy(src.transform, rows, cols)
        xs = np.array(xs).flatten()
        ys = np.array(ys).flatten()
        df = gpd.GeoDataFrame(
            {"osmtag_count": band1.flatten()},
            geometry=gpd.points_from_xy(xs, ys),
            crs=src.crs,
        )
        # Convert geometry to lat/lon
        df = df.to_crs("EPSG:4326")
        # Extract lat and lon
        df["lon"] = df.geometry.x
        df["lat"] = df.geometry.y
        # Drop geometry column and convert to pd.DataFrame
        df.drop(columns="geometry", inplace=True)
        df = pd.DataFrame(df)
        # Convert NaNs to zeros
        df.fillna(0, inplace=True)

        tiles_x_y = df.apply(
            lambda row: mercantile.tile(row["lon"], row["lat"], config.zoom), axis=1
        )
        df["x"] = [tiles_x_y.iloc[i][0] for i in range(0, len(tiles_x_y))]
        df["y"] = [tiles_x_y.iloc[i][1] for i in range(0, len(tiles_x_y))]
        df["tile_id"] = (
            df["x"].astype(str) + "_" + df["y"].astype(str) + "_" + str(config.zoom)
        )
        return df


def rasterize_points(raster_path, data_path, crs, output_path, fun="max"):
    """Create and store a raster from a csv point dataset, where each point represents one raster centroid and the value "image_count" the respective value to create a raster from.
    Currently 'image_count' is the hardcoded field name which is expected in the dataset.

    Args:
        raster_path (str): path to raster template to rasterize points to
        data_path (str): path to csv point dataset
        crs (int): crs of raster template dataset as EPSG code
        output_path (str): path to save raster to (.tif)
        fun (str, optional): function to apply to rasterize points. Defaults to "max".
    """
    # Read raster template
    with rasterio.open(raster_path) as src:
        # Read data points
        data = pd.read_csv(data_path)
        data = gpd.GeoDataFrame(
            data, geometry=gpd.points_from_xy(data["lon"], data["lat"]), crs=4326
        )
        # Reproject if needed
        if data.crs != crs:
            data = data.to_crs(crs)

        # Rasterize based on the function
        if fun == "max":
            agg_func = (
                rasterio.enums.MergeAlg.replace
            )  # TODO: max not inplemented in rasterio?
        elif fun == "sum":
            agg_func = rasterio.enums.MergeAlg.add
        else:
            raise ValueError("fun must be either 'max' or 'sum'")

        shape = src.shape
        data = data.reset_index(drop=True)
        geom_value = (
            (geom, value) for geom, value in zip(data.geometry, data["image_count"])
        )

        # Create rasterized array
        rasterized = rasterize(
            geom_value,
            out_shape=shape,
            transform=src.transform,
            all_touched=True,
            default_value=0,
            dtype=src.dtypes[0],
            merge_alg=agg_func,
        )

        # Write raster
        with rasterio.open(
            output_path,
            "w",
            driver="GTiff",
            height=shape[0],
            width=shape[1],
            count=1,
            dtype=src.dtypes[0],
            crs=crs,
            transform=src.transform,
        ) as dst:
            dst.write(rasterized, 1)

        return rasterized


def raster_ids_for_points(raster_path, data_path, output_path, crs):
    """Create table and write a csv with a column that contains the respective raster cell ids for each point in the dataset.
    Args:
        raster_path (str): path to raster template to get raster cell ids from
        data_path (str): path to point dataset to get raster cell ids for
        output_path (str): path to save csv to
        crs (int): crs of raster template as EPSG code

    """
    with rasterio.open(raster_path) as src:
        bnd = src.read(1)
        # Read data points
        data = pd.read_csv(data_path)
        data = gpd.GeoDataFrame(
            data, geometry=gpd.points_from_xy(data["lon"], data["lat"]), crs=4326
        )
        # Reproject if needed
        if data.crs != crs:
            data = data.to_crs(crs)

        # Extract raster cell_id for each point
        data["cell_ids"] = rasterstats.point_query(
            data,
            np.arange(0, bnd.shape[0] * bnd.shape[1]).reshape(
                bnd.shape[0], bnd.shape[1]
            ),
            nodata=None,
            affine=src.transform,
            interpolate="nearest",
        )

        # Add columns for lat and lon
        data["lon"] = data.geometry.x
        data["lat"] = data.geometry.y

        # Write to CSV
        data[["cell_ids", "lon", "lat"]].to_csv(output_path, index=False)
