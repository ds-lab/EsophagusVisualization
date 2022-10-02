from abc import ABC, abstractmethod
import plotly.graph_objects as go
import numpy as np
from skimage import graph
import config
from visualization_data import VisualizationData


class FigureCreator(ABC):
    """Abstract base class for figure creation"""

    @abstractmethod
    def __init__(self, visualization_data: VisualizationData):
        """
        init FigureCreator
        :param visualization_data: VisualizationData
        """
        pass

    @abstractmethod
    def get_figure(self):
        """
        returns the created figure
        """
        pass

    @abstractmethod
    def get_surfacecolor_list(self):
        """
        returns the list of surface-colors
        """
        pass

    @abstractmethod
    def get_number_of_frames(self):
        """
        returns the number of frames of the animation
        """
        pass

    @staticmethod
    def calculate_esophagus_length_px(sensor_path, start_index, end_index):
        """
        calculates the length of the sensor path inside the given part of the esophagus
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param start_index: height to start
        :param end_index: height to end
        :return: length in pixels
        """
        path_length_px = 0
        for i in range(0, len(sensor_path)):
            if i > 0 and sensor_path[i-1][1] >= start_index:
                path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
            if sensor_path[i][1] == end_index:
                break
        return path_length_px

    @staticmethod
    def calculate_esophagus_full_length_cm(sensor_path, esophagus_full_length_px, visualization_data, offset_top):
        """
        calculates the length of the sensor path inside the esophagus in cm
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param esophagus_full_length_px: length in pixels
        :param visualization_data: VisualizationData
        :param offset_top: offset between the top the x-ray image and the shape of the esophagus
        :return: length in cm
        """
        first_sensor_cm = config.coords_sensors[visualization_data.first_sensor_index]
        second_sensor_cm = config.coords_sensors[visualization_data.second_sensor_index]
        length_pixel = FigureCreator.calculate_esophagus_length_px(sensor_path, visualization_data.second_sensor_pos -
                                                                   offset_top, visualization_data.first_sensor_pos -
                                                                   offset_top)
        length_cm = first_sensor_cm - second_sensor_cm
        return length_cm * (esophagus_full_length_px / length_pixel)

    @staticmethod
    def calculate_surfacecolor_list(sensor_path, visualization_data, esophagus_full_length_px, esophagus_full_length_cm,
                                    offset_top):
        """
        calculates the surface-colors for every frame
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param visualization_data: VisualizationData
        :param esophagus_full_length_px: length in pixels
        :param esophagus_full_length_cm: length in cm
        :param offset_top: offset between the top the x-ray image and the shape of the esophagus
        :return: list of surface-colors
        """
        pressure_matrix = visualization_data.pressure_matrix
        px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px
        # path length from top for first sensor
        first_sensor_path_length_px = 0
        for i in range(0, len(sensor_path)):
            if visualization_data.first_sensor_pos - offset_top == sensor_path[i][0]:
                break
            if i > 0:
                first_sensor_path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)

        first_sensor_path_length_cm = first_sensor_path_length_px * px_to_cm_factor
        sensor_path_lengths_px = [(first_sensor_path_length_cm - (
                config.coords_sensors[visualization_data.first_sensor_index] - coord)) / px_to_cm_factor for coord
                                    in config.coords_sensors]

        surfacecolor_list = []
        for frame_number in range(pressure_matrix.shape[1]):
            surfacecolor = []
            # find the sensor (from top) that is just before the regarded area
            current_sensor_index = 0
            for i in range(len(config.coords_sensors) - 1):
                if sensor_path_lengths_px[i] < 0 and sensor_path_lengths_px[i + 1] < 0:
                    current_sensor_index = i + 1
            current_path_length_px = 0
            is_before_first_sensor = 0 < sensor_path_lengths_px[0]
            is_after_last_sensor = False
            for i in range(0, len(sensor_path)):
                if i > 0:
                    current_path_length_px += np.sqrt((sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 +
                                                      (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
                # check if before first regareded sensor
                if is_before_first_sensor and current_path_length_px < sensor_path_lengths_px[current_sensor_index]:
                    surfacecolor.append(0)
                else:
                    is_before_first_sensor = False
                    # check if switch to next sensor
                    if current_sensor_index + 2 <= len(config.coords_sensors) - 1:
                        if current_path_length_px > sensor_path_lengths_px[current_sensor_index + 1]:
                            current_sensor_index += 1
                    else:
                        # check if switching to next sensor is needed but not available
                        if current_sensor_index + 1 > len(config.coords_sensors) - 1 or current_path_length_px > \
                                sensor_path_lengths_px[current_sensor_index + 1]:
                            is_after_last_sensor = True
                    # check if after last sensor
                    if is_after_last_sensor:
                        surfacecolor.append(0)
                    else:
                        # calculate color (pressure)
                        pressure_current_sensor = pressure_matrix[current_sensor_index, frame_number]
                        pressure_next_sensor = pressure_matrix[current_sensor_index + 1, frame_number]
                        pressure = pressure_current_sensor + (pressure_next_sensor - pressure_current_sensor) * (
                                   (current_path_length_px - sensor_path_lengths_px[current_sensor_index]) / (
                                    sensor_path_lengths_px[current_sensor_index + 1] -
                                    sensor_path_lengths_px[current_sensor_index]))
                        surfacecolor.append(pressure)
            surfacecolor_list.append(surfacecolor)
        return surfacecolor_list

    @staticmethod
    def calculate_widths_and_centers_and_offsets(visualization_data):
        """
        calculates the widths (width of the esophagus shape for every height on the x-ray image),
        the centers (analogue to widths) and the offsets (area of the images outside the shape of the esophagus)
        :param visualization_data: VisualizationData
        :return: widths and centers as numpy arrays and offsets as int
        """
        widths = []
        centers = []
        offset_top = 0
        offset_bottom = 0
        top_offset_done = False

        # calculate widths and center values
        for i in range(visualization_data.xray_mask.shape[0]):
            left_index = 0
            while visualization_data.xray_mask[i, left_index] == False and left_index < \
                    visualization_data.xray_mask.shape[1] - 1:
                left_index += 1
            right_index = visualization_data.xray_mask.shape[1] - 1
            while visualization_data.xray_mask[i, right_index] == False and right_index > 0:
                right_index -= 1
            width = right_index - left_index
            if width >= 0:
                widths.append(width)
                centers.append(left_index + width/2)
                top_offset_done = True
            else:
                if not top_offset_done:
                    offset_top += 1
                else:
                    offset_bottom += 1

        # convert to numpy arrays
        widths = np.array(widths)
        centers = np.array(centers)
        return widths, centers, offset_top, offset_bottom

    @staticmethod
    def create_figure(x, y, z, surfacecolor_list, title):
        """
        creates the plotly figure
        :param x: x-values
        :param y: y-values
        :param z: z-values
        :param surfacecolor_list: list of surfacecolors for every frame
        :param title: title that is shown with the figure
        :return: plotly figure
        """
        # calculate colormatrix for first frame, the others will be done by javascript
        first_surfacecolor = np.tile(np.array([surfacecolor_list[0]]).transpose(), (1, config.figure_number_of_angles))
        figure = go.Figure(data=[
            go.Surface(x=x, y=y, z=z, surfacecolor=first_surfacecolor, colorscale=config.colorscale, cmin=config.cmin,
                       cmax=config.cmax)])
        figure.update_layout(scene=dict(aspectmode='data'), uirevision='constant',
                             title=title, title_x=0, title_y=1,
                             margin=dict(l=20, r=20, t=30, b=20), hovermode=False)
        figure.update_scenes(zaxis_autorange="reversed", xaxis_autorange="reversed", xaxis_title_text='Breite',
                             yaxis_title_text='Tiefe', zaxis_title_text='Länge')
        return figure

    @staticmethod
    def calculate_shortest_path_through_esophagus(visualization_data, offset_top, offset_bottom, center_top, center_bottom):
        """
        estimates the course of the manometry catheter in the esophagus
        :param visualization_data: VisualizationData
        :param offset_top: top offset of the x-ray image
        :param offset_bottom: bottom offset of the x-ray image
        :param center_top: center coordinate at the top of the esophagus
        :param center_bottom: center coordinate at the bottom of the esophagus
        :return: path as list of coordinates
        """
        array = visualization_data.xray_mask[offset_top:-offset_bottom]
        costs = np.where(array, 1, 1000)
        path, cost = graph.route_through_array(costs, start=(0, int(center_top)),
                                                       end=(array.shape[0]-1, int(center_bottom)), fully_connected=True)
        return path
