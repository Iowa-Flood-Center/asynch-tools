import json
import os


class JsonSettings:

    @staticmethod
    def create_scratch_file(file_path):
        """

        :param file_path:
        :return:
        """

        # basic check
        if file_path is None:
            print("Missing output file path.")
            return

        settings_obj = {
            "linkid_location_file": "LINKID_LOCATION_FILE_PATH",
            "baseflow_ini_date": "YYYY-MM-DD",
            "baseflow_end_date": "YYYY-MM-DD",
            "temporary_file_path": "TEMPORARY_FILE_PATH",
            "output_state_file_path": "OUTPUT_STATE_FILE_PATH",
            "output_graph_file_path": "OUTPUT_GRAPH_FILE_PATH",
            "toplayer_soil_water_column": 0.02,
            "k": 0.0000020425,
            "interpolation_method": "< griddata_linear / distance_weighted / thiessen / auto >",
            "base_snapshot_file_path": "< REC_FILE_PATH / H5_FILE_PATH / FILE_PATH_TEMPLATE / none >",
            "base_snapshot_states_inherit": [0, 1, 2, 4, 5, 6],
            "procedures": "[ download_data , interpolate ]",
            "gages_only_bounding_box": {
                "max_lat": 44.56,
                "min_lat": 40.14,
                "max_lng": -89.85,
                "min_lng": -97.12},
            "gages_only_csv": "< GAGES_ONLY_FILE_PATH / none >",
            "gages_ignore_csv": "< GAGES_ONLY_FILE_PATH / none >"}

        with open(file_path, "w") as w_file:
            json.dump(settings_obj, w_file, sort_keys=True, indent=4)
            print("Wrote file: {0}".format(file_path))

    @staticmethod
    def read_settings_file(file_path):
        """

        :param file_path:
        :return:
        """

        # read file
        json_obj = None
        try:
            with open(file_path, "r") as r_file:
                json_obj = json.load(r_file)
        except FileNotFoundError as e:
            print("File not found: {0}".format(file_path))
        except json.decoder.JSONDecodeError as e:
            print("Invalid JSON format: {0}".format(e.msg))

        # primary checks
        try:
            '''
            if not(os.path.exists(json_obj["output_folder"])) and (os.path.isdir(json_obj["output_folder"])):
                print("JSON settings 'output_folder' does not exist or is not a folder.")
                return None
            '''
            if "temporary_file_path" not in json_obj.keys():
                print("JSON settings 'temporary_file_path' parameter is missing.")
                return None
            if "output_state_file_path" not in json_obj.keys():
                print("JSON settings 'output_state_file_path' parameter is missing.")
                return None
            if (json_obj["output_state_file_path"] == "overwrite") and ("base_snapshot_file_path" not in json_obj):
                print("JSON settings 'output_state_file_path' is 'overwrite', but no base snapshot was given.")
                return None
            if (json_obj["output_state_file_path"] != "overwrite") and \
                            os.path.splitext(json_obj["output_state_file_path"])[1] not in (".h5", ".rec"):
                    print("JSON settings 'output_state_file_path' is not an .h5 or an .rec file.")
                    return None
            if not(os.path.exists(json_obj["linkid_location_file"])) and (os.path.isfile(json_obj["linkid_location_file"])):
                print("JSON settings 'linkid_location_file' does not exist or is not a folder.")
                return None
            if not JsonSettings.is_url_date(json_obj["baseflow_ini_date"]):
                print("JSON settings 'baseflow_ini_date' is not in proper YYYY-MM-DD format.")
                return None
            if not JsonSettings.is_url_date(json_obj["baseflow_end_date"]):
                print("JSON settings 'baseflow_end_date' is not in proper YYYY-MM-DD format.")
                return None
            if not(isinstance(json_obj["procedures"], list)):
                print("JSON settings 'procedures' is not a list (given as {0}).".format(type(json_obj["procedures"])))
                return None
            if (json_obj["gages_only_csv"] != "none") and (not os.path.exists(json_obj["gages_only_csv"])):
                print("JSON settings 'gages_only_csv' is not an existing file.")
                return None
            if (json_obj["gages_ignore_csv"] != "none") and (not os.path.exists(json_obj["gages_ignore_csv"])):
                print("JSON settings 'gages_ignore_csv' is not an existing file.")
                return None
            if not (float(json_obj["gages_only_bounding_box"]["max_lat"]) and
                    float(json_obj["gages_only_bounding_box"]["min_lat"]) and
                    float(json_obj["gages_only_bounding_box"]["max_lng"]) and
                    float(json_obj["gages_only_bounding_box"]["min_lng"])):
                print("JSON settings 'gages_only_bounding_box' is has at leas one non-float value.")
                return None
            if ("base_snapshot_file_path" in json_obj.keys()) and (json_obj["base_snapshot_file_path"] != "none"):
                if not os.path.exists(json_obj["base_snapshot_file_path"]):
                    print("JSON settings 'base_snapshot_file' is not an existing file.")
                    return None
                if os.path.splitext(json_obj["base_snapshot_file_path"])[1] not in (".h5", ".rec"):
                    print("JSON settings 'base_snapshot_file' is not an .h5 or an .rec file.")
                    return None
            if "base_snapshot_states_inherit" in json_obj.keys():
                if not isinstance(json_obj["base_snapshot_states_inherit"], list):
                    print("JSON settings 'base_snapshot_states_inherit' is not an list.")
                    return None
            if json_obj["interpolation_method"] not in ("griddata_linear", "distance_weighted", "thiessen", "auto"):
                print("JSON settings 'interpolation_method' is not one of accepted values:")
                print(" - griddata_linear : the most recommended, but requires scipy.interpolate library")
                print(" - distance_weighted : not that good and not that fast, but works.")
                print(" - thiessen : as slow as the 'distance_weighted', but also works ")
                print(" - auto : does 'griddata_linear' if possible, 'distance_weighted' otherwise")
                return None
        except KeyError as e:
            print("Missing key on settings JSON file: {0}.".format(e))
            return None
        return json_obj

    @staticmethod
    def read_gages_list_file(file_path):
        if (file_path is None) or (file_path == "none"):
            return None
        try:
            with open(file_path, 'r') as r_file:
                content = [l.strip() for l in r_file.read().split("\n")]
        except Exception as e:
            print(e)
            return None
        return content

    @staticmethod
    def is_url_date(eval_str):
        try:
            split_str = eval_str.split("-")
            y, m, d = int(split_str[0]), int(split_str[1]), int(split_str[2])
            return True
        except Exception:
            return False

    def __init__(self):
        return
