from accumulate_attribute_in_tree_lib.DistancesDefiner import DistancesDefiner
from def_lib import ArgumentsManager
import sys

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Usage: python accumulate_attribute_in_tree.py -in_csv IN_CSV_PATH -in_rvr IN_RVR_PATH -linkid LINK_ID -out_csv OUT_CSV_PATH DIRECTION FLAG")
    print("  IN_CSV_PATH    : File path for input .csv file with lines 'link_id,attribute'.")
    print("  IN_RVR_PATH    : File path for input .rvr file.")
    print("  LINK_ID        : Outlet link id.")
    print("  OUT_CSV_PATH   : File path for output .csv file.")
    print("  DIRECTION_FLAG : Accumulation direction flag. Expected '-up' or '-down'.")
    quit()

# ###################################################### ARGS ######################################################## #

# get arguments
input_csv_fpath_arg = ArgumentsManager.get_str(sys.argv, '-in_csv')
input_rvr_fpath_arg = ArgumentsManager.get_str(sys.argv, '-in_rvr')
input_linkid_arg = ArgumentsManager.get_int(sys.argv, '-linkid')
output_csv_fpath_arg = ArgumentsManager.get_str(sys.argv, '-out_csv')
is_up_arg = ArgumentsManager.get_flag(sys.argv, "-up")
is_down_arg = ArgumentsManager.get_flag(sys.argv, "-down")

# basic checks
if input_csv_fpath_arg is None:
    print("Missing '-in_csv' argument.")
    quit()
if input_rvr_fpath_arg is None:
    print("Missing '-in_rvr' argument.")
    quit()
if input_linkid_arg is None:
    print("Missing '-linkid' argument.")
    quit()
if output_csv_fpath_arg is None:
    print("Missing '-out_csv' argument.")
    quit()
if is_up_arg and is_down_arg:
    print("Only one flag '-up' or '-down' must be given, not both.")
    quit()
if (not is_up_arg) and (not is_down_arg):
    print("Missing '-up' or '-down' argument.")
    quit()

# ###################################################### DEFS ######################################################## #

sys.setrecursionlimit(10000)


# ###################################################### DEFS ######################################################## #

def read_csv_file(csv_file_path):
    """

    :param csv_file_path:
    :return:
    """

    return_dict = {}
    link_count = 1
    with open(csv_file_path, "r") as r_file:
        for line in r_file:
            clean_line = line.strip()
            if clean_line == "":
                continue
            splitted = [float(i.strip()) for i in clean_line.split(",")]
            if len(splitted) != 2:
                continue
            return_dict[int(splitted[0])] = splitted[1]
            link_count += 1

    return return_dict, link_count


def read_rvr_file(rvr_file_path):
    """
    Reads .rvr file and converts it into into a dictionary.
    :param rvr_file_path:
    :return: Dictionary of integers with format "link_id":[contr_link_id1, contr_link_id2, contr_link_id3, ...]
    """

    return_dict = {}
    with open(rvr_file_path, "r+") as rfile:
        num_links = None

        for cur_line in rfile:
            cur_line_clear = cur_line.strip()

            # ignore blank lines
            if cur_line_clear == "":
                continue

            # get header
            if num_links is None:
                num_links = int(cur_line_clear)
                continue

            cur_line_split = cur_line_clear.split(" ")

            if len(cur_line_split) < 2:
                continue

            link_id = int(cur_line_split[0])
            num_parents = int(cur_line_split[1])

            if num_parents == 0:
                return_dict[link_id] = None
            else:
                return_dict[link_id] = [int(v) for v in cur_line_split][2:]

    print("Tracked {0} of {1}.".format(len(return_dict.keys()), num_links))
    return return_dict


def write_out_file(acc_dict, output_csv_file_path):
    """

    :param acc_dict:
    :param output_csv_file_path:
    :return:
    """

    if acc_dict is None:
        print("Output file was NOT generated.")
        return

    with open(output_csv_file_path, "w+") as w_file:
        for cur_link_id, cur_accumulated_value in acc_dict.items():
            w_file.write("{0},{1}".format(cur_link_id, cur_accumulated_value))
            w_file.write("\n")

    print("Wrote file '{0}'.".format(output_csv_file_path))
    return

# ###################################################### CALL ######################################################## #

csv_data, num_links = read_csv_file(input_csv_fpath_arg)
print("Got attributes of {0} links.".format(len(csv_data.keys())))
rvr_data = read_rvr_file(input_rvr_fpath_arg)
print("Got connectivity for of {0} links.".format(len(rvr_data.keys())))
if is_up_arg:
    print("Accumulating 'up'.")
    acc_data = DistancesDefiner.calculate_links_accumulated_attributes_up(input_linkid_arg, rvr_data, csv_data)
else:
    print("Accumulating 'down'.")
    acc_data = DistancesDefiner.calculate_links_accumulated_attributes_down(input_linkid_arg, rvr_data, csv_data)
write_out_file(acc_data, output_csv_fpath_arg)
