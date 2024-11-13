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
    def __init__(self, line, label, callback=None):
        self.line = line
        self.press = None
        self.label = label
        self.is_dragging = False  # Flag to indicate dragging state
        self.callback = callback
        self.manager = None

        # Create the label with a semi-transparent white background and smaller padding
        self.text = self.line.axes.text(
            self.line.get_xdata()[-1] + 20, 
            max(self.line.get_ydata()[0] - 15, 0), 
            self.label, 
            color=self.line.get_color(), 
            ha='left',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.1', alpha=0.5)
        )

        # Blitting setup
        self.background = None
        self.canvas = self.line.figure.canvas
        self.ax = self.line.axes

    def on_press(self, event):
        if event.inaxes != self.line.axes: return

        # Check if the click is on the line or the text
        contains_line, _ = self.line.contains(event)
        contains_text = self.text.contains(event)[0]

        if not contains_line and not contains_text: return

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

        # Update the text position
        new_ydata = self.line.get_ydata()
        self.text.set_y(max(new_ydata[0] - 15, 0))

        # Redraw the full figure
        self.canvas.draw()

        # Call the callback if provided
        if self.callback:
            self.callback()

    def on_hover(self, event):
        if event.inaxes != self.line.axes: return False

        # Check if the mouse is over the line or the text
        contains_line, _ = self.line.contains(event)
        contains_text = self.text.contains(event)[0]

        if contains_line or contains_text:
            # Change cursor to hand
            self.manager.canvas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            return True
        return False

    def get_y_position(self):
        return self.line.get_ydata()[0]

    def set_y_position(self, y):
        self.line.set_ydata([y, y])
        self.text.set_y(max(y - 15, 0))
        self.canvas.draw_idle()