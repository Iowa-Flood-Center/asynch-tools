from def_lib import ArgumentsManager
from datetime import datetime
from calendar import timegm
import numpy as np
import pytz
import time
import h5py
import sys
import os

has_error = False
asynch_version_default = '1.3'

# ###################################################### ARGS ######################################################## #

# help message
if '-h' in sys.argv:
    print("Converts a .rec file or all .rec files in a folder into a .h5 files or a set of .h5 files, respectively.")
    print("Usage: python file_converter_rec_to_h5.py -mode MODE -input INPUT_PATH -output OUTPUT_PATH [-version VERSION]")
    print("  MODE        : Must be 'f' for 'single file' or 'd' for 'directory of files'.")
    print("  INPUT_PATH  : Path for a .rec file (if MODE=f) or for a folder containing .h5 files (if MODE=d).")
    print("  OUTPUT_PATH : Path for the new .h5 file (if MODE=f) or for the receiving directory (if MODE=d)")
    print("  VERSION : Asynch version. Expects values '1.2' or '1.3'. If not provided, it is assumed '1.3'.")
    quit()

# get all arguments and perform basic check

mode_arg = ArgumentsManager.get_str(sys.argv, "-mode")
if mode_arg is None:
    print("Missing '-mode' argument.")
    quit(0)

inpt_arg = ArgumentsManager.get_str(sys.argv, "-input")
if mode_arg is None:
    print("Missing '-input' argument.")
    quit(0)

outt_arg = ArgumentsManager.get_str(sys.argv, "-output")
if mode_arg is None:
    print("Missing '-output' argument.")
    quit(0)

vers_arg = ArgumentsManager.get_str(sys.argv, "-version")
if vers_arg is None:
    vers_arg = asynch_version_default
elif vers_arg not in ('1.2', '1.3'):
    print("Invalid '-version' argument: '{0}'. Expected '1.2' or '1.3'.".format(vers_arg))
    quit(0)


# ###################################################### DEFS ######################################################## #

def convert_file(input_file_path, output_file_path, asynch_version):
    """

    :param input_file_path:
    :param output_file_path:
    :return: True if able to convert file, False otherwise
    """

    # basic checks - input file must exist and have .rec extension
    if not os.path.exists(input_file_path):
        print("File does not exist: '{0}'.".format(input_file_path))
        return False
    if not input_file_path.endswith(".rec"):
        print("File does not have .rec extension: '{0}'.".format(input_file_path))
        return False

    # tries to extract timestamp from file name
    # TODO - perform it
    init_timestamp = extract_timestamp_from_filepath(input_file_path)

    # basic check
    if init_timestamp is None:
        print("Invalid filename '{0}': must have format '..._YYYY_MM_DD.rec'".format(os.path.basename(input_file_path)))
        return False

    # print("Got '{0}' from '{1}'.".format(init_timestamp, input_file_path))

    # write hdf5 file
    if asynch_version == '1.2':
        convert_file_1_2(input_file_path, output_file_path, init_timestamp=init_timestamp)
    elif asynch_version == '1.3':
        convert_file_1_3(input_file_path, output_file_path, init_timestamp=init_timestamp)
    else:
        return False

    print("Wrote file '{0}'.".format(output_file_path))

    # did it
    return True


def convert_file_1_2(input_file_path, output_file_path, init_timestamp=0):
    """

    :param input_file_path:
    :param output_file_path:
    :param init_timestamp:
    :return:
    """

    # read rec file and stores content in 'link_ids' and 'link_prm' variables
    with open(input_file_path, "r") as rfile:
        link_ids = []
        link_prm = []
        line_count = 1
        hlm_id = None
        for cur_line in rfile:
            cur_line_clean = cur_line.strip()
            if line_count == 1:
                hlm_id = int(cur_line.strip())
            elif (line_count not in (1, 2, 3)) and (cur_line.strip() != ""):
                cur_line_split = cur_line_clean.split(" ")
                if len(cur_line_split) == 1:
                    link_ids.append(int(cur_line_clean))
                else:
                    link_prm.append([float(cur_line_split[i]) for i in range(len(cur_line_split))])
            line_count += 1

    # basic check
    if hlm_id is None:
        print("Hillslope-Link Model id not identified.")
        return False

    # write hdf5 file
    with h5py.File(output_file_path, 'w') as wfile:
        wfile.attrs.create('model', [hlm_id], dtype='uint16')
        wfile.attrs.create('unix_time', [init_timestamp], dtype='uint32')
        wfile.create_dataset('index', data=link_ids, dtype='uint32')
        wfile.create_dataset('state', data=link_prm)

    # did it
    return True


