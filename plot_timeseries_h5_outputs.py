from def_lib import ArgumentsManager
import numpy as np
import h5py
import sys
import os

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Reads a sequence of snapshot files in .h5 format and generates a timeseries for a specific state.")
    print("Usage: python plot_timeseries_h5_outputs.py -linkid LINKID -h5_file FILE_H5 -field FIELDID [-out OUTPUT]")
    print("  LINKID   : Integer. A valid link id.")
    print("  FILE_H5  : String. Path for first 'h5' file in sequence of outputs.")
    print("  FIELDID  : Integer. Index of the state column in h5 file to be printed. Starts on 0.")
    print("  OUTPUT   : String. Path for the CSV file to be generated. If None, send to std. output.")
    quit()


# ###################################################### ARGS ######################################################## #

# get arguments
link_id_arg = ArgumentsManager.get_int(sys.argv, '-linkid')
first_h5_arg = ArgumentsManager.get_str(sys.argv, '-h5_file')
field_num_arg = ArgumentsManager.get_int(sys.argv, '-field')
output_arg = ArgumentsManager.get_str(sys.argv, '-out')

# basic checks
if link_id_arg is None:
    print("Missing '-linkid' argument.")
    quit()
if first_h5_arg is None:
    print("Missing '-h5_file' argument.")
    quit()
if field_num_arg is None:
    print("Missing '-field' argument.")
    quit()


# ###################################################### CLAS ######################################################## #

class DebugFileContent:

    @staticmethod
    def get_timestamp_from_filepath(self, filepath):
        """

        :param self:
        :param filepath:
        :return:
        """



    @staticmethod
    def read_all_h5(first_h5_file_path, field_num, link_id):
        """

        :param first_h5_file_path:
        :param field_num:
        :param link_id:
        :param output_path:
        :return:
        """

        # basic check - file must exist
        if not os.path.exists(first_h5_file_path):
            print("File does not exist: {0}.".format(first_h5_file_path))
            return None

        return_array = []

        # get folder and list all internal files
        inp_files_folder = os.path.dirname(first_h5_file_path)
        all_file_names = sorted(os.listdir(inp_files_folder))

        # iterates over the files
        first_file_found = False
        total_files = len(all_file_names)
        for cur_i, cur_filename in enumerate(all_file_names):

            print("Reading file {0} out of {1}.".format(cur_i, total_files))

            # check if current file comes after first one
            if not first_file_found:
                if cur_filename == os.path.basename(first_h5_file_path):
                    first_file_found = True
                else:
                    continue

            # read file
            cur_filepath = os.path.join(inp_files_folder, cur_filename)
            with h5py.File(cur_filepath, 'r') as hdf_file:
                cur_hdf_data = np.array(hdf_file.get('snapshot'))
                cur_hdf_timestamp = int(hdf_file.attrs['unix_time'][0])

            # get row related to given link
            cur_link_states = None
            for cur_hdf_row in cur_hdf_data:

                if cur_hdf_row[0] != link_id:
                    continue

                cur_link_states = list(cur_hdf_row)[1:-1]
                break

            # basic check
            if cur_link_states is None:
                print("No link {0} in '{1}'.".format(link_id, cur_filepath))
                continue

            # basic check
            if len(cur_link_states) <= field_num:
                print("Only {0} states in '{1}'.".format(len(cur_link_states), cur_filepath))
                continue

            return_array.append((cur_hdf_timestamp, cur_link_states[field_num]))
            # print("Column {0} = {1} in {2}".format(field_num, cur_link_states[field_num], cur_filepath))

        return return_array

    @staticmethod
    def print_timesries(the_timeseries, field_num, output_path=None):
        """

        :param the_timeseries:
        :param field_num:
        :param output_path:
        :return:
        """

        # basic check
        if the_timeseries is None:
            print("No timeseries readen.")
            return

        # open var
        file_w = None

        # print header
        if output_path is None:
            print("Timestamp, Field {0}".format(field_num))
        else:
            file_w = open(output_path, "w+")
            file_w.write('"Timestamp", "Field {0}"\n'.format(field_num))

        # print timeseries
        for cur_timepair in the_timeseries:
            if output_path is None:
                print("{0}, {1}".format(cur_timepair[0], cur_timepair[1]))
            else:
                file_w.write("{0}, {1}\n".format(cur_timepair[0], cur_timepair[1]))

        # wrap it up
        if file_w is not None:
            print("Wrote file '{0}'.".format(output_path))
            file_w.close()

    def __init__(self):
        return


# ###################################################### CALL ######################################################## #

# ### make the call

if first_h5_arg.endswith('h5'):
    files_timeseries = DebugFileContent.read_all_h5(first_h5_arg, field_num_arg, link_id_arg)
    DebugFileContent.print_timesries(files_timeseries, field_num_arg, output_path=output_arg)

else:
    print("Strange value for -fext:{0}.".format(fext))
