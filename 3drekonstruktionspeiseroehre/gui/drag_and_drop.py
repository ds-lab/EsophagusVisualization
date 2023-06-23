from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel, QMainWindow, QVBoxLayout
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap

#https://www.pythonguis.com/faq/pyqt-drag-drop-widgets/

class DragItem(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.setContentsMargins(25, 5, 25, 5)
        #self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.setStyleSheet("border: 1px solid black;")


    def mouseMoveEvent(self, e):

        if e.buttons() == Qt.LeftButton:
            self.raise_()
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)



class DragWidget(QWidget):

    def __init__(self, *args, orientation=Qt.Orientation.Horizontal, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                if pos.x() > w.x():
                    # Check if pos.x() is greater than the current widget's x-coordinate.
                    # If so, move to the next widget.
                    continue
                drop_here = pos.x() < w.x() + w.size().width() // 2
                # print(pos.x(), w.x() + w.size().width() // 2,w.x(), w.size().width() )

            if drop_here:
                self.blayout.insertWidget(n-1, widget)
                break
            # TODO: move element to last position
            if n == self.blayout.count()-1:
                self.blayout.insertWidget(n, widget)

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def removeItem(self, item):
        self.blayout.removeWidget(item)
        item.setParent(None)
        
