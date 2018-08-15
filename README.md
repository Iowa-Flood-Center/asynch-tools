# ASYNCH - Tools

A set of scripts for helping the creation, validation and manipulation of Asynch input files.

## Basic Usage

All *python* scripts (.py files) present an embedded short help instructions that can be viewed using the *-h* argument. 

In this help, a brief description of the purpose of the script and instructions for its use, with a list of mandatory and optional arguments, is given.

The arguments for a script are described following the rules:

- capital words: variables that must be provided by the user;
- presence of square brackets: optional argument.

Example:

    $ python example_script.py -h
    
    Exemplifies how to read an script.
    Usage: example_script.py -mand MANDATORY [-opt OPTIONAL] [-a_flag]
      MANDATORY : File path for input.
      OPTIONAL  : A title for output.
      -a_flag   : If provided, outputs in capital letters.

    $ python example_script.py -mand /Users/afile.txt

    All correct.

    $ python example_script.py -opt friend

    Missing '-mand' argument.

    $ python example_script.py -mand /Users/afile.txt -opt friend -a_flag

    ALL CORRECT, FRIEND!
 

### Using on UIowa-HPCs

If the an error with the following message appears:

    "(...)
    ImportError: No module named '[MODULE_NAME]'
    (...)"

in which `[MODULE_NAME]` is a python module as:

- psycopg2
- urllib3
- ...

it means that is necessary to load the Python module with one of the commands (if not loaded yet):

- `$ module load python/3.5.2_parallel_studio-2016.3.210` (on NEON)
- `$ module load python/3.5.3_parallel_studio-2017.1`     (on ARGON)

and to install the package in your local area using the command pip:

    $ pip install --user [MODULE_NAME]


## Script File Naming Convention

It is adapted the sollowing structure:

    ACTION_[hillslope_model_number].EXT

In which:

- `ACTION`: is an verb-substantive. Example: "`file_consistency_checker`";
- `hillslope_model_number`: receives 190 for Constant Runoff Model, 254 for Top Layer Model, etc.;
- `EXT`: usually `.py`.


## Available Scripts

The available scripts in the toolbox with a brief description are listed here in alphabetical order.

### accumulate\_attribute\_in\_tree.py

Accumulates an attribute that is distributed on a tree. The tree must be given in an typical *.rvr* file. The attribute must be given in a simple *.csv* file in the format:

    link_id, attribute
    link_id, attribute
    (...)

The options for accumulation direction are:

- **up**:
  - Accumulates the attribute from the outlet to the leaves.
  - *Example of use:* total contribution area to the outlet.
- **down**:
  - Accumulates the attribute from the leaves to the outlet.
  - *Example of use:* total distance from a link to the outlet.

The output format is another *.csv* file with the format:

    link_id, accumulated_attribute
    link_id, accumulated_attribute
    (...)

**NOTE:** because the recursive nature of the file, for large tree structures it is usually necessary to use the job system of the cluster. 

### file\_consistency\_checker\_rvr.py

Verifies if a given *.rvr* file is topologically consistent, looking for loops and downstream bifurcations.

### file\_converter\_hlmodels\_h5.py

Converts snapshot files in *.h5* format from one Hillslope-Link model to another.

*Example*: snapshot for model 254 (Top Layer, 7 states) to model 195 (Offline, 4 states).

### file\_converter\_csv\_to\_rvr.py

Converts 2-columns CSV file with the topological information of a drainage network in the format:

    source_link_id, destination_link_id
    source_link_id, destination_link_id
    (...)

To **.rvr** format. The source **.csv** file is not modified after the run.  

### file\_converter\_rec\_to\_h5.py

Converts snapshots from *.rec* into a *.h5* snapshot format.

### file\_materializer\_rvr.py

Generates a river topology file (*.rvr*) for a single database from readings from a given database.

### initialcondition\_generator\_254\_baseflow.py

Creates an initial condition file by estimating baseflow dischage from observed data. The same script executes two procedures:

- **download** observed discharge **data** from USGS gages web server, estimating local baseflows; and
- **interpolate** both baseflow discharge and soil water column in space for Top Layer (254) model.

The generated initial condition file may "inherit" the values of specific states from a previously existing snapshot file (the so called "*base snapshot*"). This is used, for example, for some data assimilation procedures, when the water column state must be updated but all the other states must be kept unchanged from previous model runs.

Because there a big number of arguments is required, the main input format for this script is a *\.json* file with a single object, which has each attribute as a parameter for the script. A scratch of the configuration file can be created using the command:

    $ python initialcondition_generator_254_baseflow.py -get_json_scratch [INSTRUCTIONS_JSON]

In which ```[INSTRUCTIONS_JSON]``` must be replaced by the file path of the scratch file to be generated.

