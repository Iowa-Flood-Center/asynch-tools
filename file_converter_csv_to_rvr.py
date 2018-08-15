from def_lib import ArgumentsManager
import sys

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Usage: python file_converter_csv_to_rvr.py -in_csv CSV_PATH -out_rvr RVR_PATH")
    print("  CSV_PATH : File path for input .csv file.")
    print("  RVR_PATH : File path for output .rvr file.")
    quit()

# ###################################################### ARGS ######################################################## #

# get arguments
input_csv_fpath_arg = ArgumentsManager.get_str(sys.argv, '-in_csv')
output_rvr_fpath_arg = ArgumentsManager.get_str(sys.argv, '-out_rvr')

# basic checks
if input_csv_fpath_arg is None:
    print("Missing '-in_csv' argument.")
    quit()
if output_rvr_fpath_arg is None:
    print("Missing '-out_rvr' argument.")
    quit()


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
            splitted = [int(i.strip()) for i in clean_line.split(",")]
            if len(splitted) != 2:
                continue
            return_dict[splitted[0]] = splitted[1]
            link_count += 1

    return return_dict, link_count


def invert_refs(csv_dict):
    """

    :param csv_dict:
    :return: Dictionary
    """

    return_dict = {}
    for cur_link_cont, cur_link_dest in csv_dict.items():
        if cur_link_dest not in return_dict.keys():
            return_dict[cur_link_dest] = []
        if cur_link_cont not in return_dict.keys():
            return_dict[cur_link_cont] = []
        return_dict[cur_link_dest].append(cur_link_cont)

    return return_dict


def write_file(inverted_tree, total_links, out_file_path):
    """

    :param inverted_tree:
    :param out_file_path:
    :return:
    """

    with open(out_file_path, "w+") as w_file:
        w_file.write(str(total_links))
        w_file.write("\n")
        w_file.write("\n")

        for rec_link_id, cont_link_ids in inverted_tree.items():
            w_file.write(str(rec_link_id))
            w_file.write(" ")
            w_file.write(str(len(cont_link_ids)))
            w_file.write(" ")
            for cur_link in cont_link_ids:
                w_file.write(str(cur_link))
                w_file.write(" ")
            w_file.write("\n")

    print("Wrote file {0}.".format(out_file_path))


# ###################################################### CALL ######################################################## #

csv_cont, num_links = read_csv_file(input_csv_fpath_arg)
inv_dict = invert_refs(csv_cont)
write_file(inv_dict, num_links, output_rvr_fpath_arg)
