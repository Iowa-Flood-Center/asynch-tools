from def_lib import ArgumentsManager
import sys
import os


# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Check if a given .rvr file presents topological inconsistency (loops or downstream bifurcation).")
    print("Usage: python file_consistency_checker.py -in_rvr RVR_PATH [ -check loop|downbif|all ]")
    print("  RVR_PATH : Path for .rvr file to be evaluated.")
    print("  -check   : Use this flag to perform only one type of check. If missing, perform all. NOT IMPLEMENTED YET.")
    print("IMPORTANT: for big watersheds (50,000 links +), use processing queues (.job file).")
    quit()


# ###################################################### ARGS ######################################################## #

# get arguments
input_rvr_fpath_arg = ArgumentsManager.get_str(sys.argv, '-in_rvr')
check_arg = ArgumentsManager.get_str(sys.argv, '-check')

# basic checks
if input_rvr_fpath_arg is None:
    print("Missing '-in_rvr' argument.")
    quit()

if check_arg is not None:
    if check_arg not in ('loop', 'downbif', 'all'):
        print("Argument '-check' should be one of {0}.".format(check_arg))
    quit()
else:
    check_arg = 'all'


# ###################################################### SYST ######################################################## #

print("Increasing recursion limit size...")

# increase recursion limit
sys.setrecursionlimit(100000)


# ###################################################### DEFS ######################################################## #

def read_rvr_file(rvr_file_path):
    """
    Reads .rvr file and converts it into into a dictionary.
    :param rvr_file_path:
    :return: Dictionary of integers with format "link_id":[contr_link_id1, contr_link_id2, contr_link_id3, ...]
    """

    # basic check
    if not os.path.exists(rvr_file_path):
        print("File '{0}' does not exits.".format(rvr_file_path))
        return None

    # build dictionary
    return_dict = {}
    with open(rvr_file_path, "r+") as rfile:
        num_links = None
        last_linkid = None
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

            # get link id
            if (len(cur_line_split) == 1) and (last_linkid is None):
                last_linkid = int(cur_line_split[0])
                continue

            # get parent links
            if last_linkid is not None:

                if len(cur_line_split) == 1:
                    return_dict[last_linkid] = None
                else:
                    return_dict[last_linkid] = [int(v) for v in cur_line_split][1:]

                last_linkid = None
                continue

    print("Tracked {0} of {1}.".format(len(return_dict.keys()), num_links))
    return return_dict


def check_downstream_bifurcation(network_dictionary):
    """

    :param network_dictionary:
    :return:
    """

    # basic check
    if network_dictionary is None:
        return False

    # count drainages
    counts_drain = {}
    for cur_up_linkids in network_dictionary.values():
        if cur_up_linkids is None:
            continue

        for cur_up_linkid in cur_up_linkids:
            if cur_up_linkid not in counts_drain.keys():
                counts_drain[cur_up_linkid] = 0
            counts_drain[cur_up_linkid] += 1

    # check
    is_valid = True
    for cur_link_id, cur_count in counts_drain.items():
        if cur_count > 1:
            is_valid = False
            print("FAIL: Link id {0} is the upstream of {1} links.".format(cur_link_id, cur_count))

    if is_valid:
        print("Downstream Bifurcation check: SUCCESS")
    else:
        print("Downstream Bifurcation check: FAIL")
    return is_valid


def check_loop(network_dictionary):
    """

    :param network_dictionary:
    :return:
    """

    # basic check
    if network_dictionary is None:
        return False

    def check_loop_recursive(network_dictionary, root_linkid, current_linkid):
        """

        :param network_dictionary:
        :param root_linkid:
        :param current_linkid:
        :return:
        """
        if root_linkid == current_linkid:
            print("FAIL: Link id '{0}' has a loop.".format(current_linkid))
            return False

        if current_linkid not in network_dictionary.keys():
            print("FAIL: Link id '{0}' not described in rvr file.".format(current_linkid))
            return False

        upstream_link_ids = network_dictionary[current_linkid]

        # basic check - node
        if upstream_link_ids is None:
            return True

        # recursive it
        all_ok = True
        for cur_upstream_link_id in upstream_link_ids:
            cur_rec_ok = check_loop_recursive(network_dictionary, root_linkid, cur_upstream_link_id)
            all_ok = cur_rec_ok if not cur_rec_ok else all_ok

        return all_ok

    # base call
    is_valid = True
    for cur_link_id_down, cur_link_id_ups in network_dictionary.items():
        if cur_link_id_ups is None:
            continue
        for cur_link_id_up in cur_link_id_ups:
            cur_ok = check_loop_recursive(network_dictionary, cur_link_id_down, cur_link_id_up)
            is_valid = cur_ok if not cur_ok else is_valid

    if is_valid:
        print("Looping check: SUCCESS")
    else:
        print("Looping check: FAIL")
    return is_valid

# ###################################################### CALL ######################################################## #

rvr_network = read_rvr_file(input_rvr_fpath_arg)
check_downstream_bifurcation(rvr_network)
check_loop(rvr_network)
