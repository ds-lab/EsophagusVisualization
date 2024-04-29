class VisualizationData:
    """Data class for values needed in many steps"""

    def __init__(self):
        """
        init VisualizationData
        """
        self._xray_filename = None
        self._xray_file = None
        self._endoscopy_filenames = None

        self._xray_polygon = None
        self._xray_image_height = None
        self._xray_image_width = None
        self._xray_mask = None

        self._endoscopy_polygons = None
        self._endoscopy_image_positions_cm = None

        self._pressure_matrix = None
        self._endoflip_screenshot = None

        self._figure_creator = None

        self._first_sensor_pos = None
        self._first_sensor_index = None
        self._second_sensor_pos = None
        self._second_sensor_index = None
        self._endoscopy_start_pos = None
        self._sphincter_upper_pos = None
        self._esophagus_exit_pos = None
        self._sphincter_length_cm = None
        self._endoflip_pos = None

        self._figure_x = None
        self._figure_y = None
        self._figure_z = None

    @property
    def xray_file(self):
        return self._xray_file

    @xray_file.setter
    def xray_file(self, value):
        self._xray_file = value

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
    def endoflip_screenshot(self):
        return self._endoflip_screenshot

    @endoflip_screenshot.setter
    def endoflip_screenshot(self, value):
        self._endoflip_screenshot = value

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

    @property
    def sphincter_upper_pos(self):
        return self._sphincter_upper_pos

    @sphincter_upper_pos.setter
    def sphincter_upper_pos(self, value):
        # value is a x,y tuple
        self._sphincter_upper_pos = value

    @property
    def esophagus_exit_pos(self):
        return self._esophagus_exit_pos

    @esophagus_exit_pos.setter
    def esophagus_exit_pos(self, value):
        # value is a x,y tuple
        self._esophagus_exit_pos = value

    @property
    def endoflip_pos(self):
        return self._endoflip_pos

    @endoflip_pos.setter
    def endoflip_pos(self, value):
        # value is a x,y tuple
        self._endoflip_pos = value

    @property
    def sphincter_length_cm(self):
        return self._sphincter_length_cm

    @sphincter_length_cm.setter
    def sphincter_length_cm(self, value):
        self._sphincter_length_cm = value

    @property
    def figure_x(self):
        return self._figure_x

    @figure_x.setter
    def figure_x(self, value):
        self._figure_x = value

    @property
    def figure_y(self):
        return self._figure_y

    @figure_y.setter
    def figure_y(self, value):
        self._figure_y = value

    @property
    def figure_z(self):
        return self._figure_z

    @figure_z.setter
    def figure_z(self, value):
        self._figure_z = value