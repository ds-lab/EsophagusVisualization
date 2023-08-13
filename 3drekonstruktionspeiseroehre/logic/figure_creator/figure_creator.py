from abc import ABC, abstractmethod

import config
import numpy as np
import plotly.graph_objects as go
import shapely.geometry
from logic.visualization_data import VisualizationData
from skimage import graph


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

    @abstractmethod
    def get_metrics(self):
        """
        returns the calculated metric values as list over time
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
        # TODO: handle end_index correctly, idea: handle full calculation and segment calc (used in calculate_esophagus_full_length_cm) differently by adding a full:boolean parameter
        path_length_px = 0
        for i in range(0, len(sensor_path)):
            if i > 0 and sensor_path[i - 1][1] >= start_index:
                # Add euklidean distance of the previous point and the current one
                path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
            # TODO: only check for this if a segment length has to be calculated (if not full:)
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
        # Map sensor indices to centimeter
        first_sensor_cm = config.coords_sensors[visualization_data.first_sensor_index]
        second_sensor_cm = config.coords_sensors[visualization_data.second_sensor_index]

        # Calculate segement length to find out centimeter to pixel ratio
        length_pixel = FigureCreator.calculate_esophagus_length_px(sensor_path, visualization_data.second_sensor_pos -
                                                                   offset_top, visualization_data.first_sensor_pos -
                                                                   offset_top)
        length_cm = first_sensor_cm - second_sensor_cm

        # Calculate centimeter length using ratio and full pixel length
        # Idea: also return ratio here
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
                # check if before first regarded sensor
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

        # TODO: wann sind mehr als 2 Punkte in der Ebene? 
        # calculate widths and center values
        # Iterate over xray mask height vertically (y-axis)
        for i in range(visualization_data.xray_mask.shape[0]):
            left_index = 0
            width = []
            center = []

            # Iterate over xray mask width horizontally (x-axis)
            for j in range(visualization_data.xray_mask.shape[1]):
                # Enter polygon
                if (visualization_data.xray_mask[i, j] is True and visualization_data.xray_mask[i, j - 1] is False) or (
                        visualization_data.xray_mask[i, j] is True and j == 0):
                    left_index = j
                # Exit polygon
                elif visualization_data.xray_mask[i, j - 1] is True and visualization_data.xray_mask[i, j] is False:
                    right_index = j - 1
                    width.append(right_index - left_index)
                    center.append(left_index + width / 2)
                    top_offset_done = True
                # Polygon is cut off at right side of the image
                elif j == visualization_data.xray_mask.shape[1] - 1 and visualization_data.xray_mask[i, j] is True:
                    right_index = j
                    width.append(right_index - left_index)
                    center.append(left_index + width / 2)
                    top_offset_done = True

                # Calculate offsets if nothing else is todo
                else:
                    if top_offset_done:
                        offset_bottom += 1
                    else:
                        offset_top += 1

            # Append to bigger list that will be returned finally
            widths.append(width)
            centers.append(center)

        # Convert to numpy arrays
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
    def calculate_shortest_path_through_esophagus(visualization_data, offset_top, offset_bottom, center_top,
                                                  center_bottom):
        """
        estimates the course of the manometry catheter in the esophagus
        :param visualization_data: VisualizationData
        :param offset_top: top offset of the x-ray image
        :param offset_bottom: bottom offset of the x-ray image
        :param center_top: center coordinate at the top of the esophagus
        :param center_bottom: center coordinate at the bottom of the esophagus
        :return: path as list of coordinates
        """
        # TODO: handle centers (list of lists) correctly
        array = visualization_data.xray_mask[offset_top:-offset_bottom]
        # Replace zeros with 1000 for cost calculation of shortest path
        # This results in a "mask"/image where the esophagus has values of 1, and the remaining pixels have values of 1000
        costs = np.where(array, 1, 1000)
        # TODO: end is not that easily calculate-able because it is not always the most south point
        # idea: let user choose esophagus exit in GUI, get the centers of the same y and find the element with the closest x in that list OR just use the annotated point ?
        path, cost = graph.route_through_array(costs, start=(0, int(center_top)),
                                               end=(array.shape[0] - 1, int(center_bottom)), fully_connected=True)
        return path

    @staticmethod
    def calculate_index_by_startindex_and_cm_position(start_index, position_cm, sensor_path, esophagus_full_length_px,
                                                      esophagus_full_length_cm):
        """
        calculates an index by going up from a given start
        :param start_index: start index
        :param position_cm: way in cm
        :param sensor_path: estimated path
        :param esophagus_full_length_px: length in pixels
        :param esophagus_full_length_cm: length in cm
        :return: index
        """
        length_fraction = position_cm / esophagus_full_length_cm
        length_px = esophagus_full_length_px * length_fraction
        # find index of sensor_path that corresponds to start_index
        start_iterator = 0
        for i in range(len(sensor_path)):
            if sensor_path[i][0] == start_index:
                start_iterator = i
                break
        # iterate over sensor_path from start_iterator to find requested index
        current_length = 0
        for i in range(start_iterator, -1, -1):
            if i < start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i + 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i + 1][
                                                                                                  1]) ** 2)
            if current_length >= length_px:
                return sensor_path[i][0]
        return None

    @staticmethod
    def calculate_lower_sphincter_center(visualization_data, surfacecolor_list):
        """
        calculates the center position of the lower sphincter by searching for the maximum pressure
        @param visualization_data: VisualizationData
        @param surfacecolor_list: list of surfacecolors for every frame
        @return: index
        """
        # TODO: sphincter upper pos is now a list of 2 points 
        center_index_per_timestep = []
        for i in range(len(surfacecolor_list)):
            max_value_upper_pos = 0
            max_value_lower_pos = 0
            max_value = 0
            for j in range(visualization_data.sphincter_upper_pos, len(surfacecolor_list[0])):
                if surfacecolor_list[i][j] > max_value:
                    max_value_lower_pos = j
                    max_value_upper_pos = j
                    max_value = surfacecolor_list[i][j]
                elif surfacecolor_list[i][j] == max_value and max_value_lower_pos < j:
                    max_value_lower_pos = j
            center_index_per_timestep.append((max_value_upper_pos + max_value_lower_pos) / 2)
        return int(sum(center_index_per_timestep) / len(center_index_per_timestep))

    @staticmethod
    def calculate_lower_sphincter_boundary(visualization_data, lower_sphincter_center, sensor_path, max_index,
                                           esophagus_full_length_cm, esophagus_full_length_px):
        """
        calculates the upper and lower boundary of the sphincter by its center and the length
        @param visualization_data: VisualizationData
        @param lower_sphincter_center: center index of the sphincter
        @param sensor_path: estimated path
        @param max_index: maximum index value at the bottom
        @param esophagus_full_length_cm: length in cm
        @param esophagus_full_length_px: length in pixels
        @return: tuple of upper and lower boundary index
        """
        cm_to_px_factor = esophagus_full_length_px / esophagus_full_length_cm
        sphincter_length_px = visualization_data.sphincter_length_cm * cm_to_px_factor

        # find index of sensor_path that corresponds to lower_sphincter_center
        start_iterator = 0
        for i in range(len(sensor_path)):
            if sensor_path[i][0] == lower_sphincter_center:
                start_iterator = i
                break

        # upper border index
        upper_border_index = 0
        current_length = 0
        for i in range(start_iterator, -1, -1):
            if i < start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i + 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i + 1][
                                                                                                  1]) ** 2)
            if current_length >= sphincter_length_px / 2:
                upper_border_index = sensor_path[i][0]
                break

        # lower border index
        lower_border_index = max_index
        current_length = 0
        for i in range(start_iterator, len(sensor_path)):
            if i > start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i - 1][
                                                                                                  1]) ** 2)
            if current_length >= sphincter_length_px / 2:
                lower_border_index = sensor_path[i][0]
                break

        return upper_border_index, lower_border_index

    @staticmethod
    def calculate_metrics(visualization_data, figure_x, figure_y, surfacecolor_list, sensor_path, max_index,
                          esophagus_full_length_cm, esophagus_full_length_px):
        """
        calculates the metrics for tubular part (volume*pressure) and sphincter (volume/pressure)
        @param visualization_data: VisualizationData
        @param figure_x: x-values of the figure
        @param figure_y: y-values of the figure
        @param surfacecolor_list: list of surfacecolors for every frame
        @param sensor_path: estimated path
        @param max_index: maximum index value at the bottom
        @param esophagus_full_length_cm: length in cm
        @param esophagus_full_length_px: length in pixels
        @return: tuple of two lists containing the metrics
        """
        lower_sphincter_center = FigureCreator.calculate_lower_sphincter_center(visualization_data, surfacecolor_list)
        lower_sphincter_boundary = FigureCreator.calculate_lower_sphincter_boundary(visualization_data,
                                                                                    lower_sphincter_center, sensor_path,
                                                                                    max_index, esophagus_full_length_cm,
                                                                                    esophagus_full_length_px)
        tubular_part_upper_boundary = FigureCreator.calculate_index_by_startindex_and_cm_position(
            lower_sphincter_boundary[0], config.length_tubular_part_cm, sensor_path, esophagus_full_length_px,
            esophagus_full_length_cm)
        if tubular_part_upper_boundary is None:
            tubular_part_upper_boundary = 0

        px_as_cm = esophagus_full_length_cm / esophagus_full_length_px

        # calculate tubular metric
        metric_tubular = np.zeros(len(surfacecolor_list))
        for i in range(tubular_part_upper_boundary, lower_sphincter_boundary[0]):
            shapely_poly = shapely.geometry.Polygon(tuple(zip(figure_x[i], figure_y[i])))
            volume_slice = shapely_poly.area * px_as_cm
            for j in range(len(surfacecolor_list)):
                metric_tubular[j] += volume_slice * surfacecolor_list[j][i]

        # calculate sphincter metric
        metric_sphincter = np.zeros(len(surfacecolor_list))
        for i in range(lower_sphincter_boundary[0], lower_sphincter_boundary[1] + 1):
            shapely_poly = shapely.geometry.Polygon(tuple(zip(figure_x[i], figure_y[i])))
            volume_slice = shapely_poly.area * px_as_cm
            for j in range(len(surfacecolor_list)):
                metric_sphincter[j] += volume_slice / surfacecolor_list[j][i]

        return metric_tubular, metric_sphincter
