try:
    if False:
        raise ImportError
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
try:
    if False:
        raise ImportError
    from scipy.interpolate import griddata
    HAS_SCIPYINTERPOL = True
except ImportError:
    HAS_SCIPYINTERPOL = False
try:
    if True:
        raise ImportError
    import urllib3
    HAS_URLLIB3 = True
except ImportError:
    import subprocess
    HAS_URLLIB3 = False
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False


class SystemStatus:
    HAS_MATPLOTLIB = HAS_MATPLOTLIB
    HAS_SCIPYINTERPOL = HAS_SCIPYINTERPOL
    HAS_URLLIB3 = HAS_URLLIB3
    HAS_PSYCOPG2 = HAS_PSYCOPG2
    HAS_H5PY = HAS_H5PY

    def __init__(self):
        return
