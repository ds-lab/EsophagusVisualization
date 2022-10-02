import shapely.geometry
from shapely.geometry import LineString
import numpy as np
from scipy.interpolate import interp1d
import config
from figure_creator import FigureCreator
from visualization_data import VisualizationData


class FigureCreatorWithEndoscopy(FigureCreator):
    """Implements FigureCreator for figure creation with endoscopy"""

    def __init__(self, visualization_data: VisualizationData):
        """
        initFigureCreatorWithEndoscopy
        :param visualization_data: VisualizationData
        """
        self.number_of_frames = visualization_data.pressure_matrix.shape[1]
        widths, centers, offset_top, offset_bottom = FigureCreator.calculate_widths_and_centers_and_offsets(visualization_data)
        sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(visualization_data, offset_top,
                                                                              offset_bottom, centers[0],
                                                                              centers[centers.shape[0]-1])
        angles = np.linspace(0, 2 * np.pi, config.figure_number_of_angles)
        esophagus_full_length_px = FigureCreator.calculate_esophagus_length_px(sensor_path, 0, centers.shape[0] - 1)
        esophagus_full_length_cm = FigureCreator.calculate_esophagus_full_length_cm(sensor_path, esophagus_full_length_px,
                                                                                    visualization_data, offset_top)

        # shape with endoscopy data
        distances_from_centroid = []
        for polygon in visualization_data.endoscopy_polygons:
            shapely_poly = shapely.geometry.Polygon(polygon)
            centroid = shapely_poly.centroid
            max_diameter = shapely_poly.length  # upper bound
            current_polygon_distances_from_centroid = []
            for angle in angles:
                line = [(centroid.x, centroid.y),
                        (centroid.x + (np.cos(angle) * max_diameter), centroid.y + (np.sin(angle) * max_diameter))]
                shapely_line = shapely.geometry.LineString(line)
                boundary = [LineString([pt1, pt2]) for pt1, pt2 in
                            zip(shapely_poly.boundary.coords, shapely_poly.boundary.coords[1:])]
                intersections = []
                for boundary_line in boundary:
                    intersection = shapely_line.intersection(boundary_line)
                    if intersection:
                        intersections.append(intersection)
                distance = max(
                    [shapely.geometry.LineString([centroid, intersection]).length for intersection in intersections] + [
                        0])  # distance from centroid to outer polygon bound in specific angle
                current_polygon_distances_from_centroid.append(distance)
            distances_from_centroid.append(current_polygon_distances_from_centroid)

        # transform endoscopy position information
        endoscopy_image_indexes = FigureCreatorWithEndoscopy.__calculate_endoscopy_indexes(
            visualization_data.endoscopy_image_positions_cm, visualization_data.endoscopy_start_pos - offset_top, sensor_path,
            esophagus_full_length_px, esophagus_full_length_cm)
        # remove outliers
        indexes_to_remove = [i for i, v in enumerate(endoscopy_image_indexes) if v is None]
        for i in indexes_to_remove:
            distances_from_centroid[i] = None
        endoscopy_image_indexes = [i for i in endoscopy_image_indexes if i is not None]
        distances_from_centroid = [i for i in distances_from_centroid if i is not None]

        # interpolation
        interpolated_radius = np.empty((widths.shape[0], config.figure_number_of_angles))
        for i in range(config.figure_number_of_angles):

            x_for_interpolation = endoscopy_image_indexes.copy()
            y_for_interpolation = [row[i] for row in distances_from_centroid]
            if 0 not in x_for_interpolation:
                x_for_interpolation.append(0)
                y_for_interpolation.append(distances_from_centroid[0][i])
            if widths.shape[0] - 1 not in x_for_interpolation:
                x_for_interpolation.append(widths.shape[0] - 1)
                y_for_interpolation.append(distances_from_centroid[len(distances_from_centroid)-1][i])
            interpolation_function = interp1d(x_for_interpolation, y_for_interpolation, kind='linear')
            interpolated_radius[:, i] = [interpolation_function(index) for index in range(widths.shape[0])]

        theta, v = np.meshgrid(angles, range(widths.shape[0]))

        x = np.cos(theta) * interpolated_radius
        y = np.sin(theta) * interpolated_radius
        z = v

        # shift the center to zero and apply scale information from xray
        for i in range(z.shape[0]):
            # x direction
            max_x = np.max(x[i])
            min_x = np.min(x[i])
            width = max_x - min_x
            x[i] = (x[i] - (min_x + (width / 2))) * ((widths[i] / width) if width > 0 else 1)
            # y direction
            max_y = np.max(y[i])
            min_y = np.min(y[i])
            height = max_y - min_y
            y[i] = (y[i] - (min_y + (height / 2))) * (
                (widths[i] / width) if width > 0 else 1)  # same factor as for x

        # shift x according to information from xray
        x = x + centers[:, np.newaxis]

        # shift axes to start at zero and scale to cm
        px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px
        x = (x - x.min()) * px_to_cm_factor
        y = (y - y.min()) * px_to_cm_factor
        z = z * px_to_cm_factor

        # calculate colors
        self.surfacecolor_list = FigureCreator.calculate_surfacecolor_list(sensor_path, visualization_data,
                                                                           esophagus_full_length_px,
                                                                           esophagus_full_length_cm, offset_top)

        # create figure
        self.figure = FigureCreator.create_figure(x, y, z, self.surfacecolor_list,
                                                  '3D-Ansicht aus Röntgen-, Endoskopie- und Manometriedaten')

    def get_figure(self):
        return self.figure

    def get_surfacecolor_list(self):
        return self.surfacecolor_list

    def get_number_of_frames(self):
        return self.number_of_frames

    @staticmethod
    def __calculate_endoscopy_indexes(endoscopy_image_positions_cm, start_index, sensor_path, esophagus_full_length_px,
                                      esophagus_full_length_cm):
        """
        calculates the pixel positions of the endoscopy images
        :param endoscopy_image_positions_cm: the positions given by the filenames
        :param start_index: start position
        :param sensor_path: estimated path
        :param esophagus_full_length_px: length in pixels
        :param esophagus_full_length_cm: length in cm
        :return: indexes
        """
        endoscopy_image_indexes = []
        for position in endoscopy_image_positions_cm:
            endoscopy_image_indexes.append(FigureCreatorWithEndoscopy.__calculate_index_by_startindex_and_cm_position(
                start_index, position, sensor_path, esophagus_full_length_px, esophagus_full_length_cm))
        return endoscopy_image_indexes

    @staticmethod
    def __calculate_index_by_startindex_and_cm_position(start_index, position_cm, sensor_path, esophagus_full_length_px,
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
        # find index of sensor_length that corresponds to start_index
        start_iterator = 0
        for i in range(len(sensor_path)):
            if sensor_path[i][1] == start_index:
                start_iterator = i
                break
        # iterate over sensor_path from start_iterator to find requested index
        current_length = 0
        for i in range(start_iterator, -1, -1):
            if i < start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i+1][0]) ** 2 + (sensor_path[i][1] -
                                                                                            sensor_path[i+1][1]) ** 2)
            if current_length >= length_px:
                return sensor_path[i][1]
        return None
