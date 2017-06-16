from def_lib import ArgumentsManager
import sys

default_swc = 0.02
default_k3 = 0.000002042

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Creates an initial condition file (.rec) extrapolating the discharge/area coefficient given at the outlet of a given drainage network.")
    print("Usage: python initialconditions_generator_254_idealized.py -in_prm IN_PRM -ref_linkid LINK_ID -disc DISCHARGE -out_rec OUT_REC [-swc SWC] [-k3 K3]")
    print("  IN_PRM    : File path for the .prm file of the modeled system.")
    print("  LINK_ID   : Integer with the link id of the link taken as reference. Usually the outlet of a watersed.")
    print("  DISCHARGE : Discharge value, in m3/s, at the reference link.")
    print("  SWC       : Soil Water Column value in all links. If not provided, it is assumed 0.02.")
    print("  K3        : Value of k3 coefficient. If not provided, it is assumed 0.000002042.")
    quit()

# ###################################################### ARGS ######################################################## #

# get arguments
input_fpath_arg = ArgumentsManager.get_str(sys.argv, '-in_prm')
reference_linkid_arg = ArgumentsManager.get_int(sys.argv, '-ref_linkid')
reference_discharge_arg = ArgumentsManager.get_flt(sys.argv, '-disc')
output_fpath_arg = ArgumentsManager.get_str(sys.argv, '-out_rec')
swc_arg = ArgumentsManager.get_flt(sys.argv, '-swc')
k3_arg = ArgumentsManager.get_flt(sys.argv, '-k3')

# basic checks
if input_fpath_arg is None:
    print("Missing '-in_prm' argument.")
    quit()
if reference_linkid_arg is None:
    print("Missing '-ref_linkid' argument.")
    quit()
if reference_discharge_arg is None:
    print("Missing '-disc' argument.")
    quit()
if output_fpath_arg is None:
    print("Missing '-out_rec' argument.")
    quit()
the_swc = swc_arg if swc_arg is not None else default_swc
the_k3 = k3_arg if k3_arg is not None else default_k3


# ###################################################### CLAS ######################################################## #

def read_prm_file(file_path):
    """

    :param file_path:
    :return:
    """

    num_links = None
    read_header = False
    last_link_id = None
    return_dict = {}
    with open(file_path, "r+") as rfile:
        for cur_line in rfile:
            cur_line = cur_line.strip()
            # read header
            if not read_header:
                num_links = int(cur_line)
                read_header = True
                continue

            # ignore blank lines
            if cur_line == "":
                continue

            if last_link_id is None:
                last_link_id = int(cur_line)
                continue
            else:
                return_dict[last_link_id] = [float(v) for v in cur_line.split(" ")]
                last_link_id = None
                continue

    # basic check
    if num_links != len(return_dict.keys()):
        print("Be careful! PRM file has a header of '{0}' but describes '{1}' links.".format(num_links,
                                                                                             len(return_dict.keys())))

    return return_dict


def write_rec_file(output_fpath, prm_content, ref_linkid, ref_discharg, swc, k3):
    """

    :param output_fpath:
    :param prm_content:
    :param ref_linkid:
    :param ref_discharg:
    :param swc:
    :param k3:
    :return:
    """

    # define ratio disch/up_area
    ref_up_area = prm_content[ref_linkid][0]
    c2 = ref_discharg / ref_up_area

    with open(output_fpath, "w+") as wfile:
        # write header
        wfile.write("254\n")
        wfile.write("{0}\n".format(len(prm_content.keys())))
        wfile.write("0.0\n")
        wfile.write("\n")
        print("Wrote header.")

        # write states
        for cur_linkid in prm_content.keys():
            cur_link_area = prm_content[cur_linkid][0]
            tq = c2 * cur_link_area               # total discharge
            ss = c2 / k3 * 0.06 / 1000            # water stored in subsurface
            pd = 0                                # water ponded in surface
            sw = swc                              # soil in topy layer
            ap = 0                                # accumulated precipitation
            ar = 0                                # accumulated runoff
            bq = tq                               # base flow
            wfile.write("{0}\n".format(cur_linkid))
            wfile.write("{0} {1} {2} {3} {4} {5} {6}\n".format(tq, pd, sw, ss, ap, ar, bq))

    print("Wrote file '{0}'.".format(output_fpath))


# ###################################################### RUNS ######################################################## #

prm_file_content = read_prm_file(input_fpath_arg)
write_rec_file(output_fpath_arg, prm_file_content, reference_linkid_arg, reference_discharge_arg, the_swc, the_k3)
