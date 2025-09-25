from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QSizePolicy


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

    def _equalize_stretch(self):
        # Ensure each child in the layout gets the same stretch factor
        # so items split the available space equally (1/2, 1/3, ...).
        for i in range(self.blayout.count()):
            self.blayout.setStretch(i, 1)
            try:
                w = self.blayout.itemAt(i).widget()
                if w is not None:
                    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            except Exception:
                pass

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
                try:
                    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                except Exception:
                    pass

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
                try:
                    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                except Exception:
                    pass
                break

        # Accept the drop event.
        e.accept()
        # After any reordering, normalize stretches to keep equal widths
        self._equalize_stretch()

    def add_item(self, item):
        # Add a DragItem to the DragWidget's layout.
        try:
            item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        except Exception:
            pass
        self.blayout.addWidget(item)
        # Keep all items at equal stretch so space is distributed evenly
        self._equalize_stretch()

    def removeItem(self, item):
        # Remove a DragItem from the DragWidget's layout.
        self.blayout.removeWidget(item)
        item.setParent(None)
        # Rebalance remaining items
        self._equalize_stretch()
