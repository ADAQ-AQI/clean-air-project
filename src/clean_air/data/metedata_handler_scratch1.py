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

        for outer_key in self.get_allfiles_dict():
            print('Outer Key = ', outer_key)

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

            # from util.crs.py   transform_points(xs, ys, source, target)
            # [x],[y]

            #Simple Pyproj transformation
            # import pyproj
            # from pyproj import Proj, transform
            # inProj = Proj(init='epsg:3857')
            # outProj = Proj(init='epsg:4326')
            # x1, y1 = -11705274.6374, 4826473.6922
            # x2, y2 = transform(inProj, outProj, x1, y1)

            # Using
            # pyproj >= 2.2
            # .0
            # import pyproj
            # print(pyproj.__version__)  # 2.4.1
            # print(pyproj.proj_version_str)  # 6.2.1
            #
            # proj = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
            #
            # x1, y1 = (-11705274.6374, 4826473.6922)
            # x2, y2 = proj.transform(x1, y1)
            # print((x2, y2))  # (-105.15027111593008, 39.72785727727918)

        # Check if point falls within bounding box
        # Make bounding box in shapley . NB. It follows pattern box( south, north, west, east) & point is Point ( Easting, Northing)
        bbox = box(south, north, west, east)
        # pnt = Point(point_lat, point_long)
        pnt = Point(y, x)
        answer = bbox.contains(pnt)
        print(f'is point in poly {answer}')

        return answer

    # def access_inner_dictionary(self):
    #    for key, value in self.dfh.get_allfiles_dict().items():  # items() function gives back key value pair as tuple
    #        print(key, 'main keys', value, 'value')
    #        for inner_dict_value in value:
    #           #if key[inner_dict_value] is type(dict):
    #                print('  ', inner_dict_value, 'is', key[inner_dict_value])

    def __set_switch_outer(self, include: bool, variable: str):  # TODO: have one version of these for a single value and one for a list
        """ Accesses the outer loop of the all files dict to check the value given is contained in the metadata
         and if so switches the to reverse of its previous value"""

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

    # def print_inner_dict(self):
    # #THINK THIS CRAZY BIT OF CODE ACTUALLY DOES WHAT I WANT :-)
    # # PUT THE FILTER HANDLER , NOT HERE ..AND HAVE TWO VERSIONS SO CAN UPDATE THE FILTERS ( PLAIN & INNER VERSIONS)
    #     # #KEEP  THIS IN TTHIS PRINT VERSION TOO SO CAN SEE WHAT HECK IS GOING ON !!
    #     for outer_key in self.get_allfiles_dict():
    #         print('Outer Key = ', outer_key)  #outer key is the yaml filename
    #         for inner_key in self.get_allfiles_dict()[outer_key]: #Now we have a possible key/value pair (this enough for simple ones)
    #             print('   ',
    #                   'Inner Key', inner_key,
    #                   'Inner Value', self.get_allfiles_dict()[outer_key][inner_key] ,
    #                   'Inner Value Type', type(self.get_allfiles_dict()[outer_key][inner_key]))
    #             #Now check to see if inner key is actually a list of key/value pairs
    #             if type(self.get_allfiles_dict()[outer_key][inner_key]) is list:
    #                for goal in self.get_allfiles_dict()[outer_key][inner_key]:
    #                    print('      ', type(self.get_allfiles_dict()[outer_key][inner_key]) , goal, type(goal))
    #                    #Now get the values in these mini dictionaries
    #                    if type(goal) is dict:
    #                       for key, value in goal.items():
    #                           print('         ', type(goal), str(key) + " => " + str(value))




    def test(self):
        print('METADATA HANDLER')
        # print yaml all file dict
        dict_printer(self.yaml_allfiles_dict)
        dict_printer(self.filters_dict)

        # now check if a filter is on:
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/music.yaml')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/dance.yaml')

        # Turn a filter off
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/veggies.yaml')

        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        dict_printer(self.filters_dict)

        self.turn_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        dict_printer(self.filters_dict)

        # self.dfh.turn_filter_off_contains('filetype','ground')
        # self.dfh.turn_filter_on_contains('sweet_potato','2')

        self.get_filtered_data_subsets()

        # print('ACCESS INNER DICTIONARY')
        # self.access_inner_dictionary(self.dfh.filters_dict)  #This not working !

    def test2(self):
        print('ACCESS INNER DICTIONARY')
        # self.access_inner_dictionary()#self.dfh.filters_dict)  # This not working !
        # self.access_inner_dict()
        self.print_access_inner_dict()

        print('METEDATA ONE TEST', )
        # now check if a filter is on:
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print('     Obs Level:ground')
        # Turn a filter off using obs level
        self.set_observation_level_filter(False, 'ground')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        # Turn a filter on using obs level
        self.set_observation_level_filter(True, 'ground')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print('     Data Source:health')
        # Turn a filter off using data_source
        self.set_data_source_filter(False, 'air_quality')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        # Turn a filter on using data_source
        self.set_data_source_filter(True, 'air_quality')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print('     Chemical Species: no2, pm2.5')
        # Turn a filter off using data_source
        self.set_chemical_species_filter(['no2', 'pm2.5'])
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print('     Chemical Species: pm10')
        # Turn a filter off using data_source
        self.set_chemical_species_filter(['pm10'])
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print('     Chemical Species: []')
        # Turn a filter on using data_source
        #self.set_chemical_species_filter({})
        #self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

    def test3(self):
        print('ACCESS INNER DICTIONARY')
        # self.access_inner_dictionary()#self.dfh.filters_dict)  # This not working !
        # self.access_inner_dict()
        self.print_access_inner_dict()

    def test_obs_level(self):
        """This test demos all working filters ! """
        print('METADATA TEST', 'Build list of all metadata files and turn filters to on by default \n')
        dict_printer(self.filters_dict)

        # now check if a filter is on:
        #self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        #print("\033[1;32m This text is Bright Green  \n")
        #print("\033[1;31m This text is Bright Red  \n")

        print('\n  \033[1;30m    Obs Level:GROUND', ' Turn off all datasets containing Ground')
        # Turn a filter off using obs level
        self.set_observation_level_filter(False, 'ground')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        # Turn a filter on using obs level
        print('\033[1;30m     Obs Level:GROUND', ' Turn on all datasets containing Ground')
        self.set_observation_level_filter(True, 'ground')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        print(' \033[1;30m    Data Source:AIR_QUALITY', ' Turn off all datasets containing Air Quality' )
        # Turn a filter off using data_source
        self.set_data_source_filter(False, 'air_quality')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

        # Turn a filter on using data_source
        print(' \033[1;30m    Data Source:AIR_QUALITY', ' Turn on all datasets containing Air Quality')
        self.set_data_source_filter(True, 'air_quality')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/station_metadata.yaml')

    def test_location(self):
    # Test the location filter ( add test for antartica in polar steriographic projection)
        self.set_location_filter(0.0984, 51.5138)

m = MetadataHandler()
# m.test()

#m.test2()

#m.test3()

#m.test4()

m.test_location()
