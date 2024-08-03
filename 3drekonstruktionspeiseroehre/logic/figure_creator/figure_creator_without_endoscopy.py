import config
from math import atan
import numpy as np
from logic.figure_creator.figure_creator import FigureCreator
from logic.visualization_data import VisualizationData


class FigureCreatorWithoutEndoscopy(FigureCreator):
    """Implements FigureCreator for figure creation without endoscopy"""

    def __init__(self, visualization_data: VisualizationData):
        """
        initFigureCreatorWithoutEndoscopy
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

        # Calculate shape without endoscopy data by approximating profile as circles
        # Get array of 50 equi-spaced values between 0 and 2pi
        angles = np.linspace(0, 2 * np.pi, config.figure_number_of_angles)

        # Initialize lists to store the calculated x, y, and z values
        x = []
        y = []
        z = []

        # Iterate over each position
        for i in range(len(widths)):
            x.append(np.cos(angles) * (widths[i] / 2))
            y.append(np.sin(angles) * (widths[i] / 2))
            z.append([0] * len(angles))

        # Convert the lists of values to arrays
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

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

        # Shift axes to start at zero and scale to cm
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
        self.figure = FigureCreator.create_figure(x, y, z, self.surfacecolor_list, config.title_without_endoscopy)

        self.esophagus_length_cm = FigureCreator.calculate_esophagus_full_length_cm(
            sensor_path, esophagus_full_length_px, visualization_data)

        # Create endoflip table and colors if necessary
        if visualization_data.endoflip_screenshot:
            self.table_figures= FigureCreator.colored_vertical_endoflip_tables_and_colors(visualization_data.endoflip_screenshot)
            self.endoflip_surface_color = FigureCreator.get_endoflip_surface_color(sensor_path, visualization_data, esophagus_full_length_cm, esophagus_full_length_px)
        else:
            self.table_figures = None
            self.endoflip_surface_color = None

        # Calculate metrics
        self.metrics = FigureCreator.calculate_metrics(visualization_data, x, y, self.surfacecolor_list, sensor_path,
                                                       len(centers) - 1, esophagus_full_length_cm,
                                                       esophagus_full_length_px)

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