def convert_file_1_3(input_file_path, output_file_path, init_timestamp=0):
    """

    :param input_file_path:
    :param output_file_path:
    :param init_timestamp:
    :return:
    """

    # read rec file and stores content in 'link_ids' and 'link_prm' variables
    with open(input_file_path, "r") as rfile:
        link_ids = []
        link_prm = []
        link_prms = []
        line_count = 1
        hlm_id = None
        for cur_line in rfile:
            cur_line_clean = cur_line.strip()
            if line_count == 1:
                hlm_id = int(cur_line.strip())
            elif (line_count not in (1, 2, 3)) and (cur_line.strip() != ""):
                cur_line_split = cur_line_clean.split(" ")
                if len(cur_line_split) == 1:
                    link_ids.append(np.uint32(int(cur_line_clean)))
                else:
                    cur_params = [np.float64(float(cur_line_split[i])) for i in range(len(cur_line_split))]

                    link_prms.append(cur_params)

                    # build matrix if necessary
                    if len(link_prm) == 0:
                        for cur_state in range(len(cur_params)):
                            link_prm.append([])

                    # fill content
                    for cur_idx, cur_val in enumerate(cur_params):
                        link_prm[cur_idx].append(cur_val)
            line_count += 1

    # basic check
    if hlm_id is None:
        print("Hillslope-Link Model id not identified.")
        return False

    # create data type
    dtype_arg = list()
    dtype_arg.append(("link_id", np.uint32))
    for cur_idx in range(len(link_prm)):
        dtype_arg.append(("state_{0}".format(cur_idx), np.float64))
    the_dtype = np.dtype(dtype_arg)

    # compress data
    compress_data = []
    for cur_idx in range(len(link_ids)):
        cur_list = [link_ids[cur_idx]]
        for cur_par in link_prms[cur_idx]:
            cur_list.append(cur_par)
        cur_list_np = np.array(tuple(cur_list), dtype=the_dtype)
        compress_data.append(cur_list_np)

    # write hdf5 file
    with h5py.File(output_file_path, 'w') as wfile:
        wfile.attrs.create('model', [hlm_id], dtype='uint16')
        wfile.attrs.create('unix_time', [init_timestamp], dtype='uint32')
        wfile.attrs.create('version', "1.3.2", dtype='S6')
        wfile.create_dataset('snapshot', dtype=the_dtype, data=compress_data, compression="gzip", compression_opts=5)

    # did it
    return True


def extract_timestamp_from_filepath(filepath):
    """

    :param filepath:
    :return:
    """

    file_basename = os.path.basename(os.path.splitext(filepath)[0])
    splitted_filename = file_basename.split("_")

    if len(splitted_filename) == 1:
        return None
    elif len(splitted_filename) == 2:
        try:
            return int(splitted_filename[1])
        except ValueError:
            return None
    elif len(splitted_filename) == 4:
        try:
            year = splitted_filename[1]
            month = splitted_filename[2]
            day = splitted_filename[3]

            time_string = "{0}-{1}-{2} 00:00:00 GMT".format(year, month, day)

            timestamp = timegm(time.strptime(time_string, '%Y-%m-%d %H:%M:%S %Z'))

            return timestamp
        except ValueError:
            return None


def convert_directory(input_dir_path, output_dir_path, asynch_version):
    """

    :param input_dir_path:
    :param output_dir_path:
    :return:
    """

    # basic checks
    if not os.path.exists(input_dir_path):
        print("Directory does not exist: '{0}'.".format(input_dir_path))
        return False
    if not os.path.exists(output_dir_path):
        print("Directory does not exist: '{0}'.".format(output_dir_path))
        return False

    # list all rec files in input directory
    all_rec_file_names = []
    for cur_file_name in os.listdir(input_dir_path):
        if cur_file_name.endswith(".rec"):
            all_rec_file_names.append(cur_file_name)

    # convert each of listed files
    for cur_rec_file_name in all_rec_file_names:
        cur_hf5_file_name = cur_rec_file_name.replace(".rec", ".h5")
        cur_hf5_file_path = os.path.join(output_dir_path, cur_hf5_file_name)
        cur_rec_file_path = os.path.join(input_dir_path, cur_rec_file_name)
        convert_file(cur_rec_file_path, cur_hf5_file_path, asynch_version)


# ###################################################### CALL ######################################################## #

if mode_arg == 'd':
    convert_directory(inpt_arg, outt_arg, vers_arg)
elif mode_arg == 'f':
    convert_file(inpt_arg, outt_arg, vers_arg)
else:
    print("Unexpected argument for mode: '{0}'. Expects 'f' or 'd'.".format(mode_arg))
