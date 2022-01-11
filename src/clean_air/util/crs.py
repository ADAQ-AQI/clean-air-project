"""
Helper functions for dealing with coordinate reference systems.
"""

import warnings

import numpy as np
import cartopy.crs as ccrs
import pyproj
import shapely.ops

# Cartopy classes corresponding to EPSG codes
_CARTOPY_EPSG = {
    4326: (ccrs.Geodetic, {}),
    23032: (ccrs.EuroPP, {}),
    27700: (ccrs.OSGB, {"approx": False}),
    29902: (ccrs.OSNI, {"approx": False}),
}

# Map of proj4 projection names to appropriate classes
# Expected parameters have been noted for reference only, there's no need to
# manually validate these
_CARTOPY_CLASSES = {
    # no arguments
    "lonlat": ccrs.Geodetic,

    # lon_0
    "eqc": ccrs.PlateCarree,
    "cea": ccrs.LambertCylindrical,
    "igh": ccrs.InterruptedGoodeHomolosine,
    "mill": ccrs.Miller,  # note: spheres only

    # lon_0, lat_0
    "ortho": ccrs.Orthographic,
    "gnom": ccrs.Gnomonic,  # note: spheres only

    # lon_0, x_0, y_0
    "eck1": ccrs.EckertI,
    "eck2": ccrs.EckertII,
    "eck3": ccrs.EckertIII,
    "eck4": ccrs.EckertIV,
    "eck5": ccrs.EckertV,
    "eck6": ccrs.EckertVI,
    "eqearth": ccrs.EqualEarth,
    "moll": ccrs.Mollweide,
    "robin": ccrs.Robinson,
    "sinu": ccrs.Sinusoidal,
    "stere": ccrs.Stereographic,

    # lon_0, lat_0, x_0, y_0
    "laea": ccrs.LambertAzimuthalEqualArea,
    "aeqd": ccrs.AzimuthalEquidistant,

    # lon_0, lat_0, x_0, y_0, lat_1, lat_2
    "lcc": ccrs.LambertConformal,
    "aea": ccrs.AlbersEqualArea,
    "eqdc": ccrs.EquidistantConic,

    # The following all set units = "m", which we may want to verify is true

    # lon_0, x_0, y_0, lat_ts, k_0
    "merc": ccrs.Mercator,
    # Note: also takes a min_latitude and max_latitude, used to determine its
    # boundary

    # lon_0, lat_0, k, x_0, y_0
    "tmerc": ccrs.TransverseMercator,

    # zone, south
    "utm": ccrs.UTM,

    # lon_0, lat_0, h, x_0, y_0
    "geos": ccrs.Geostationary,
    "nsper": ccrs.NearsidePerspective,
}

# Map of proj4 names to keyword arguments for a cartopy Globe
_GLOBE_PARAMS = {
    "datum": "datum",
    "ellps": "ellipse",
    "a": "semimajor_axis",
    "b": "semiminor_axis",
    "f": "flattening",
    "rf": "inverse_flattening",
    "towgs84": "towgs84",
    "nadgrids": "nadgrids",
}

# Map of proj4 names to keyword arguments for a cartopy CRS
_CRS_PARAMS = {
    "lon_0": "central_longitude",  # Except rotated geodetic
    "lat_0": "central_latitude",
    "x_0": "false_easting",
    "y_0": "false_northing",
    "k": "scale_factor",
    "k_0": "scale_factor",
    "lat_ts": "latitude_true_scale",
    "h": "satellite_height",
    "south": "southern_hemisphere",

    # We'll use names like "[foo]" to indicate that the value of "foo" must
    # be an array, which all values will be appended to
    "lat_1": "[standard_parallels]",
    "lat_2": "[standard_parallels]",

    # Will only be used for rotated geodetic
    "o_lon_p": "central_rotated_longitude",
    "o_lat_p": "pole_latitude",
}

# Ignore the warning from pyproj that converting to a proj4 string loses
# information
warnings.filterwarnings(
    "ignore",
    "You will likely lose important projection information",
)


def as_pyproj_crs(crs):
    """
    Represent a cartopy CRS as a pyproj CRS.
    """
    if isinstance(crs, pyproj.CRS):
        return crs

    if isinstance(crs, ccrs.CRS):
        # Conveniently, Cartopy exposes a proj4 init string, which pyproj
        # can handle
        return pyproj.CRS(crs.proj4_init)

    raise TypeError(f"Unrecognised CRS: {crs}")