A typical *\.json* input file for this script would have the following content:

    {
      "base_snapshot_file_path": "(...).h5",
      "baseflow_end_date": "[DATE_INI]",
      "baseflow_ini_date": "[DATE_END]",
      "gages_ignore_csv": "/(...).csv",
      "gages_only_bounding_box": {
        "max_lat": 44.56, 
        "max_lng": -89.85,
        "min_lat": 40.14, 
        "min_lng": -97.12
      },
      "gages_only_csv": "/(...)/(...).csv",
      "interpolation_method": "auto",
      "k": 2.0425e-06,
      "linkid_location_file": "/(...)/(...).csv",
      "output_graph_file_path": "/(...)/(...).png",
      "output_state_file_path": "/(...)/(...).h5",
      "procedures": ["download_data", "interpolate"],
      "temporary_file_path": "/(...)/temp.txt",
      "toplayer_soil_water_column": 0.02,
      "base_snapshot_states_inherit":[1, 2, 4, 5, 6]
    }

In which:

- **base\_snapshot\_file\_path**
  - Description: File path for the *base snapshot* if it is going to be used, expects "none" otherwise. 
  - Example: "/a\_folder/a\_file\_1.h5"
- **base\_snapshot\_states\_inherit**
  - Description: List of state indexes to be inherited from the *base snapshot* file.
  - Example: *[1, 2]* would inherit only pounded and top layer water column. 
- **baseflow\_ini\_date**
  - Description: String in *YYYY-MM-DD* format with beginning of data interval retrieved.
  - Example: "2017-10-22"
- **baseflow\_end\_date** 
  - Description: String in *YYYY-MM-DD* format with ending of data interval retrieved.
  - Example: "2017-10-27"
- **gages\_ignore\_csv**
  - Description: File path for a text file with a list of USGS gages ID to be ignored.
  - More description: Usually gages downstream of human controled reservoirs need to be removed.
- **gages\_only\_bounding\_box**
  - Description: bounding box that contains all considered USGS gages ID 
- **gages\_only\_csv**
  - Description: File path for a text file with a list of USGS gages ID to be taken into consideration.
  - More description: It is usually used when only small gages are desired.
- **interpolation\_method**
  - Description: Describes which interpolation algorithm should be used.
  - More description: Each method depends on different libraries. 
  - Even more: "auto" will try to get the best given the libraries available. 
  - Options: "griddata\_linear", "distance\_weighted", "thiessen", or "auto"
- **k**
  - Description: Float value of *K3* variable in Top Layer model to be considered.
  - Example: 2.0425e-06
- **linkid\_location\_file**
  - Description: File path for a *.csv* file that associates each link id to a geographic coordinate.
  - Example: "/a\_folder/a\_file.csv"
- **output\_graph\_file\_path**
  - Description: File path for a *.png* file with a scratch of the moisture distribution in space 
  - Example: "/a\_folder/a\_file.png"
- **output\_state\_file\_path**
  - Description: File path for the output file to be created 
  - Example: "/a\_folder/a\_file\_2.h5"
- **procedures**
  - Description: Array of the procedures to be executed in this run. Expects "download\_data" and/or "interpolate".
  - More description: Because each step takes a considerable amount of time, one can do each at a time.
  - Even more: You will probably want to run both steps most of times. 
  - Even more: "interpolate" can only be run after "download\_data". It requires a *temp* file.  
  - Example: ["download\_data"], or ["download\_data", "interpolate"] 
- **temporary\_file\_path**
  - Description: File path to be used as an intermediate storage between "download\_data" and "interpolate" process.
  - Example: "/a\_folder/a\_file.txt"
- **toplayer\_soil\_water\_column**
  - Description: Float number with the uniform value for toplayer water column when not inherited.
  - Example: 0.02

### initialcondition\_generator\_254\_idealized.py

Creates an *.rec* initial condition file by extrapolation of the outlet/drainage area relationship on a given link (usually the outlet link) for Top Layer (254) model.

### initialcondition\_selector\_10days.py

Given a folder ```F``` that contains a set of initial condition files named with the pattern ```[PREFIX]_[UNIX_TIMESTAMP].h5```, in which:

- ```[PREFIX]```: is a set alphanumeric characters not ending with a numerical character;
- ```[UNIX_TIMESTAMP]```: is a integer representing a unix timestamp, in seconds.

This script **deletes** all ```.h5``` files from folder ```F``` that have ```UNIX_TIMESTAMP``` values not representing the midnight of days *01*, *11* or *21* of every month.
     

### plot\_timeseries\_h5\_outputs.py

It has the purpose of providing a simplified way for plotting timeseries from sequential runs that accumulates or generates sets of snapshot files (as the case of realtime systems).

Outputs the timeseries data of a given state for a specific link from a set of sequential .h5 snapshot files. The output format can be both via *std. out* or as writing a new *.csv* file.