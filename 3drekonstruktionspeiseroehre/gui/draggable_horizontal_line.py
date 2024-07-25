class DraggableHorizontalLine:
    def __init__(self, line, label, callback=None):
        self.line = line
        self.press = None
        self.label = label
        self.is_dragging = False  # Flag to indicate dragging state
        self.cidpress = line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.callback = callback
        self.text = self.line.axes.text(self.line.get_xdata()[-1], max(self.line.get_ydata()[0] - 10, 0), self.label, color=self.line.get_color(), ha='left')

    def on_press(self, event):
        if event.inaxes != self.line.axes: return
        contains, attr = self.line.contains(event)
        if not contains: return
        self.press = self.line.get_ydata(), event.ydata
        self.is_dragging = True  # Start dragging

    def on_motion(self, event):
        if self.press is None: return
        if event.inaxes != self.line.axes: return
        y0, ypress = self.press
        dy = event.ydata - ypress
        self.line.set_ydata(y0 + dy)
        self.line.figure.canvas.draw()
        if self.text:  # Remove the label if it exists
            self.text.remove()
        self.text = self.line.axes.text(self.line.get_xdata()[-1], max(self.line.get_ydata()[0] - 10, 0), self.label, color=self.line.get_color(), ha='left')
        if self.callback:  # Call the callback function if it exists
            self.callback()

    def on_release(self, event):
        self.press = None
        self.is_dragging = False  # Stop dragging
        self.line.figure.canvas.draw()
        # if self.text:  # Remove the label if it exists
        #     self.text.remove()
        # self.text = self.line.axes.text(self.line.get_xdata()[-1], max(self.line.get_ydata()[0] - 10, 0), self.label, color=self.line.get_color(), ha='left')
        if self.callback:  # Call the callback function if it exists
            self.callback()

    def disconnect(self):
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)

    def get_y_position(self):
        return self.line.get_ydata()[0]