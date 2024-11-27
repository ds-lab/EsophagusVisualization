import sys
# Config file

# data validation for database:
min_value_year = 1900
missing_int = -1
missing_dropdown = "---"
missing_text = ""
mandatory_values_patient = ["patient_id", "birth_year", "center"]
mandatory_values_prev_therapy = ["therapy"]
mandatory_values_visit = ["year_of_visit", "visit_type"]
mandatory_values_medication = ["medication_use"]

# Text in Dash-Server / Data-Visualization:
animation_start = "Start animation"
animation_stop = "Stop animation"
select_aggregation_form = "Select aggregation form"
label_median = "Median"
label_mean = "Mean"
label_minimum = "Minimum"
label_maximum = "Maximum"
label_hide = "Hide"
label_barium_swallow = "Barium Swallow"
label_manometry_data = "Manometry Data"
label_endoflip_data = "Endoflip Data"
label_time_0 = " Time: 0.00s"
# The string for the metrics display is composed from several parts
# Display will be, f. e. Metrics: tubular part (15.00 cm) [Volume*Pressure]: 3.14; lower sphincter (2.00 cm) [Volume/Pressure]: 3.14
metrics_text_part1 = "Metrics: tubular part ("
metrics_text_part2 = "cm) [Volume*Pressure]: "
metrics_text_part3 = "; lower sphincter ("
metrics_text_part4 = "cm) [Volume/Pressure]: "
# These are the strings for the composition of the metrics for the animation
metrics_animation_part1 = "Time: "
metrics_animation_part2 = "s"
metrics_animation_part3 = "Metrics: tubular part ("
metrics_animation_part4 = "cm) [Volume*Pressure]: "
metrics_animation_part5 = "; lower sphincter ("
metrics_animation_part6 = "cm) [Volume/Pressure]: "

# Text in figure_creator.py for data visualization:
label_length = "Length"
label_width = "Width"
label_depth = "Depth"

# Title of plots
title_with_endoscopy = "3D view from X-ray, endoscopy, and manometry data"
title_without_endoscopy = "3D view from X-ray and manometry data"


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

# manometry sensor: sensor positions in cm for catheter CE4-0062 (from top to bottom) P22 - 0cm und P1 - 40cm
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
diagonal_cost = 3  # costs for shortest path calculation
distance_to_border = 10 # number of pixels the sensor path is away form the border
# The esophagus is artifically expanded to create a straight line at the top.
# This defines the number of pixels the esophagus is expanded BEYOND just building a straight line.
# Necessary for better shortest paths / centers at the top of the esophagus
expansion_delta = 5


# CHECKERS

volumen_upper_boundary = 1
volumen_lower_boundary = 2 # sys.maxint
max_eso_length = 40
min_eso_length = 10