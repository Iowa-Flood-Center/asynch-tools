from def_lib import ArgumentsManager
import datetime
import pytz
import sys
import os

selectmode_std = "fn"

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Delete all h5 files that are not monthly days 01, 11 and 21, hour 00, minute 00, second 00.")
    print("Usage: python initialconditions_selector_10days.py -folder FOLDERPATH [-sel_mode MODE]")
    print("  FOLDERPATH : Folder path in which a set of h5 files is stored")
    print("  MODE       : If 'fn' or None, evaluates timestamp in filename. If 'at', evaluates timestamp in attribute.")
    quit()

# ###################################################### ARGS ######################################################## #

# get arguments
folderpath_arg = ArgumentsManager.get_str(sys.argv, '-folder')
selectmode_arg = ArgumentsManager.get_str(sys.argv, '-sel_mode')
selectmode_arg = selectmode_std if selectmode_arg is None else selectmode_arg

# basic check
if folderpath_arg is None:
    print("Missing '-folder' argument.")
    quit()


# ###################################################### CLAS ######################################################## #

class TimestampsSelector:

    @staticmethod
    def accept(file_path, select_mode, days=(1, 11, 21)):
        """

        :param file_path:
        :param select_mode:
        :param days:
        :return:
        """

        # basic check
        if not file_path.endswith(".h5"):
            print("Ignoring '{0}': not a .h5 file.".format(file_path))
            return False

        if select_mode == 'fn':
            file_name = os.path.basename(file_path)
            local_tz = pytz.timezone("America/Chicago")
            fp_timestamp = int(file_name.split(".")[0].split("_")[-1])
            fp_datetime_nve = datetime.datetime.fromtimestamp(fp_timestamp)
            fp_datetime_tzn = local_tz.localize(fp_datetime_nve)
            fp_datetime_utc = fp_datetime_tzn.astimezone(pytz.utc)
            fp_day = int(fp_datetime_utc.strftime("%d"))
            fp_min = int(fp_datetime_utc.strftime("%H"))
            fp_sec = int(fp_datetime_utc.strftime("%M"))
            return True if ((fp_day in days) and (fp_min == 0) and (fp_sec == 0)) else False

        else:
            print("Selection mode '{0}' not implemented yet.".format(select_mode))
            return False

    def __init__(self):
        return


# ###################################################### DEFS ######################################################## #

def select_files(folder_path, select_mode):
    """

    :param folder_path:
    :param select_mode:
    :return:
    """

    all_filepaths = sorted([os.path.join(folder_path, fn) for fn in os.listdir(folder_path)])
    for cur_filepath in all_filepaths:
        if TimestampsSelector.accept(cur_filepath, select_mode):
            print("Let '{0}'.".format(cur_filepath))
        else:
            print("Delete '{0}'.".format(cur_filepath))
            os.remove(cur_filepath)

    print("Done.")

# ###################################################### CALL ######################################################## #

select_files(folderpath_arg, selectmode_arg)
