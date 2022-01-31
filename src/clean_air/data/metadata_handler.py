#WIP . Need to add Chemical Species filters

import pyproj
from shapely.geometry import box, Point

from clean_air.data.data_filter_handler import DataFilterHandler, dict_printer
from clean_air.util.crs import transform_points

CHEMICAL_SPECIES = 'chemical_species'
CRS_LATLONG = "EPSG:4326"
CRS_CONST = 'cs'
BBOX_CONST = 'bbox'

#TODO: Should I keep a record of what has been turned on / off for each file ? Would Have be held within filters dictionary
#TODO: OR maybe I never want to turn the filters on ? , Only off or reset all ??

class MetadataHandler(DataFilterHandler):
    """This class manages the metadata. Inherits from DataFilterHandler
    It gets its values from the appropriate metadata yaml files and uses the data filter handler to switch filters on and off for each dataset as appropriate.
    Currently all metadata is handled at file level"""

    def __init__(self, filepath='.'):
        super().__init__(filepath)
        self.filepath = filepath
        # self.dfh = DataFilterHandler(self.filepath)  #NB: I have changed this to inherit & broken my code !!. Put back if not using inheritance !!

    def set_observation_level_filter(self, include: bool, obs_level: str):
        """Function to check metadata yaml files and set the filter using observation level eg: model, ground, airbourne
        pass include:True if you want dataset included, false if you want dataset excluded.
        eg: include:true, obs_level: ground would include all ground data sets
        include:false, obs_level ground would exclude all ground data sets"""

        self.__set_switch_outer(include, obs_level)

    def set_data_source_filter(self, include: bool, data_source: str):
        """Function to check metadata yaml files and set the filter using data source eg: air_quality, health"""
        self.__set_switch_outer(include, data_source)

    def set_time_range_filter(self, min_time, max_time):
        """Function to check metadata yaml files and set the filter using time
        Any files within given time values are switched on
        Any files outside given time values are switched off"""
        
        # *Test Commit

        # GO through the big old loop to set a time start & time end variable in a standard time format.
        # Then do this

        # if min_time >= dataset_time_start & max time <= dataset_time_end:
        #     self.dfh.turn_filter_on()
        # else:
        #     self.dfh.turn_filter_off()

        # TODO: Standardise time format !
        pass

    def set_chemical_species_filter(self, species_list: list):
        """Function to check metadata yaml files and set the filter using chemical species .
         eg: no2, o3, so2, pm2.5, pm10 :

         Any values within given list of chemical species ar switched on
         Any values not withing given list of chemical species are switched off"""

        self.__set_switch_inner(species_list, CHEMICAL_SPECIES)


    def set_location_filter(self, point_lat:float, point_long:float):
        """Function to check metadata yaml files and set the filter using data source eg: lat/lon falls within bbox with N/S/E/W co-ordinates"""

        #TODO:  Searches for point location within DATASET using metadata. Needs to be expanded to search at file level too.

        for outer_key in self.get_allfiles_dict():

            # reset values for bounding box
            north = None
            south = None
            east = None
            west = None
            cs = None
            latlong_dict = None

            for inner_key in self.get_allfiles_dict()[outer_key]:
                if inner_key == CRS_CONST:
                    cs = self.get_allfiles_dict()[outer_key][inner_key]
                    print(f'Coord ref system {inner_key} , {cs}')

                if inner_key == BBOX_CONST:
                    latlong_dict = (self.get_allfiles_dict()[outer_key][inner_key])

                    #get values from dictionary
                    north = latlong_dict.get('north')
                    south = latlong_dict.get('south')
                    east  = latlong_dict.get('east')
                    west  = latlong_dict.get('west')

            if (north != None and cs !=None):
                print(f'North {north}, South{south}, East{east}, West{west}/n')

                #Evaluate if co-ordinates in box and update result accordingly
                if(self.__evaluate_coordinates_in_box(cs, east, north, south, west, point_lat, point_long)):
                    self.turn_filter_on(outer_key)
                else:
                    self.turn_filter_off(outer_key)
            else:
                pass
                # Either this file doesnt contain bbox at all or its missing its CRS info
                # If later , it needs incomplete metadata error throwing here

    def __evaluate_coordinates_in_box(self, cs, east, north, south, west, point_lat, point_long)->bool:
        """ Returns True if coordinates are in bounding box, otherwise returns false"""

        # Check CRS
        if cs == CRS_LATLONG:  # (NB THE assumption in that the POINT being compared to this bbox is always a lat/long
            # this is fine
            x = point_long
            y = point_lat
        else:
            source_crs = pyproj.CRS(CRS_LATLONG)
            target_crs = pyproj.CRS(cs)  # create crs object

            transformed_x, transformed_y = transform_points([point_long], [point_lat], source_crs, target_crs)
            x = transformed_x[0]
            y = transformed_y[0]


        # Check if point falls within bounding box
        # Make bounding box in shapley . NB. It follows pattern box( south, north, west, east) & point is Point ( Easting, Northing)
        bbox = box(south, north, west, east)
        # pnt = Point(point_lat, point_long)
        pnt = Point(y, x)
        answer = bbox.contains(pnt)
        print(f'is point in poly {answer}')

        return answer


    def __set_switch_outer(self, include: bool, variable: str):  # TODO: have one version of these for a single value and one for a list
        """ Accesses the outer loop of the all files dict to check the value given is contained in the metadata
         . Switches On or Off dependant on the value given for the include variable True = On, False = Off """

        for outer_key in self.get_allfiles_dict():
            for inner_key in self.get_allfiles_dict()[outer_key]:  # Now we have a possible key/value pair (this enough for simple ones)
                # print('   ', 'Inner Key', inner_key, 'Inner Value', self.get_allfiles_dict()[outer_key][inner_key])
                if str(self.get_allfiles_dict()[outer_key][inner_key]) == variable:
                    if include:
                        self.turn_filter_on(outer_key)
                    else:
                        self.turn_filter_off(outer_key)

    def __set_switch_inner(self, species_list: list):
        pass


