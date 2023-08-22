from abc import ABC, abstractmethod

import config
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import shapely.geometry
from logic.visualization_data import VisualizationData
from skimage import graph
from sklearn.linear_model import LinearRegression
from scipy import spatial
import matplotlib.pyplot as plt


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
    def calculate_esophagus_length_px(sensor_path, start_index: int, end_index: tuple):
        """
        calculates the length of the sensor path inside the given part of the esophagus
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param start_index: height to start
        :param end_index: endpoint of esophagus
        :return: length in pixels
        """
        path_length_px = 0
        for i in range(0, len(sensor_path)):
            if i > 0 and sensor_path[i - 1][0] >= start_index:
                # Add euklidean distance of the previous point and the current one, [0] corresponds to the y-axis
                path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
            
            # Stop calculating length at endpoint
            if sensor_path[i][1] == end_index[1] and sensor_path[i][0] == end_index[0]:
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

        # Find the first point on the sensor_path that matches the y-value of the first sensor position
        endpoint = next((point for point in sensor_path if int(point[0]) == int(visualization_data.first_sensor_pos - offset_top)), None)

        # Calculate segement length to find out centimeter to pixel ratio
        length_pixel = FigureCreator.calculate_esophagus_length_px(sensor_path, visualization_data.second_sensor_pos -
                                                                   offset_top, endpoint)
        
        length_cm = first_sensor_cm - second_sensor_cm

        # Calculate centimeter length using ratio and full pixel length
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
    def calculate_widths_centers_slope_offset(visualization_data, sensor_path):
        """
        calculates the widths (width of the esophagus shape for every height on the x-ray image),
        the centers (analogue to widths) and the offsets (area of the images outside the shape of the esophagus)
        :param visualization_data: VisualizationData
        :return: widths and centers as lists of lists and offsets as int
        """
        widths = []
        centers = []
        slopes = []
        offset_top = sensor_path[0][0] # y-value of first point in path

        num_points_for_polyfit = 60

        ####
        # Create a figure and axis FOR DEBUGGING
        # fig, ax = plt.subplots()

        # # Invert y-axis to have positive y downwards FOR DEBUGGING
        # ax.invert_yaxis()
        # # plot xray FOR DEBUGGING
        # coordinates = [(row_idx, col_idx) for row_idx, row in enumerate(visualization_data.xray_mask) for col_idx, value in enumerate(row) if value == 1]
        # x_values, y_values = zip(*coordinates)
        # ax.scatter(y_values, x_values)

        # # plot shortest path FOR DEBUGGING
        # x_values = [point[1] for point in sensor_path] # in sensor path stehen die x werte an index 1
        # y_values = [point[0] for point in sensor_path]
        # ax.plot(x_values,y_values, color="red")
        #plt.savefig("path.png")
        ####

        for i in range(len(sensor_path)-1):
            # Create slope_points that are used to calculate linear regression (slope)
            if i < num_points_for_polyfit //2:
                # Before we have num_points_for_polyfit point available skip to the part where we have enough to calcuate the slope
                point = sensor_path[i]
                slope_points = sensor_path[0 : num_points_for_polyfit-1]
            elif i + num_points_for_polyfit // 2 > len(sensor_path) - 1:
                # At the end we don't have enough points to calculate the slope, use the last point where it was possible
                point = sensor_path[i]
                slope_points = sensor_path[len(sensor_path) - num_points_for_polyfit : len(sensor_path) - 1]
            else:
                # Get surrounding points
                point = sensor_path[i]
                slope_points = sensor_path[i-num_points_for_polyfit//2 : i+num_points_for_polyfit//2 - 1]
            
            # x and y coords of slope_points
            x = np.array([p[1] for p in slope_points]).reshape(-1, 1)
            # Edit x so x-values aren't the same (sklearn can't handle that)
            x = np.array([x+ i * 0.00001 for i, x in enumerate(x)])
            y = np.array([p[0] for p in slope_points])
            # Calculate linear regression to get slope of esophagus segment
            model = LinearRegression()
            model.fit(x,y)
            # Calculate perpendicular slope, use epsilon to avoid divisions by zero or values close to zero
            if model.coef_[0] == 0:
                perpendicular_slope = -1 / (model.coef_[0] + 0.0001)
            else:
                perpendicular_slope = -1 / model.coef_[0]
            slopes.append(perpendicular_slope)

            line_length = visualization_data.xray_mask.shape[1]
            # Calculate equidistant points between two points on perpendicular (equidistant to avoid skipping points later)
            # new_y                        y     + m               * (new_x - x)
            perpendicular_start_y=  point[0] + perpendicular_slope * (0 - point[1]) # TODO: fix 
            perpendicular_end_y = point[0] + perpendicular_slope * (visualization_data.xray_mask.shape[1] - 1 - point[1])
            perpendicular_start = (perpendicular_start_y, 0)
            perpendicular_end = (perpendicular_end_y, visualization_data.xray_mask.shape[1]-1)

            if model.coef_[0] > 1000 or model.coef_[0] < -1000:
                # If the points used for the lin reg are inline along the y axis (slope is very high/steep)
                perpendicular_start = (point[0] , point[1] - line_length)
                perpendicular_end = (point[0], point[1] + line_length)

            if model.coef_[0] > -0.0001 and model.coef_[0] < 0.0001:
                # If the points used for the lin reg are inline along the x axis (slope is zero)
                perpendicular_start = (point[0] - line_length , point[1])
                perpendicular_end = (point[0]+ line_length, point[1] )

            y1,x1 = int(perpendicular_start[0]), int(perpendicular_start[1])
            y2,x2 = int(perpendicular_end[0]), int(perpendicular_end[1])
            num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1
            perpendicular_x_values = np.linspace(x1, x2, num_points, dtype=int)
            perpendicular_y_values = np.linspace(y1, y2, num_points, dtype=int)
            perpendicular_points = [(int(y), int(x)) for y, x in zip(perpendicular_y_values, perpendicular_x_values)]

            # Find index of current point / its closest equal in perpendicular
            _, index = spatial.KDTree(np.array(perpendicular_points)).query(np.array(point))
        
            boundary_1 = None
            boundary_2 = None
        
            # Move left and right from the current point along the perpendicular to find the boundaries
            for j in range(len(perpendicular_points) // 2 - 5):
                # TODO: für die Lücken -> maybe weil der sensor_path an der Grenze lang läuft werden die boundaries hier komisch, siehe geplottete centers die an der Grenze entlang laufen
                # Move "left" until boundary is found
                if boundary_1 is None:
                    point_along_line = perpendicular_points[index-j]
                    # Check that point is within image
                    if point_along_line[0] >= 0 and point_along_line[1] >= 0 and point_along_line[0] < visualization_data.xray_mask.shape[0] and point_along_line[1]<visualization_data.xray_mask.shape[1]:
                        if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 0 and boundary_1 is None:
                            boundary_1 = perpendicular_points[index-j]
                    
                # Move "right" until boundary is found
                if boundary_2 is None:
                    point_along_line = perpendicular_points[index+j]
                    # Check that point is within image
                    if point_along_line[0] >= 0 and point_along_line[1] >= 0 and point_along_line[0] < visualization_data.xray_mask.shape[0] and point_along_line[1]<visualization_data.xray_mask.shape[1]:
                        if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 0:
                            boundary_2 = perpendicular_points[index+j]

            
            #### FOR DEBUGGING
            if boundary_1 is not None and boundary_2 is not None:
                #plt.plot([boundary_1[1], boundary_2[1]],[boundary_1[0], boundary_2[0]], color="red")
                pass
            ####

            # Check if there are at least 2 boundary points 
            if boundary_1 is None or boundary_2 is None:
                plt.plot(perpendicular_x_values,perpendicular_y_values, color="green") # FOR DEBUGGING
                plt.savefig("perp_points.png")
                break
            # Step 2: Calculate Width
            # Calculate the distance between two boundary points
            width = np.linalg.norm(np.array(boundary_1) - np.array(boundary_2))
            
            # Step 3: Calculate Center
            # Calculate the midpoint between two boundary points
            center = (np.array(boundary_1) + np.array(boundary_2)) / 2
            center = (int(center[0]), int(center[1]))
            
            # Store the calculated width and center
            widths.append(width)
            centers.append(center)
        #### FOR DEBUGGING
        #plt.savefig("perp_points.png") 
        #plt.scatter([point[1] for point in centers], [point[0] for point in centers], color="green")
        #plt.savefig("centers.png")
        ####
            
        return widths, centers, slopes, offset_top

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
        #first_surfacecolor = np.tile(np.array([surfacecolor_list[0]]).transpose(), (1, config.figure_number_of_angles))
        # figure = go.Figure(data=[go.Surface(x=x, y=y, z=z)])
        colors = z
        data = {"x": x.flatten(), "y": y.flatten(), "z": z.flatten(), "colors": colors.flatten()}
        figure = px.scatter_3d(data, x="x", y="y", z="z", color="colors", color_continuous_scale=config.colorscale, range_color=(config.cmin,config.cmax))
        figure.update_layout(scene=dict(aspectmode='data'), uirevision='constant',
                             title=title, title_x=0, title_y=1,
                             margin=dict(l=20, r=20, t=30, b=20), hovermode=False)
        figure.update_scenes(zaxis_autorange="reversed", xaxis_autorange="reversed", xaxis_title_text='Breite',
                             yaxis_title_text='Tiefe', zaxis_title_text='Länge')
        return figure

    @staticmethod
    def calculate_shortest_path_through_esophagus(visualization_data):
        """
        estimates the course of the manometry catheter in the esophagus
        :param visualization_data: VisualizationData
        :param offset_top: top offset of the x-ray image
        :param offset_bottom: bottom offset of the x-ray image
        :param center_top: center coordinate at the top of the esophagus
        :param center_bottom: center coordinate at the bottom of the esophagus
        :return: path as list of coordinates
        """
        # Cut off offsets from xray mask
        array = visualization_data.xray_mask
        # Replace zeros with 1000 for cost calculation of shortest path
        # This results in a "mask"/image where the esophagus has values of 1, and the remaining pixels have values of 1000
        costs = np.where(array, 1, 1000)

        start_top = None
        end_top = None
        found_top = False


        # Search startpoint
        for i in range(visualization_data.xray_mask.shape[0]):
            # Iterate over xray mask width horizontally (x-axis)
            for j in range(visualization_data.xray_mask.shape[1]):
                if visualization_data.xray_mask[i, j]:
                    if not start_top:
                        start_top = (i, j)
                    end_top = (i, j)
                    found_top = True
            if found_top:
                startpoint = (start_top[0], (start_top[1] + end_top[1]) // 2)
                break      

        # Use annotated endpoint as end of shortest path
        endpoint = visualization_data.esophagus_exit_pos
        # Calculate shortest path
        path, cost = graph.route_through_array(costs, start=startpoint,
                                               end=(endpoint[1],endpoint[0]), fully_connected=True)
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
