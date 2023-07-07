from PyQt5.QtCore import QMimeData, Qt, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
                             QVBoxLayout, QWidget)

# Improved version of -> https://www.pythonguis.com/faq/pyqt-drag-drop-widgets/

class DragItem(QWidget):
    # Item/ Widget that is draggable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseMoveEvent(self, e):

        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            # Show item while dragging
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)



class DragWidget(QWidget):
    # Container/Widget that holds several DragItems and accepts drag and drop actions

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
        e.accept()

    def dropEvent(self, e):
        # Get Position and currently dragged DragItem
        pos = e.pos()
        widget = e.source()

        for n in range(self.blayout.count()):
            # Get the widget at each index
            w = self.blayout.itemAt(n).widget()

            if n == self.blayout.count()-1:
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
                self.blayout.insertWidget(n-1, widget)
                break

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def removeItem(self, item):
        self.blayout.removeWidget(item)
        item.setParent(None)
        
