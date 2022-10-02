

class VisualizationData:
    """Data class for values needed in many steps"""

    def __init__(self):
        """
        init VisualizationData
        """
        self._xray_filename = None
        self._endoscopy_filenames = None

        self._xray_polygon = None
        self._xray_image_height = None
        self._xray_image_width = None
        self._xray_mask = None

        self._endoscopy_polygons = None
        self._endoscopy_image_positions_cm = None

        self._pressure_matrix = None

        self._figure_creator = None

        self._first_sensor_pos = None
        self._first_sensor_index = None
        self._second_sensor_pos = None
        self._second_sensor_index = None
        self._endoscopy_start_pos = None

    @property
    def xray_filename(self):
        return self._xray_filename

    @xray_filename.setter
    def xray_filename(self, value):
        self._xray_filename = value

    @property
    def xray_polygon(self):
        return self._xray_polygon

    @xray_polygon.setter
    def xray_polygon(self, value):
        self._xray_polygon = value

    @property
    def xray_image_height(self):
        return self._xray_image_height

    @xray_image_height.setter
    def xray_image_height(self, value):
        self._xray_image_height = value

    @property
    def xray_image_width(self):
        return self._xray_image_width

    @xray_image_width.setter
    def xray_image_width(self, value):
        self._xray_image_width = value

    @property
    def xray_mask(self):
        return self._xray_mask

    @xray_mask.setter
    def xray_mask(self, value):
        self._xray_mask = value

    @property
    def pressure_matrix(self):
        return self._pressure_matrix

    @pressure_matrix.setter
    def pressure_matrix(self, value):
        self._pressure_matrix = value

    @property
    def endoscopy_filenames(self):
        return self._endoscopy_filenames

    @endoscopy_filenames.setter
    def endoscopy_filenames(self, value):
        self._endoscopy_filenames = value

    @property
    def endoscopy_image_positions_cm(self):
        return self._endoscopy_image_positions_cm

    @endoscopy_image_positions_cm.setter
    def endoscopy_image_positions_cm(self, value):
        self._endoscopy_image_positions_cm = value

    @property
    def endoscopy_polygons(self):
        return self._endoscopy_polygons

    @endoscopy_polygons.setter
    def endoscopy_polygons(self, value):
        self._endoscopy_polygons = value

    @property
    def figure_creator(self):
        return self._figure_creator

    @figure_creator.setter
    def figure_creator(self, value):
        self._figure_creator = value

    @property
    def first_sensor_pos(self):
        return self._first_sensor_pos

    @first_sensor_pos.setter
    def first_sensor_pos(self, value):
        self._first_sensor_pos = value

    @property
    def second_sensor_pos(self):
        return self._second_sensor_pos

    @second_sensor_pos.setter
    def second_sensor_pos(self, value):
        self._second_sensor_pos = value

    @property
    def endoscopy_start_pos(self):
        return self._endoscopy_start_pos

    @endoscopy_start_pos.setter
    def endoscopy_start_pos(self, value):
        self._endoscopy_start_pos = value

    @property
    def first_sensor_index(self):
        return self._first_sensor_index

    @first_sensor_index.setter
    def first_sensor_index(self, value):
        self._first_sensor_index = value

    @property
    def second_sensor_index(self):
        return self._second_sensor_index

    @second_sensor_index.setter
    def second_sensor_index(self, value):
        self._second_sensor_index = value
