from datetime import datetime
import subprocess

from initialcondition_generator_lib.SystemStatus import SystemStatus
from initialcondition_generator_lib.GridSet import GridSet
from initialcondition_generator_lib.UsgsGauge import UsgsGauge

if SystemStatus.HAS_URLLIB3:
    import urllib3


class InitialConditionCreator254:

    @staticmethod
    def process_http_usgs_request(http_request_content, debug_file_id=None):
        """
        Gets text returned by website and splits it into a list of discharges (in ft^3/sec).
        If returned content contains HTML (missing data at web service), it does not process.
        :param http_request_content: Text content
        :return: List of discharges if possible to processes, None otherwise
        """

        if http_request_content is None:
            print("Nothing was obtained from HTTP request")
            return None

        # debug
        '''
        if debug_file_id is not None:
            debug_file_path = "/Dedicated/IFC/Asynch_tools/initialcondition_generator_test/debug_gage_{0}.txt"
            debug_file_path =  debug_file_path.format(debug_file_id)
            with open(debug_file_id, "w+") as w_file:
                w_file.write(debug_file_path)
        '''

        all_discharges = []
        all_lines = http_request_content.split('\n')
        for cur_line in all_lines:

            if (len(cur_line.strip()) == 0) or (cur_line.strip()[0] == '#'):
                continue
            elif (len(cur_line.strip()) == 0) or (cur_line.strip()[0] == '<'):
                # print("{0} contains HTML!".format(cur_line))
                return None

            cur_discharge_line_splitted = cur_line.split('\t')
            if len(cur_discharge_line_splitted) > 3:
                try:
                    cur_discharge = float(cur_discharge_line_splitted[3])
                    all_discharges.append(cur_discharge)
                except ValueError:
                    continue

        return all_discharges

    @staticmethod
    def process_http_usgs_request_for_gauges_desc(http_request_content, pois_id_only=None, pois_id_ignore=None):
        """
        Gets the text returned by website related to gauges description (location and area), splits it and ???
        :param http_request_content: Text content
        :param pois_id_only:
        :param pois_id_ignore:
        :return: List of USGS gages description
        """

        if http_request_content is None:
            return None

        # debug_vars
        lines_comment = 0
        lines_ignored = 0
        lines_discarded = 0
        lines_added = 0
        lines_exception = 0

        all_usgs_gages = {}
        all_lines = http_request_content.split('\n')
        print(" Read {0} lines.".format(len(all_lines)))
        for cur_line in all_lines:

            if (len(cur_line.strip()) == 0) or (cur_line.strip()[0] == '#'):
                lines_comment += 1
                continue
            cur_discharge_line_splitted = cur_line.split('\t')
            if len(cur_discharge_line_splitted) > 5:
                try:
                    cur_id = cur_discharge_line_splitted[0].strip()
                    cur_lat = float(cur_discharge_line_splitted[1].strip())
                    cur_lng = float(cur_discharge_line_splitted[2].strip())
                    cur_drain_area = float(cur_discharge_line_splitted[5].strip()) * 2.51  # for some reason I need to do it

                    # check if USGS gage must be ignored
                    if (pois_id_ignore is not None) and (cur_id in pois_id_ignore):
                        lines_ignored += 1
                        continue

                    # check if USGS gages must be disposed
                    if (pois_id_only is not None) and (str(int(cur_id)) not in pois_id_only):
                        # print("It '{0}'.".format(str(int(cur_id))))
                        # print("is not in {0}".format(pois_id_only))
                        # quit()
                        lines_discarded += 1
                        continue

                    # add USGS gage
                    cur_gauge = UsgsGauge(cur_id, cur_drain_area)
                    cur_gauge.set_lat(cur_lat)
                    cur_gauge.set_lng(cur_lng)
                    all_usgs_gages[cur_id] = cur_gauge
                    lines_added += 1

                except ValueError:
                    lines_exception += 1
                    continue

        # debug
        print(" Ignored {0} gages.".format(lines_ignored))
        print(" Discarded {0} gages.".format(lines_discarded))
        print(" Got {0} gages.".format(len(all_usgs_gages.keys())))

        return all_usgs_gages

    @staticmethod
    def retrieve_gauges_ids_from_usgs_webservice_box(begin_date, end_date, bounding_box, pois_id_only=None,
                                                     pois_id_ignore=None):
        """

        :param begin_date:
        :param end_date:
        :param pois_id_ignore:
        :return:
        """

        # url for web service that provides all gages with stream flow parameter (0060) inside a square
        url_usgs = "http://nwis.waterdata.usgs.gov/nwis/dv?referred_module=sw&site_tp_cd=OC&site_tp_cd=OC-CO&site_tp_cd=ES&" \
                   "site_tp_cd=LK&site_tp_cd=ST&site_tp_cd=ST-CA&site_tp_cd=ST-DCH&site_tp_cd=ST-TS&" \
                   "nw_longitude_va={0}&nw_latitude_va={1}&se_longitude_va={2}&se_latitude_va={3}&" \
                   "coordinate_format=decimal_degrees&index_pmcode_00060=1&group_key=NONE&format=sitefile_output&" \
                   "sitefile_output_format=rdb&column_name=site_no&column_name=dec_lat_va&column_name=dec_long_va&" \
                   "column_name=drain_area_va&range_selection=date_range&begin_date={4}&end_date={5}&" \
                   "date_format=YYYY-MM-DD&rdb_compression=value&" \
                   "list_of_search_criteria=lat_long_bounding_box%2Csite_tp_cd%2Crealtime_parameter_selection"
        url_usgs = url_usgs.format(bounding_box["min_lng"], bounding_box["max_lat"], bounding_box["max_lng"],
                                   bounding_box["min_lat"], begin_date, end_date)

        # debug
        # print("URL: {0}".format(url_usgs))

        # request, read and parse result
        if SystemStatus.HAS_URLLIB3:
            print("Retrieving gauges in bounding box using urllib3.")
            http = urllib3.PoolManager()
            http_response = http.request('GET', url_usgs).data.decode()
        else:
            print("Retrieving gauges in bounding box using raw wget.")
            url = "wget -q -O - '{0}'".format(url_usgs)
            # print("URL: {0}".format(url))
            http_response = subprocess.Popen([url], shell=True,
                                             stdout=subprocess.PIPE).communicate()[0].decode()

        all_usgs_gages = InitialConditionCreator254.process_http_usgs_request_for_gauges_desc(
            http_response, pois_id_only=pois_id_only, pois_id_ignore=pois_id_ignore)

        # debug
        '''
        debug_file = "/Dedicated/IFC/Asynch_tools/initialcondition_generator_test/debug_gages.txt"
        with open(debug_file, "w+") as w_file:
            w_file.write(http_response.decode())
        print("Wrote: {0}".format(debug_file))
        # quit()
        '''

        print(" Retrieved {0} gages.".format(len(all_usgs_gages.keys())))

        return all_usgs_gages

    @staticmethod
    def retrieve_discharge_series_from_usgs_webservice(begin_date, end_date, usgs_gauges):
        """
        USEFUL
        :param begin_date: String containing date in the format '2016-03-19'
        :param end_date: String containing date in the format '2016-03-19'
        :param usgs_gauges: List of USGS geuges IDs
        :return: None. Changes are performed within usgs_gauges dictionary objects
        """

        if usgs_gauges is None:
            return

        if SystemStatus.HAS_URLLIB3:
            urllib3_http = urllib3.PoolManager()
            print("Retrieving gauges observed data with urllib3.")
        else:
            urllib3_http = None
            print("Retrieving gauges observed data using raw wget.")

        #
        print(" Calling {0} gages.".format(len(usgs_gauges.keys())))
        deleted_gages = []
        count_debug = None
        for cur_usgs_gauge_id in usgs_gauges.keys():

            # build URL
            url_usgs = 'http://nwis.waterdata.usgs.gov/ia/nwis/dv/' \
                       '?cb_00060=on&format=rdb&&begin_date={0}&end_date={1}&site_no={2}'
            url_usgs = url_usgs.format(begin_date, end_date, cur_usgs_gauge_id)

            # debug
            print("  URL: {0}".format(url_usgs))

            # retrieve HTTP data
            if SystemStatus.HAS_URLLIB3:
                http_response = http.request('GET', url_usgs).data.decode()
            else:
                http_response = subprocess.Popen(["wget -q -O - '{0}'".format(url_usgs)], shell=True,
                                                 stdout=subprocess.PIPE).communicate()[0].decode()

            cur_all_discharge_lines = InitialConditionCreator254.process_http_usgs_request(
                http_response, debug_file_id=cur_usgs_gauge_id)
            if (cur_all_discharge_lines is not None) and (len(cur_all_discharge_lines) > 0):
                cur_usgs_gauge = usgs_gauges[cur_usgs_gauge_id]
                minimum_discharge = min(cur_all_discharge_lines)
                cur_usgs_gauge.set_min_discharge(minimum_discharge)
                print("   Minimum discharge from gage {0}: {1}".format(cur_usgs_gauge.get_id(), minimum_discharge))
            else:
                print("   Unable to read.")
                deleted_gages.append(cur_usgs_gauge_id)

            if count_debug is not None:
                if count_debug > 0:
                    count_debug -= 1
                else:
                    break

        # delete gages
        print(" Ignoring {0} of {1} gages.".format(len(deleted_gages), len(usgs_gauges.keys())))
        for cur_del_gage in deleted_gages:
            del usgs_gauges[cur_del_gage]

    @staticmethod
    def get_usgs_gages_to_be_ignored(downstream_reservoirs=True):
        """

        :param downstream_reservoirs:
        :return:
        """

        return_list = []
        downstream_reservoirs_list = ["05487500", "edyi4", "OTMI4", "otmi4", "05489500", "05490500", "KEQI4", "keqi4",
                                      "05482000", "DMOI4", "dmoi4", "05485500", "DESI4", "desi4", "05488500",
                                      "trci4", "TRCI4", "05488110", "peli4", "PELI4", "rrdi4", "RRDI4"]  # downstream Coralville
        downstream_reservoirs_list.extend(["05454500", "IOWI4", "iowi4", "05455700", "LNTI4", "lnti4", "CJTI4", "cjti4",
                                           "05465500", "WAPI4", "wapi4"])  # downstream Saylorville
        if downstream_reservoirs:
            return_list.extend(downstream_reservoirs_list)

        return return_list if len(return_list) > 0 else None

    @staticmethod
    def retrieve_all_linkid_location_from_file():
        """
        USEFUL
        :return:
        """

        # debug
        # print("Read link locations")

        linkid_location_file_path = "/Dedicated/IFC/Asynch_tools/initialcondition_generator_lib/linkid_locations_uparea.csv"
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

        # debug
        # print("Link locations was read")

        return return_dict

    @staticmethod
    def build_grid_object(links_location, lat_resolution=1100, lng_resolution=1800):
        """
        USEFUL
        Related to the 'interpolate_discharge_lib()' function
        :param links_location:
        :param lat_resolution:
        :param lng_resolution:
        :return:
        """

        min_lat = float('inf')
        min_lng = float('inf')
        max_lat = -float('inf')
        max_lng = -float('inf')

        # define min/max lat/long from links
        for cur_link_location in links_location.values():
            cur_lat = cur_link_location.get_lat()
            cur_lng = cur_link_location.get_lng()
            min_lat = cur_lat if cur_lat < min_lat else min_lat
            min_lng = cur_lng if cur_lng < min_lng else min_lng
            max_lat = cur_lat if cur_lat > max_lat else max_lat
            max_lng = cur_lng if cur_lng > max_lng else max_lng

        # build grid
        the_grid_set = GridSet(min_lat, min_lng, max_lat, max_lng, lat_resolution, lng_resolution)

        return the_grid_set

    @staticmethod
    def interpolate_disch_area(usgs_linkds_discharge, links_location, output_state_file_path, output_graph_file_path=None,
                               base_snapshot_file_path=None, base_snapshot_inherit_states=None, interpolation_method="auto"):
        """

        :param usgs_linkds_discharge:
        :param links_location:
        :param output_state_file_path:
        :param output_graph_file_path:
        :param base_snapshot_file_path:
        :param base_snapshot_inherit_states:
        :return: True if able to generate state file. False otherwise.
        """

        # build interpolation grid
        print("Building grid object.")
        the_grid_set = InitialConditionCreator254.build_grid_object(links_location,
                                                                    lat_resolution=550,
                                                                    lng_resolution=900)
        print(" Grid object built.")

        # adding USGS gages to the grid
        print("Adding baseflow/area to grid object.")
        count_i = 0
        for cur_usgs_gauge in usgs_linkds_discharge.values():
            cur_discharge = cur_usgs_gauge.get_min_discharge()
            cur_upstream_area = cur_usgs_gauge.get_upstream_area()
            cur_c2 = cur_discharge / cur_upstream_area
            the_grid_set.set_value(cur_usgs_gauge.get_lat(), cur_usgs_gauge.get_lng(), cur_c2, for_interpolate=True)
            count_i += 1
        print(" Added {0} base flows to the grid object.".format(count_i))
        if count_i <= 0:
            return False

        # interpolating
        print("Creation of grid data started at {0}".format(datetime.now()))
        # the_grid_set.interpolate_linear(plot_it=True)
        if not the_grid_set.crate_griddata(output_graph_file_path, interpolation_method):
            return False

        print("Conversion from Ft/S to M/S started at {0}".format(datetime.now()))
        the_grid_set.set_up_other_variables(links_location)

        print("Saving values into file at {0}.".format(datetime.now()))
        the_grid_set.save_values(output_state_file_path, links_location, base_snapshot_file_path,
                                 base_snapshot_inherit_states)

        # TODO - continue from here
        # http://scipy-cookbook.readthedocs.io/items/RadialBasisFunctions.html#id1
        return True

    def __init__(self):
        return
