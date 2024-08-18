import config
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import shapely.geometry
import cv2
import tcod
from abc import ABC, abstractmethod
from natsort import natsorted
from sklearn.linear_model import LinearRegression
from scipy import spatial
from PIL import Image
from matplotlib import cm
from logic.visualization_data import VisualizationData


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

    @abstractmethod
    def get_esophagus_full_length_cm(self):
        """
        returns the length of the esophagus in cm
        """
        pass

    @staticmethod
    def calculate_esophagus_length_px(sensor_path, start_index: int, end_index: tuple):
        """
        calculates the length of the sensor path inside the given part of the esophagus
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param start_index: height to start
        :param end_index: endpoint of the esophagus
        :return: length of the esophagus in pixels
        """
        path_length_px = 0
        for i in range(0, len(sensor_path)):
            # The euclidean distance of the start- and endpoint of the esophagus is calculated by adding the
            # euclidean distance between every previous point and the current point.
            # sensor_path is a list of coordinates (y, x), therefore [0] corresponds to the y-axis
            if i > 0 and sensor_path[i - 1][0] >= start_index:
                path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
            # Stop calculating length at endpoint of the esophagus
            if sensor_path[i][1] == end_index[1] and sensor_path[i][0] == end_index[0]:
                break
        return path_length_px

    @staticmethod
    def calculate_esophagus_full_length_cm(sensor_path, esophagus_full_length_px, visualization_data):
        """
        calculates the length of the sensor path inside the esophagus in cm
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param esophagus_full_length_px: length of the esophagus in pixels
        :param visualization_data: VisualizationData
        :return: length in cm
        """
        # Map sensor indices to centimeter
        first_sensor_cm = config.coords_sensors[visualization_data.first_sensor_index]
        second_sensor_cm = config.coords_sensors[visualization_data.second_sensor_index]

        # sensor_pos are coordinates (x, y) and sensor_path is a list of coordinates (y, x)
        # to find the nearest points on sensor_path: sensor_pos_switched
        first_sensor_pos_switched = (visualization_data.first_sensor_pos[1], visualization_data.first_sensor_pos[0])
        second_sensor_pos_switched = (visualization_data.second_sensor_pos[1], visualization_data.second_sensor_pos[0])

        # KDTree uses the switched first and second_sensor_pos to find the nearest points on the sensor_path
        _, index_first = spatial.KDTree(np.array(sensor_path)).query(np.array(first_sensor_pos_switched))
        _, index_second = spatial.KDTree(np.array(sensor_path)).query(np.array(second_sensor_pos_switched))

        path_length_px = 0
        # The euclidean distance of the first and second_sensor_pos is calculated by adding the
        # euclidean distance between every previous and the current point on the sensor_path.
        # sensor_path is a list of coordinates (y, x), therefore [0] corresponds to the y-axis
        for i in range(index_second, index_first + 1):
            path_length_px += np.sqrt(
                (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)
            if i == index_first:
                break

        length_cm = first_sensor_cm - second_sensor_cm

        # Calculate centimeter length using ratio and full pixel length
        return length_cm * (esophagus_full_length_px / path_length_px)

    @staticmethod
    def calculate_surfacecolor_list(sensor_path, visualization_data, esophagus_full_length_px,
                                    esophagus_full_length_cm):
        """
        calculates the surface-colors for every frame
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :param visualization_data: VisualizationData
        :param esophagus_full_length_px: length in pixels
        :param esophagus_full_length_cm: length in cm
        :return: list of surface-colors
        """
        pressure_matrix = visualization_data.pressure_matrix
        px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px

        # sensor_pos are coordinates (x, y) and sensor_path is a list of coordinates (y, x)
        # to calculate the length of the esophagus: sensor_pos_switched
        first_sensor_pos_switched = (visualization_data.first_sensor_pos[1], visualization_data.first_sensor_pos[0])
        _, index_first = spatial.KDTree(np.array(sensor_path)).query(np.array(first_sensor_pos_switched))

        # The euclidean distance from the top to the first sensor is calculated by adding the
        # euclidean distance between every previous and the current point on the sensor_path.
        first_sensor_path_length_px = 0
        for i in range(0, len(sensor_path)):
            if i == index_first:
                break
            elif i > 0:
                first_sensor_path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2)

        # Convert to cm
        first_sensor_path_length_cm = first_sensor_path_length_px * px_to_cm_factor
        sensor_path_lengths_px = [(first_sensor_path_length_cm - (
                config.coords_sensors[visualization_data.first_sensor_index] - coord)) / px_to_cm_factor for coord
                                  in config.coords_sensors]

        surfacecolor_list = []
        # Iterate over frames for animation
        for frame_number in range(pressure_matrix.shape[1]):
            surfacecolor = []
            # Find the sensor (from top) that is just before the regarded area
            current_sensor_index = 0
            for i in range(len(config.coords_sensors) - 1):
                if sensor_path_lengths_px[i] < 0 and sensor_path_lengths_px[i + 1] < 0:
                    current_sensor_index = i + 1
            current_path_length_px = 0
            is_before_first_sensor = 0 < sensor_path_lengths_px[0]
            is_after_last_sensor = False
            for i in range(len(sensor_path)):
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
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :return: widths and centers as lists of lists and offsets as int
        """
        widths = []  # width of the esophagus shape for every height on the x-ray image
        centers = []  # center of the esophagus shape for every height on the x-ray image
        slopes = []  # slope of esophagus segment using linear regression
        offset_top = sensor_path[0][0]  # y-value of first point in path

        num_points_for_polyfit = config.num_points_for_polyfit_smooth
        count = 0
        point_distance = config.point_distance_in_polyfit
        for i in range(len(sensor_path)):
            # if there is a sharp edge, more points are used to refine the line
            if i > (point_distance * 2) and abs(sensor_path[i][1] - sensor_path[i - (point_distance * 2)][1]) < abs(
                    sensor_path[i][1] - sensor_path[i - point_distance][1]):
                num_points_for_polyfit = config.num_points_for_polyfit_sharp
                count = 1
            if 0 < count < config.points_for_smoothing_in_sharp_edges:
                num_points_for_polyfit = config.num_points_for_polyfit_sharp
                count += 1
            elif count == config.points_for_smoothing_in_sharp_edges:
                count = 0
                num_points_for_polyfit = config.num_points_for_polyfit_smooth
            # Create slope_points that are used to calculate linear regression (slope)
            if i < num_points_for_polyfit // 2:
                # If there are not enough num_points_for_polyfit available,
                # skip to the part where enough points to calculate the slope are available
                point = sensor_path[i]
                slope_points = sensor_path[0: num_points_for_polyfit - 1]
            elif i + num_points_for_polyfit // 2 > len(sensor_path) - 1:
                # If at the end there are not enough points available to calculate the slope,
                # the last possible point is used
                point = sensor_path[i]
                slope_points = sensor_path[len(sensor_path) - num_points_for_polyfit: len(sensor_path) - 1]
            else:
                # Get surrounding points
                point = sensor_path[i]
                slope_points = sensor_path[i - num_points_for_polyfit // 2: i + num_points_for_polyfit // 2 - 1]

            # x and y coords of slope_points
            x = np.array([p[1] for p in slope_points]).reshape(-1, 1)
            # Edit x so x-values aren't the same (sklearn can't handle that)
            x = np.array([x + i * 0.00001 for i, x in enumerate(x)])
            # Take only last and first value for regression
            x1 = x[0]
            x2 = x[-1]
            x = np.array([x1, x2])
            y = np.array([p[0] for p in slope_points])
            y1 = y[0]
            y2 = y[-1]
            y = np.array([y1, y2])
            # Calculate linear regression to get slope of esophagus segment
            model = LinearRegression()
            model.fit(x, y)

            # Calculate perpendicular slope, use epsilon to avoid divisions by zero or values close to zero
            if model.coef_[0] == 0:
                perpendicular_slope = -1 / (model.coef_[0] + 0.0001)
            else:
                perpendicular_slope = -1 / model.coef_[0]

            # If the esophagus shows a tight curve/bend, wrong slopes may be calculated (very steep perpendicular)
            # -> in this case take the previous slope to skip the wrong one
            if i > 1 and abs(perpendicular_slope) > 30 and abs(perpendicular_slope / slopes[i - 1]) > 50:
                perpendicular_slope = slopes[i - 1]

            slopes.append(perpendicular_slope)

            line_length = visualization_data.xray_mask.shape[1] * 2
            # Calculate equidistant points between two points on perpendicular
            # (equidistant to avoid skipping points later)
            # new_y               =          y     + m             * (new_x - x)
            perpendicular_start_y = point[0] + perpendicular_slope * (0 - point[1])
            perpendicular_end_y = point[0] + perpendicular_slope * (
                    visualization_data.xray_mask.shape[1] - 1 - point[1])
            perpendicular_start = (perpendicular_start_y, 0)
            perpendicular_end = (perpendicular_end_y, visualization_data.xray_mask.shape[1] - 1)

            if model.coef_[0] > 1000 or model.coef_[0] < -1000:
                # If the points used for the linear regression are inline along the y-axis (slope is very high/steep)
                perpendicular_start = (point[0], point[1] - line_length)
                perpendicular_end = (point[0], point[1] + line_length)

            if -0.0001 < model.coef_[0] < 0.0001:
                # If the points used for the lin reg are inline along the x-axis (slope is zero)
                # slope der perpendicular ist sehr steil, fast senkrecht
                # überprüfen ob die boundaries die durch diese Stellen entstanden sind, Sinn machen
                perpendicular_start = (point[0] - line_length, point[1])
                perpendicular_end = (point[0] + line_length, point[1])

            y1, x1 = int(perpendicular_start[0]), int(perpendicular_start[1])
            y2, x2 = int(perpendicular_end[0]), int(perpendicular_end[1])
            num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1
            perpendicular_x_values = np.linspace(x1, x2, num_points, dtype=int)
            perpendicular_y_values = np.linspace(y1, y2, num_points, dtype=int)
            perpendicular_points = [(int(y), int(x)) for y, x in zip(perpendicular_y_values, perpendicular_x_values)]

            # Find index of current point / its closest equal in perpendicular
            _, index = spatial.KDTree(np.array(perpendicular_points)).query(np.array(point))

            # Sometimes the index isn't completely correct due to rounding errors and can lie outside the esophagus
            # Find 'correct' index by searching left and right along the perpendicular
            index_l = index
            index_r = index
            point_along_line = perpendicular_points[index]

            while visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 0 and index_r < len(
                    perpendicular_points) and index_l > 0:
                index_l = index_l - 1
                point_along_line = perpendicular_points[index_l]
                if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 1:
                    index = index_l
                    break
                index_r = index_r + 1
                point_along_line = perpendicular_points[index_r]
                if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 1:
                    index = index_r
                    break

            boundary_1 = None
            boundary_2 = None
            # Move left and right from the current point along the perpendicular to find the boundaries
            for j in range(len(perpendicular_points) - 1):
                # Move "left" until boundary is found
                if boundary_1 is None and (index - j) >= 0:
                    point_along_line = perpendicular_points[index - j]
                    # Check that point is within image
                    if 0 <= point_along_line[0] < visualization_data.xray_mask.shape[0] and 0 <= point_along_line[1] < \
                            visualization_data.xray_mask.shape[1]:
                        if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 0:
                            boundary_1 = point_along_line
                        # Esophagus touches left image edge
                        elif point_along_line[0] == 0 or point_along_line[1] == 0:
                            boundary_1 = point_along_line

                # Move "right" until boundary is found
                if boundary_2 is None and (index + j) <= len(perpendicular_points) - 1:
                    point_along_line = perpendicular_points[index + j]
                    # Check that point is within image
                    if 0 <= point_along_line[0] < visualization_data.xray_mask.shape[0] and 0 <= point_along_line[1] < \
                            visualization_data.xray_mask.shape[1]:
                        if visualization_data.xray_mask[point_along_line[0]][point_along_line[1]] == 0:
                            boundary_2 = point_along_line
                        # Esophagus touches right image edge
                        elif point_along_line[0] == visualization_data.xray_mask.shape[0] - 1 or point_along_line[1] == \
                                visualization_data.xray_mask.shape[1] - 1:
                            boundary_2 = point_along_line

            # Check if there are at least 2 boundary points 
            if boundary_1 is None or boundary_2 is None:
                if i == 0:
                    # In very few cases the top is extremely tilted so that only one boundary can be found,
                    # in this case "fake" this point by creating a small width
                    boundary_1 = (perpendicular_points[index][0] - 1, perpendicular_points[index][1] - 1)
                    boundary_2 = (perpendicular_points[index][0] + 1, perpendicular_points[index][1] + 1)
                else:
                    raise ValueError(f"Algorithm wasn't able to detect esophagus width at sensor_point {i}")

            # Step 2: Calculate Width
            # Calculate the distance between two boundary points
            if boundary_1 is not None and boundary_2 is not None:
                width = np.linalg.norm(np.array(boundary_1) - np.array(boundary_2))

            # Step 3: Calculate Center
            # Calculate the midpoint between two boundary points
            if boundary_1 is not None and boundary_2 is not None:
                center = (np.array(boundary_1) + np.array(boundary_2)) / 2
                center = (int(center[0]), int(center[1]))

            # Store the calculated width and center
            widths.append(width)
            centers.append(center)

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
        first_surfacecolor = np.tile(np.array([surfacecolor_list[0]]).transpose(), (1, config.figure_number_of_angles))

        figure = go.Figure(data=[
            go.Surface(x=x, y=y, z=z, surfacecolor=first_surfacecolor, colorscale=config.colorscale, cmin=config.cmin,
                       cmax=config.cmax)])

        figure.update_layout(scene=dict(aspectmode='data'), uirevision='constant',
                             title=dict(text=title, font=dict(size=24)), title_x=0, title_y=1,
                             margin=dict(l=20, r=20, t=30, b=20), hovermode=False)
        figure.update_scenes(zaxis_autorange="reversed", xaxis_autorange="reversed", xaxis_title_text='Breite',
                             yaxis_title_text='Tiefe', zaxis_title_text='Länge')
        return figure

    @staticmethod
    def calculate_shortest_path_through_esophagus(visualization_data):
        """
        estimates the course of the manometry catheter in the esophagus
        :param visualization_data: VisualizationData
        :return: path as list of coordinates
        """

        # Shortest path calculation: utilization of points between which the shortest path should be calculated
        # User-defined esophagus-exit position at the "bottom" of the esophagus
        # (does not necessarily need to be the point that is most at the bottom)
        # The middle of the most upper horizontal line of the x-ray mask at the top of the esophagus
        # However, due to drawing inaccuracies of the xray-polygon the most upper "line" is not always horizontal
        # (or even one single "line")
        # -> find the most upper horizontal contour of the xray-mask, straighten it and find its middle

        array = visualization_data.xray_mask

        # Reverse the values in the xray_mask (array), to find the contours in a black figure on white background
        for row in range(len(array)):
            for col in range(len(array[row])):
                if array[row][col] == 0:
                    array[row][col] = 1
                elif array[row][col] == 1:
                    array[row][col] = 0
                else:
                    print("nicht 0 oder 1")

        # Step1: Find and straighten contours around esophagus xray_mask
        # adapted from: https://stackoverflow.com/questions/60227551/rectify-edges-of-a-shape-in-mask-with-opencv

        # Convert array to image
        image = Image.fromarray(np.uint8(cm.Greys(array) * 255))

        # Convert the Pillow Image to a NumPy array
        image_np = np.array(image)

        # Convert the image to grayscale (CV_8UC1)
        gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # From the black and white image we find the contours
        # (threshold describes which pixel values are regarded as black vs. white)
        _, threshold = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0]

        peri = cv2.arcLength(contours, closed=True)
        approx = cv2.approxPolyDP(contours, epsilon=0.01 * peri, closed=True)

        # Delta threshold
        t = config.px_threshold_for_straight_line

        # n - Number of vertices
        n = approx.shape[0]

        # now to true (straight) contours are approximated
        for i in range(n):
            #      p1              p2
            #       *--------------*
            #       |
            #       |
            #       |
            #       *
            #      p0

            p0 = approx[(i + n - 1) % n][0]  # Previous vertex
            p1 = approx[i][0]  # Current vertex
            p2 = approx[(i + 1) % n][0]  # Next vertex
            dx = p2[0] - p1[0]  # Delta pixels in horizontal direction
            dy = p2[1] - p1[1]  # Delta pixels in vertical direction

            # Fix x index of vertices p1 and p2 to be with same x coordinate ([<p1>, <p2>] form horizontal line).
            if abs(dx) < t:
                if ((dx < 0) and (p0[0] > p1[0])) or ((dx > 0) and (p0[0] < p1[0])):
                    p2[0] = p1[0]
                else:
                    p1[0] = p2[0]

            # Fix y index of vertices p1 and p2 to be with same y coordinate ([<p1>, <p2>] form vertical line).
            if abs(dy) < t:
                if ((dy < 0) and (p0[1] > p1[1])) or ((dy > 0) and (p0[1] < p1[1])):
                    p2[1] = p1[1]
                else:
                    p1[1] = p2[1]

            approx[i][0] = p1
            approx[(i + 1) % n][0] = p2

        # Step2: Calculate middle point of most upper horizontal line
        embedded_lists = [inner_list[0] for inner_list in approx]
        sorted_lists = sorted(embedded_lists, key=lambda x: (x[1]))

        x1 = sorted_lists[0][0]
        x2 = sorted_lists[1][0]
        middle_y = sorted_lists[0][1]
        length = x2 - x1
        middle_x = x1 + length // 2

        # Step3: Expand Esophagus = add some white pixels at the top at the esophagus
        # for better estimation of the shortest paths and centers
        # find first row which contains the esophagus
        top_y = None
        for row in range(len(array)):
            for col in range(len(array[row])):
                # to detect the esophagus/xray_mask, find the values equal to 0
                if array[row][col] == 0 and top_y is None:
                    top_y = row
                    break

        # To straighten the top line of the esophagus
        # -> Zeroes are added between the first row that contains the esophagus (top_y) and middle_y
        # To create a better estimation of the shortest path
        # -> top_y - config.expansion_delta: start a little higher, so that the esophagus is expanded a little more
        # take max from (top_y - config.expansion_delta) and 1 to avoid out-of-range plus (1 instead of 0)
        # to leave at least one "none-esophagus" line at the top (to avoid errors
        # due to missing boundary-points in case of very skewed esophagus)
        for row in range(max(top_y - config.expansion_delta, 1), middle_y + 1):
            for col in range(x1, x2):
                array[row][col] = 0

        # Step4: Calculate the shortest path on original xray mask from "middle" to endpoint
        # reverse the values in the array again back to original values for calculation of the shortest path
        for row in range(len(array)):
            for col in range(len(array[row])):
                if array[row][col] == 0:
                    array[row][col] = 1
                elif array[row][col] == 1:
                    array[row][col] = 0
                else:
                    print("nicht 0 oder 1")

        # Use annotated endpoint as end of the shortest path
        endpoint = visualization_data.esophagus_exit_pos

        # Shortest path calculation
        cost = np.where(array, 1, 0)  # define costs according to needs of library tcod
        graph_path = tcod.path.SimpleGraph(cost=cost, cardinal=config.cardinal_cost, diagonal=config.diagonal_cost)
        pf = tcod.path.Pathfinder(graph_path)
        pf.add_root((middle_y, middle_x))
        path = np.array(pf.path_to((endpoint[1], endpoint[0])).tolist())

        return path

    @staticmethod
    def calculate_index_by_startindex_and_cm_position(start_index, position_cm, sensor_path, esophagus_full_length_px,
                                                      esophagus_full_length_cm):
        """
        calculates an index by going up from a given start_index
        :param start_index: start_index / lower sphincter boundary (upper)
        :param position_cm: way in cm (15cm)
        :param sensor_path: estimated path
        :param esophagus_full_length_px: length in pixels
        :param esophagus_full_length_cm: length in cm
        :return: index
        """
        length_fraction = position_cm / esophagus_full_length_cm
        length_px = esophagus_full_length_px * length_fraction

        # iterate over sensor_path from start_iterator to find requested index
        current_length = 0
        for i in range(start_index, -1, -1):
            if i < start_index:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i + 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i + 1][
                                                                                                  1]) ** 2)
            if current_length >= length_px:
                return i
        return None

    @staticmethod
    def calculate_lower_sphincter_center(visualization_data, surfacecolor_list, sensor_path):
        """
        calculates the center position of the lower sphincter by searching for the maximum pressure
        :param visualization_data: VisualizationData
        :param surfacecolor_list: list of surfacecolors for every frame
        :param sensor_path: estimated path of the sensor catheter as list of coordinates
        :return: index
        """
        center_index_per_timestep = []

        # Find index of sphincter_upper_pos in sensor_path
        _, index = spatial.KDTree(np.array(sensor_path)).query(np.array(visualization_data.sphincter_upper_pos))

        for i in range(len(surfacecolor_list)):
            max_value_upper_pos = 0
            max_value_lower_pos = 0
            max_value = 0
            for j in range(index, len(surfacecolor_list[0])):
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
        @param sensor_path: estimated path of the sensor catheter as list of coordinates
        @param max_index: maximum index value at the bottom
        @param esophagus_full_length_cm: length of the esophagus in cm
        @param esophagus_full_length_px: length of the esophagus in pixels
        @return: tuple of upper and lower boundary index
        """
        cm_to_px_factor = esophagus_full_length_px / esophagus_full_length_cm
        # Convert user defined sphincter length to px
        sphincter_length_px = visualization_data.sphincter_length_cm * cm_to_px_factor

        start_iterator = lower_sphincter_center

        # Upper border index
        upper_border_index = 0
        current_length = 0
        # Count down from start_iterator to 0
        for i in range(start_iterator, -1, -1):
            if i < start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i + 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i + 1][
                                                                                                  1]) ** 2)
            if current_length >= sphincter_length_px / 2:
                upper_border_index = i
                break

        # Lower border index
        lower_border_index = max_index
        current_length = 0
        for i in range(start_iterator, len(sensor_path)):
            if i > start_iterator:
                current_length += np.sqrt((sensor_path[i][0] - sensor_path[i - 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                              sensor_path[i - 1][
                                                                                                  1]) ** 2)
            if current_length >= sphincter_length_px / 2:
                lower_border_index = i
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
        @param sensor_path: estimated path of the sensor catheter as list of coordinates
        @param max_index: maximum index value at the bottom (len(centers)-1))
        @param esophagus_full_length_cm: length in cm
        @param esophagus_full_length_px: length in pixels
        @return: tuple of two lists containing the metrics
        """
        # Find index of lower sphincter center
        lower_sphincter_center = FigureCreator.calculate_lower_sphincter_center(visualization_data, surfacecolor_list,
                                                                                sensor_path)
        # Find upper and lower boundary (index) for sphincter (index 0 = upper, index 1 = lower)
        lower_sphincter_boundary = FigureCreator.calculate_lower_sphincter_boundary(visualization_data,
                                                                                    lower_sphincter_center, sensor_path,
                                                                                    max_index, esophagus_full_length_cm,
                                                                                    esophagus_full_length_px)

        tubular_part_upper_boundary = FigureCreator.calculate_index_by_startindex_and_cm_position(
            lower_sphincter_boundary[0], config.length_tubular_part_cm, sensor_path, esophagus_full_length_px,
            esophagus_full_length_cm)
        if tubular_part_upper_boundary is None:
            tubular_part_upper_boundary = 0

        one_px_as_cm = esophagus_full_length_cm / esophagus_full_length_px

        # Calculate tubular metric between upper tubular boundary and upper lower sphincter boundary
        # Length according to frames in surfacecolor_list
        metric_tubular = np.zeros(len(surfacecolor_list))
        volume_sum_tubular = 0
        for i in range(tubular_part_upper_boundary, lower_sphincter_boundary[0]):
            shapely_poly = shapely.geometry.Polygon(tuple(zip(figure_x[i], figure_y[i])))
            # one_px_as_cm factor is needed, because of the third dimension height
            # (height of a single slice is one pixel)
            volume_slice = shapely_poly.area * one_px_as_cm
            volume_sum_tubular = volume_sum_tubular + volume_slice
            for j in range(len(surfacecolor_list)):
                # Calculate metric for frame and height
                metric_tubular[j] += volume_slice * surfacecolor_list[j][i]

        # Calculate sphincter metric between upper and lower sphincter boundary
        metric_sphincter = np.zeros(len(surfacecolor_list))
        volume_sum_sphincter = 0
        for i in range(lower_sphincter_boundary[0], lower_sphincter_boundary[1] + 1):
            shapely_poly = shapely.geometry.Polygon(tuple(zip(figure_x[i], figure_y[i])))
            # one_px_as_cm factor is needed, because of the third dimension height
            # (height of a single slice is one pixel)
            volume_slice = shapely_poly.area * one_px_as_cm
            volume_sum_sphincter = volume_sum_sphincter + volume_slice
            for j in range(len(surfacecolor_list)):
                # Calculate metric for frame and height
                if surfacecolor_list[j][i] != 0:
                    metric_sphincter[j] += volume_slice / surfacecolor_list[j][i]
                else:
                    metric_sphincter[j] += 0

        # Calculate max pressure over timeline for lower_sphincter_center
        # (lower_sphincter_center is the region with the max pressure in space)
        max_pressure_sphincter = 0
        for j in range(len(surfacecolor_list)):
            if surfacecolor_list[j][lower_sphincter_center] > max_pressure_sphincter:
                max_pressure_sphincter = surfacecolor_list[j][lower_sphincter_center]

        # Calculate max pressure over time and space for tubular part of esophagus
        max_pressure_tubular = 0
        for i in range(tubular_part_upper_boundary, lower_sphincter_boundary[0]):
            for j in range(len(surfacecolor_list)):
                if surfacecolor_list[j][i] > max_pressure_tubular:
                    max_pressure_tubular = surfacecolor_list[j][i]

        # Save metrics in local database
        # ToDO: Wie damit umgehen, dass die Daten jeweils nur einmal gespeichert werden sollen und nicht z.B. wenn die Rekonstruktion nochmals betrachtet wird erneut?
        # z.B. vorher Abfrage ob die Daten (visit_id und time) bereits in der Datenbank sind oder (visit_id und time) als primary_key?
        """
        with database.engine_local.connect() as conn:
            conn.execute(
                insert(data_models.metrics_table).
                values(visit_id=1,  # ToDO: bisher gibt es noch keine visit-id -> anpassen
                       time=1, #anpassen
                       metric_tubular_mean=np.mean(metric_tubular),
                       metric_sphincter_mean=np.mean(metric_sphincter),
                       metric_tubular_max=max(metric_tubular),
                       metric_sphincter_max=max(metric_sphincter),
                       metric_tubular_min=min(metric_tubular),
                       metric_sphincter_min=min(metric_sphincter),
                       pressure_tubular_max=max_pressure_tubular,
                       pressure_sphincter_max=max_pressure_sphincter,
                       volume_tubular=volume_sum_tubular,
                       volume_sphincter=volume_sum_sphincter,
                       esophagus_length_cm=esophagus_full_length_cm)
            )
            conn.commit()
        """
        

        return metric_tubular, metric_sphincter, volume_sum_tubular, volume_sum_sphincter, \
            max_pressure_tubular, max_pressure_sphincter, max(metric_tubular), max(metric_sphincter), min(
            metric_tubular), min(metric_sphincter), visualization_data.esophageal_pressurization_index

    @staticmethod
    def colored_vertical_endoflip_tables_and_colors(data):
        """
        creates colored vertical tables for the use of data from endoflip
        @param data: endoflip data
        @return: tables
        """
        tables = {}
        common_columns = natsorted(set(data['30']['aggregates'].keys()) & set(data['40']['aggregates'].keys()))
        # Reverse List because P16 is on top and P1 is at the bottom
        common_columns = common_columns[::-1]
        for agg in ['median', 'min', 'max', 'mean']:
            cell_texts_30 = []
            cell_texts_40 = []

            # rainbow to visualize high/low diameters
            colorscale = px.colors.sample_colorscale("jet", [(30 - (n + 1)) / (30 - 1) for n in range(30)])

            for column in common_columns:
                # Get aggregated values for each dataset
                agg_30 = data['30']['aggregates'][column][agg]
                agg_40 = data['40']['aggregates'][column][agg]

                cell_texts_30.append(f'{agg_30:.2f}')
                cell_texts_40.append(f'{agg_40:.2f}')

            color_30_40 = [np.array(colorscale)[[int(float(x)) for x in cell_texts_30]],
                           np.array(colorscale)[[int(float(x)) for x in cell_texts_40]]]

            # Create a table with colored cells and text annotations
            table = go.Table(
                header=dict(values=['<b>30ml</b>', '<b>40ml</b>'],
                            line_color='white',
                            fill_color='white',
                            font=dict(color='black', size=13)),
                cells=dict(values=[cell_texts_30,
                                   cell_texts_40],
                           fill_color=color_30_40,
                           line_color=color_30_40,
                           font=dict(color='white', size=11),
                           height=20),
                columnwidth=[1, 1],
            )

            figure = go.Figure(data=[table])
            figure.update_layout(width=150, margin=dict(l=10, r=10, t=60, b=10), title="Endoflip")
            tables[agg] = figure
        return tables

    @staticmethod
    def get_endoflip_surface_color(sensor_path, visualisation_data: VisualizationData, esophagus_full_length_cm,
                                   esophagus_full_length_px):
        """
        @param sensor_path: estimated path of the sensor catheter as list of coordinates
        @param visualisation_data: VisualizationData
        @param esophagus_full_length_cm: length of the esophagus in centimeters
        @param esophagus_full_length_px: length of the esophagus in pixels
        @return: surface_color_collect
        """

        distance_cm = visualisation_data.endoflip_screenshot['30']['distance']

        # Find index of endoflip_pos in sensor_path, matched y/x-axis order of endoflip_pos to sensor_path
        _, null_pos_index = spatial.KDTree(np.array(sensor_path)).query(np.array((visualisation_data.endoflip_pos[1],
                                                                                  visualisation_data.endoflip_pos[0])))

        # Get stop criterion (endoflip measurement length = number_of_sensors*distance_between_sensors)
        measurement_length_fraction = distance_cm * 16 / esophagus_full_length_cm
        measurement_length_px = esophagus_full_length_px * measurement_length_fraction

        # Color change criterion for each sensor
        sensor_length_fraction = distance_cm / esophagus_full_length_cm
        sensor_length_px = esophagus_full_length_px * sensor_length_fraction

        surface_color_collect = {}

        # Get ballon_volume 30 and 40
        for ballon_volume in visualisation_data.endoflip_screenshot:
            bv_color_collect = {}

            # Iterate over the aggregate rows of the pandas dataframe
            for agg, row_data in visualisation_data.endoflip_screenshot[ballon_volume]['aggregates'].iterrows():
                endoflip_colors = row_data

                # Iterate over sensor_path
                current_length = 0
                endoflip_surface_color = []
                color_index = 0

                # Iterate over sensor_path from bottom to top (P1 is at the bottom of the sphincter, P16 at the top)
                for i in range(len(sensor_path) - 1, -1, -1):
                    # Find endoflip section on esophagus
                    if i < null_pos_index and current_length < measurement_length_px and color_index + 1 < len(
                            endoflip_colors):
                        current_length += np.sqrt(
                            (sensor_path[i][0] - sensor_path[i + 1][0]) ** 2 + (sensor_path[i][1] -
                                                                                sensor_path[i + 1][
                                                                                    1]) ** 2)
                        # Append appropriate color for endoflip sensor
                        current_sensor = endoflip_colors[color_index]
                        next_sensor = endoflip_colors[color_index + 1]
                        # Smooth color transition
                        endoflip_value = current_sensor + (next_sensor - current_sensor) * (
                                (current_length - sensor_length_px * (color_index)) / (
                                sensor_length_px * (color_index + 1) -
                                sensor_length_px * (color_index)))
                        endoflip_surface_color.append(endoflip_value)

                        # Check if the next endoflip sensor has been reached 
                        if current_length >= sensor_length_px * (color_index + 1):
                            color_index += 1

                    elif current_length >= measurement_length_px or i >= null_pos_index or color_index + 1 >= len(
                            endoflip_colors):
                        # Out of the endoflip section, add high value to simulate None values
                        endoflip_surface_color.append(40)

                # Reverse colors because the color list was created in reverse
                bv_color_collect[agg] = endoflip_surface_color[::-1]
            # Append all colors per aggregation per current ballon_volume
            surface_color_collect[ballon_volume] = bv_color_collect

        return surface_color_collect
