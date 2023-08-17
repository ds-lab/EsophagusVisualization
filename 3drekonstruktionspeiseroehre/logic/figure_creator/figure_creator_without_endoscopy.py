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
        sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(visualization_data, offset_top,
                                                                              offset_bottom, centers[0])
        
        esophagus_full_length_px = FigureCreator.calculate_esophagus_length_px(sensor_path, 0, visualization_data.esophagus_exit_pos)

        esophagus_full_length_cm = FigureCreator.calculate_esophagus_full_length_cm(sensor_path,
                                                                                    esophagus_full_length_px,
                                                                                    visualization_data, offset_top)

 

        # Calculate shape without endoscopy data by approximating profile as circles
        # TODO: handle list of lists widths and centers

        # Get array of 50 equi-spaced values between 0 and 2pi
        angles = np.linspace(0, 2 * np.pi, config.figure_number_of_angles)

        # Initialize lists to store the calculated x, y, and z values
        x = []
        y = []
        z = []

        # Iterate over each position
        for i in range(len(widths)):
                for w, c in zip(widths[i], centers[i]):
                        x.append(np.cos(angles) * (w / 2) + c)
                        y.append(np.sin(angles) * (w / 2))
                        z.append([i] * len(angles))

        # Convert the lists of values to arrays
        x = np.array(x)
        y = np.array(y)
        #theta, v = np.meshgrid(angles, range(7))
        z = np.array(z)

        # Shift axes to start at zero and scale to cm
        px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px
        x = (x - x.min()) * px_to_cm_factor
        y = (y - y.min()) * px_to_cm_factor
        z = z * px_to_cm_factor

        # calculate colors
        # self.surfacecolor_list = FigureCreator.calculate_surfacecolor_list(sensor_path, visualization_data,
        #                                                                    esophagus_full_length_px,
        #                                                                    esophagus_full_length_cm, offset_top)

        self.surfacecolor_list = []
        # create figure
        self.figure = FigureCreator.create_figure(x, y, z, self.surfacecolor_list,
                                                  '3D-Ansicht aus Röntgen- und Manometriedaten')

        # calculate metrics
        # TODO: todo correct centers usage
        # self.metrics = FigureCreator.calculate_metrics(visualization_data, x, y, self.surfacecolor_list, sensor_path,
        #                                                len(centers)-1, esophagus_full_length_cm, esophagus_full_length_px)
        self.metrics = [0],[0]

    def get_figure(self):
        return self.figure

    def get_surfacecolor_list(self):
        return self.surfacecolor_list

    def get_number_of_frames(self):
        return self.number_of_frames

    def get_metrics(self):
        return self.metrics
