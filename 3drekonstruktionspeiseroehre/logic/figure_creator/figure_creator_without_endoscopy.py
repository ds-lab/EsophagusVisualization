import config
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
        # Frames of the pressure (Manometrie) animation
        self.number_of_frames = visualization_data.pressure_matrix.shape[1]
        # Extract information necessary for reconstruction and metrics from input
        widths, centers, offset_top, offset_bottom = FigureCreator.calculate_widths_and_centers_and_offsets(
            visualization_data)
        # Calculate a path through the esophagus along the xray image
        # TODO Uebergabeparameter centers[0] und centers[centers.shape[0]-1] anpassen
        sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(visualization_data, offset_top,
                                                                              offset_bottom, centers[0],
                                                                              centers[centers.shape[0] - 1])
        
        esophagus_full_length_px = FigureCreator.calculate_esophagus_length_px(sensor_path, 0, centers.shape[0] - 1)
        esophagus_full_length_cm = FigureCreator.calculate_esophagus_full_length_cm(sensor_path,
                                                                                    esophagus_full_length_px,
                                                                                    visualization_data, offset_top)

        # Calculate shape without endoscopy data by approximating profile as circle
        # TODO: handle list of lists widths and centers

        # Get array of 50 equi-spaced values between 0 and 2pi
        angles = np.linspace(0, 2 * np.pi, config.figure_number_of_angles)

        # Theta == array of a number of width.shape[0], each row containing the angles list
        #  V == array of a number of angles columns, each column containing 0 to widths.shape[0]
        # TODO: currently x and y assume one circle shape -> idea loop over widths/centers and += x and y to get correct values
        # TODO: get a better understanding on what input xyz should be for plotly's Surface figure
        theta, v = np.meshgrid(angles, range(widths.shape[0]))
        x = np.cos(theta) * (widths/2)[:, np.newaxis] + centers[:, np.newaxis]
        y = np.sin(theta) * (widths/2)[:, np.newaxis]
        z = v

        # Shift axes to start at zero and scale to cm
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
                                                  '3D-Ansicht aus Röntgen- und Manometriedaten')

        # calculate metrics
        # TODO: todo correct centers usage
        self.metrics = FigureCreator.calculate_metrics(visualization_data, x, y, self.surfacecolor_list, sensor_path,
                                                       len(centers)-1, esophagus_full_length_cm, esophagus_full_length_px)

    def get_figure(self):
        return self.figure

    def get_surfacecolor_list(self):
        return self.surfacecolor_list

    def get_number_of_frames(self):
        return self.number_of_frames

    def get_metrics(self):
        return self.metrics
