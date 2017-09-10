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

### file\_consistency\_checker\_rvr.py

Verifies if a given *.rvr* file is topologically consistent, looking for loops and downstream bifurcations.

### file\_converter\_hlmodels\_h5.py

Converts snapshot files in *.h5* format from one Hillslope-Link model to another.

*Example*: snapshot for model 254 (Top Layer, 7 states) to model 195 (Offline, 4 states).

### file\_converter\_rec\_to\_h5.py

Converts snapshots from *.rec* into a *.h5* snapshot format.

### initialcondition\_generator\_254\_idealized.py

Creates an *.rec* initial condition file by extrapolation of the outlet/drainage area relationship on a given link (usually the outlet link) for Top Layer (254) model.

<!---
### initialcondition\_generator\_254\_idealized.py

TODO - describe it
--->

### plot\_timeseries\_h5\_outputs.py

Creates a .csv file with the timeseries data of a for a specific link from a set of sequential .h5 state files. It has the purpose of providing a simplified way for plotting timeseries from sequential runs (as the case of realtime systems). 