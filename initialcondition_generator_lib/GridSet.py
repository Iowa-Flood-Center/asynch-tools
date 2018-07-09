from datetime import datetime
import numpy as np
import h5py

from initialcondition_generator_lib.SystemStatus import SystemStatus

if SystemStatus.HAS_SCIPYINTERPOL:
    from scipy.interpolate import griddata
if SystemStatus.HAS_MATPLOTLIB:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt


class GridSet:
    _max_lat_value = None
    _min_lat_value = None
    _max_lng_value = None
    _min_lng_value = None
    _grid = None           # expected to have a 2D matrix of doubles with shape [self._lng_res X self._lat_res] of Cs
    _min_lat = None
    _max_lat = None
    _min_lng = None
    _max_lng = None
    _lat_res = None
    _lng_res = None
    _x_set = None
    _y_set = None
    _z_set = None
    _swc = None

    k = 0.0000020425

    @staticmethod
    def set_swc(new_swc_value):
        GridSet._swc = new_swc_value

    def _get_x(self, lng):
        return ((self._lng_res - 1)/(self._max_lng - self._min_lng))*(lng - self._min_lng)

    def _get_y(self, lat):
        return ((self._lat_res - 1)/(self._max_lat - self._min_lat))*(lat - self._min_lat)

    def __init__(self, min_lat, min_lng, max_lat, max_lng, lat_res, lng_res):
        self._min_lat = min_lat
        self._max_lat = max_lat
        self._min_lng = min_lng
        self._max_lng = max_lng
        self._lat_res = lat_res
        self._lng_res = lng_res

    def set_value(self, lat, lng, value, for_interpolate=False):
        if for_interpolate:
            if self._x_set is None:
                self._x_set = []
                self._y_set = []
                self._z_set = []
            self._x_set.append(lng)
            self._y_set.append(lat)
            self._z_set.append(value)

    def interpolate_rbf(self, plot_file_path=None):
        """

        :param plot_file_path:
        :return:
        """

        # adding extra corner fake points
        max_x_idx = self._x_set.index(max(self._x_set))
        min_x_idx = self._x_set.index(min(self._x_set))
        max_y_idx = self._y_set.index(max(self._y_set))
        min_y_idx = self._y_set.index(min(self._y_set))
        max_x_min_y = ((self._z_set[max_x_idx])+(self._z_set[min_y_idx]))/2
        max_x_max_y = ((self._z_set[max_x_idx]) + (self._z_set[max_y_idx]))/2
        min_x_min_y = ((self._z_set[min_x_idx]) + (self._z_set[min_y_idx]))/2
        min_x_max_y = ((self._z_set[min_x_idx]) + (self._z_set[max_y_idx]))/2
        self._x_set.extend((self._max_lng, self._max_lng, self._min_lng, self._min_lng))
        self._y_set.extend((self._min_lat, self._max_lat, self._min_lat, self._max_lat))
        self._z_set.extend((max_x_min_y, max_x_max_y, min_x_min_y, min_x_max_y))
        print("Added ({0},{1}), ({2},{3}), ({4},{5}), ({6},{7})".format(self._max_lng, self._min_lat,
                                                                        self._max_lng, self._max_lat,
                                                                        self._min_lng, self._min_lat,
                                                                        self._min_lng, self._max_lat))

        # interpolating
        print("interpolate_rbf: x set has {0}, y set has {1}, z set has {2}".format(len(self._x_set), len(self._y_set),
                                                                                len(self._z_set)))
        rbf = Rbf(self._x_set, self._y_set, self._z_set)
        xi, yi = np.meshgrid(np.linspace(self._min_lng, self._max_lng, self._lng_res),
                             np.linspace(self._min_lat, self._max_lat, self._lat_res))
        self._grid = rbf(xi, yi)

        # plot it
        if plot_file_path is not None:
            plt.subplot(1, 1, 1)
            plt.pcolor(xi, yi, self._grid, cmap=cm.jet)
            plt.title('RBF interpolation - multiquadrics')
            plt.xlim(self._min_lng, self._max_lng)
            plt.ylim(self._min_lat, self._max_lat)
            plt.colorbar()
            # plt.scatter(self._x_set, self._y_set, 100, self._z_set, cmap=cm.jet)
            plt.savefig(plot_file_path)

    def crate_griddata(self, plot_file_path=None, interpolation_method="auto"):
        """
        Interpolates
        :param plot_file_path:
        :param interpolation_method:
        :return:
        """

        # MINE - adding extra corner fake points with averages
        max_x_idx = self._x_set.index(max(self._x_set))
        min_x_idx = self._x_set.index(min(self._x_set))
        max_y_idx = self._y_set.index(max(self._y_set))
        min_y_idx = self._y_set.index(min(self._y_set))
        max_x_min_y = ((self._z_set[max_x_idx]) + (self._z_set[min_y_idx])) / 2
        max_x_max_y = ((self._z_set[max_x_idx]) + (self._z_set[max_y_idx])) / 2
        min_x_min_y = ((self._z_set[min_x_idx]) + (self._z_set[min_y_idx])) / 2
        min_x_max_y = ((self._z_set[min_x_idx]) + (self._z_set[max_y_idx])) / 2
        self._x_set.extend((self._max_lng, self._max_lng, self._min_lng, self._min_lng))
        self._y_set.extend((self._min_lat, self._max_lat, self._min_lat, self._max_lat))
        self._z_set.extend((max_x_min_y, max_x_max_y, min_x_min_y, min_x_max_y))

        # create mesh grid using scipy tools
        x_griddata, y_griddata = np.meshgrid(np.linspace(self._min_lng, self._max_lng, self._lng_res),
                                             np.linspace(self._min_lat, self._max_lat, self._lat_res))

        effective_method = None
        Ti = None

        if (not SystemStatus.HAS_SCIPYINTERPOL) and (interpolation_method == "griddata_linear"):
            print(" Unable to use griddata_linear method: scipy.interpol not available.")
            return False

        elif SystemStatus.HAS_SCIPYINTERPOL and (interpolation_method in ("griddata_linear", "auto")):

            effective_method = "griddata_linear"
            print(" Interpolating using griddata linear method at {0}.".format(datetime.now()))
            x_array = np.asarray(self._x_set)
            y_array = np.asarray(self._y_set)
            z_array = np.asarray(self._z_set)
            Ti = griddata((x_array, y_array), z_array, (x_griddata, y_griddata), method='linear')
            self._grid = Ti.T

        elif (interpolation_method == "distance_weighted") or \
                ((not SystemStatus.HAS_SCIPYINTERPOL) and (interpolation_method == "auto")):

            effective_method = "distance_weighted"
            print(" Interpolating using inverse distance weighted {0}.".format(datetime.now()))
            # create grid 'dumbly'
            self._grid = np.empty((self._lng_res, self._lat_res), dtype=np.float32)
            lng_min = min(self._x_set)
            lat_min = min(self._y_set)
            lng_res = (max(self._x_set) - lng_min) / self._lng_res
            lat_res = (max(self._y_set) - lat_min) / self._lat_res
            for cur_x in range(0, self._lng_res):
                cur_lng = ((cur_x + 0.5) * lng_res) + lng_min
                for cur_y in range(0, self._lat_res):
                    cur_lat = ((cur_y + 0.5) * lat_res) + lat_min
                    acc_up = 0
                    acc_div = 0
                    for cur_obs_x, cur_obs_y, cur_obs_z in zip(self._x_set, self._y_set, self._z_set):
                        cur_dist = math.sqrt(((cur_obs_x - cur_lng)**2) + ((cur_obs_y - cur_lat)**2))
                        acc_up += cur_obs_z / cur_dist
                        acc_div += 1 / cur_dist
                    self._grid[cur_x][cur_y] = acc_up / acc_div

        elif interpolation_method == "thiessen":

            effective_method = "thiessen"
            print(" Interpolating using Thiessen polygons.")

            # create grid using thiessen polygons
            self._grid = np.empty((self._lng_res, self._lat_res), dtype=np.float32)
            lng_min = min(self._x_set)
            lat_min = min(self._y_set)
            lng_res = (max(self._x_set) - lng_min) / self._lng_res
            lat_res = (max(self._y_set) - lat_min) / self._lat_res
            for cur_x in range(0, self._lng_res):
                cur_lng = ((cur_x + 0.5) * lng_res) + lng_min
                for cur_y in range(0, self._lat_res):
                    cur_lat = ((cur_y + 0.5) * lat_res) + lat_min
                    min_dist = min_dist_z = None
                    for cur_obs_x, cur_obs_y, cur_obs_z in zip(self._x_set, self._y_set, self._z_set):
                        cur_dist = ((cur_obs_x - cur_lng)**2) + ((cur_obs_y - cur_lat)**2)
                        if (min_dist is None) or (cur_dist < min_dist):
                            min_dist = cur_dist
                            min_dist_z = cur_obs_z

                    self._grid[cur_x][cur_y] = min_dist_z

        print("  Interpolation completed at {0}.".format(datetime.now()))

        # plot graph if possible
        if (plot_file_path is not None) and SystemStatus.HAS_MATPLOTLIB:
            print("Creating scratch graph at {0}.".format(datetime.now()))
            '''
            if Ti is not None:
                plt.contourf(X_grid, Y_grid, Ti)
                plt.colorbar()
            else:
            '''
            plt.imshow(np.transpose(self._grid))
            plt.colorbar()
            plt.title('C values (method = {0})'.format(effective_method))
            plt.savefig(plot_file_path)
            print(" Created scratch graph '{0}'.".format(plot_file_path))
        elif (plot_file_path is not None) and (not SystemStatus.HAS_MATPLOTLIB):
            print("Skipping creation of scratch graph: matplotlib not available.")
        else:
            print("Skipping creation of scratch graph: not requested.")

        return True

    def set_up_other_variables(self, links_location):
        """
        Calculates the status of pounded storage, surface storage, subsurface storage, and channel storage for each link
        :return: None. Changes are done in 'links_location' argument object
        """

        if self._grid is None:
            print("None _grid")
            return
        for cur_link in links_location.values():
            if cur_link is None:
                print("None cur_link")
                continue

            # get current discharge
            cur_x = self._get_x(cur_link.get_lng())
            cur_y = self._get_y(cur_link.get_lat())
            cur_c = self._grid[round(cur_x)][round(cur_y)]

            # calculate C and set up object
            cur_st_pounded = 0
            cur_st_surface = GridSet._swc
            cur_st_subsurface = cur_c / GridSet.k * 0.06 / 1000
            cur_st_channel = cur_c * cur_link.get_upstream_area()
            cur_link.set_storages(cur_st_pounded, cur_st_surface, cur_st_subsurface, cur_st_channel)

            # debug
            if cur_link.get_link_id() == 434514:
                print(" Link id: {0}".format(cur_link.get_link_id()))
                print("  k: {0}".format(GridSet.k))
                print("  c: {0}".format(cur_c))
                print("  up area: {0}".format(cur_link.get_upstream_area()))
                print("  discharge: {0}".format(cur_st_channel))

    @staticmethod
    def load_base_snapshot_hdf5_file(file_path):
        """

        :param file_path:
        :return:
        """

        h5file = h5py.File(file_path, 'r')
        print("  Opened '{0}'.".format(file_path))
        return h5file

    def save_values(self, output_file_path, links_location, base_snapshot_file_path=None,
                    base_snapshot_inherit_states=None):
        """

        :param output_file_path:
        :param links_location:
        :param base_snapshot_file_path:
        :param base_snapshot_inherit_states:
        :return:
        """

        base_h5_file = None

        # basic checks - pre loaded data
        if self._grid is None:
            print(" Unable to write file: no grid data.")
            return False

        # replace output files if needed
        if output_file_path == "overwrite":
            out_snapshot_file_path = base_snapshot_file_path
            init_snapshot_file_path = base_snapshot_file_path.replace(".h5", "_tmp.h5")
            shutil.copy(out_snapshot_file_path, init_snapshot_file_path)
        else:
            init_snapshot_file_path = base_snapshot_file_path
            out_snapshot_file_path = output_file_path

        # basic checks - load init cond if needed
        if init_snapshot_file_path is not None:
            if base_snapshot_inherit_states is None:
                print(" Provided base snapshot file, but inherit states list is missing.")
                return False
            print(" Opening base snapshot file.")
            if init_snapshot_file_path.endswith(".h5"):
                base_h5_file = GridSet.load_base_snapshot_hdf5_file(init_snapshot_file_path)
            else:
                print(" Base snapshot format not supported yet.")
        else:
            print(" Not using a base snapshot file.")
            base_h5_file = None

        if out_snapshot_file_path.endswith(".h5"):
            GridSet.save_values_h5(links_location, out_snapshot_file_path, base_h5_file=base_h5_file,
                                   base_inherit_states=base_snapshot_inherit_states)
        elif out_snapshot_file_path.endswith(".rec"):
            GridSet.save_values_rec(links_location, out_snapshot_file_path)

        if base_h5_file is not None:
            base_h5_file.close()

        return True

    @staticmethod
    def save_values_rec(links_location, output_file_path):
        """

        :param links_location:
        :param output_file_path:
        :return:
        """

        # write output file
        with open(output_file_path, "w+") as w_file:

            w_file.write("254\n")
            w_file.write("{0}\n".format(len(links_location.values())))
            w_file.write("0.0\n\n".format(len(links_location.values())))

            for cur_link in links_location.values():
                if cur_link is None:
                    continue
                cur_storages = cur_link.get_storages()
                w_file.write("{0}\n".format(cur_link.get_link_id()))

                #
                w_file.write("{0} {1} {2} {3} 0 0 {0}\n".format(cur_storages[3], cur_storages[0], cur_storages[1],
                                                                cur_storages[2]))

        return True

    @staticmethod
    def save_values_h5(links_location, output_file_path, base_h5_file=None, base_inherit_states=None):
        """

        :param links_location:
        :param output_file_path:
        :param base_h5_file: Open H5 File
        :param base_inherit_states:
        :return:
        """

        # define data type
        dtype_arg = list()
        dtype_arg.append(("link_id", np.uint32))
        for cur_idx in range(7):
            dtype_arg.append(("state_{0}".format(cur_idx), np.float64))
        the_dtype = np.dtype(dtype_arg)

        # prepare input data
        compress_data = []
        missmatch = 0
        print("  Preparing table data at {0}.".format(datetime.now()))

        if base_h5_file is None:
            for cur_link in links_location.values():
                cur_stgs = cur_link.get_storages()
                the_tuple = (cur_link.get_link_id(), cur_stgs[3], cur_stgs[0], cur_stgs[1], cur_stgs[2], 0, 0, cur_stgs[3])
                compress_data.append(np.array(the_tuple, dtype=the_dtype))
        else:
            for cur_h5e, cur_link in zip(base_h5_file['snapshot'], links_location.values()):
                cur_stgs = cur_link.get_storages()
                link_id = cur_link.get_link_id()
                if link_id != cur_h5e[0]:
                    missmatch += 1
                    continue
                # print("HDF 5 line for {0}: {1}...".format(link_id, cur_h5e))
                state_0 = cur_h5e[1] if 0 in base_inherit_states else cur_stgs[3]
                state_1 = cur_h5e[2] if 1 in base_inherit_states else cur_stgs[0]
                state_2 = cur_h5e[3] if 2 in base_inherit_states else cur_stgs[1]
                state_3 = cur_h5e[4] if 3 in base_inherit_states else cur_stgs[2]
                state_4 = cur_h5e[5] if 4 in base_inherit_states else 0
                state_5 = cur_h5e[6] if 5 in base_inherit_states else 0
                state_6 = cur_h5e[7] if 6 in base_inherit_states else cur_stgs[3]
                the_tuple = (link_id, state_0, state_1, state_2, state_3, state_4, state_5, state_6)
                compress_data.append(np.array(the_tuple, dtype=the_dtype))

        print("    Lines mismatch: {0}.".format(missmatch))
        print("   Done with table data at {0}.".format(datetime.now()))

        # open file
        print("  Opening output HDF5 for writing.")
        with h5py.File(output_file_path, 'w') as w_file:
            print("   File open.")

            # define attributes
            try:
                unix_time = 0 if base_h5_file is None else base_h5_file.attrs['unix_time']
                async_ver = 0 if base_h5_file is None else base_h5_file.attrs['version']
            except KeyError:
                unix_time = 0
                async_ver = "1.4"

            # write attributes
            w_file.attrs.create('model', 254, dtype='uint16')
            w_file.attrs.create('unix_time', unix_time, dtype='uint32')
            w_file.attrs.create('version', async_ver, dtype='S6')

            # create snapshot table

            # compress_data = [np.array((0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), dtype=the_dtype)]
            w_file.create_dataset('snapshot', dtype=the_dtype, data=compress_data, compression="gzip", compression_opts=5)

            # fill snapshot table
            # TODO

        print("  Wrote '{0}'.".format(output_file_path))
        return True
