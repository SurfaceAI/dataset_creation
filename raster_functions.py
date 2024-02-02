import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from PIL import Image
import numpy as np
import mercantile

import utils
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


# function to create a raster template
def create_raster(
    xmin, xmax, ymin, ymax, crs, output_path, nrows=False, ncols=False, resolution=False
):
    """create rasster based on bounding box coordinates, crs, output_path, and either nrows, ncols, or resolution.
    Wrapper for

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
    robjects.r(
        """
    library(terra)|> suppressPackageStartupMessages()
    library(sf)|> suppressPackageStartupMessages()
            
    create_raster_rows_cols <- function(xmin, xmax, ymin, ymax, crs, output_path, nrows, ncols){
        raster_template <- terra::rast(crs= terra::crs(crs), 
                                        xmin= xmin,
                                        xmax= xmax,
                                        ymin= ymin,
                                        ymax= ymax,
                                        ncols = ncols,
                                        nrows = nrows,
                                        vals= 0)

        terra::writeRaster(raster_template, output_path, overwrite=TRUE)
    }
               
    create_raster_res <- function(xmin, xmax, ymin, ymax, crs, output_path,resolution){
        raster_template <- terra::rast(crs= terra::crs(crs), 
                                        xmin= xmin,
                                        xmax= xmax,
                                        ymin= ymin,
                                        ymax= ymax,
                                        resolution = resolution,
                                        vals= 0)

        terra::writeRaster(raster_template, output_path, overwrite=TRUE)
    }
    """
    )
    if nrows and ncols:
        create_raster_R = robjects.globalenv["create_raster_rows_cols"]
        return create_raster_R(
            xmin, xmax, ymin, ymax, crs, output_path, nrows=nrows, ncols=ncols
        )
    elif resolution:
        create_raster_R = robjects.globalenv["create_raster_res"]
        return create_raster_R(
            xmin, xmax, ymin, ymax, crs, output_path, resolution=resolution
        )
    else:
        print("either nrows and ncols or resolution must be specified")


def raster_to_tiledf(raster_path):
    """Return a dataframe from a raster image. Currently 'osmtag_count' is the hardcoded raster layer name.

    Args:
        raster_path (str): path to raster image

    Returns:
        df: dataframe with columns x, y, and osmtag_count (value of raster)
    """
    # get raster cell centroids with values
    # centroid to x y z
    robjects.r(
        """
    library(terra)|> suppressPackageStartupMessages()
    library(sf)|> suppressPackageStartupMessages()
                   
    raster_to_tiledf <- function(raster_path){
        raster <- rast(raster_path)
        all_cells <- cellFromRowColCombine(raster, c(1:nrow(raster)), c(1:ncol(raster)))
        coord_pairs <- xyFromCell(raster, all_cells)
        coords4326 <- st_as_sf(data.frame(x = coord_pairs[,1], y = coord_pairs[,2]), coords = c("x", "y"), crs = 3857) |> 
                        sf::st_transform(4326)    
        values <- values(raster)

        df <- data.frame(st_coordinates(coords4326), values)
        names(df) <- c('lon', 'lat', 'osmtag_count')
        return(df)
        }
    """
    )

    raster_to_tiledf_R = robjects.globalenv["raster_to_tiledf"]
    df = raster_to_tiledf_R(raster_path)
    with (robjects.default_converter + pandas2ri.converter).context():
        df = robjects.conversion.get_conversion().rpy2py(df)

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
    """Create and store a raster from a point dataset (r wrapper), where each point represents one raster centroid and the value "image_count" the respective value to create a raster from.
    Currently 'image_count' is the hardcoded field name which is expected in the dataset.

    Args:
        raster_path (str): path to raster template to rasterize points to
        data_path (str): path to csv point dataset
        crs (int): crs of raster template dataset as EPSG code
        output_path (str): path to save raster to (.tif)
        fun (str, optional): function to apply to rasterize points. Defaults to "max".
    """

    robjects.r(
        """

    rasterize_points <- function(raster_path, data_path, crs, output_path, fun){
        library(sf)
               
        raster_template <- terra::rast(raster_path)
        data <- readr::read_csv(data_path, show_col_types = F)|> 
            st_as_sf( coords = c("lon", "lat"), crs = 4326)|> 
            sf::st_transform(crs)

        if (fun == "max"){
        raster_template <- terra::rasterize(data, raster_template, field="image_count", fun=max)
        } else if (fun == "sum"){
            raster_template <- terra::rasterize(data, raster_template, fun=sum)
        } else {
            stop("fun must be either 'max' or 'count'")
        }
               
        terra::writeRaster(raster_template, output_path, overwrite=TRUE)
        
        }
    """
    )

    rasterize_points_R = robjects.globalenv["rasterize_points"]
    return rasterize_points_R(raster_path, data_path, crs, output_path, fun)


def raster_ids_for_points(raster_path, data_path, output_path, crs):
    """Create table and write a csv with a column that contains the respective raster cell ids for each point in the dataset.
    (R wrapper)
    Args:
        raster_path (str): path to raster template to get raster cell ids from
        data_path (str): path to point dataset to get raster cell ids for
        output_path (str): path to save csv to
        crs (int): crs of raster template as EPSG code

    """
    robjects.r(
        """
        library(terra)|> suppressPackageStartupMessages()
        library(sf)|> suppressPackageStartupMessages()
               
        raster_ids_for_points <-function(raster_path, data_path, output_path, crs){
               
            raster_template <- terra::rast(raster_path)
            print(crs(raster_template))
            values(raster_template) <- 1:ncell(raster_template)
            data <- readr::read_csv(data_path, show_col_types = F)|> 
                st_as_sf( coords = c("lon", "lat"), crs = 4326)|> 
                sf::st_transform(crs)
               
            cells <- extract(raster_template, data)
            data$cell_ids <- cells$lyr.1
            
            # create lat and lon as columns again
            data <- st_transform(data, 4326)
            data$lon <- st_coordinates(data)[, "X"]
            data$lat <- st_coordinates(data)[, "Y"]
            
            print(data|> st_drop_geometry() )
            readr::write_delim(data|> st_drop_geometry() , output_path, delim=",")
        }
        """
    )

    raster_ids_for_points_R = robjects.globalenv["raster_ids_for_points"]
    raster_ids_for_points_R(raster_path, data_path, output_path, crs)
