"""
Unit tests for the util.crs submodule
"""

import numpy as np
import cartopy.crs as ccrs
import pyproj
import shapely.geometry
import pytest

from clean_air import util

cases = [(pyproj.CRS.from_epsg(4326), ccrs.Geodetic()),
         (pyproj.CRS.from_epsg(27700), ccrs.OSGB(approx=False)),

         # Skip this (for now..?) because there are too many subtle differences:
         # - cartopy does not name an ellipse, when it should really use WGS84
         # - when not using EPSG codes, pyproj notices likes to represent spheres
         #   with radius R instead of semimajor/minor axes a and b
         # - a "wktext" parameter turns up in the EPSG definition that we can't
         #   reasonably add while converting
         # (pyproj.CRS.from_epsg(3857), ccrs.Mercator.GOOGLE),

         (pyproj.CRS.from_epsg(3057), ccrs.LambertConformal(-19, 65, false_easting=500_000, false_northing=500_000,
                                                            standard_parallels=(64.25, 65.75),
                                                            globe=ccrs.Globe(ellipse="GRS80"))),
         # Not sure how else to define this case other than copying what our cartopy -> pyproj converter does...
         (pyproj.CRS.from_epsg("""+ellps=WGS84 +a=6371229 +b=6371229 +proj=ob_tran +o_proj=latlon +o_lon_p=0.0 
         +o_lat_p=177.5 +lon_0=217.5 +to_meter=0.0174532925199433 +no_defs"""),
          ccrs.RotatedGeodetic(37.5, 177.5, globe=ccrs.Globe(semimajor_axis=6371229, semiminor_axis=6371229)))]


@pytest.mark.parametrize("source, target", cases)
def test_as_cartopy(source, target):
    """
    GIVEN a source CRS of EPSG:4326,
    WHEN converted to Cartopy CRS type through as_cartopy_crs,
    THEN resulting CRS parameters will match following proj4 parameters:
        proj=latlon, datum=WGS84, ellps=WGS84, no_defs, type=crs, source=EPSG:4326
    """
    converted = util.crs.as_cartopy_crs(source)
    # Cartopy implements equality by comparing proj4 strings, which may fail due to differences such as the order of
    # parameters, or whether a number ends with ".0" or not.  Instead, compare the underlying dicts.
    assert converted.proj4_params == target.proj4_params


# Note that we can reuse the same cases, but labeled the other way round
@pytest.mark.parametrize("target, source", cases)
def test_as_pyproj(source, target):
    """
    GIVEN a source CRS of Geodetic (proj=lonlat, datum=WGS84, ellps=WGS84, no_defs, type=CRS),
    WHEN converted to pyproj CRS through as_pyproj_crs,
    THEN the resulting dictionary of converted values will match the following target values:
        proj=longlat, datum=WGS84, no_defs, type=crs
    """
    converted = util.crs.as_pyproj_crs(source)
    # Check only proj4 parameters.  Pyproj can handle a lot more than proj4
    # can describe, so may have got some of those extra things wrong.
    assert converted.to_dict() == target.to_dict()


class TestTransform:
    def setup_class(self):
        """SETUP variables for all tests"""
        self.latlon_point = shapely.geometry.Point(-0.4, 51.5)
        self.osgb_point = shapely.geometry.Point(511160, 179110)

    def test_cartopy(self):
        """
        GIVEN a Geodetic Cartopy CRS and a lat-lon point,
        WHEN point is transformed through transform_shape with a Cartopy OSGB CRS as the final argument,
        THEN the resultant point has an OSGB CRS.
        """
        latlon = ccrs.Geodetic()
        osgb = ccrs.OSGB(approx=False)
        transformed = util.crs.transform_shape(self.latlon_point, latlon, osgb)
        transformed = np.array(transformed).round(-1)
        assert np.all(transformed == np.array(self.osgb_point))

    def test_pyproj(self):
        """
        GIVEN a pyproj EPSG:4326 CRS and a lat-lon point,
        WHEN point is transformed through transform_shape with a pyproj EPSG:27700 CRS as the final argument,
        THEN the resultant point has an OSGB CRS.
        """
        latlon = pyproj.CRS.from_epsg(4326)
        osgb = pyproj.CRS.from_epsg(27700)
        transformed = util.crs.transform_shape(self.latlon_point, latlon, osgb)
        transformed = np.array(transformed).round(-1)
        assert np.all(transformed == np.array(self.osgb_point))

    def test_cartopy_to_pyproj(self):
        """
        GIVEN a Geodetic Cartopy CRS and a lat-lon point,
        WHEN point is transformed through transform_shape with a pyproj OSGB:27700 CRS as the final argument,
        THEN the resultant point has an OSGB CRS.
        """
        latlon = ccrs.Geodetic()
        osgb = pyproj.CRS.from_epsg(27700)
        transformed = util.crs.transform_shape(self.latlon_point, latlon, osgb)
        transformed = np.array(transformed).round(-1)
        assert np.all(transformed == np.array(self.osgb_point))

    def test_pyproj_to_cartopy(self):
        """
        GIVEN a pyproj EPSG:4326 CRS and a lat-lon point,
        WHEN point is transformed through transform_shape with a cartopy OSGB CRS as the final argument,
        THEN the resultant point has an OSGB CRS.
        """
        latlon = pyproj.CRS.from_epsg(4326)
        osgb = ccrs.OSGB(approx=False)
        transformed = util.crs.transform_shape(self.latlon_point, latlon, osgb)
        transformed = np.array(transformed).round(-1)
        assert np.all(transformed == np.array(self.osgb_point))
