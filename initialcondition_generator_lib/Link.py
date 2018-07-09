class Link:
    _link_id = None
    _lat = None
    _lng = None
    _discharge = None           # c. meter / seq
    _upstream_area = None       # km^2
    _storage_pounded = 0        # c. meter
    _storage_surface = None     # c. meter
    _storage_subsurface = None  # c. meter
    _storage_channel = None     # c. meter

    def __init__(self, link_id):
        self._link_id = link_id

    def set_discharge(self, discharge):
        self._discharge = discharge

    def set_storages(self, st_pounded, st_surface, st_subsurface, st_channel):
        self._storage_pounded = st_pounded
        self._storage_surface = st_surface
        self._storage_subsurface = st_subsurface
        self._storage_channel = st_channel

    def set_latlng(self, lat, lng):
        self._lat = lat
        self._lng = lng

    def set_upstream_area(self, upstream_area):
        self._upstream_area = upstream_area

    def get_storages(self):
        return self._storage_pounded, self._storage_surface, self._storage_subsurface, self._storage_channel

    def get_upstream_area(self):
        return self._upstream_area

    def get_link_id(self):
        return self._link_id

    def get_lat(self):
        return self._lat

    def get_lng(self):
        return self._lng

    def get_discharge(self):
        return self._discharge