def as_cartopy_crs(crs):
    """
    Represent a pyproj CRS as a cartopy CRS.
    """
    if isinstance(crs, ccrs.CRS):
        return crs

    if not isinstance(crs, pyproj.CRS):
        raise TypeError(f"Unrecognised CRS: {crs}")

    # Check EPSG code to use specific cartopy classes where possible.
    # Minor note of caution: this method (by default) finds a "close enough"
    # EPSG code, with a confidence level of 70%. Apparently this is useful
    # because "trivial" differences like listing the axes in a different order,
    # or missing names, are taken into account.
    epsg = crs.to_epsg()
    if epsg in _CARTOPY_EPSG:
        constructor, args = _CARTOPY_EPSG[epsg]
        return constructor(**args)

    # Otherwise, we have the tedious task of converting proj4 parameters to
    # a cartopy class + parameters + globe parameters
    constructor = None
    crs_params = {}
    globe_params = {}

    # First need proj4 params, as a dict instead of an actual proj4 string
    params = crs.to_dict()

    # Determine the projection
    proj_name = params.pop("proj")
    if proj_name in _CARTOPY_CLASSES:
        constructor = _CARTOPY_CLASSES[proj_name]
    elif proj_name == "ob_tran" and params.pop("o_proj") == "latlon":
        # Check for rotated pole as a special case
        constructor = ccrs.RotatedGeodetic
        crs_params["pole_longitude"] = params.pop("lon_0") - 180

    if constructor is None:
        raise ValueError(f"Cannot handle projection '{proj_name}'")

    # Special handling for spheres
    r = params.pop("R", None)
    if r is not None:
        params["a"] = params["b"] = r

    # Split the parameters into those for the globe and those for the crs
    # Note: the sorting is specifically to guarantee that we handle lat_1
    # before lat_2, because they need to be put into an array in that order
    unrecognised = []
    for key, val in sorted(params.items()):
        # Handle "flags" - parameters that have no meaningful "value" so
        # were given a value of None
        if key == "south":
            val = True

        if key in _GLOBE_PARAMS:
            globe_params[_GLOBE_PARAMS[key]] = val
        elif key in _CRS_PARAMS:
            name = _CRS_PARAMS[key]
            if name.startswith("["):
                # Force into an array if needed
                name = name.strip("[]")
                crs_params.setdefault(name, []).append(val)
            else:
                crs_params[name] = val
        elif key not in ("no_defs", "wktext", "type", "units", "to_meter"):
            unrecognised.append((key, val))

    if unrecognised:
        warnings.warn(f"Some parameters were not handled: {unrecognised}")

    # Special handling for scale factors
    # Cartopy refuses to accept both "scale_factor" and "latitude_true_scale",
    # even if they match the defaults that proj4 defines.  Try to avoid it
    # raising this error by removing these defaults.
    if crs_params.get("latitude_true_scale") == 0:
        crs_params.pop("latitude_true_scale")
    if crs_params.get("scale_factor") == 1:
        crs_params.pop("scale_factor")

    return constructor(**crs_params, globe=ccrs.Globe(**globe_params))


def match_crs_type(crs, like):
    """
    Convert CRSs to either a cartopy or pyproj type.

    Arguments:
        crs (cartopy.CRS|pyproj.CRS): CRS in a potentially unwanted type
        like (cartopy.CRS|pyproj.CRS): CRS of the desired type

    Returns:
        (cartopy.CRS|pyproj.CRS): a CRS equivalent to `crs`, of the same
            type as `like`
    """
    if isinstance(like, ccrs.CRS):
        return as_cartopy_crs(crs)

    if isinstance(like, pyproj.CRS):
        return as_pyproj_crs(crs)

    raise TypeError(f"Unrecognised CRS: {like}")


def _get_transformer(source, target):
    # Assumes that source and target have the same type - caller should
    # have arranged this.

    if isinstance(target, ccrs.CRS):
        def transform(xs, ys, zs=None):
            xs = np.array(xs)
            ys = np.array(ys)
            if zs is not None:
                zs = np.array(zs)
            tfpoints = target.transform_points(source, xs, ys, zs)

            # Cartopy gave us an array of shape (n, 3), but shapely expects
            # output of the same type as the input, ie two (or three) lists
            # of length n.
            # A numpy array of shape (m, n) can be unpacked into m lists of
            # length n, so just need to transpose, and possibly drop the z
            # coordinates.
            if zs is None:
                tfpoints = tfpoints[:, 0:2]
            return tfpoints.T

        return transform

    if isinstance(target, pyproj.CRS):
        # Note: `always_xy` has nothing to do with 2d vs 3d - it ensures that
        # the first coordinate of the output are the xs, and the second the ys.
        # Without this, it's whichever order they appear in the target CRS
        # definition
        transformer = pyproj.Transformer.from_crs(source, target, always_xy=True)
        return transformer.transform

    raise TypeError(f"Unrecognised CRS: {target}")


def transform_shape(shape, source, target):
    """
    Convert a shapely geometry from one CRS to another.

    Arguments:
        shape (shapely.BaseGeometry): geometry to transform
        source (cartopy.CRS|pyproj.CRS): CRS that the shape is currently
            defined for
        target (cartopy.CRS|pyproj.CRS): desired CRS

    Returns:
        (shapely.BaseGeometry): transformed shape
    """
    # Determine an appropriate transformation function based on type
    # If the CRSs are not compatible types, assume it is slightly more helpful
    # to match the target, so convert the source
    source = match_crs_type(source, target)
    transformer = _get_transformer(source, target)

    return shapely.ops.transform(transformer, shape)


def transform_points(xs, ys, source, target):
    """
    Convert coordinates from one CRS to another.

    Arguments:
        xs (array): list of x coordinates. Can be any sequence accepted by
            `np.array`.
        ys (array): list of corresponding y coordinates
        source (cartopy.CRS|pyproj.CRS): CRS that the coordinates are currently
            defined for
        target (cartopy.CRS|pyproj.CRS): desired CRS

    Returns:
        (xs, ys): transformed points
    """
    # Determine an appropriate transformation function based on type
    source = match_crs_type(source, target)
    transform = _get_transformer(source, target)

    return transform(np.array(xs), np.array(ys))
