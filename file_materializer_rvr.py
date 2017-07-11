from def_lib import ArgumentsManager
import psycopg2
import json
import sys
import os

# ###################################################### HELP ######################################################## #

if '-h' in sys.argv:
    print("Generates a .rvr file for a specific watershed.")
    print("Usage: python file_materializer.py -linkid LINKID -fpath_out OUTPUT_PATH -source DBSOURCE [-dbuser DBUSER] [-dbpass DBPASS]")
    print("  LINKID      : Integer. The link id related to the outlet of the watershed to be extracted.")
    print("  OUTPUT_PATH : String. File full path of the file to be generated.")
    print("  DSOURCE     : String. Path for a .json file with the following fields:")
    print("  - host : String. Address of the server hosting the database. Example: 'xyz.iihr.uiowa.edu'")
    print("  - port : Integer. Port to be used to connect to the database server. Example: 5432")
    print("  - database : String. Name of the database that contains the topology table. Example: 'model_ifc'")
    print("  - table : String. Name of the table that contains the topology. Example: env_master_km")
    print("               The table must present at least the columns 'left', 'right' and 'link_id'")
    print("  DBUSER      : String. Database username for described database.")
    print("  DBPASS      : String. Database password for described database.")
    quit()

# ###################################################### ARGS ######################################################## #

# get basic arguments
outlet_linkid_arg = ArgumentsManager.get_int(sys.argv, '-linkid')
output_fpath_arg = ArgumentsManager.get_str(sys.argv, '-fpath_out')
source_arg = ArgumentsManager.get_str(sys.argv, '-source')
dbuser_arg = ArgumentsManager.get_str(sys.argv, '-dbuser')
dbpass_arg = ArgumentsManager.get_str(sys.argv, '-dbpass')
input_fpath_arg = ArgumentsManager.get_str(sys.argv, '-fpath_in')

# basic checks
if (outlet_linkid_arg is None) or (output_fpath_arg is None) or (source_arg is None):
    quit()
if source_arg.endswith(".json"):
    if dbuser_arg is None:
        print("Missing '-dbuser' argument.")
        quit()
    elif dbpass_arg is None:
        print("Missing '-dbpass' argument.")
        quit()
else:
    print("Invalid file type provided for argument '-source'.")
    quit()

# ###################################################### CLAS ######################################################## #


class DatabaseProvider:
    """
    USEFUL
    """

    def __init__(self):
        return

    @staticmethod
    def open_db_connection(json_content, dbuser, dbpass):
        """
        Opens a database connection.
        DO NOT FORGET TO CLOSE CONNECTION AFTER USING IT!
        :param source:
        :param dbuser:
        :param dbpass:
        :return: psycopg2 open connection object
        """

        SQL_USER = dbuser
        SQL_PASS = dbpass
        SQL_HOST = json_content['host']
        SQL_PORT = json_content['port']
        SQL_DB = json_content['database']

        # open connection and return it
        try:
            return psycopg2.connect(database=SQL_DB, user=SQL_USER, password=SQL_PASS, host=SQL_HOST, port=SQL_PORT)
        except psycopg2.OperationalError as e:
            print("Unable to connect to the database. Error '{0}'.".format(str(e).strip()))
            return None

    @staticmethod
    def define_select_sql(json_content, outlet_link_id):
        """

        :param json_content:
        :param outlet_link_id:
        :return:
        """

        query_sel = 'WITH outlet AS(' \
                            'SELECT link_id, "left", "right" ' \
                            'FROM {0} ' \
                            'WHERE link_id = {1}) ' \
                        'SELECT open.link_id, open.parent_link, (open."right"-open."left"-1)/2 AS num_children ' \
                        'FROM _env_master_km open ' \
                        'INNER JOIN outlet ' \
                        'ON open."left" >= outlet."left" ' \
                        'AND open."right" <= outlet."right" ' \
                        'ORDER BY num_children'.format(json_content["table"], outlet_link_id)
        return query_sel

# ###################################################### DEFS ######################################################## #


def extract_topo_file_from_db(outlet_link_id, output_fpath, source, dbuser, dbpass):
    """

    :param outlet_link_id:
    :param output_fpath:
    :param source:
    :param dbuser:
    :param dbpass:
    :return: None. Change is performed in the file system
    """

    # basic check
    if output_fpath is None:
        print("An output file direction must be provided.")
        return

    # ready from database
    all_rvr = read_topology_from_db(source, dbuser, dbpass, outlet_link_id)
    if (all_rvr is None) or (len(all_rvr) <= 0):
        print("Not enough data in database.")
        return

    # build intermediate dictionary
    tmp_dic = {}
    for cur_param in all_rvr:
        # the root is ignored here, but don't worry: it will be added in their children's iteration. Believe me.
        if cur_param[0] == outlet_link_id:
            continue

        # add itself if leaf
        if cur_param[2] == 0:
            tmp_dic[cur_param[0]] = []

        # add to parent
        if cur_param[1] not in tmp_dic.keys():
            tmp_dic[cur_param[1]] = []
        tmp_dic[cur_param[1]].append(str(cur_param[0]))

    # write file
    with open(output_fpath_arg, "w+") as output_file:
        output_file.write("{0}\n\n\n".format(len(tmp_dic.keys())))
        for key, lst in tmp_dic.items():
            output_file.write("{0}\n".format(key))
            output_file.write("{0} {1}\n\n".format(len(lst), " ".join(lst)))

    print("Wrote file '{0}'.".format(output_fpath_arg))


def read_topology_from_db(source, dbuser, dbpass, outlet_link_id):
    """

    :param source:
    :param dbuser:
    :param dbpass:
    :param outlet_link_id:
    :return: A list of tuples with columns 'link_id', 'parent_link_id', 'aperture'
    """

    # basic checks
    if (source is None) or (dbuser is None) or (dbpass is None):
        print("Database source, user or password not provided.")
        return None
    if not os.path.exists(source):
        print("File not found: '{0}'.".format(source))
        return None

    # read database description
    with open(source, "r") as json_file:
        json_content = json.load(json_file)

    # open db, basic check and get cursor
    db_conn = DatabaseProvider.open_db_connection(json_content, dbuser, dbpass)
    if db_conn is None:
        print("Not possible to open database connection.")
        return
    db_cursor = db_conn.cursor()

    # get query, basic check and execute it
    query_sel = DatabaseProvider.define_select_sql(json_content, outlet_link_id)
    if query_sel is not None:
        db_cursor.execute(query_sel)
        all_results = db_cursor.fetchall()
    else:
        all_results = None

    # close connection pointers
    db_cursor.close()
    db_conn.close()

    return all_results


def extract_topo_file_from_file(outlet_linkid, output_fpath, input_fpath):
    """

    :param outlet_linkid:
    :param output_fpath:
    :param input_fpath:
    :return:
    """

    print("Option for extracting data from other .rvr not implemented yet.")

    return

# ###################################################### RUNS ######################################################## #

if source_arg.endswith(".json"):
    extract_topo_file_from_db(outlet_linkid_arg, output_fpath_arg, source_arg, dbuser_arg, dbpass_arg)
elif source_arg.startswith(".rvr"):
    extract_topo_file_from_file(outlet_linkid_arg, output_fpath_arg, source_arg)
else:
    print("Unexpected source argument: '{0}'.".format(source_arg))
