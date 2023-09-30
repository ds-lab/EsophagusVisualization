# Config file

# dash server:
dash_port_range = (50000, 50100)  # the dash server tries to use a port inside this range

# visualization: (these values can be lowered to run the animation on slower hardware)
figure_number_of_angles = 100  # number of angles used to calculate the profile of the figure
animation_frames_per_second = 5  # (should be a divisor of csv_values_per_second)

# metrics:
length_tubular_part_cm = 15  # regarded length of the tubular part above the lower sphincter

# colorscale (as in 'Laborie'-software)
colorscale = [[0, "rgb(16, 1, 255)"],
              [0.123552143573761, "rgb(5, 252, 252)"],
              [0.274131298065186, "rgb(19, 254, 3)"],
              [0.5, "rgb(252, 237, 3)"],
              [0.702702701091766, "rgb(255, 0, 0)"],
              [1, "rgb(91, 5, 132)"]]
cmin = -15  # min pressure -> 0 in colorscale
cmax = 200  # max pressure -> 1 in colorscale

# manometry sensor: sensor positions in cm for catheter CE4-0062 (from top to bottom)
coords_sensors = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 24, 26, 28, 30, 31, 32, 33, 34, 35, 40]

# csv import
csv_skiprows = 6  # top rows in the csv file which are not needed
csv_drop_columns = [' Resp1', ' Resp2', ' Resp3', ' Swallow1', ' Swallow2', ' Swallow3', ' Marker']
csv_values_per_second = 20  # how many values belong to one second

# window size
window_start_size_width = 600
window_start_size_height = 350

# figure creation
# (these values may be modified in later version of the program)
num_points_for_polyfit_smooth = 80  # points for polyfit in parts of the sensor-paths where there is no sharp edge
num_points_for_polyfit_sharp = 40  # points for polyfit in parts of the sensor-paths where there IS a sharp edge
point_distance_in_polyfit = 10  # distance of the points on the sensor-paths that are used for the polyfit
points_for_smoothing_in_sharp_edges = 20  # number of points after a detected sharp edge for which num_points_for_polyfit_sharp is used
px_threshold_for_straight_line = 10  # pixel threshold for detecting the upper most horizontal line in shorted paths calculation
cardinal_cost = 2  # costs for shortest path calculation
diagnonal_cost = 3  # costs for shortest path calculation