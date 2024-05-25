from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget


# Based on -> https://www.pythonguis.com/faq/pyqt-drag-drop-widgets/

# A draggable item/widget.
class DragItem(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            # Create a drag object and set its mime data.
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            # Show item while dragging
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            # Execute the drag-and-drop operation as a move action.
            drag.exec(Qt.DropAction.MoveAction)


# A container/widget that holds several DragItems and accepts drag-and-drop actions.
class DragWidget(QWidget):
    def __init__(self, *args, orientation=Qt.Orientation.Horizontal, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the layout orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        # Accept the drag event.
        e.accept()

    def dropEvent(self, e):
        # Get Position and currently dragged DragItem.
        pos = e.position()
        widget = e.source()

        for n in range(self.blayout.count()):
            # Get the widget at each index
            w = self.blayout.itemAt(n).widget()

            if n == self.blayout.count() - 1:
                # DragItem (widget) is being dragged beyond the last element of DragWidget -> Drop item to the very right or bottom
                self.blayout.insertWidget(n, widget)

            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                if pos.y() > w.y():
                    # Check if pos.y() is greater than the current widget's y-coordinate.
                    # If so, move to the next widget.
                    continue

                # Drop position found
                drop_here = pos.y() < w.y() + w.size().height() // 2

            else:
                # Drag drop horizontally.
                if pos.x() > w.x():
                    # Check if pos.x() is greater than the current widget's x-coordinate.
                    # If so, move to the next widget.
                    continue

                # Drop position found
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                # Drop item left of the current widget
                self.blayout.insertWidget(n - 1, widget)
                break

        # Accept the drop event.
        e.accept()

    def add_item(self, item):
        # Add a DragItem to the DragWidget's layout.
        self.blayout.addWidget(item)

    def removeItem(self, item):
        # Remove a DragItem from the DragWidget's layout.
        self.blayout.removeWidget(item)
        item.setParent(None)
