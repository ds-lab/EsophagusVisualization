from matplotlib.widgets import RectangleSelector

class CustomRectangleSelector(RectangleSelector):
    def __init__(self, ax, onselect, **kwargs):
        super().__init__(ax, onselect, **kwargs)
        self._allow_creation = False # otherwise the default rectangle is deleted when the user clicks/drags sth in the plot for the first time
    