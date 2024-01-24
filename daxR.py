import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QWidget 
from PyQt5.QtCore import Qt, QObject, pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
from PIL import Image
import time 
import numpy as np

# inf defaults(?)
bin1 = 1
bin2 = 1
dt = 16
endian = "little" 
rows = 2048
cols = 2048
numf = 100
x_s = 1 
x_e = 2048
y_s = 1 
y_e = 2048 
channels = 5

cframe = np.empty((rows, cols))
tfile = ""
currimg = 0
currchan = 0 
# dimg = display image
dimg = None

# false implies inf file DNE 
def checkInf(infp):
    if os.path.exists(infp):
        global bin1
        global bin2
        global dt
        global endian
        global rows
        global cols
        global numf
        global x_s 
        global x_e
        global y_s
        global y_e
        global channels
        
        with open(infp, 'r') as file: 
            file_in = file.read()

        for line in file_in.split('\n'):
            if '=' in line:
                key, value = map(str.strip, line.split('='))
            if key == 'binning':
                bin1, bi2 = map(int, value.split('x'))
            elif key == 'data type':
                dt = int(value.split()[0])
            elif key == 'frame dimensions':
                rows, cols = map(int, value.split('x'))
            elif key == 'number of frames':
                numf = int(value)
            elif key == 'x_start':
                x_s = int(value)
            elif key == 'x_end':
                x_e = int(value)
            elif key == 'y_start':
                y_s = int(value)
            elif key == 'y_end':
                y_e = int(value)
        return True
    else:
        return False

class implot(QWidget):
    def __init__(self, parent=None):
        super(implot, self).__init__(parent)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def plot(self):
        self.ax.clear()
        self.ax.imshow(dimg[currimg, currchan, :, :], cmap="gray")
        self.ax.set_title('placeholder')
        self.canvas.draw()

class DaxViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global channels
        self.setWindowTitle('DAX Viewer')
        self.setFixedSize(900,675)
        
        self.open_button = QPushButton('Open DAX file', self)
        self.open_button.clicked.connect(self.openImage)
        
        self.clabel = QLabel('Channel: ')
        self.cinput = QLineEdit()

        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.nextImage)
        
        self.linput = QLineEdit()

        self.prev_button = QPushButton('Previous', self)
        self.prev_button.clicked.connect(self.prevImage)         
        
        self.mplw = implot(self) 
        
        self.clabel.setFixedWidth(55)
        self.cinput.setFixedWidth(15)
        self.cinput.setText(str(currchan))
        self.cinput.setAlignment(Qt.AlignCenter)
        self.cinput.textChanged.connect(self.cinput_change)

        self.linput.setFixedWidth(25)
        self.linput.setText(str(currimg))
        self.linput.setAlignment(Qt.AlignCenter)
        self.linput.textChanged.connect(self.linput_change)
        
        self.mlabel = QLabel('')
        self.mlabel.setFixedHeight(25)
        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.clabel)
        button_layout.addWidget(self.cinput)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.linput)
        button_layout.addWidget(self.next_button)
        
        message_layout = QHBoxLayout()
        message_layout.addWidget(self.mlabel)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(message_layout)
        main_layout.addWidget(self.mplw)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    @pyqtSlot(str)
    def cinput_change(self, text):
        if text == '' or text == '-':
            return
        global currchan
        upc = int(text)
        if upc >= 0 and upc < channels:
            currchan = upc
            self.mplw.plot()
            self.mlabel.setText('')
        else: 
            self.mlabel.setText('invalid channel')

    @pyqtSlot(str)
    def linput_change(self, text):
        if text == '' or text == '-':
            return
        global currimg
        upl = int(text)
        if upl >= 0 and upl < (numf//channels):
            currimg = upl
            self.mplw.plot()
            self.mlabel.setText('')
        else:
            self.mlabel.setText('invalid layer')

    def openImage(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open DAX file", "", "DAX Files (*.dax);;All Files (*)", options=options)

        if file_path:
            global tfile
            global dimg 
            tfile = os.path.splitext(os.path.basename(file_path))[0]

            check = checkInf(os.path.splitext(file_path)[0]+".inf")
            if check == False:
                print("CAUTION: using defaults")
            else: 
                print("using associated inf file")
            
            dimg = np.reshape(np.fromfile(file_path, dtype=np.uint16), [numf//channels, channels, rows, cols])
            self.mplw.plot()

    def nextImage(self):
        global currimg
        global tfile

        if currimg + 1 > ((numf//channels)-1):
            return

        currimg += 1
        self.linput.setText(str(currimg))
        self.mplw.plot()        

    def prevImage(self):
        global currimg 
        global tfile
        
        if currimg - 1 < 0:
            return

        currimg -= 1
        self.linput.setText(str(currimg))
        self.mplw.plot()

def main():
    app = QApplication(sys.argv)
    viewer = DaxViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
