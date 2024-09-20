class DraggableHorizontalLine:
    def __init__(self, line, label, callback=None):
        self.line = line
        self.press = None
        self.label = label
        self.is_dragging = False  # Flag to indicate dragging state
        self.callback = callback

        # Connect events
        self.cidpress = line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # Create the label
        self.text = self.line.axes.text(self.line.get_xdata()[-1], max(self.line.get_ydata()[0] - 10, 0), self.label, color=self.line.get_color(), ha='left')

        # Blitting setup
        self.background = None
        self.canvas = self.line.figure.canvas
        self.ax = self.line.axes

    def on_press(self, event):
        if event.inaxes != self.line.axes: return
        contains, attr = self.line.contains(event)
        if not contains: return
        self.press = self.line.get_ydata(), event.ydata
        self.is_dragging = True  # Start dragging

        # Cache the background
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def on_motion(self, event):
        if not self.is_dragging: return
        if event.inaxes != self.line.axes: return

        ydata, ypress = self.press
        dy = event.ydata - ypress
        new_ydata = ydata + dy

        # Update the line and label
        self.line.set_ydata(new_ydata)
        self.text.set_y(max(new_ydata[0] - 10, 0))

        # Restore the background
        self.canvas.restore_region(self.background)

        # Redraw only the line and label
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.text)

        # Blit the updated region
        self.canvas.blit(self.ax.bbox)
        # if self.callback:  # Call the callback function if it exists
        #     self.callback()

    def on_release(self, event):
        self.is_dragging = False  # Stop dragging
        self.press = None

        # Redraw the full figure
        self.canvas.draw()

        # Call the callback if provided
        if self.callback:
            self.callback()

    def disconnect(self):
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)

    def get_y_position(self):
        return self.line.get_ydata()[0]