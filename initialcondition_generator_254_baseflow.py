import sys
import os

from initialcondition_generator_lib.InitialConditionCreator254 import InitialConditionCreator254
from initialcondition_generator_lib.Link import Link
from initialcondition_generator_lib.GridSet import GridSet
from initialcondition_generator_lib.SystemStatus import SystemStatus
from initialcondition_generator_lib.JsonSettings import JsonSettings
from initialcondition_generator_lib.UsgsGauge import UsgsGauge
from def_lib import ArgumentsManager

has_error = False
execute_1 = True
execute_2 = True

# ###################################################### ARGS ######################################################## #

# show help
if '-h' in sys.argv:
    print("Creates an initial condition file (.rec) from a spatial regression of discharge/area coefficient.")
    print("Basically:");
    print(" - retrieves USGS historical discharge data for a given time interval for all gages USGS in Iowa;")
    print(" - estimates baseflow for all sites in given time interval;")
    print(" - spatially interpolates discharge/area coefficents;")
    print(" - generates an initial condition for iowa, model 254 (Top Layer).")
    print("Usage 1: python initialconditions_generator_254.py INSTRUCTIONS_JSON")
    print("  Executes all steps for generating an initial condition file.")
    print("  INSTRUCTIONS_JSON : File path for JSON file with all parameters.")
    print("Usage 2: python initialconditions_generator_254.py -get_json_scratch INSTRUCTIONS_JSON")
    print("  Creates a scratch for the JSON file with all parameters for this tool.")
    print("  INSTRUCTIONS_JSON : File path for JSON file scrathc to be generated.")
    print("Usage 3: python initialconditions_generator_254.py -h")
    print("  Shows this help.")
    print("Python libraries status:")
    print("  Has matplotlib: {0}".format(SystemStatus.HAS_MATPLOTLIB))
    print("  Has scipy.interpolate: {0}".format(SystemStatus.HAS_SCIPYINTERPOL))
    print("  Has urllib3: {0}".format(SystemStatus.HAS_URLLIB3))
    print("  Has psycopg2: {0}".format(SystemStatus.HAS_PSYCOPG2))
    print("  Has h5py: {0}".format(SystemStatus.HAS_H5PY))
    # print("  VERSION : Asynch version. Expects values '1.2' or '1.3'. If not provided, it is assumed 1.3.")
    quit()

# create scratch JSON
json_scrath_path = ArgumentsManager.get_str(sys.argv, '-get_json_scratch')
if '-get_json_scratch' in sys.argv:
    JsonSettings.create_scratch_file(json_scrath_path)
    quit()

# basic check arguments
if len(sys.argv) < 2:
    print("Missing settings file path. See help (-h) for more information.")
    quit()

run_settings = JsonSettings.read_settings_file(sys.argv[1])
if run_settings is None:
    print("Unable to get settings.")
    quit()

try:
    swc = run_settings['toplayer_soil_water_column']
    k = run_settings['k']
    execute_1 = True if 'download_data' in run_settings['procedures'] else False
    execute_2 = True if 'interpolate' in run_settings['procedures'] else False
    time_init = run_settings['baseflow_ini_date']
    time_end = run_settings['baseflow_end_date']
    linkid_rawdischarge_file_path = run_settings['temporary_file_path']
    output_state_file_path = run_settings['output_state_file_path']
    output_graph_file_path = run_settings['output_graph_file_path'] \
        if 'output_graph_file_path' in run_settings else None
    linkid_location_file_path = run_settings['linkid_location_file']
    usgs_gauges_to_ignore = JsonSettings.read_gages_list_file(run_settings['gages_ignore_csv'])
    usgs_gauges_to_consider = JsonSettings.read_gages_list_file(run_settings['gages_only_csv'])
    usgs_gauges_bounding_box = run_settings['gages_only_bounding_box']
    base_snapshot_file_path = run_settings['base_snapshot_file_path'] \
        if 'base_snapshot_file_path' in run_settings else None
    base_snapshot_states_inherit = run_settings['base_snapshot_states_inherit'] \
        if 'base_snapshot_states_inherit' in run_settings else None
    interpolation_method = run_settings['interpolation_method']
except KeyError as e:
    print("Unable to find key: {0}.".format(e))
    quit()


# ###################################################### DEFS ######################################################## #


def create_linkid_discharge_file():
    """
    Gets all USGS gauges registered in database respectively associated to linkids, gets data from USGS webservice, store file
    :return: None. Changes are performed in file system.
    """

    usgs_gauges = InitialConditionCreator254.retrieve_gauges_ids_from_usgs_webservice_box(
        time_init, time_end,
        bounding_box=usgs_gauges_bounding_box,
        pois_id_only=usgs_gauges_to_consider,
        pois_id_ignore=usgs_gauges_to_ignore)

    InitialConditionCreator254.retrieve_discharge_series_from_usgs_webservice(time_init, time_end, usgs_gauges)
    store_discharges_in_file(usgs_gauges, linkid_rawdischarge_file_path)


