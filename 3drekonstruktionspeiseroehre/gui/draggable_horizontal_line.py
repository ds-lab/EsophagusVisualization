from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

class DraggableLineManager:
    def __init__(self, canvas):
        self.lines = []
        self.selector = None
        self.canvas = canvas

    def add_line(self, draggable_line):
        self.lines.append(draggable_line)
        draggable_line.manager = self

    def set_selector(self, selector):
        self.selector = selector

    def on_hover(self, event):
        cursor_set = False
        for line in self.lines:
            if line.on_hover(event):
                cursor_set = True
        if self.selector and self.selector.contains(event):
            self.canvas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cursor_set = True
        if not cursor_set:
            self.canvas.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def on_press(self, event):
        for line in self.lines:
            line.on_press(event)

    def on_release(self, event):
        for line in self.lines:
            line.on_release(event)

    def on_motion(self, event):
        for line in self.lines:
            line.on_motion(event)

class DraggableHorizontalLine:
    def __init__(self, line, label, color, callback=None):
        self.line = line
        self.press = None
        self.label = label
        self.color = color  # Set the initial color for the line
        self.is_dragging = False  # Flag to indicate dragging state
        self.callback = callback
        self.manager = None

        # Set the color of the line
        self.line.set_color(self.color)

        # Blitting setup
        self.background = None
        self.canvas = self.line.figure.canvas
        self.ax = self.line.axes

    def on_press(self, event):
        if event.inaxes != self.line.axes: return

        # Check if the click is on the line
        contains_line, _ = self.line.contains(event)
        if not contains_line: return

        self.press = self.line.get_ydata(), event.ydata
        self.is_dragging = True  # Start dragging

        # Change cursor to grabbing hand
        self.manager.canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

        # Cache the background
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def on_motion(self, event):
        if not self.is_dragging: return
        if event.inaxes != self.line.axes: return

        ydata, ypress = self.press
        dy = event.ydata - ypress
        new_ydata = ydata + dy

        # Update the line position
        self.line.set_ydata(new_ydata)

        # Restore the background
        self.canvas.restore_region(self.background)

        self.manager.canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

        # Redraw only the line
        self.ax.draw_artist(self.line)

        # Blit the updated region
        self.canvas.blit(self.ax.bbox)

    def on_release(self, event):
        self.is_dragging = False  # Stop dragging
        self.press = None

        # Change cursor back to default
        self.manager.canvas.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # Redraw the full figure
        self.canvas.draw()

        # Call the callback if provided
        if self.callback:
            self.callback()

    def on_hover(self, event):
        if event.inaxes != self.line.axes: return False

        # Check if the mouse is over the line
        contains_line, _ = self.line.contains(event)
        if contains_line:
            # Change cursor to hand
            self.manager.canvas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            return True
        return False

    def get_y_position(self):
        return self.line.get_ydata()[0]

    def set_y_position(self, y):
        self.line.set_ydata([y, y])
        self.canvas.draw_idle()

    def set_line_color(self, color):
        """Allows updating the color of the line"""
        self.color = color
        self.line.set_color(self.color)
        self.canvas.draw_idle()
