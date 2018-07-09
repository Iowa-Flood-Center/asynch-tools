class UsgsGauge:
    _id = None
    _link_id = None
    _upstream_area = None
    _min_discharge = None
    _lat = None
    _lng = None

    def __init__(self, id, upstream_area):
        self._id = id
        self._upstream_area = upstream_area

    def set_link_id(self, link_id):
        self._link_id = link_id

    def set_min_discharge(self, min_discharge):
        self._min_discharge = min_discharge

    def set_lat(self, lat):
        self._lat = lat

    def set_lng(self, lng):
        self._lng = lng

    def get_id(self):
        return self._id

    def get_upstream_area(self):
        return self._upstream_area

    def get_link_id(self):
        return self._link_id

    def get_min_discharge(self):
        return self._min_discharge

    def get_lat(self):
        return self._lat

    def get_lng(self):
        return self._lng