def create_interpolation_products(linkid_rawdischarge_filepath, output_state_file_path, output_graph_file_path,
                                  base_snapshot_file_path, base_snapshot_inherit_states, interpolation_method):
    """
    USEFUL
    :param linkid_rawdischarge_filepath:
    :param output_state_file_path:
    :param output_graph_file_path:
    :param base_snapshot_file_path:
    :param base_snapshot_inherit_states:
    :return:
    """

    # read inputs
    usgs_linkds_discharge = retrieve_linkid_discharge_from_csv_file(linkid_rawdischarge_filepath, convert_to_is=True)
    links_location = retrieve_all_linkid_location_from_file()

    # interpolate
    InitialConditionCreator254.interpolate_disch_area(usgs_linkds_discharge, links_location, output_state_file_path,
                                                      output_graph_file_path=output_graph_file_path,
                                                      base_snapshot_file_path=base_snapshot_file_path,
                                                      base_snapshot_inherit_states=base_snapshot_inherit_states,
                                                      interpolation_method=interpolation_method)


def store_discharges_in_file(usgs_gauges, file_path):
    """
    USEFUL
    :param usgs_gauges:
    :param file_path:
    :return:
    """

    if (usgs_gauges is None) or (file_path is None):
        print("Not writing csv file. One argument is None: {0}, {1}".format(usgs_gauges, file_path))
        return None

    with open(file_path, "w+") as fwrite:
        print("Writing file '{0}'.".format(file_path))
        for cur_usgs_gauges in usgs_gauges.values():
            if cur_usgs_gauges.get_link_id() is not None:
                fwrite.write("{0},{1},{2}\n".format(cur_usgs_gauges.get_link_id(),
                                                    cur_usgs_gauges.get_id(),
                                                    cur_usgs_gauges.get_min_discharge()))
            elif (cur_usgs_gauges.get_lat() is not None) and (cur_usgs_gauges.get_lng() is not None):
                fwrite.write("{0},{1},{2},{3},{4}\n".format(cur_usgs_gauges.get_lat(), cur_usgs_gauges.get_lng(),
                                                            cur_usgs_gauges.get_id(),
                                                            cur_usgs_gauges.get_min_discharge(),
                                                            cur_usgs_gauges.get_upstream_area()))
            else:
                continue
        print(" Done.")


def retrieve_linkid_discharge_from_csv_file(csv_file_path, convert_to_is=False):
    """
    USEFUL
    :param csv_file_path:
    :return:
    """

    return_dict = {}

    print("Reading baseflow data from file:")
    print("  '{0}'".format(csv_file_path))

    with open(csv_file_path, "r") as csv_file:
        count_line = 1

        for cur_line in csv_file:
            cur_line_splitted = cur_line.split(',')
            if len(cur_line_splitted) > 4:
                cur_usgs_gage = UsgsGauge(cur_line_splitted[2], float(cur_line_splitted[4].strip()))
                cur_usgs_gage.set_lat(float(cur_line_splitted[0]))
                cur_usgs_gage.set_lng(float(cur_line_splitted[1]))
                cur_raw_disch_value = cur_line_splitted[3]

                try:
                    if not convert_to_is:
                        cur_usgs_gage.set_min_discharge(float(cur_raw_disch_value))
                    else:
                        cur_usgs_gage.set_min_discharge(float(cur_raw_disch_value) * 0.0283)
                    return_dict[int(cur_line_splitted[2].strip())] = cur_usgs_gage
                except ValueError:
                    # print("Unable to parse line {0}: '{1}'".format(count_line, cur_line.strip()))
                    count_line = count_line

            count_line += 1

    print(" Retrieved {0} baseflow values.".format(len(return_dict.keys())))
    return return_dict


def retrieve_all_linkid_location_from_file():
    """
    USEFUL
    :return:
    """

    print("Read link locations")

    return_dict = {}

    with open(linkid_location_file_path, "r") as csv_file:
        for cur_line in csv_file:
            cur_line_splitted = cur_line.split(',')
            if len(cur_line_splitted) > 2:
                cur_link_id = int(cur_line_splitted[0].strip())
                cur_link = Link(cur_link_id)
                cur_link.set_latlng(float(cur_line_splitted[1].strip()), float(cur_line_splitted[2].strip()))
                cur_link.set_upstream_area(float(cur_line_splitted[3].strip()))
                return_dict[cur_link_id] = cur_link

    print(" Retrieved {0} link locations.".format(len(return_dict.keys())))

    return return_dict


# ###################################################### CALL ######################################################## #

if has_error:
    print("Invalid set of arguments. Use -h for help.")
    exit()

GridSet.set_swc(swc)

if execute_1:

    # execute functions
    create_linkid_discharge_file()

if execute_2:
    # execute functions
    if not os.path.exists(linkid_rawdischarge_file_path):
        print("Missing file '{0}'.".format(linkid_rawdischarge_file_path))
        print("Execute part1 first.")
    else:
        create_interpolation_products(linkid_rawdischarge_file_path, output_state_file_path, output_graph_file_path,
                                      base_snapshot_file_path, base_snapshot_states_inherit, interpolation_method)
