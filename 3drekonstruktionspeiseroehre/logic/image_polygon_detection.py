import cv2
import numpy as np


def calculate_endoscopy_polygon(image):
    """
    estimates the shape of the profile in the given image
    :param image: image
    :return: polygon
    """
    # remove alpha channel
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

    # remove black corners
    image = __remove_black_border_any_shape(image)

    # convert to gray
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # blur
    smooth = cv2.GaussianBlur(gray, (11, 11), 0)

    # find dark area
    _, thresh = cv2.threshold(smooth, 70, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy, = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    polygon = []
    if len(contours) > 0:
        contour = max(contours, key=cv2.contourArea)
        if len(contour) > 2:
            for point in contour:
              polygon.append((int(point[0][0]), int(point[0][1])))
            # reduce amount of points
            polygon = __reduce_polygon(polygon)
    return polygon


def calculate_xray_polygon(image):
    """
    estimates the shape of the esophagus in the given image
    :param image: image
    :return: polygon
    """
    # remove black border
    cropped_image, border_x, border_y, border_w, border_h = __remove_black_border_rectangle(image)

    # gray
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2GRAY)

    # blur
    smooth = cv2.GaussianBlur(gray_image, (11, 11), 0)

    # find dark area
    _, thresh = cv2.threshold(smooth, 150, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy, = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    polygon = []
    if len(contours) > 0:
        contour = max(contours, key=cv2.contourArea)
        if len(contour) > 2:
            for point in contour:
                polygon.append((border_x + int(point[0][0]), border_y + int(point[0][1])))
            # reduce amount of points
            polygon = __reduce_polygon(polygon)
    return polygon


def __remove_black_border_rectangle(image):
    """
    removes the black border around the image
    :param image: image
    :return: image without black border
    """
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray_image, 100, 255, cv2.THRESH_BINARY)
    border_x, border_y, border_w, border_h = cv2.boundingRect(thresh)
    cropped_image = image[border_y:border_y + border_h, border_x:border_x + border_w]
    return cropped_image, border_x, border_y, border_w, border_h


def __remove_black_border_any_shape(image):
    """
    paints black surroundings white
    :param image: image
    :return: new image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # mask
    mask = cv2.inRange(gray, 5, 255)
    # get contours
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # get biggest contour
    biggest = max(contours, key=cv2.contourArea)
    # make mask with biggest contour
    new_mask = np.zeros_like(mask)
    cv2.drawContours(new_mask, [biggest], -1, 255, -1)
    # redraw with white
    new_image = image.copy()
    new_image[new_mask == 0] = (255, 255, 255)
    return new_image


def __reduce_polygon(polygon, angle_threshold=5, distance_threshold=20):
    """
    reduces the amount of points for the given polygon
    :param polygon: polygon
    :param angle_threshold: remove point when angle is smaller than threshold
    :param distance_threshold: remove point when distance is smaller than threshold
    :return: new polygon
    """
    polygon = np.array(polygon)
    angle_threshold_rad = np.deg2rad(angle_threshold)
    points_to_remove = [0]
    while len(points_to_remove):
        points_to_remove = list()
        for i in range(0, len(polygon)-2, 2):
            v01 = polygon[i-1] - polygon[i]
            v12 = polygon[i] - polygon[i+1]
            d01 = np.linalg.norm(v01)
            d12 = np.linalg.norm(v12)
            # remove if distance smaller than threshold
            if d01 < distance_threshold and d12 < distance_threshold:
                points_to_remove.append(i)
                continue
            angle = np.arccos(np.clip(np.dot(v01, v12) / (d01 * d12), -1.0, 1.0))
            # remove if angle smaller than threshold
            if angle < angle_threshold_rad:
                points_to_remove.append(i)
        polygon = np.delete(polygon, points_to_remove, axis=0)
    return polygon.tolist()

