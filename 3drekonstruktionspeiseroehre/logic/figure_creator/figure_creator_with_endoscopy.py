import warnings
import config
import numpy as np
import shapely.geometry
from logic.figure_creator.figure_creator import FigureCreator
from logic.visualization_data import VisualizationData
from scipy.interpolate import interp1d
from shapely.geometry import LineString
from math import atan
from scipy import spatial


class FigureCreatorWithEndoscopy(FigureCreator):
    """Implements FigureCreator for figure creation with endoscopy"""

    def __init__(self, visualization_data: VisualizationData):
        """
        initFigureCreatorWithEndoscopy
        :param visualization_data: VisualizationData
        """
        # Frames of the pressure (Manometry) animation
        self.number_of_frames = visualization_data.pressure_matrix.shape[1]

        # Calculate a path through the esophagus along the xray image
        sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(visualization_data)

        # Extract information necessary for reconstruction and metrics from input
        widths, centers, slopes, offset_top = FigureCreator.calculate_widths_centers_slope_offset(
            visualization_data, sensor_path)

        esophagus_full_length_px = FigureCreator.calculate_esophagus_length_px(sensor_path, 0,
                                                                               visualization_data.esophagus_exit_pos)

        esophagus_full_length_cm = FigureCreator.calculate_esophagus_full_length_cm(sensor_path,
                                                                                    esophagus_full_length_px,
                                                                                    visualization_data)

        # Calculate shape with endoscopy data
        # Get array of n equi-spaced values between 0 and 2pi
        angles = np.linspace(0, 2 * np.pi, config.figure_number_of_angles)

        # Calculates distance to endoscopy screenshot centroid for each angle
        distances_from_centroid = []
        for polygon in visualization_data.endoscopy_polygons:
            shapely_poly = shapely.geometry.Polygon(polygon)
            centroid = shapely_poly.centroid
            max_diameter = int(round(shapely_poly.length))  # Round to the nearest integer for max_diameter
            current_polygon_distances_from_centroid = []
            for angle in angles:
                x1, y1 = int(round(centroid.x)), int(round(centroid.y))
                x2, y2 = int(round(centroid.x + (np.cos(angle) * max_diameter))), int(round(centroid.y + (np.sin(angle) * max_diameter)))
                
                line = [(x1, y1), (x2, y2)]
                shapely_line = shapely.geometry.LineString(line)
                
                boundary = [LineString([pt1, pt2]) for pt1, pt2 in
                            zip(shapely_poly.boundary.coords, shapely_poly.boundary.coords[1:])]
                
                intersections = []
                for boundary_line in boundary:
                    # Not all boundaries and lines intersect (logically), suppress shapely warning if no intersections occur
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        intersection = shapely_line.intersection(boundary_line)
                        if not intersection.is_empty:
                            intersections.append(intersection)
                
                distance = max(
                    [shapely.geometry.LineString([(x1, y1), (int(round(intersection.x)), int(round(intersection.y)))]).length for intersection in intersections] + [
                        0])  # distance from centroid to outer polygon bound in specific angle
                current_polygon_distances_from_centroid.append(distance)
            distances_from_centroid.append(current_polygon_distances_from_centroid)

        # Transform endoscopy position information
        endoscopy_image_indexes = FigureCreatorWithEndoscopy.__calculate_endoscopy_indexes(
            visualization_data.endoscopy_image_positions_cm, visualization_data.endoscopy_start_pos, offset_top,
            sensor_path,
            esophagus_full_length_px, esophagus_full_length_cm)

        # Remove outliers
        indexes_to_remove = [i for i, v in enumerate(endoscopy_image_indexes) if v is None]
        for i in indexes_to_remove:
            distances_from_centroid[i] = None
        endoscopy_image_indexes = [i for i in endoscopy_image_indexes if i is not None]
        distances_from_centroid = [i for i in distances_from_centroid if i is not None]

        # Interpolation
        interpolated_radius = np.empty((len(widths), config.figure_number_of_angles))
        for i in range(config.figure_number_of_angles):
            x_for_interpolation = endoscopy_image_indexes.copy()
            y_for_interpolation = [row[i] for row in distances_from_centroid]
            if 0 not in x_for_interpolation:
                x_for_interpolation.append(0)
                y_for_interpolation.append(distances_from_centroid[0][i])
            if len(widths) - 1 not in x_for_interpolation:
                x_for_interpolation.append(len(widths) - 1)
                y_for_interpolation.append(distances_from_centroid[len(distances_from_centroid) - 1][i])
            interpolation_function = interp1d(x_for_interpolation, y_for_interpolation, kind='linear')
            interpolated_radius[:, i] = [interpolation_function(index) for index in range(len(widths))]

        # Initialize lists to store the calculated x, y, and z values
        x = []
        y = []
        z = []

        # Iterate over each position
        for i in range(len(widths)):
            x.append(np.cos(angles) * interpolated_radius[i])
            y.append(np.sin(angles) * interpolated_radius[i])
            z.append([0] * len(angles))

        # Convert the lists of values to arrays
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

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

        # Apply rotation matrix
        for i in range(len(z)):
            slope_in_rad = atan(slopes[i])
            # Rotate around y-axis according to slopes
            rotated_coordinates = np.matmul(
                np.array([[np.cos(slope_in_rad), 0, -np.sin(slope_in_rad)],
                          [0, 1, 0],
                          [np.sin(slope_in_rad), 0, np.cos(slope_in_rad)]]), np.array([x[i], y[i], z[i]]))

            # Rotated x and z coordinates
            x[i], _, z[i] = rotated_coordinates
            x[i] += centers[i][1]
            z[i] += centers[i][0]

        # shift axes to start at zero and scale to cm
        px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px
        x = (x - x.min()) * px_to_cm_factor
        y = (y - y.min()) * px_to_cm_factor
        z = z * px_to_cm_factor

        # to store the values of the figure for 3d-export
        visualization_data.figure_x = x
        visualization_data.figure_y = y
        visualization_data.figure_z = z

        # calculate colors
        self.surfacecolor_list = FigureCreator.calculate_surfacecolor_list(sensor_path, visualization_data,
                                                                           esophagus_full_length_px,
                                                                           esophagus_full_length_cm)

        # create figure
        self.figure = FigureCreator.create_figure(x, y, z, self.surfacecolor_list, config.title_with_endoscopy)
        
        # Create endoflip table and colors if necessary
        if visualization_data.endoflip_screenshot:
            self.table_figures = FigureCreator.colored_vertical_endoflip_tables_and_colors(visualization_data.endoflip_screenshot)
            self.endoflip_surface_color = FigureCreator.get_endoflip_surface_color(sensor_path,
                                                                                   visualization_data,
                                                                                   esophagus_full_length_cm,
                                                                                   esophagus_full_length_px)
        else:
            self.table_figures = None
            self.endoflip_surface_color = None

        # calculate metrics
        self.metrics = FigureCreator.calculate_metrics(visualization_data, x, y, self.surfacecolor_list, sensor_path,
                                                       len(centers) - 1, esophagus_full_length_cm,
                                                       esophagus_full_length_px)

        self.esophagus_length_cm = FigureCreator.calculate_esophagus_full_length_cm(
            sensor_path, esophagus_full_length_px, visualization_data)

    def get_figure(self):
        return self.figure

    def get_endoflip_tables(self):
        return self.table_figures
    
    def get_endoflip_surface_color(self, ballon_volume: str, aggregate_function: str):
        return self.endoflip_surface_color[ballon_volume][aggregate_function]

    def get_surfacecolor_list(self):
        return self.surfacecolor_list

    def get_number_of_frames(self):
        return self.number_of_frames

    def get_metrics(self):
        return self.metrics

    def get_esophagus_full_length_cm(self):
        return self.esophagus_length_cm

    @staticmethod
    def __calculate_endoscopy_indexes(endoscopy_image_positions_cm, endoscopy_start_pos, offset_top, sensor_path,
                                      esophagus_full_length_px,
                                      esophagus_full_length_cm):
        """
        calculates the pixel positions of the endoscopy images
        :param endoscopy_image_positions_cm: the positions given by the filenames
        :param endoscopy_start_pos: start position of the endoscopy
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param esophagus_full_length_px: length of the esophagus in pixels
        :param esophagus_full_length_cm: length of the esophagus in cm
        :return: indexes
        """
        endoscopy_image_indexes = []
        endoscopy_start_pos = (endoscopy_start_pos[1], endoscopy_start_pos[0])
        # Find endoscopy start position in sensor_path
        _, index = spatial.KDTree(np.array(sensor_path)).query(np.array(endoscopy_start_pos))
        for position in endoscopy_image_positions_cm:
            endoscopy_image_indexes.append(FigureCreator.calculate_index_by_startindex_and_cm_position(
                index, position, sensor_path, esophagus_full_length_px, esophagus_full_length_cm))
        return endoscopy_image_indexes
