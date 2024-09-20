from matplotlib.widgets import RectangleSelector

class CustomRectangleSelector(RectangleSelector):
    def __init__(self, ax, onselect, **kwargs):
        super().__init__(ax, onselect, **kwargs)
        self._allow_creation = False # otherwise the default rectangle is deleted when the user clicks/drags sth in the plot for the first time
        self.border_threshold = 5
    
    def contains(self, event):
        """Check if the event (mouse position) is on the borders of the rectangle."""
        if event.xdata is None or event.ydata is None:
            return False
        x0, x1, y0, y1 = self.extents
        border_threshold = self.border_threshold / self.ax.figure.dpi * 72  # Convert points to data units

        on_left_border = x0 - border_threshold <= event.xdata <= x0 + border_threshold
        on_right_border = x1 - border_threshold <= event.xdata <= x1 + border_threshold
        on_bottom_border = y0 - border_threshold <= event.ydata <= y0 + border_threshold
        on_top_border = y1 - border_threshold <= event.ydata <= y1 + border_threshold

        return (on_left_border or on_right_border) and y0 <= event.ydata <= y1 or \
               (on_bottom_border or on_top_border) and x0 <= event.xdata <= x1
    