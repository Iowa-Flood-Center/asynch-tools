from def_lib import ArgumentsManager
import numpy as np
import h5py
import sys
import os

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Converts a snapshot file (.h5) from an hl-model format to another (example: from 254 to 195).")
    print("Usage: python file_converter_hlmodels_h5.py -mode MODE -in_path INPUT_PATH -out_path OUTPUT_PATH -out_hl HL")
    print("  MODE        : Must be 'f' for 'single file' or 'd' for 'directory of files'.")
    print("  INPUT_PATH  : Path for a .h5 file (if MODE=f) or for a folder containing .h5 files (if MODE=d).")
    print("  OUTPUT_PATH : Path for the new .h5 file (if MODE=f) or for the receiving directory (if MODE=d)")
    print("  HL          : An Asynch Hillslope-Link model code (example: 190, 195, 254...)")
    quit()

# ###################################################### ARGS ######################################################## #

# get arguments
mode_arg = ArgumentsManager.get_str(sys.argv, "-mode")
inpp_arg = ArgumentsManager.get_str(sys.argv, "-in_path")
outp_arg = ArgumentsManager.get_str(sys.argv, "-out_path")
outhl_arg = ArgumentsManager.get_int(sys.argv, "-out_hl")

# basic checks
if mode_arg is None:
    print("Missing '-mode' argument.")
    quit()
if inpp_arg is None:
    print("Missing '-in_path' argument.")
    quit()
if outp_arg is None:
    print("Missing '-out_path' argument.")
    quit()
if outhl_arg is None:
    print("Missing '-out_hl' argument.")
    quit()


# ###################################################### CLAS ######################################################## #

class InitialConditionConverter:

    _OUT_ASYNCH_VERSION = "1.3.2"

    @staticmethod
    def convert_directory(input_folder_path, output_folder_path, output_hlmodel_id):
        """

        :param input_folder_path:
        :param output_folder_path:
        :param output_hlmodel_id:
        :return:
        """

        # basic check - folders exist
        if (not os.path.exists(input_folder_path)) or (not os.path.isdir(input_folder_path)):
            print("Folder not found: {0}.".format(input_folder_path))
            return False
        elif (not os.path.exists(output_folder_path)) or (not os.path.isdir(output_folder_path)):
            print("Folder not found: {0}.".format(output_folder_path))
            return False

        #
        all_in_file_names = os.listdir(input_folder_path)
        for cur_in_file_name in all_in_file_names:
            if not cur_in_file_name.endswith(".h5"):
                continue
            cur_out_file_name = InitialConditionConverter.try_to_guess_output_file_name(cur_in_file_name,
                                                                                        output_hlmodel_id)
            cur_out_file_name = cur_out_file_name if cur_out_file_name is not None else None

            cur_in_file_path = os.path.join(input_folder_path, cur_in_file_name)
            cur_out_file_path = os.path.join(output_folder_path, cur_out_file_name)

            InitialConditionConverter.convert_file(cur_in_file_path, cur_out_file_path, output_hlmodel_id)

    @staticmethod
    def convert_file(input_file_path, output_file_path, output_hlmodel_id):
        """

        :param input_file_path:
        :param output_file_path:
        :param output_hlmodel_id:
        :return:
        """

        # basic check - file exists
        if not os.path.exists(input_file_path):
            print("File not found: {0}.".format(input_file_path))
            return False

        # get input hl-model version and basic check it
        input_hlmodel = InitialConditionConverter.identify_hlmodel_id(input_file_path)
        if input_hlmodel is None:
            print("Unable to identify HL-Model version of file: {0}".format(input_file_path))
            return False

        # route to proper converter
        if (input_hlmodel == 254) and (output_hlmodel_id == 195):
            return InitialConditionConverter.convert_from_254_to_195(input_file_path, output_file_path)
        else:
            print("Conversion from {0} to {1} not available.".format(input_hlmodel, output_hlmodel_id))
            print("  ({0}) and ({1})".format(type(input_hlmodel), type(output_hlmodel_id)))
            return False

    @staticmethod
    def identify_hlmodel_id(in_path):
        """

        :param in_path:
        :return:
        """

        try:
            with h5py.File(in_path, 'r') as hdf_file:
                return int(hdf_file.attrs['model'][0])
        except IndexError:
            return None

    @staticmethod
    def convert_from_254_to_195(in_path, out_path):
        """

        :param in_path:
        :param out_path:
        :return:
        """

        # read inp file
        with h5py.File(in_path, 'r') as r_file:
            unix_time = int(r_file.attrs['unix_time'][0])
            in_hdf_data = np.array(r_file.get('snapshot'))

        # basic check
        if in_hdf_data.size == 1:
            print("Unable to find 'snapshot' dataset in file: {0}.".format(in_path))
            return False

        # create data type
        dtype_arg = list()
        dtype_arg.append(("link_id", np.uint32))
        for cur_idx in range(4):
            dtype_arg.append(("state_{0}".format(cur_idx), np.float64))
        the_dtype = np.dtype(dtype_arg)

        # compress data
        compress_data = []
        for cur_hdf_row in in_hdf_data:
            cur_list = []
            cur_list.append(cur_hdf_row[0])                                 # link id
            cur_list.append(cur_hdf_row[1])                                 # discharge
            cur_list.append(cur_hdf_row[2])                                 # ponded water
            cur_list.append(float(cur_hdf_row[3]) + float(cur_hdf_row[4]))  # soil water
            cur_list.append(cur_hdf_row[5])                                 # acc. precip.

            cur_list_np = np.array(tuple(cur_list), dtype=the_dtype)
            compress_data.append(cur_list_np)

        # write output file
        with h5py.File(out_path, 'w') as w_file:
            w_file.attrs.create('model', [195], dtype='uint16')
            w_file.attrs.create('unix_time', [unix_time], dtype='uint32')
            w_file.attrs.create('version', InitialConditionConverter._OUT_ASYNCH_VERSION, dtype='S6')
            w_file.create_dataset('snapshot', dtype=the_dtype, data=compress_data, compression="gzip",
                                  compression_opts=5)

        print("Created file: {0}".format(out_path))
        return True

    @staticmethod
    def try_to_guess_output_file_name(input_file_name, output_hlmodel_id):
        """

        :param input_file_name:
        :param output_hlmodel_id:
        :return:
        """
        splitted_file_name = input_file_name.split('_')
        if len(splitted_file_name) != 2:
            return None
        if not splitted_file_name[0].startswith('state'):
            return None

        out_file_name = "state{0}_{1}".format(output_hlmodel_id, splitted_file_name[1])
        return out_file_name

    def __init__(self):
        return

# ###################################################### RUNS ######################################################## #

if mode_arg == "f":
    InitialConditionConverter.convert_file(inpp_arg, outp_arg, outhl_arg)
elif mode_arg == "d":
    InitialConditionConverter.convert_directory(inpp_arg, outp_arg, outhl_arg)
else:
    print("Unexpected value for '-mode' argument: '{0}'. Expecting 'f' or 'd'.")