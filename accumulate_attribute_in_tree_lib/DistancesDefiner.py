import numpy as np


# Static Class - Library of functions (its methods) for dealing with distances
class DistancesDefiner:

    @staticmethod
    def calculate_links_accumulated_attributes_down(outlet_linkid, dict_topo, dict_attribute):
        """

        :param outlet_linkid:
        :param dict_topo:
        :param dict_attribute:
        :return: Dictionary with the distances of each link id to the outlet of the watershed
        """

        # basic check
        if outlet_linkid is None:
            print("Invalid outlet link id: {0}.".format(outlet_linkid))
            return None
        elif outlet_linkid not in list(dict_attribute.keys()):
            print("Outlet link id ({0}) not found in attributes list.".format(outlet_linkid))
            return None
        elif outlet_linkid not in list(dict_topo.keys()):
            print("Outlet link id ({0}) not found in topology list.".format(outlet_linkid))
            return None

        print("Starting up at {0} -> {1} ({2}).".format(outlet_linkid, dict_topo[outlet_linkid],
                                                        dict_attribute[outlet_linkid]))

        dict_cumm = {}
        DistancesDefiner._set_cumulative_attribute_up(outlet_linkid, 0, dict_topo, dict_attribute, dict_cumm)

        print("Defined cumulative distances for {0} links.".format(len(dict_cumm.keys())))
        max_key = None
        max_dist = 0
        for cur_key in dict_cumm.keys():
            cur_dist = dict_cumm[cur_key]
            if cur_dist > max_dist:
                max_dist = cur_dist
                max_key = cur_key
        print("Maximum distance is {0}km ({1}).".format(max_dist, max_key))

        return dict_cumm

    @staticmethod
    def _set_cumulative_attribute_up(parent_link_id, dist_accumulated, topo_dict, leng_dict, cumulative_dict):
        """

        :param dist_accumulated:
        :param topo_dict:
        :param leng_dict:
        :param cumulative_dict:
        :return:
        """
        cur_link_length = leng_dict[parent_link_id]
        cur_link_accum = cur_link_length + dist_accumulated
        cumulative_dict[parent_link_id] = cur_link_accum
        # print("Setting for link {0}.".format(parent_link_id))
        if parent_link_id not in topo_dict.keys():
            print("Missing link {0} in topology.".format(parent_link_id))
            return
        elif topo_dict[parent_link_id] is None:
            return
        for cur_par_link_id in topo_dict[parent_link_id]:
            DistancesDefiner._set_cumulative_attribute_up(cur_par_link_id, cur_link_accum, topo_dict, leng_dict,
                                                          cumulative_dict)
        return

    @staticmethod
    def calculate_links_accumulated_attributes_up(outlet_linkid, dict_topo, dict_attribute):
        """

        :param outlet_linkid:
        :param dict_topo:
        :param dict_attribute:
        :return:
        """

        # basic check
        if outlet_linkid is None:
            print("Invalid outlet link id: {0}.".format(outlet_linkid))
            return None
        elif outlet_linkid not in list(dict_attribute.keys()):
            print("Outlet link id ({0}) not found in attributes list.".format(outlet_linkid))
            return None
        elif outlet_linkid not in list(dict_topo.keys()):
            print("Outlet link id ({0}) not found in topology list.".format(outlet_linkid))
            return None

        print("Starting down at {0} -> {1} ({2}).".format(outlet_linkid, dict_topo[outlet_linkid],
                                                          dict_attribute[outlet_linkid]))

        dict_cumm = {}
        DistancesDefiner._set_cumulative_attribute_down(outlet_linkid, dict_topo, dict_attribute, dict_cumm)

        print("Defined cumulative distances for {0} links.".format(len(dict_cumm.keys())))
        max_key = None
        max_dist = 0
        for cur_key in dict_cumm.keys():
            cur_dist = dict_cumm[cur_key]
            if cur_dist > max_dist:
                max_dist = cur_dist
                max_key = cur_key
        print("Maximum attribute is {0} (link {1}).".format(max_dist, max_key))

        return dict_cumm

    @staticmethod
    def _set_cumulative_attribute_down(parent_link_id, topo_dict, leng_dict, cumulative_dict):
        """

        :param dist_accumulated:
        :param topo_dict:
        :param leng_dict:
        :param cumulative_dict:
        :return:
        """

        cur_link_attribute = leng_dict[parent_link_id]

        if parent_link_id not in topo_dict.keys():
            print("Missing link {0} in topology.".format(parent_link_id))
            return
        elif topo_dict[parent_link_id] is None:
            down_sum = 0
        else:
            up_values = []
            for cur_par_link_id in topo_dict[parent_link_id]:
                up_values.append(DistancesDefiner._set_cumulative_attribute_down(cur_par_link_id, topo_dict, leng_dict,
                                                                                 cumulative_dict))
            down_sum = sum(up_values)

        cur_link_accum = cur_link_attribute + down_sum
        cumulative_dict[parent_link_id] = cur_link_accum
        return cur_link_accum

    def __init__(self):
        return
