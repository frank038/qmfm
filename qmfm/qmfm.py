#!/usr/bin/env python3
# version alpha 12

from PyQt5.QtCore import (QEvent,QObject,QUrl,QFileInfo,QRect,QStorageInfo,QMimeData,QMimeDatabase,QFile,QThread,Qt,pyqtSignal,QSize,QMargins,QDir,QByteArray,QItemSelection,QItemSelectionModel,QPoint)
from PyQt5.QtWidgets import (qApp,QBoxLayout,QLabel,QPushButton,QDesktopWidget,QApplication,QDialog,QGridLayout,QMessageBox,QLineEdit,QTabWidget,QWidget,QGroupBox,QComboBox,QCheckBox,QProgressBar,QListView,QFileSystemModel,QItemDelegate,QStyle,QFileIconProvider,QAbstractItemView,QFormLayout,QAction,QMenu)
from PyQt5.QtGui import (QDrag,QPixmap,QStaticText,QTextOption,QIcon,QStandardItem,QStandardItemModel,QFontMetrics,QColor,QPalette,QClipboard,QPainter,QFont)

import sys
from pathlib import PosixPath
import os
import stat
from urllib.parse import unquote, quote
import shutil
import time
import datetime
import glob
import importlib
import subprocess
import pwd
import threading
from xdg.BaseDirectory import *
from xdg.DesktopEntry import *
from cfg import *

# 
LARGETHUMS = 0
if THUMB_SIZE > ICON_SIZE:
    LARGETHUMS = 1

#
if ICON_SIZE > ITEM_WIDTH:
    ITEM_WIDTH = ICON_SIZE

## set the font used in the application
thefont = QFont()
thefont.setPointSize(FONT_SIZE)

# max number of items - 1 to show in the message dialog
ITEMSDELETED = 30

# with of the dialog windows
dialWidth = 600

# where to look for desktop files or default locations
if xdg_data_dirs:
    xdgDataDirs = xdg_data_dirs
else:
    xdgDataDirs = ['/usr/local/share', '/usr/share', os.path.expanduser('~')+"/local/share"]
# consinstency
if "/usr/share" not in xdgDataDirs:
    xdgDataDirs.append("/usr/share")
if os.path.expanduser('~')+"/.local/share" not in xdgDataDirs:
    xdgDataDirs.append(os.path.expanduser('~')+"/.local/share")


class firstMessage(QWidget):
    
    def __init__(self, *args):
        super().__init__()
        title = args[0]
        message = args[1]
        self.setWindowTitle(title)

        box = QBoxLayout(QBoxLayout.TopToBottom)
        box.setContentsMargins(5,5,5,5)
        self.setLayout(box)
        label = QLabel(message)
        box.addWidget(label)
        button = QPushButton("Close")
        box.addWidget(button)
        button.clicked.connect(self.close)
        
        self.show()

        self.center()

    def center(self):
        
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if not os.path.exists("winsize.cfg"):
    try:
        with open("winsize.cfg", "w") as ifile:
            ifile.write("1200;900;False")
    except:
        app = QApplication(sys.argv)
        fm = firstMessage("Error", "The file winsize.cfg cannot be created.")
        sys.exit(app.exec_())

if not os.access("winsize.cfg", os.R_OK):
    app = QApplication(sys.argv)
    fm = firstMessage("Error", "The file winsize.cfg cannot be read.")
    sys.exit(app.exec_())

WINW = 0
WINH = 0
WINM = ""
try:
    with open("winsize.cfg", "r") as ifile:
        fcontent = ifile.readline()
    aw, ah, am = fcontent.split(";")
    WINW = aw
    WINH = ah
    WINM = am
except:
    app = QApplication(sys.argv)
    fm = firstMessage("Error", "The file winsize.cfg cannot be read.")
    sys.exit(app.exec_())

isXDGDATAHOME = 1

if USE_THUMB == 1:
    try:
        from pythumb import *
    except Exception as E:
        USE_THUMB = 0

# media module
if USE_MEDIA:
    try:
        import media_module
    except Exception as E:
        app = QApplication(sys.argv)
        fm = firstMessage("Error", "Error while importing the module:\n{}".format(str(E)))
        sys.exit(app.exec_())

# trash module
if USE_TRASH:
    try:
        import trash_module
    except Exception as E:
        app = QApplication(sys.argv)
        fm = firstMessage("Error", "Error while importing the module:\n{}".format(str(E)))
        sys.exit(app.exec_())

if not os.path.exists("modules_custom"):
    try:
        os.mkdir("modules_custom")
    except:
        print("Cannot create the modules_custom folder. Exiting...")
        sys.exit()

sys.path.append("modules_custom")
mmod_custom = glob.glob("modules_custom/*.py")
list_custom_modules = []
for el in reversed(mmod_custom):
    try:
        ee = importlib.import_module(os.path.basename(el)[:-3])
        list_custom_modules.append(ee)
    except ImportError as ioe:
        app = QApplication(sys.argv)
        fm = firstMessage("Error", "Error while importing the plugin:\n{}".format(str(ioe)))
        sys.exit(app.exec_())

if not os.path.exists("icons"):
    print("The folder icons doesn't exist. Exiting...")
    sys.exit()

MMTAB = object
TCOMPUTER = 0

class clabel2(QLabel):
    
    def __init__(self, parent=None):
        super(clabel2, self).__init__(parent)
    
    def setText(self, text, wWidth):
        
        boxWidth = wWidth*QApplication.instance().devicePixelRatio()
        font = self.font()
        metric = QFontMetrics(font)
        string = text
        ctemp = ""
        ctempT = ""
        for cchar in string:
            ctemp += str(cchar)
            width = metric.width(ctemp)
            if width < boxWidth:
                ctempT += str(cchar)
                continue
            else:
                ctempT += str(cchar)
                ctempT += "\n"
                ctemp = str(cchar)
        
        ntext = ctempT
        
        super(clabel2, self).setText(ntext)

# simply info dialog
class MyDialog(QDialog):
    def __init__(self, *args, parent=None):
        super(MyDialog, self).__init__(parent)
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle(args[0])
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,300)
        self.setFont(thefont)
        
        grid = QGridLayout()
        grid.setContentsMargins(5,5,5,5)
        #
        label = clabel2()
        label.setText(args[1], self.size().width()-12)
        label.setWordWrap(True)
        #
        button_ok = QPushButton("     Ok     ")
        grid.addWidget(label, 0, 1, 1, 3, Qt.AlignCenter)
        grid.addWidget(button_ok, 1, 1, 1, 3, Qt.AlignHCenter)
        self.setLayout(grid)
        button_ok.clicked.connect(self.close)
        self.exec_()

# dialog message with info list
class MyMessageBox(QMessageBox):
    def __init__(self, *args, parent=None):
        super(MyMessageBox, self).__init__(parent)
        self.setIcon(QMessageBox.Information)
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle(args[0])
        self.setText(args[1])
        self.setInformativeText(args[2])
        self.setDetailedText("The details are as follows:\n\n"+args[3])
        self.setStandardButtons(QMessageBox.Ok)
        self.setFont(thefont)
        
        retval = self.exec_()

# renaming dialog - with drag-n-drop
class MyDialogRename(QDialog):
    def __init__(self, *args, parent=None):
        super(MyDialogRename, self).__init__(parent)
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Rename")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,300)
        self.setFont(thefont)
        
        mbox = QBoxLayout(QBoxLayout.TopToBottom)
        mbox.setContentsMargins(5,5,5,5)
        self.setLayout(mbox)
        
        label1 = QLabel("Old name:")
        mbox.addWidget(label1)
        
        label2 = clabel2()
        label2.setText(args[0], self.size().width()-12)
        mbox.addWidget(label2)
        
        label3 = QLabel("New name:")
        mbox.addWidget(label3)
        
        self.lineedit = QLineEdit()
        self.lineedit.setText(args[0])
        self.lineedit.setCursorPosition(0)
        args_basename = QFileInfo(args[0]).baseName()
        len_args_basename = len(args_basename)
        self.lineedit.setSelection(0 , len_args_basename)
        mbox.addWidget(self.lineedit)
        
        box = QBoxLayout(QBoxLayout.LeftToRight)
        mbox.addLayout(box)
        
        button1 = QPushButton("OK")
        box.addWidget(button1)
        button1.clicked.connect(lambda:self.faccept(args[0]))
        
        button2 = QPushButton("Skip")
        box.addWidget(button2)
        button2.clicked.connect(self.fskip)
        
        button3 = QPushButton("Cancel")
        box.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        
        self.Value = ""
        self.exec_()
        
    def getValues(self):
        return self.Value
    
    def faccept(self, item_name):
        if self.lineedit.text() != "":
            if self.lineedit.text() != item_name:
                self.Value = self.lineedit.text()
                self.close()
    
    def fskip(self):
        self.Value = -2
        self.close() 
    
    def fcancel(self):
        self.Value = -1
        self.close()

# renaming dialog - from listview contextual menu
class MyDialogRename2(QDialog):
    def __init__(self, *args, parent=None):
        super(MyDialogRename2, self).__init__(parent)
        self.item_name = args[0]
        self.dest_path = args[1]
        self.itemPath = os.path.join(self.dest_path, self.item_name)
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Rename")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,300)
        
        mbox = QBoxLayout(QBoxLayout.TopToBottom)
        mbox.setContentsMargins(5,5,5,5)
        self.setLayout(mbox)
        
        label1 = QLabel("Old name:")
        mbox.addWidget(label1)
        
        label2 = clabel2()
        label2.setText(self.item_name, self.size().width()-12)
        mbox.addWidget(label2)
        
        label3 = QLabel("New name:")
        mbox.addWidget(label3)
        
        self.lineedit = QLineEdit()
        self.lineedit.setText(self.item_name)
        self.lineedit.setCursorPosition(0)
        args_basename = QFileInfo(self.item_name).baseName()
        len_args_basename = len(args_basename)
        self.lineedit.setSelection(0 , len_args_basename)
        mbox.addWidget(self.lineedit)
        
        box = QBoxLayout(QBoxLayout.LeftToRight)
        mbox.addLayout(box)
        
        button1 = QPushButton("OK")
        box.addWidget(button1)
        button1.clicked.connect(lambda:self.faccept(self.item_name))
        
        button3 = QPushButton("Cancel")
        box.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        
        self.Value = ""
        self.exec_()
    
    def getValues(self):
        return self.Value
    
    def faccept(self, item_name):
        newName = self.lineedit.text()
        if newName != "":
            if newName != item_name:
                if not os.path.exists(os.path.join(self.dest_path, newName)):
                    self.Value = self.lineedit.text()
                    self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()

# renaming dialog - Paste and Merge
class MyDialogRename22(QDialog):
    def __init__(self, *args, parent=None):
        super(MyDialogRename22, self).__init__(parent)
        self.item_name = args[0]
        self.dest_path = args[1]
        self.itemPath = os.path.join(self.dest_path, self.item_name)
        self.setFont(thefont)
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Rename")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,300)
        
        mbox = QBoxLayout(QBoxLayout.TopToBottom)
        mbox.setContentsMargins(5,5,5,5)
        self.setLayout(mbox)
        
        label1 = QLabel("Old name:")
        mbox.addWidget(label1)
        
        label2 = clabel2()
        label2.setText(self.item_name, self.size().width()-12)
        mbox.addWidget(label2)
        
        label3 = QLabel("New name:")
        mbox.addWidget(label3)
        
        self.lineedit = QLineEdit()
        self.lineedit.setText(self.item_name)
        self.lineedit.setCursorPosition(0)
        args_basename = QFileInfo(self.item_name).baseName()
        len_args_basename = len(args_basename)
        self.lineedit.setSelection(0 , len_args_basename)
        mbox.addWidget(self.lineedit)
        
        box = QBoxLayout(QBoxLayout.LeftToRight)
        mbox.addLayout(box)
        
        button1 = QPushButton("OK")
        box.addWidget(button1)
        button1.clicked.connect(lambda:self.faccept(self.item_name))
        
        button3 = QPushButton("Cancel")
        box.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        
        self.Value = ""
        self.exec_()
    
    def getValues(self):
        return self.Value
    
    def faccept(self, item_name):
        newName = self.lineedit.text()
        if newName != "":
            # it doesnt exists or it is a broken link
            if os.path.exists(os.path.join(self.dest_path, newName)) or os.path.islink(os.path.join(self.dest_path, newName)):
                return
            else:
                self.Value = self.lineedit.text()
                self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()

# renaming dialog - when a new file is been created
class MyDialogRename3(QDialog):
    def __init__(self, *args, parent=None):
        super(MyDialogRename3, self).__init__(parent)
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Set a new name")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,300)
        self.setFont(thefont)
        
        mbox = QBoxLayout(QBoxLayout.TopToBottom)
        mbox.setContentsMargins(5,5,5,5)
        self.setLayout(mbox)
        
        label1 = QLabel("Choose a new name:")
        mbox.addWidget(label1)
        
        self.lineedit = QLineEdit()
        self.lineedit.setText(args[0])
        self.lineedit.setCursorPosition(0)
        args_basename = QFileInfo(args[0]).baseName()
        len_args_basename = len(args_basename)
        self.lineedit.setSelection(0 , len_args_basename)
        mbox.addWidget(self.lineedit)
        
        box = QBoxLayout(QBoxLayout.LeftToRight)
        mbox.addLayout(box)
        
        button1 = QPushButton("OK")
        box.addWidget(button1)
        button1.clicked.connect(lambda:self.faccept(args[0], args[1]))
        
        button3 = QPushButton("Cancel")
        box.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        
        self.Value = ""
        self.exec_()

    def getValues(self):
        return self.Value
    
    def faccept(self, item_name, destDir):
        if self.lineedit.text() != "":
            if not os.path.exists(os.path.join(destDir, self.lineedit.text())):
                self.Value = self.lineedit.text()
                self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()

# dialog - open a file with another program
class otherApp(QDialog):

    def __init__(self, itemPath, parent=None):
        super(otherApp, self).__init__(parent)
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Other application")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth,100)
        self.setFont(thefont)
        
        grid = QGridLayout()
        grid.setContentsMargins(5,5,5,5)
        #
        label1 = QLabel("\nChoose the application:")
        grid.addWidget(label1, 0, 0, Qt.AlignCenter)
        #
        self.lineedit = QLineEdit()
        grid.addWidget(self.lineedit, 1, 0)
        #
        button_box = QBoxLayout(QBoxLayout.LeftToRight)
        grid.addLayout(button_box, 2, 0)
        #
        button1 = QPushButton("OK")
        button_box.addWidget(button1)
        button1.clicked.connect(self.faccept)
        #
        button3 = QPushButton("Cancel")
        button_box.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        #
        self.setLayout(grid)
        self.Value = -1
        self.exec_()
        
    def getValues(self):
        return self.Value
    
    def faccept(self):
        if self.lineedit.text() != "":
            self.Value = self.lineedit.text()
            self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()

# property dialog for one item
class propertyDialog(QDialog):
    def __init__(self, itemPath, parent=None):
        super(propertyDialog, self).__init__(parent)
        self.itemPath = itemPath
        #
        storageInfo = QStorageInfo(self.itemPath)
        storageInfoIsReadOnly = storageInfo.isReadOnly()
        #
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Property")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(600, 300)
        self.setFont(thefont)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        #
        self.gtab = QTabWidget()
        self.gtab.setContentsMargins(5,5,5,5)
        self.gtab.setMovable(False)
        self.gtab.setElideMode(Qt.ElideRight)
        self.gtab.setTabsClosable(False)
        vbox.addWidget(self.gtab)
        #
        page1 = QWidget()
        self.gtab.addTab(page1, "General")
        grid1 = QGridLayout()
        grid1.setContentsMargins(5,5,5,5)
        page1.setLayout(grid1)
        #
        labelName = QLabel("Name")
        grid1.addWidget(labelName, 0, 0, 1, 1, Qt.AlignRight)
        self.labelName2 = QLabel()
        self.labelName2.setWordWrap(True)
        grid1.addWidget(self.labelName2, 0, 1, 1, 1, Qt.AlignRight)
        #
        labelMime = QLabel("MimeType")
        grid1.addWidget(labelMime, 2, 0, 1, 1, Qt.AlignRight)
        self.labelMime2 = QLabel()
        grid1.addWidget(self.labelMime2, 2, 1, 1, 4, Qt.AlignLeft)
        #
        labelSize = QLabel("Size")
        grid1.addWidget(labelSize, 4, 0, 1, 1, Qt.AlignRight)
        self.labelSize2 = clabel2()
        grid1.addWidget(self.labelSize2, 4, 1, 1, 4, Qt.AlignLeft)
        #
        labelCreation = QLabel("Creation")
        grid1.addWidget(labelCreation, 5, 0, 1, 1, Qt.AlignRight)
        self.labelCreation2 = QLabel()
        grid1.addWidget(self.labelCreation2, 5, 1, 1, 4, Qt.AlignLeft)
        #
        labelModification = QLabel("Modification")
        grid1.addWidget(labelModification, 6, 0, 1, 1, Qt.AlignRight)
        self.labelModification2 = QLabel()
        grid1.addWidget(self.labelModification2, 6, 1, 1, 4, Qt.AlignLeft)
        #
        labelAccess = QLabel("Access")
        grid1.addWidget(labelAccess, 7, 0, 1, 1, Qt.AlignRight)
        self.labelAccess2 = QLabel()
        grid1.addWidget(self.labelAccess2, 7, 1, 1, 4, Qt.AlignLeft)
        #
        page2 = QWidget()
        self.gtab.addTab(page2, "Permissions")
        vboxp2 = QBoxLayout(QBoxLayout.TopToBottom)
        page2.setLayout(vboxp2)
        #
        gBox1 = QGroupBox("Ownership")
        vboxp2.addWidget(gBox1)
        grid2 = QGridLayout()
        grid2.setContentsMargins(5,5,5,5)
        gBox1.setLayout(grid2)
        #
        labelgb11 = QLabel("Owner")
        grid2.addWidget(labelgb11, 0, 0, 1, 1, Qt.AlignRight)
        self.labelgb12 = QLabel()
        grid2.addWidget(self.labelgb12, 0, 1, 1, 5, Qt.AlignLeft)
        #
        labelgb21 = QLabel("Group")
        grid2.addWidget(labelgb21, 1, 0, 1, 1, Qt.AlignRight)
        self.labelgb22 = QLabel()
        grid2.addWidget(self.labelgb22, 1, 1, 1, 5, Qt.AlignLeft)
        #
        gBox2 = QGroupBox("Permissions")
        vboxp2.addWidget(gBox2)
        grid3 = QGridLayout()
        grid3.setContentsMargins(5,5,5,5)
        gBox2.setLayout(grid3)
        if storageInfoIsReadOnly:
            gBox2.setEnabled(False)
        #
        labelOwnerPerm = QLabel("Owner")
        grid3.addWidget(labelOwnerPerm, 0, 0, 1, 1, Qt.AlignRight)
        self.combo1 = QComboBox()
        self.combo1.addItems(["Read and Write", "Read", "Forbidden"])
        grid3.addWidget(self.combo1, 0, 1, 1, 5, Qt.AlignLeft)
        #
        labelGroupPerm = QLabel("Group")
        grid3.addWidget(labelGroupPerm, 1, 0, 1, 1, Qt.AlignRight)
        self.combo2 = QComboBox()
        self.combo2.addItems(["Read and Write", "Read", "Forbidden"])
        grid3.addWidget(self.combo2, 1, 1, 1, 5, Qt.AlignLeft)
        #
        labelOtherPerm = QLabel("Others")
        grid3.addWidget(labelOtherPerm, 2, 0, 1, 1, Qt.AlignRight)
        self.combo3 = QComboBox()
        self.combo3.addItems(["Read and Write", "Read", "Forbidden"])
        grid3.addWidget(self.combo3, 2, 1, 1, 5, Qt.AlignLeft)
        
        if os.path.isdir(self.itemPath):
            self.cb1 = QCheckBox('folder access')
        else:
            self.cb1 = QCheckBox('is executable')

        grid3.addWidget(self.cb1, 4, 0, 1, 5, Qt.AlignLeft)

        button1 = QPushButton("OK")
        button1.clicked.connect(self.faccept)

        hbox = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox)
        hbox.addWidget(button1)

        self.tab()

        self.exec_()
    
    def tab(self):

        fileInfo = QFileInfo(self.itemPath)
        self.labelName2.setText(fileInfo.fileName())
        imime = QMimeDatabase().mimeTypeForFile(self.itemPath, QMimeDatabase.MatchDefault)
        self.labelMime2.setText(imime.name())
        
        if not os.path.exists(self.itemPath):
            if os.path.islink(self.itemPath):
                self.labelSize2.setText.setText("(Broken Link)", self.size().width()-50)
            else:
                self.labelSize2.setText("Unrecognizable", self.size().width()-50)
        if os.path.isfile(self.itemPath):
            if os.access(self.itemPath, os.R_OK):
                self.labelSize2.setText(self.convert_size(QFileInfo(self.itemPath).size()), self.size().width()-50)
            else:
                self.labelSize2.setText("(Not readable)", self.size().width()-50)
        elif os.path.isdir(self.itemPath):
            if os.access(self.itemPath, os.R_OK):
                self.labelSize2.setText(str(self.convert_size(self.folder_size(self.itemPath))), self.size().width()-50)
            else:
                self.labelSize2.setText("(Not readable)")
   
        #
        mctime = datetime.datetime.fromtimestamp(os.stat(self.itemPath).st_ctime).strftime('%c')
        #
        mmtime = datetime.datetime.fromtimestamp(os.stat(self.itemPath).st_mtime).strftime('%c')
        #
        matime = datetime.datetime.fromtimestamp(os.stat(self.itemPath).st_atime).strftime('%c')
        #
        self.labelCreation2.setText(str(mctime))
        self.labelModification2.setText(str(mmtime))
        self.labelAccess2.setText(str(matime))
        #
        self.labelgb12.setText(fileInfo.owner())
        self.labelgb22.setText(fileInfo.group())
        #
        perms = fileInfo.permissions()
        #
        if perms & QFile.ExeOwner:
            self.cb1.setCheckState(Qt.Checked)
        self.cb1.stateChanged.connect(self.fcb1)

        nperm = self.fgetPermissions()
        
        if nperm[0] + nperm[1] + nperm[2] in [6, 7]:
            self.combo1.setCurrentIndex(0)
        elif nperm[0] + nperm[1] + nperm[2] in [4, 5]:
            self.combo1.setCurrentIndex(1)
        else:
            self.combo1.setCurrentIndex(2)
        #
        if nperm[3] + nperm[4] + nperm[5] in [6, 7]:
            self.combo2.setCurrentIndex(0)
        elif nperm[3] + nperm[4] + nperm[5] in [4, 5]:
            self.combo2.setCurrentIndex(1)
        else:
            self.combo2.setCurrentIndex(2)
        #
        if nperm[6] + nperm[7] + nperm[8] in [6, 7]:
            self.combo3.setCurrentIndex(0)
        elif nperm[6] + nperm[7] + nperm[8] in [4, 5]:
            self.combo3.setCurrentIndex(1)
        else:
            self.combo3.setCurrentIndex(2)
        self.combo1.currentIndexChanged.connect(self.fcombo1)
        self.combo2.currentIndexChanged.connect(self.fcombo2)
        self.combo3.currentIndexChanged.connect(self.fcombo3)
    
    def convert_size(self, fsize2):
        
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize    

    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if os.path.islink(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size
    
    def tperms(self, perms):
        tperm = ""
        tperm = str(perms[0] + perms[1] + perms[2])+str(perms[3] + perms[4] + perms[5])+str(perms[6] + perms[7] + perms[8])
        return tperm
    
    def fcb1(self, state):
        perms = self.fgetPermissions()
        #
        if state == 2:
            perms[2] = 1
            perms[5] = 1
            perms[8] = 1
            tperm =self.tperms(perms)
            try:
                os.chmod(self.itemPath, int("{}".format(int(tperm)), 8))
            except Exception as E:
                MyDialog("Error", str(E))
        else:
            perms[2] = 0
            perms[5] = 0
            perms[8] = 0
            tperm =self.tperms(perms)
            try:
                os.chmod(self.itemPath, int("{}".format(int(tperm)), 8))
            except Exception as E:
                MyDialog("Error", str(E))
    
    def fcombo1(self, index):
        perms = self.fgetPermissions()
        if index == 0:
            perms[0] = 4
            perms[1] = 2
        elif index == 1: 
            perms[0] = 4
            perms[1] = 0
        elif index == 2:
            perms[0] = 0
            perms[1] = 0

        tperm = self.tperms(perms)
        try:
            os.chmod(self.itemPath, int("{}".format(tperm), 8))
        except Exception as E:
                MyDialog("Error", str(E))
    
    def fcombo2(self, index):
        perms = self.fgetPermissions()
        if index == 0:
            perms[3] = 4
            perms[4] = 2
        elif index == 1: 
            perms[3] = 4
            perms[4] = 0
        elif index == 2:
            perms[3] = 0
            perms[4] = 0

        tperm = self.tperms(perms)
        try:
            os.chmod(self.itemPath, int("{}".format(tperm), 8))
        except Exception as E:
                MyDialog("Error", str(E))
    
    def fcombo3(self, index):
        perms = self.fgetPermissions()
        if index == 0:
            perms[6] = 4
            perms[7] = 2
        elif index == 1: 
            perms[6] = 4
            perms[7] = 0
        elif index == 2:
            perms[6] = 0
            perms[7] = 0

        tperm = self.tperms(perms)
        try:
            os.chmod(self.itemPath, int("{}".format(tperm), 8))
        except Exception as E:
                MyDialog("Error", str(E))

    def fsetPermissions(self, perms):
        currUser = pwd.getpwuid(os.getuid())[0]

    def fgetPermissions(self):
        perms = QFile(self.itemPath).permissions()
        # 
        permissions = []
        #
        if perms & QFile.ReadOwner:
            permissions.append(4)
        else:
            permissions.append(0)
        if perms & QFile.WriteOwner:
            permissions.append(2)
        else:
            permissions.append(0)
        if perms & QFile.ExeOwner:
            permissions.append(1)
        else:
            permissions.append(0)
        #
        if perms & QFile.ReadGroup:
            permissions.append(4)
        else:
            permissions.append(0)
        if perms & QFile.WriteGroup:
            permissions.append(2)
        else:
            permissions.append(0)
        if perms & QFile.ExeGroup:
            permissions.append(1)
        else:
            permissions.append(0)
        #
        if perms & QFile.ReadOther:
            permissions.append(4)
        else:
            permissions.append(0)
        if perms & QFile.WriteOther:
            permissions.append(2)
        else:
            permissions.append(0)
        if perms & QFile.ExeOther:
            permissions.append(1)
        else:
            permissions.append(0)
        #
        return permissions
    
    
    def faccept(self):
        self.close()


# property dialog for more than one item
class propertyDialogMulti(QDialog):
    def __init__(self, itemSize, itemNum, parent=None):
        super(propertyDialogMulti, self).__init__(parent)
        #
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Property")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(600, 100)
        self.setFont(thefont)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        self.setLayout(vbox)
        #
        label1 = QLabel("Number of items: {}".format(itemNum))
        vbox.addWidget(label1)
        label2 = QLabel("Total size of the items: {}".format(itemSize))
        vbox.addWidget(label2)
        #
        button1 = QPushButton("Close")
        vbox.addWidget(button1)
        button1.clicked.connect(self.close)
        
        self.exec_()


# dialog - for file with the execution bit
class execfileDialog(QDialog):
    def __init__(self, itemPath, flag, parent=None):
        super(execfileDialog, self).__init__(parent)
        self.itemPath = itemPath
        self.flag = flag
        #
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Info")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(600, 100)
        self.setFont(thefont)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        #
        label1 = QLabel("This is an executable file.\nWhat do you want to do?")
        vbox.addWidget(label1)
        hbox = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox)
        #
        if self.flag == 0 or self.flag == 3:
            button1 = QPushButton("Open")
            hbox.addWidget(button1)
            button1.clicked.connect(self.fopen)
        if self.flag != 3:
            button2 = QPushButton("Execute")
            hbox.addWidget(button2)
            button2.clicked.connect(self.fexecute)
        button3 = QPushButton("Cancel")
        hbox.addWidget(button3)
        button3.clicked.connect(self.fcancel)
        self.Value = 0
        self.exec_()

    def getValue(self):
        return self.Value

    def fopen(self):
        self.Value = 1
        self.close()
    
    def fexecute(self):
        self.Value = 2
        self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()

# dialog - whit item list and return of the choise
class retDialogBox(QMessageBox):
    def __init__(self, *args, parent=None):
        super(retDialogBox, self).__init__(parent)
        self.setIcon(QMessageBox.Information)
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle(args[0])
        self.setText(args[1])
        self.setInformativeText(args[2])
        self.setDetailedText("The details are as follows:\n\n"+args[3])
        self.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        self.setFont(thefont)
        
        self.Value = None
        retval = self.exec_()
        
        if retval == QMessageBox.Yes:
            self.Value = 1
        elif retval == QMessageBox.Cancel:
            self.Value = 0
    
    def getValue(self):
        return self.Value

# dialog - Paste-n-Merge
class pasteNmergeDialog(QDialog):
    
    def __init__(self, itemsPath, overwrite, parent=None):
        super(pasteNmergeDialog, self).__init__(parent)
        # useless
        self.itemsPath = itemsPath
        # number of items already present at destination
        self.overwrite = overwrite
        #
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Paste and Merge")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(dialWidth, 100)
        self.setFont(thefont)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        #
        label1 = QLabel("This action will overwrite some items.\nPlease choose an action.\n\nItems with the same name: {}".format(self.overwrite))
        vbox.addWidget(label1)
        #
        hbox = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox)
        # skip all the items
        skipButton = QPushButton("Skip all")
        hbox.addWidget(skipButton)
        skipButton.clicked.connect(lambda:self.fsetValue(1))
        # overwrite all the items
        overwriteButton = QPushButton("Merge/Overwrite")
        hbox.addWidget(overwriteButton)
        overwriteButton.clicked.connect(lambda:self.fsetValue(2))
        # a new name for all the items
        newnameButton = QPushButton("New name")
        hbox.addWidget(newnameButton)
        newnameButton.clicked.connect(lambda:self.fsetValue(3))
        # add an preformatted extension to the items
        automaticButton = QPushButton("Automatic")
        hbox.addWidget(automaticButton)
        automaticButton.clicked.connect(lambda:self.fsetValue(4))
        # abort the operation
        cancelButton = QPushButton("Cancel")
        hbox.addWidget(cancelButton)
        cancelButton.clicked.connect(self.fcancel)
        
        self.Value = 0
        self.exec_()
    
    def getValue(self):
        return self.Value
    
    def fsetValue(self, n):
        self.Value = n
        self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()
    
############################
# for item copying - Paste function only
class copyThread(QThread):
    
    sig = pyqtSignal(list)
    
    def __init__(self, action, newList, parent=None):
        super(copyThread, self).__init__(parent)
        self.action = action
        self.newList = newList

    def run(self):
        time.sleep(1)
        self.item_op()

    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if not os.path.exists(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size 

    def item_op(self):
        items_skipped = ""
        #
        action = self.action
        newList = self.newList
        total_size = 0
        incr_size = 0
        for sitem in newList[::2]:
            if os.path.islink(sitem):
                total_size += 512
            elif os.path.isfile(sitem):
                item_size = QFileInfo(sitem).size()
                total_size += max(item_size, 512)
            elif os.path.isdir(sitem):
                item_size = self.folder_size(sitem)
                total_size += max(item_size, 512)

        self.sig.emit(["Starting...", 0, total_size])
        # copy
        if action == 1:
            i = 0
            for dfile in newList[::2]:
                if not self.isInterruptionRequested():
                    time.sleep(0.1)
                    if os.path.islink(dfile):
                        try:
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            # create a link to the file, do not copy the symlink
                            ltarget = QFile.symLinkTarget(dfile)
                            os.symlink(ltarget, newList[i+1])
                            #
                            incr_size += 512
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            #
                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    
                    elif os.path.isdir(dfile):
                        try:
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            shutil.copytree(dfile, newList[i+1], symlinks=True, ignore=None)
                            incr_size += max(self.folder_size(dfile), 512)
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))

                    elif os.path.isfile(dfile):
                        try:
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            shutil.copy2(dfile, newList[i+1])
                            #
                            incr_size += max(QFileInfo(dfile).size(), 512)
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            #
                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    i += 2
                else:
                    self.sig.emit(["Cancelled!", 1, total_size, items_skipped])
                    return
            self.sig.emit(["mDone", 1, total_size, items_skipped])
        # cut
        elif action == 2:
            i = 0
            for dfile in newList[::2]:
                
                if not self.isInterruptionRequested():
                    time.sleep(0.1)
                    try:
                        self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                        #
                        if os.path.islink(dfile):
                            incr_size += 512
                            # create a link to the file, do not copy the symlink
                            ltarget = QFile.symLinkTarget(dfile)
                            os.symlink(ltarget, newList[i+1])
                            # delete the original link
                            os.unlink(dfile)
                        elif os.path.isfile(dfile):
                            incr_size += max(QFileInfo(dfile).size(), 512)
                            shutil.move(dfile, newList[i+1])
                        elif os.path.isdir(dfile):
                            incr_size += max(self.folder_size(dfile), 512)
                            shutil.move(dfile, newList[i+1])
                        
                        self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])

                    except Exception as E:
                        items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    i += 2
                else:
                    self.sig.emit(["Cancelled!", 1, total_size, items_skipped])
                    return
            
            self.sig.emit(["mDone", 1, total_size, items_skipped])
        # link
        elif action == 4:
            i = 0
            for dfile in newList[::2]:
                if not self.isInterruptionRequested():
                    time.sleep(0.1)
                    if QFileInfo(dfile).isSymLink():
                        ltarget = QFile.symLinkTarget(dfile)
                        if QFile.exists(ltarget):
                            try:
                                self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                                if os.path.isfile(dfile):
                                    incr_size += max(QFileInfo(dfile).size(), 512)
                                elif os.path.isdir(dfile):
                                    incr_size += max(self.folder_size(dfile), 512)

                                os.symlink(ltarget, newList[i+1])
                                self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            except Exception as E:
                                items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    else:
                        try:
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])
                            if os.path.isfile(dfile):
                                incr_size += max(QFileInfo(dfile).size(), 512)
                            elif os.path.isdir(dfile):
                                incr_size += max(self.folder_size(dfile), 512)

                            os.symlink(dfile, newList[i+1])
                            self.sig.emit([os.path.basename(dfile), incr_size/total_size, total_size])

                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    i += 2
                else:
                    self.sig.emit(["Cancelled!", 1, total_size, items_skipped])
                    return
            self.sig.emit(["mDone", 1, total_size, items_skipped])

# Paste function only
class copyItems():
    def __init__(self, action, newList):
        self.action = action
        self.newList = newList
        self.myDialog()

    def myDialog(self):
        self.mydialog = QDialog()
        self.mydialog.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.mydialog.setWindowTitle("Copying...")
        self.mydialog.setWindowModality(Qt.ApplicationModal)
        self.mydialog.resize(600,300)
        # 
        grid = QGridLayout()
        grid.setContentsMargins(5,5,5,5)
        #
        self.label1 = clabel2()
        self.label1.setText("Processing...", self.mydialog.size().width()-12)
        self.label1.setWordWrap(True)
        grid.addWidget(self.label1, 0, 0, 1, 4, Qt.AlignCenter)
        #
        self.label2 = QLabel()
        grid.addWidget(self.label2, 1, 0, 1, 4, Qt.AlignCenter)
        #
        self.pb = QProgressBar()
        self.pb.setMinimum(0)
        self.pb.setMaximum(100)
        self.pb.setValue(0)
        grid.addWidget(self.pb, 3, 0, 1, 4, Qt.AlignCenter)
        #
        self.button1 = QPushButton("Close")
        self.button1.clicked.connect(self.fbutton1)
        grid.addWidget(self.button1, 4, 0, 1, 2, Qt.AlignCenter)
        #
        self.button1.setEnabled(False)
        #
        self.button2 = QPushButton("Abort")
        self.button2.clicked.connect(self.fbutton2)
        grid.addWidget(self.button2, 4, 2, 1, 2, Qt.AlignCenter)
        #
        self.mydialog.setLayout(grid)
        self.mythread = copyThread(self.action, self.newList)
        self.mythread.sig.connect(self.threadslot)
        self.mythread.start()
        #
        self.mydialog.exec()

    def convert_size(self, fsize2):
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize    
    
    def threadslot(self, aa):
        self.label1.setText("Done.", self.mydialog.size().width()-12)
        self.label2.setText("Total size: {}".format(self.convert_size(aa[2])))
        self.pb.setValue(int(aa[1]*100))
        if self.pb.value() == 100:
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)
        if len(aa) == 4 and aa[3] != "":
            MyMessageBox("Info", "Some errors with some items", "", aa[3])

    def fbutton1(self):
        self.mydialog.close()

    def fbutton2(self):
        self.mythread.requestInterruption()

################################
# for item copying - Paste and Merge function
class copyThread2(QThread):
    
    sig = pyqtSignal(list)
    
    def __init__(self, action, newList, atype, pathdest, parent=None):
        super(copyThread2, self).__init__(parent)
        # action: 1 copy - 2 cut
        self.action = action
        # the list of the items
        self.newList = newList
        # 1 skip - 2 overwrite - 3 rename - 4 automatic suffix
        self.atype = atype
        # destination path
        self.pathdest = pathdest
        #
        # ask for a new name from a dialog
        self.sig.connect(self.provasygnal)
        # used for main program-thread communication
        self.reqNewNm = ""
    
    def provasygnal(self, l=None):
        if l[0] == "SendNewName":
            self.reqNewNm = l[1]
        #
        elif l[0] == "SendNewAtype":
            self.reqNewNm = l[1]

    def run(self):
        time.sleep(1)
        self.item_op()

    # calculate the folder size 
    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if not os.path.exists(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size 

    
    # total size of the list
    def listTotSize(self):
        total_size = 0
        skipped = ""
        for sitem in newList:
            try:
                if os.path.islink(sitem):
                    # just a number
                    total_size += 512
                elif os.path.isfile(sitem):
                    item_size = QFileInfo(sitem).size()
                    total_size += max(item_size, 512)
                elif os.path.isdir(sitem):
                    item_size = self.folder_size(sitem)
                    total_size += max(item_size, 512)
            except:
                skipped += sitem+"\n"
        #
        return total_size

    ## self.atype 4
    # add a suffix to the filename if the file exists at destination
    def faddSuffix(self, dest):
        # it exists or it is a broken link
        if os.path.exists(dest) or os.path.islink(dest):
            if USE_DATE == 1:
                z = datetime.datetime.now()
                #dY, dM, dD, dH, dm, ds, dms
                dts = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
                new_name = os.path.basename(dest)+dts
                dest = os.path.join(os.path.dirname(dest), new_name)
                
                return dest
            
            elif USE_DATE == 0:
                i = 1
                dir_name = os.path.dirname(dest)
                bname = os.path.basename(dest)
                dest = ""
                while i:
                    nn = bname+"_("+str(i)+")"
                    if os.path.exists(os.path.join(self.lvDir, nn)):
                        i += 1
                    else:
                        dest = os.path.join(dir_name, nn)
                        i = 0
                
                return dest
    
    # self.atype: 1 skip - 2 overwrite - 3 rename - 4 automatic suffix
    def item_op(self):
        items_skipped = ""
        #
        action = self.action
        newList = self.newList
        total_size = 1
        incr_size = 1

        self.sig.emit(["Starting...", 0, total_size])
        ## action: copy 1 - cut 2
        #
        for dfile in newList:
            # the user can interrupt the operation for the next items
            if self.isInterruptionRequested():
                self.sig.emit(["mDone", 1, 1, items_skipped])
                break
            time.sleep(0.1)
            #
            # one signal for each element in the list
            self.sig.emit(["mSending", os.path.basename(dfile)])
            #
            # file or link/broken link
            if os.path.isfile(dfile) or os.path.islink(dfile):
                # check for an item/broken link with the same name at destination
                tdest = os.path.join(self.pathdest, os.path.basename(dfile))
                # if not the exactly same item
                if dfile != tdest:
                    if os.path.exists(tdest) or os.path.islink(tdest):
                        # 1 skip
                        if self.atype == 1:
                            items_skipped += "{}:\n{}\n------------\n".format(dfile, "Skipped.")
                            continue
                        # 2 overwrite
                        elif self.atype == 2:
                            try:
                                # if broken link no overwrite
                                if os.path.islink(dfile):
                                    if not os.path.exists(os.readlink(dfile)):
                                        items_skipped += "{}:\n{}\n------------\n".format(dfile, "Broken link.")
                                        continue
                                if os.path.islink(tdest):
                                    os.unlink(tdest)
                                    # 
                                    if action == 1:
                                        shutil.copy2(dfile, tdest, follow_symlinks=False)
                                    elif action == 2:
                                        shutil.move(dfile, tdest)
                                # regular file
                                else:
                                    # 
                                    if action == 1:
                                        shutil.copy2(dfile, tdest, follow_symlinks=False)
                                    elif action == 2:
                                        shutil.move(dfile, tdest)
                            except Exception as E:
                                items_skipped += "{}:\n{}\n------------\n".format(dfile, str(E))
                        # 3 rename
                        elif self.atype == 3:
                            try:
                                # item name - destination path
                                iDestPath = os.path.dirname(tdest)
                                self.sig.emit(["ReqNewName", os.path.basename(dfile), iDestPath])
                                while self.reqNewNm == "":
                                    time.sleep(1)
                                else:
                                    # -1 means cancelled from the rename dialog
                                    if self.reqNewNm == -1:
                                        items_skipped += "{}:\n{}\n------------\n".format(dfile, "Skipped.")
                                    try:
                                        shutil.copy2(dfile, os.path.join(iDestPath,self.reqNewNm), follow_symlinks=False)
                                        #
                                        if action == 2:
                                            os.remove(dfile)
                                    except Exception as E:
                                        items_skipped += "{}:\n{}\n------------\n".format(dfile, str(E))
                                        # reset
                                        self.reqNewNm = ""
                                    # reset
                                    self.reqNewNm = ""
                            except Exception as E:
                                items_skipped += "{}:\n{}\n------------\n".format(dfile, str(E))
                        # 4 automatic
                        elif self.atype == 4:
                            try:
                                ret = self.faddSuffix(tdest)
                                shutil.copy2(dfile, ret, follow_symlinks=False)
                                #
                                if action == 2:
                                    os.remove(dfile)
                            except Exception as E:
                                items_skipped += "{}:\n{}\n------------\n".format(dfile, str(E))
                    # it doesnt exist at destination
                    else:
                        try:
                            if action == 1:
                                shutil.copy2(dfile, tdest, follow_symlinks=False)
                            elif action == 2:
                                shutil.move(dfile, tdest)
                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(dfile, str(E))
                #
                else:
                    items_skipped += "{}:\n{}\n------------\n".format(dfile, "Exactly same item.")
            # dir
            elif os.path.isdir(dfile):
                tdest = os.path.join(self.pathdest, os.path.basename(dfile))
                #
                len_dfile = len(dfile)
                # 1 skip - 2 replace - 3 new name - a automatic
                dcode = 0
                # if not the exactly same item
                if dfile != tdest:
                    #
                    # the dir doesnt exist at destination or it is a broken link
                    if not os.path.exists(tdest):
                        # if skipped - broken link
                        if self.atype == 1:
                            items_skipped += "{}:\nSkipped.\n------------\n".format(dfile)
                            continue
                        try:
                            if os.path.islink(tdest):
                                ret = self.faddSuffix(tdest)
                                shutil.move(tdest, ret)
                                items_skipped += "{}:\nRenamed (broken link).\n------------\n".format(tdest)
                                #
                                if action == 1:
                                    shutil.copytree(dfile, tdest, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                                elif action == 2:
                                    shutil.move(dfile, tdest)
                            # if not broken link
                            else:
                                if action == 1:
                                    shutil.copytree(dfile, tdest, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                                elif action == 2:
                                    shutil.move(dfile, tdest)
                        except Exception as E:
                            items_skipped += "{}:\n{}\n------------\n".format(tdest, str(E))
                            # reset
                            self.reqNewNm = ""
                    #
                    # exists at destination
                    elif os.path.exists(tdest):
                        # abort if skip or cancel
                        if self.atype == 1 or self.atype == -1:
                            items_skipped += "{}:\n{}\n------------\n".format(dfile, "Operation aborted by the user.")
                            break
                        #
                        # new dir name if an item exists at destination with the same name
                        newDestDir = ""
                        # it is of another type
                        if not os.path.isdir(tdest):
                            # -1 means cancel from the rename dialog
                            if self.atype == -1:
                                break
                            # 1 skip
                            elif self.atype == 1:
                                items_skipped += "{}:\n{}\n------------\n".format(tdest, "Skipped.")
                                continue
                            # 2 overwrite but rename the item at destination
                            elif self.atype == 2:
                                try:
                                    # the destination is a link (not a broken link)
                                    if os.path.islink(tdest):
                                        os.unlink(tdest)
                                        items_skipped += "{}:\nBroken link: deleted\n------------\n".format(tdest)
                                    
                                    ret = self.faddSuffix(tdest)
                                    os.rename(tdest, os.path.join(os.path.dirname(tdest),ret))
                                    items_skipped += "{}:\nRenamed:\n{}\n------------\n".format(tdest, ret)
                                except Exception as E:
                                    items_skipped += "{}:\n{}\n------------\n".format(tdest, str(E))
                            # 3 new name
                            elif self.atype == 3 or self.atype == 4:
                                try:
                                    # item name - destination path
                                    iDestPath = os.path.dirname(tdest)
                                    self.sig.emit(["ReqNewName", os.path.basename(tdest), iDestPath])
                                    while self.reqNewNm == "":
                                        time.sleep(1)
                                    else:
                                        # -1 means cancel from the rename dialog
                                        if self.reqNewNm == -1:
                                            items_skipped += "{}:\n{}\n------------\n".format(tdest, "Skipped.")
                                            #
                                            continue
                                        # new dir name
                                        newDestDir = os.path.join(os.path.dirname(tdest), self.reqNewNm)
                                except Exception as E:
                                    items_skipped += "{}:\n{}\n------------\n".format(tdest, str(E))
                                    # reset
                                    self.reqNewNm = ""
                                    #
                                    continue
                                # reset
                                self.reqNewNm = ""
                            ## automatic - do nothing
                            #elif self.atype == 4:
                                #pass
                        # the new dir name if atype 3 - make the dir eventually
                        if newDestDir != "":
                            os.makedirs(newDestDir)
                        #
                        if newDestDir != "":
                            destdir = newDestDir
                        else:
                            destdir = tdest
                        #
                        # make the dirs and copy the relatives files in them
                        for sdir,ddir,ffile in os.walk(dfile):
                            todest = os.path.join(destdir, sdir[len(dfile)+1:])
                            #
                            for dr in ddir:
                                # lenght of destdir - base paht in common at destination
                                len_destdir = len(destdir)
                                #
                                todest2 = os.path.join(todest,dr)
                                if not os.path.exists(todest2):
                                    # require python >= 3.3
                                    os.makedirs(todest2, exist_ok=True)
                            #
                            # copy all the non-folder items from the base dir
                            for sitem in ffile:
                                fileToDest = os.path.join(todest,sitem)
                                
                                # exists one item at destination at least or it is a broken link
                                if os.path.exists(fileToDest) or os.path.islink(fileToDest):
                                    # link at destination
                                    if os.path.islink(fileToDest):
                                        os.unlink(fileToDest)
                                        items_skipped += "{}:\n{}\n------------\n".format(fileToDest, "Broken link. Deleted")
                                    
                                    # exist at destination - atype is needed
                                    else:
                                        # file to copy from the origin folder - full path
                                        fpsitem = os.path.join(sdir,sitem)
                                        # atype choosing dialog if dcode is 0 (no choises previously made)
                                        if dcode == 0:
                                            self.sig.emit(["ReqNewAtype"])
                                            while self.reqNewNm == "":
                                                time.sleep(1)
                                            else:
                                                dcode = self.reqNewNm
                                                # reset
                                                self.reqNewNm = ""
                                        #
                                        # -1 means cancel from the rename dialog
                                        if dcode == -1:
                                            items_skipped += "Operation cancelled by the user\n------------\n"
                                            break
                                        # 1 skip
                                        elif dcode == 1:
                                            items_skipped += "{}:\n{}\n------------\n".format(fpsitem, "Skipped.")
                                            continue
                                        # 2 overwrite
                                        elif dcode == 2:
                                            try:
                                                # link
                                                if os.path.islink(fileToDest):
                                                    os.unlink(fileToDest)
                                                # dir
                                                elif os.path.isdir(fileToDest):
                                                    shutil.rmtree(fileToDest)
                                                # copy or overwrite
                                                if action == 1:
                                                    shutil.copy2(fpsitem, fileToDest, follow_symlinks=False)
                                                elif action == 2:
                                                    shutil.move(fpsitem, fileToDest)
                                                #
                                            except Exception as E:
                                                items_skipped += "{}:\n{}\n------------\n".format(fpsitem, str(E))
                                        # 3 new name - 4 automatic
                                        elif dcode == 3 or dcode == 4:
                                            try:
                                                ret = self.faddSuffix(fileToDest)
                                                iNewName = os.path.join(os.path.dirname(fileToDest),ret)
                                                if action == 1:
                                                    shutil.copy2(fpsitem, iNewName, follow_symlinks=False)
                                                elif action == 2:
                                                    shutil.move(fpsitem, iNewName)
                                                items_skipped += "{}:\nRenamed:\n{}\n------------\n".format(fpsitem, ret)
                                                #
                                            except Exception as E:
                                                items_skipped += "{}:\n{}\n------------\n".format(fpsitem, str(E))
                                #
                                # nothing at destination
                                else:
                                    try:
                                        if action == 1:
                                            shutil.copy2(os.path.join(sdir,sitem), fileToDest, follow_symlinks=False)
                                        elif action == 2:
                                            shutil.move(os.path.join(sdir,sitem), fileToDest)
                                    except Exception as E:
                                        items_skipped += "{}:\n{}\n------------\n".format(os.path.join(sdir,sitem), str(E))
                        #
                        # action 2: delete the origin dir if empty
                        if action == 2:
                            if os.path.exists(dfile):
                                if len(os.listdir(dfile)) == 0:
                                    shutil.rmtree(dfile)
                                else:
                                    items_skipped += "{}:\n{}\n------------\n".format(dfile, "This dir is not empty.")
                #
                # origin and destination are the exactly same directory
                else:
                    items_skipped += "{}:\n{}\n------------\n".format(os.path.basename(dfile), "Same item.")
        #
        # DONE
        self.sig.emit(["mDone", 1, 1, items_skipped])


# Paste and Merge function only
class copyItems2():
    def __init__(self, action, newList, atype, pathdest):
        self.action = action
        self.newList = newList
        self.atype = atype
        self.pathdest = pathdest
        self.myDialog()

    def myDialog(self):
        self.mydialog = QDialog()
        self.mydialog.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.mydialog.setWindowTitle("Copying...")
        self.mydialog.setWindowModality(Qt.ApplicationModal)
        self.mydialog.resize(600,300)
        # 
        grid = QGridLayout()
        grid.setContentsMargins(5,5,5,5)
        #
        self.label1 = clabel2()
        self.label1.setText("Processing...", self.mydialog.size().width()-12)
        self.label1.setWordWrap(True)
        grid.addWidget(self.label1, 0, 0, 1, 4, Qt.AlignCenter)
        #
        self.label2 = QLabel("")
        grid.addWidget(self.label2, 1, 0, 1, 4, Qt.AlignCenter)
        #
        self.pb = QProgressBar()
        self.pb.setMinimum(0)
        self.pb.setMaximum(100)
        self.pb.setValue(0)
        grid.addWidget(self.pb, 3, 0, 1, 4, Qt.AlignCenter)
        #
        self.button1 = QPushButton("Close")
        self.button1.clicked.connect(self.fbutton1)
        grid.addWidget(self.button1, 4, 0, 1, 2, Qt.AlignCenter)
        #
        self.button1.setEnabled(False)
        #
        self.button2 = QPushButton("Abort")
        self.button2.clicked.connect(self.fbutton2)
        grid.addWidget(self.button2, 4, 2, 1, 2, Qt.AlignCenter)
        #
        # number of items in the list
        self.numItemList = len(self.newList)
        # number of items processed
        self.numItemProc = 0
        #
        self.mydialog.setLayout(grid)
        self.mythread = copyThread2(self.action, self.newList, self.atype, self.pathdest)
        self.mythread.sig.connect(self.threadslot)
        self.mythread.start()
        #
        self.mydialog.exec()

    def convert_size(self, fsize2):
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize    
    
    def threadslot(self, aa):
        # aa[0] code - aa[1] dir - aa[2] item name
        if aa[0] == "ReqNewName":
            # item name - dest path
            sNewName = MyDialogRename22(aa[1],aa[2]).getValues()
            # -1 is cancelled
            self.mythread.sig.emit(["SendNewName", sNewName])
        #
        elif aa[0] == "ReqNewAtype":
            sNewAtype = pasteNmergeDialog("", 1).getValue()
            self.mythread.sig.emit(["SendNewAtype", sNewAtype])
        #
        # copying process
        elif aa[0] == "mSending":
            self.label1.setText(aa[1], self.mydialog.size().width()-12)
            self.numItemProc += 1
            self.label2.setText("Items: {}/{}".format(self.numItemProc,self.numItemList))
            self.pb.setValue(int(self.numItemProc/self.numItemList*100))
        # the copying process ends
        elif aa[0] == "mDone":
            self.label1.setText("Done", self.mydialog.size().width()-12)
            if self.numItemProc == self.numItemList:
                self.pb.setValue(100)
            # change the button state
            self.button1.setEnabled(True)
            self.button2.setEnabled(False)
            # something happened with some items
            if len(aa) == 4 and aa[3] != "":
                MyMessageBox("Info", "Some errors with some items", "", aa[3])
            
    def fbutton1(self):
        self.mydialog.close()

    def fbutton2(self):
        self.mythread.requestInterruption()

#################################

class MyQlist(QListView):
    def __init__(self, parent=None):
        super(MyQlist, self).__init__(parent)
        self.verticalScrollBar().setSingleStep(25)

    def startDrag(self, supportedActions):
        item_list = []
        for index in self.selectionModel().selectedIndexes():
            filepath = index.data(Qt.UserRole+1)
            try:
                if stat.S_ISREG(os.stat(filepath).st_mode) or stat.S_ISDIR(os.stat(filepath).st_mode) or stat.S_ISLNK(os.stat(filepath).st_mode):
                    item_list.append(QUrl.fromLocalFile(filepath))
                else:
                    continue
            except:
                continue
        drag = QDrag(self)
        if len(item_list) > 1:
            pixmap = QPixmap("icons/items_multi.svg").scaled(ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
        elif len(item_list) == 1:
            try:
                model = self.model()
                for i in range(len(self.selectionModel().selectedIndexes())):
                    index = self.selectionModel().selectedIndexes()[i]
                    filepath = index.data(Qt.UserRole+1)
                    if stat.S_ISREG(os.stat(filepath).st_mode) or stat.S_ISDIR(os.stat(filepath).st_mode) or stat.S_ISLNK(os.stat(filepath).st_mode):
                        file_icon = model.fileIcon(index)
                        pixmap = file_icon.pixmap(QSize(ICON_SIZE, ICON_SIZE))
                        break
                    else:
                        continue
            except:
                pixmap = QPixmap("icons/empty.svg").scaled(ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
        else:
            return
        
        drag.setPixmap(pixmap)
        data = QMimeData()
        data.setUrls(item_list)
        drag.setMimeData(data)
        drag.setHotSpot(pixmap.rect().topLeft())
        drag.exec_(Qt.CopyAction|Qt.MoveAction|Qt.LinkAction, Qt.CopyAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.pos().y() > self.viewport().size().height() - 100:
            step = 10
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + step)
        elif event.pos().y() < 100:
            step = -10
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + step)
                        
        dest_path = self.model().rootPath()
        curr_dir = QFileInfo(dest_path)
        if not curr_dir.isWritable():
            event.ignore()

        if event.mimeData().hasUrls:
            if isinstance(event.source(), MyQlist):
                pointedItem = self.indexAt(event.pos())
                ifp = self.model().data(pointedItem, QFileSystemModel.FilePathRole)

                if pointedItem.isValid():

                    if os.path.isdir(ifp):
                        for uurl in event.mimeData().urls():
                            if uurl.toLocalFile() == ifp:
                                event.ignore()
                                break
                        else:
                            event.acceptProposedAction()
                    else:
                        event.ignore()
                else:
                    event.ignore()
            else:
                event.acceptProposedAction()

    def dropEvent(self, event):
        
        dest_path = self.model().rootPath()
        curr_dir = QFileInfo(dest_path)
        if not curr_dir.isWritable():
            MyDialog("Info", "The current folder is not writable: "+os.path.basename(dest_path))
            event.ignore()
            return
        if event.mimeData().hasUrls:
            
            event.accept()
            filePathsTemp = [ str(url.toLocalFile()) for url in event.mimeData().urls() ]

            filePaths = []
            for item in filePathsTemp:
                if stat.S_ISREG(os.stat(item).st_mode) or stat.S_ISDIR(os.stat(item).st_mode) or stat.S_ISLNK(os.stat(item).st_mode):
                    filePaths.append(item)
            
            for item in filePaths:
                if os.path.exists(item):
                    if stat.S_ISREG(os.stat(item).st_mode):
                        dir_name = os.path.dirname(item)
                        nroot, ext = os.path.splitext(os.path.basename(item))
                        if ext == ".html" or ext == ".htm":
                            fname = os.path.join(dir_name, nroot+"_files")
                            if os.path.exists(fname):
                                if fname not in filePaths:
                                    if stat.S_ISDIR(os.stat(fname).st_mode) and os.access(fname, os.R_OK):
                                        filePaths.append(fname)
                    if stat.S_ISDIR(os.stat(item).st_mode):
                        dir_name = os.path.dirname(item)
                        base_name = os.path.basename(item)
                        nroot = base_name[:-6]
                        if not os.path.join(dir_name, nroot+".html") in filePaths:
                            if os.path.exists(os.path.join(dir_name, nroot+".html")):
                                filePaths.append(os.path.join(dir_name, nroot+".html"))
                        if not os.path.join(dir_name, nroot+".htm") in filePaths:
                            if os.path.exists(os.path.join(dir_name, nroot+".htm")):
                                filePaths.append(os.path.join(dir_name, nroot+".htm"))
            
            if filePaths:

                pointedItem = self.indexAt(event.pos())

                if pointedItem.isValid():
                    ifp = self.model().data(pointedItem, QFileSystemModel.FilePathRole)
                    if os.path.isdir(ifp):
                        if os.access(ifp, os.W_OK):
                            newList = self.fnewList(filePaths, ifp)
                            if newList == -1:
                                return
                            if newList:
                                copyItems(event.proposedAction(), newList)

                        else:
                            MyDialog("Info", "The following folder in not writable: "+os.path.basename(ifp))
                            return

                    else:
                        newList = self.fnewList(filePaths, dest_path)
                        if newList == -1:
                            return
                        if newList:
                            copyItems(event.proposedAction(), newList)
                else:
                    newList = self.fnewList(filePaths, dest_path)
                    if newList == -1:
                        return
                    if newList:
                        copyItems(event.proposedAction(), newList)
            else:
                event.ignore()
        else:
            event.ignore()
    
    def fnewList(self, filePaths, dest_path):
        nlist = []
        items_skipped = ""
        for ditem in filePaths:
            if QFileInfo(ditem).isReadable():
                file_name = os.path.basename(ditem)
                dest_filePath = os.path.join(dest_path, file_name)
                if not os.path.exists(dest_filePath):
                    nlist.append(ditem)
                    nlist.append(dest_filePath)
                else:
                    ret = self.wrename(ditem, dest_path)
                    if ret == -2:
                        continue
                    elif ret == -1:
                        return -1
                    else:
                        nlist.append(ditem)
                        nlist.append(ret)
            else:
                items_skipped += "{}\n-----------\n".format(os.path.basename(ditem))
        if items_skipped != "":
            MyMessageBox("Info", "Items skipped because not readable 1", "", items_skipped)
        return nlist

    def wrename(self, ditem, dest_path):
        dfitem = os.path.basename(ditem)
        ret = dfitem
        ret = MyDialogRename(dfitem).getValues()
        if ret == -1 or ret == -2:
                return ret
        elif not ret:
            return -1
        else:
            while QFile.exists(os.path.join(dest_path, ret)):
                ret = MyDialogRename(dfitem).getValues()
            else:
                return os.path.join(dest_path, ret)
    

class itemDelegate(QItemDelegate):

    def __init__(self, parent=None):
        super(itemDelegate, self).__init__(parent)
    
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        ##painter.setRenderHint(QPainter.HighQualityAntialiasing)
        iicon = index.data(QFileSystemModel.FileIconRole)
        ppath = index.data(QFileSystemModel.FilePathRole)

        ## disabled
        #if option.state & QStyle.State_MouseOver:
            #pred = option.palette.color(QPalette.Highlight).red()
            #pgreen = option.palette.color(QPalette.Highlight).green()
            #pblue = option.palette.color(QPalette.Highlight).blue()
            #painter.setBrush(QColor(pred, pgreen, pblue, 170))
            #painter.setPen(QColor(pred, pgreen, pblue, 170))
            #painter.drawRoundedRect(QRect(option.rect.x(),option.rect.y(),option.rect.width(),ITEM_HEIGHT), 5.0, 5.0, Qt.AbsoluteSize)

        #el
        if option.state & QStyle.State_Selected:
            painter.setBrush(option.palette.color(QPalette.Highlight))
            painter.setPen(option.palette.color(QPalette.Highlight))
            painter.drawRoundedRect(QRect(option.rect.x(),option.rect.y(),option.rect.width(),ITEM_HEIGHT), 5.0, 5.0, Qt.AbsoluteSize)

        painter.restore()

        # use larger thumbs
        if LARGETHUMS:
            if not index.data(QFileSystemModel.FileIconRole).name():
                pixmap = iicon.pixmap(QSize(THUMB_SIZE, THUMB_SIZE))
                size_pixmap = pixmap.size()
                pw = size_pixmap.width()
                ph = size_pixmap.height()
                xpad = (ITEM_WIDTH - pw) / 2
                ypad = (ITEM_HEIGHT - ph) / 2
                painter.drawPixmap(option.rect.x() + xpad,option.rect.y() + ypad, -1,-1, pixmap,0,0,-1,-1)
            else:
                pixmap = iicon.pixmap(QSize(ICON_SIZE, ICON_SIZE))
                size_pixmap = pixmap.size()
                pw = size_pixmap.width()
                ph = size_pixmap.height()
                xpad = (ITEM_WIDTH - pw) / 2
                ypad = (ITEM_HEIGHT - ph) / 2
                painter.drawPixmap(option.rect.x() + xpad,option.rect.y() + ypad, -1,-1, pixmap,0,0,-1,-1)
        
        else:
            pixmap = iicon.pixmap(QSize(ICON_SIZE, ICON_SIZE))
            size_pixmap = pixmap.size()
            pw = size_pixmap.width()
            ph = size_pixmap.height()
            xpad = (ITEM_WIDTH - pw) / 2
            ypad = (ITEM_HEIGHT - ph) / 2
            painter.drawPixmap(option.rect.x() + xpad,option.rect.y() + ypad, -1,-1, pixmap,0,0,-1,-1)

        
        qstring = index.data(QFileSystemModel.FileNameRole)
        st = QStaticText(qstring)
        st.setTextWidth(ITEM_WIDTH)
        to = QTextOption(Qt.AlignCenter)
        to.setWrapMode(QTextOption.WrapAnywhere)
        st.setTextOption(to)
        painter.drawStaticText(option.rect.x(), option.rect.y()+ITEM_HEIGHT, st)

        if not os.path.isdir(ppath):
            if not index.data(QFileSystemModel.FilePermissions) & QFile.WriteUser or not index.data(QFileSystemModel.FilePermissions) & QFile.ReadUser:
                ppixmap = QPixmap('icons/emblem-readonly.svg').scaled(ICON_SIZE2, ICON_SIZE2, Qt.KeepAspectRatio, Qt.FastTransformation)
                painter.drawPixmap(option.rect.x(), option.rect.y()+ITEM_HEIGHT-ICON_SIZE2,-1,-1, ppixmap,0,0,-1,-1)
        else:
            if not index.data(QFileSystemModel.FilePermissions) & QFile.WriteUser or not index.data(QFileSystemModel.FilePermissions) & QFile.ReadUser or not index.data(QFileSystemModel.FilePermissions) & QFile.ExeOwner:
                ppixmap = QPixmap('icons/emblem-readonly.svg').scaled(ICON_SIZE2, ICON_SIZE2, Qt.KeepAspectRatio, Qt.FastTransformation)
                painter.drawPixmap(option.rect.x(), option.rect.y()+ITEM_HEIGHT-ICON_SIZE2,-1,-1, ppixmap,0,0,-1,-1)
                 
        if os.path.islink(ppath):
            lpixmap = QPixmap('icons/emblem-symbolic-link.svg').scaled(ICON_SIZE2, ICON_SIZE2, Qt.KeepAspectRatio, Qt.FastTransformation)
            painter.drawPixmap(option.rect.x()+ITEM_WIDTH-ICON_SIZE2, option.rect.y()+ITEM_HEIGHT-ICON_SIZE2,-1,-1, lpixmap,0,0,-1,-1)
        
    
    def sizeHint(self, option, index):
        qstring = index.data(QFileSystemModel.FileNameRole)
        st = QStaticText(qstring)
        st.setTextWidth(ITEM_WIDTH)
        to = QTextOption(Qt.AlignCenter)
        to.setWrapMode(QTextOption.WrapAnywhere)
        st.setTextOption(to)
        ww = st.size().width()
        hh = st.size().height()
        return QSize(int(ww), int(hh)+ITEM_HEIGHT)


# used for the trashcan and main
class IconProvider(QFileIconProvider):
    # set the icon theme
    QIcon.setThemeName(ICON_THEME)
    
    def evaluate_pixbuf(self, ifull_path, imime):
        hmd5 = "Null"
        hmd5 = create_thumbnail(ifull_path, imime)
        #
        file_icon = "Null"
        if hmd5 != "Null":
            if LARGETHUMS:
                file_icon = QIcon(QPixmap(XDG_CACHE_LARGE+"/"+str(hmd5)+".png"))
            else:
                file_icon = QIcon(QPixmap(XDG_CACHE_LARGE+"/"+str(hmd5)+".png"))
        #
        return file_icon
    
    def icon(self, fileInfo):
        try:
            if fileInfo.exists():
                if fileInfo.isFile():
                    if fileInfo.isSymLink():
                        ireal_path = os.path.realpath(fileInfo.absoluteFilePath())
                        if fileInfo.exists():
                            imime = QMimeDatabase().mimeTypeForFile(ireal_path, QMimeDatabase.MatchDefault)
                            if imime:
                                try:
                                    if USE_THUMB == 1:
                                        file_icon = self.evaluate_pixbuf(ireal_path, imime.name())
                                        if file_icon != "Null":
                                            return file_icon
                                        else:
                                            file_icon = QIcon.fromTheme(imime.iconName())
                                            return file_icon
                                    elif USE_THUMB == 0:
                                        file_icon = QIcon.fromTheme(imime.iconName())
                                        return file_icon
                                except:
                                    return QIcon("icons/empty.svg")
                            else:
                                try:
                                    file_icon = QIcon.fromTheme("text-plain")
                                    return file_icon
                                except:
                                    return QIcon("icons/empty.svg")
                        else:
                            return QIcon("icons/error2.svg")
                    else:
                        file_ap = fileInfo.absoluteFilePath()
                        if fileInfo.exists():
                            imime = QMimeDatabase().mimeTypeForFile(file_ap, QMimeDatabase.MatchDefault)
                            if imime:
                                try:
                                    if USE_THUMB == 1:
                                        file_icon = self.evaluate_pixbuf(file_ap, imime.name())
                                        if file_icon != "Null":
                                            return file_icon
                                        else:
                                            file_icon = QIcon.fromTheme(imime.iconName())
                                            return file_icon
                                    elif USE_THUMB == 0:
                                        file_icon = QIcon.fromTheme(imime.iconName())
                                        return file_icon
                                except:
                                    return QIcon("icons/empty.svg")
                            else:
                                try:
                                    file_icon = QIcon.fromTheme("text-plain")
                                    return file_icon
                                except:
                                    return QIcon("icons/error2.svg")
        
                        else:
                            return QIcon("icons/error2.svg")
                elif fileInfo.isDir():
                    if fileInfo.exists():
                        if fileInfo.isSymLink():
                            try:
                                return QIcon.fromTheme("inode-directory")
                            except:
                                return QIcon("icons/folder.svg")
                        else:
                            try:
                                return QIcon.fromTheme("inode-directory",QIcon("icons/folder.svg"))
                            except:
                                return QIcon("icons/folder.svg")
        
                    else:
                        return QIcon("icons/error2.svg")
                else:
                    file_icon = QIcon.fromTheme("text-plain")
                    return file_icon

            else:
                return QIcon("icons/error2.svg")
        #
        except:
            return QIcon("icons/empty.svg")


class MainWin(QWidget):
    
    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        
        self.setWindowIcon(QIcon("icons/file-manager-blue.svg"))
        
        if FOLDER_TO_OPEN == "HOME":
            HOME = os.path.expanduser('~')
        else:
            if os.path.exists(FOLDER_TO_OPEN):
                if os.access(FOLDER_TO_OPEN, os.R_OK):
                    HOME = FOLDER_TO_OPEN
                else:
                    HOME = os.path.expanduser('~')
            else:
                HOME = os.path.expanduser('~')
        
        self.resize(int(WINW), int(WINH))
        if WINM == "True":
            self.showMaximized()
        
        self.setWindowTitle("qmfm")
        
        self.vbox = QBoxLayout(QBoxLayout.TopToBottom)
        self.vbox.setContentsMargins(QMargins(2,2,2,2))
        self.setLayout(self.vbox)
        
        self.obox1 = QBoxLayout(QBoxLayout.RightToLeft)
        self.vbox.addLayout(self.obox1)
        # buttons
        qbtn = QPushButton(QIcon.fromTheme("window-close"), None)
        qbtn.setToolTip("Exit")
        qbtn.clicked.connect(qApp.quit)
        self.obox1.addWidget(qbtn, 1, Qt.AlignRight)
        
        if USE_TRASH:
            tbtn = QPushButton(QIcon.fromTheme("user-trash"), None)
            tbtn.setToolTip("Recycle Bin")
            self.obox1.addWidget(tbtn, 0, Qt.AlignLeft)
            if not isXDGDATAHOME:
                tbtn.setEnabled(False)
            else:
                tbtn.clicked.connect(lambda:openTrash(self, "HOME"))
        #
        if USE_MEDIA:
            dbtn = QPushButton(QIcon.fromTheme("drive-harddisk"), None)
            dbtn.setToolTip("Media")
            self.obox1.addWidget(dbtn, 0, Qt.AlignLeft)
            dbtn.clicked.connect(lambda:openDisks(self))
        #
        rootbtn = QPushButton(QIcon.fromTheme("computer"), None)
        rootbtn.setToolTip("Root")
        rootbtn.clicked.connect(lambda:self.openDir("/", 1))
        self.obox1.addWidget(rootbtn, 0, Qt.AlignLeft)
        #
        hbtn = QPushButton(QIcon.fromTheme("user-home"), None)
        hbtn.setToolTip("Home")
        hbtn.clicked.connect(lambda:self.openDir(HOME, 1))
        self.obox1.addWidget(hbtn, 0, Qt.AlignLeft)
        self.mtab = QTabWidget()
        global MMTAB
        MMTAB = self.mtab
        self.mtab.setMovable(True)
        self.mtab.setElideMode(Qt.ElideRight)
        self.mtab.setTabsClosable(True)
        self.mtab.tabCloseRequested.connect(self.closeTab)

        self.vbox.addWidget(self.mtab)
        
        parg = ""
        if len(sys.argv) > 1:
            for i in range(1, len(sys.argv) -1):
                parg += sys.argv[i]+" "
            parg += sys.argv[len(sys.argv) - 1]
        if parg != "":
            if parg[-1] == "/":
                parg = parg[0:-1]
        if len(sys.argv) > 1:
            self.openDir(parg, 1)
        else:
            self.openDir(HOME, 1)
    
    def keyPressEvent(self, event):
        if event.modifiers() ==  Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                try:
                    with open("winsize.cfg", "r") as ifile:
                        fcontent = ifile.readline()
                    aw, ah, am = fcontent.split(";")
                    window_width = self.width()
                    window_height = self.height()
                    isMaximized = self.isMaximized()
                    if isMaximized:
                        if am == "False":
                            with open("winsize.cfg", "w") as ifile:
                                ifile.write("{};{};{}".format(aw, ah, str(isMaximized)))
                    else:
                        if window_width != int(aw) or window_height != int(ah):
                            with open("winsize.cfg", "w") as ifile:
                                ifile.write("{};{};{}".format(window_width, window_height, str(isMaximized)))
                        else:
                            with open("winsize.cfg", "w") as ifile:
                                ifile.write("{};{};{}".format(aw, ah, str(isMaximized)))
                except Exception as E:
                    MyDialog("Error", str(E))
    
    def openDir(self, ldir, flag):
        page = QWidget()
        clv = LView(ldir, self, flag)
        if os.path.isdir(ldir):
            self.mtab.addTab(page, os.path.basename(ldir) or "ROOT")
            self.mtab.setTabToolTip(self.mtab.count()-1, ldir)
        elif os.path.isfile(ldir):
            self.mtab.addTab(page, os.path.basename(os.path.dirname(ldir)) or "ROOT")
            self.mtab.setTabToolTip(self.mtab.count()-1, os.path.dirname(ldir))
        page.setLayout(clv)
        self.mtab.setCurrentIndex(self.mtab.count()-1)

    def closeTab(self, index):
        if self.mtab.count() > 1:
            if  self.mtab.tabText(index) == "Media":
                global TCOMPUTER
                TCOMPUTER = 0

            self.mtab.removeTab(index)

class openTrash(QBoxLayout):
    def __init__(self, window, tdir, parent=None):
        super(openTrash, self).__init__(QBoxLayout.TopToBottom, parent)
        self.window = window
        self.tdir = tdir
        self.setContentsMargins(QMargins(0,0,0,0))

        page = QWidget()
        #
        self.ilist = QListView()
        self.ilist.setSpacing(10)
        # the background color
        if USE_BACKGROUND_COLOUR == 1:
            palette = self.ilist.palette()
            palette.setColor(QPalette.Base, QColor(ORED,OGREEN,OBLUE))
            self.ilist.setPalette(palette)
        
        self.ilist.clicked.connect(self.flist)
        self.ilist.doubleClicked.connect(self.flist2)
        self.addWidget(self.ilist, 0)
        
        self.ilist.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ilist.setWrapping(True)
        self.ilist.setWordWrap(True)
        
        self.model = QStandardItemModel(self.ilist)

        self.ilist.setModel(self.model)
        #
        self.ilist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ilist.customContextMenuRequested.connect(self.onRightClick)
        #
        obox = QBoxLayout(QBoxLayout.LeftToRight)
        obox.setContentsMargins(QMargins(5,5,5,5))
        self.insertLayout(1, obox)
        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignRight)
        #
        self.label1 = QLabel("Name")
        self.label2 = QLabel("Origin")
        self.label3 = QLabel("Deletion date")
        self.label4 = QLabel("Type")
        self.label5 = QLabel("Size")
        self.label6 = clabel()
        self.label7 = clabel()
        self.label8 = QLabel("")
        self.label9 = QLabel("")
        self.label10 = QLabel("")
        layout.addRow(self.label1, self.label6)
        layout.addRow(self.label2, self.label7)
        layout.addRow(self.label3, self.label8)
        layout.addRow(self.label4, self.label9)
        layout.addRow(self.label5, self.label10)

        obox.insertLayout(1, layout, 1)
        box2 = QBoxLayout(QBoxLayout.TopToBottom)
        box2.setContentsMargins(QMargins(0,0,0,0))
        obox.insertLayout(1, box2, 0)
        #
        button1 = QPushButton("R")
        button1.setToolTip("Restore the selected items")
        button1.clicked.connect(self.ftbutton1)
        box2.addWidget(button1)
        # 
        button2 = QPushButton("D")
        button2.setToolTip("Delete the selected items")
        button2.clicked.connect(self.ftbutton2)
        box2.addWidget(button2)
        #
        button3 = QPushButton("E")
        button3.setToolTip("Empty the Recycle Bin")
        button3.clicked.connect(self.ftbutton3)
        box2.addWidget(button3)
        #
        if self.tdir == "HOME":
            ttag = "Home"
        else:
            ttag = os.path.basename(str(self.tdir))
        self.window.mtab.addTab(page, "Recycle Bin - {}".format(ttag))
        page.setLayout(self)
        self.window.mtab.setCurrentIndex(self.window.mtab.count()-1)
        self.popTrash()
    
    def popTrash(self):
        llista = trash_module.ReadTrash(self.tdir).return_the_list()
        
        if llista == -2:
            MyDialog("ERROR", "The trash directory and its subfolders have some problem.")
            return
        
        if llista == -1:
            MyDialog("ERROR", "Got some problem during the reading of the trashed items.\nSolve the issue manually.")
            return
        
        if llista != -1:
            for item in llista:
                if self.tdir == "HOME":
                    prefix_real_name = os.path.expanduser('~')
                else:
                    prefix_real_name = self.tdir
                real_name = os.path.join(prefix_real_name, item.realname)
                fake_name = item.fakename
                deletion_date = item.deletiondate
                item = QStandardItem(3,1)
                item.setData(os.path.basename(real_name), Qt.DisplayRole)
                item.setData(real_name, Qt.UserRole)
                item.setData(fake_name, Qt.UserRole+1)
                item.setData(deletion_date, Qt.UserRole+2)
                Tpath = trash_module.mountPoint(self.tdir).find_trash_path()
                item_path = os.path.join(Tpath, "files", fake_name)
                item.setIcon(self.iconItem(item_path))
                item.setCheckable(True)
                self.model.appendRow(item)
    
    def iconItem(self, item):
        path = item
        imime = QMimeDatabase().mimeTypeForFile(path, QMimeDatabase.MatchDefault)
        if imime:
            try:
                file_icon = QIcon.fromTheme(imime.iconName())
                if file_icon:
                    return file_icon
                else:
                    return QIcon("icons/empty.svg")
            except:
                return QIcon("icons/empty.svg")
        else:
            return QIcon("icons/empty.svg")
    
    def ftbutton1(self):
        checkedItems = []
        i = 0
        while self.model.item(i):
            if self.model.item(i).checkState():
                checkedItems.append(self.model.item(i))
            i += 1
        
        for iitem in checkedItems:
            restore_items = []
            index = iitem.index()
            RestoreTrashedItems.fakename = index.data(Qt.UserRole+1)
            RestoreTrashedItems.realname = index.data(Qt.UserRole)
            #
            restore_items.append(RestoreTrashedItems)
            #
            ret = trash_module.RestoreTrash(self.tdir, restore_items).itemsRestore()
            if ret == -2:
                MyDialog("ERROR", "The items cannot be restored.\nDo it manually.")
                return
            if ret != [1,-1]:
                MyDialog("ERROR", ret)
            else:
                self.model.removeRow(index.row())
                self.label6.setText("", self.window.size().width())
                self.label7.setText("", self.window.size().width())
                self.label8.setText("")
                self.label9.setText("")
                self.label10.setText("")
    
    def ftbutton2(self):
        checkedItems = []
        i = 0
        while self.model.item(i):
            if self.model.item(i).checkState():
                checkedItems.append(self.model.item(i))
            i += 1

        for iitem in checkedItems:
            restore_items = []
            index = iitem.index()
            RestoreTrashedItems.fakename = index.data(Qt.UserRole+1)
            RestoreTrashedItems.realname = index.data(Qt.UserRole)
            #
            restore_items.append(RestoreTrashedItems)
            #
            ret = trash_module.deleteTrash(self.tdir, restore_items).itemsDelete()
            if ret == -2:
                MyDialog("ERROR", "The items cannot be deleted.\nDo it manually.")
                return
            #
            if ret != [1,-1]:
                MyDialog("ERROR", ret)
            else:
                self.model.removeRow(index.row())
                self.label6.setText("", self.window.size().width())
                self.label7.setText("", self.window.size().width())
                self.label8.setText("")
                self.label9.setText("")
                self.label10.setText("")
    
    def ftbutton3(self):
        ret = trash_module.emptyTrash(self.tdir).tempty()
        if ret == -2:
            MyDialog("ERROR", "The Recycle Bin cannot be empty.\nDo it manually.")
            return
        self.model.clear()
        self.label6.setText("", self.window.size().width())
        self.label7.setText("", self.window.size().width())
        self.label8.setText("")
        self.label9.setText("")
        self.label10.setText("")
        if ret == -1:
            MyDialog("ERROR", "Error with some files in the Recycle Bin.\nTry to remove them manually.")
    
    def flist(self, index):
        real_name = index.data(Qt.UserRole)
        itemName = os.path.basename(real_name)
        itemPath = os.path.dirname(real_name)
        #
        fake_name = index.data(Qt.UserRole+1)
        #
        deletionDate = index.data(Qt.UserRole+2)
        #
        self.label6.setText(itemName, self.window.size().width())
        self.label7.setText(itemPath, self.window.size().width())
        self.label8.setText(str(deletionDate).replace("T", " - "))

        Tpath = trash_module.mountPoint(self.tdir).find_trash_path()
        fpath = os.path.join(Tpath, "files", fake_name)
        imime = QMimeDatabase().mimeTypeForFile(fpath, QMimeDatabase.MatchDefault)
        self.label9.setText(imime.name())
        
        if not os.path.exists(fpath):
            self.label10.setText("(Broken Link)")
        elif os.path.isfile(fpath):
            if os.access(fpath, os.R_OK):
                self.label10.setText(self.convert_size(QFileInfo(fpath).size()))
            else:
                self.label10.setText("(Not readable)")
        elif os.path.isdir(fpath):
            if os.access(fpath, os.R_OK):
                self.label10.setText(self.convert_size(self.folder_size(fpath)))
            else:
                self.label10.setText("(Not readable)")
    
    def flist2(self, index):
        fake_name = index.data(Qt.UserRole+1)
        Tpath = trash_module.mountPoint(self.tdir).find_trash_path()
        path = os.path.join(Tpath, "files", fake_name)
        if os.path.isdir(path):
            if os.access(path, os.R_OK):
                try:
                    self.window.openDir(path, 0)
                except Exception as E:
                    MyDialog("ERROR", str(E))
            else:
                MyDialog("Info", path+"\n\n   Not readable")
        elif os.path.isfile(path):
            perms = QFileInfo(path).permissions()
            # can be execute
            if perms & QFile.ExeOwner:
                imime = QMimeDatabase().mimeTypeForFile(path, QMimeDatabase.MatchDefault).name()
                if imime == "application/x-sharedlib":
                    MyDialog("Info", "This is a binary file.")
                    return
                else:
                    ret = execfileDialog(path, 3).getValue()
                if ret == 2:
                    try:
                        subprocess.Popen(path, shell=True)
                    except Exception as E:
                        MyDialog("Error", str(E))
                    finally:
                        return
                elif ret == -1:
                    return

            defApp = getDefaultApp(path).defaultApplication()
            if defApp != "None":
                try:
                    subprocess.Popen([defApp, path])
                except Exception as E:
                    MyDialog("Error", str(E))
    
    def onRightClick(self, position):
        time.sleep(0.2)
        pointedItem = self.ilist.indexAt(position)
        vr = self.ilist.visualRect(pointedItem)
        pointedItem2 = self.ilist.indexAt(QPoint(vr.x(),vr.y()))
        if vr:
            itemName = self.model.data(pointedItem2, Qt.UserRole+1)
            menu = QMenu("Menu", self.ilist)
            Tpath = trash_module.mountPoint(self.tdir).find_trash_path()
            if os.path.isfile(os.path.join(Tpath, "files", itemName)):
                subm_openwithAction= menu.addMenu("Open with...")
                listPrograms = getAppsByMime(os.path.join(Tpath, "files", itemName)).appByMime()
                
                ii = 0
                defApp = getDefaultApp(os.path.join(Tpath, "files", itemName)).defaultApplication()
                progActionList = []
                if listPrograms != []:
                    for iprog in listPrograms[::2]:
                        if iprog == defApp:
                            progActionList.append(QAction("{} - {} (Default)".format(os.path.basename(iprog), listPrograms[ii+1]), self))
                            progActionList.append(iprog)
                        else:
                            progActionList.append(QAction("{} - {}".format(os.path.basename(iprog), listPrograms[ii+1]), self))
                            progActionList.append(iprog)
                        ii += 2
                    #
                    ii = 0
                    for paction in progActionList[::2]:
                        paction.triggered.connect(lambda checked, index=ii:self.fprogAction(progActionList[index+1], os.path.join(Tpath, "files", itemName)))
                        subm_openwithAction.addAction(paction)
                        ii += 2
                subm_openwithAction.addSeparator()
                otherAction = QAction("Other Program")
                otherAction.triggered.connect(lambda:self.fotherAction(os.path.join(Tpath, "files", itemName)))
                subm_openwithAction.addAction(otherAction)
            #
            menu.exec_(self.ilist.mapToGlobal(position))
    
    def fprogAction(self, iprog, path):
        try:
            subprocess.Popen([iprog, path])
        except Exception as E:
            MyDialog("Error", str(E))
    
    def fotherAction(self, itemPath):
        ret = otherApp(itemPath).getValues()
        if ret == -1:
            return
        if shutil.which(ret):
            try:
                subprocess.Popen([ret, itemPath])
            except Exception as E:
                MyDialog("Error", str(E))
        else:
            MyDialog("Error", "The program\n"+ret+"\ncannot be found")
    
    def convert_size(self, fsize2):
        
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize  
    
    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if not os.path.exists(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size 


class RestoreTrashedItems():
    def __init__(self):
        self.fakename = ""
        self.realname = ""
        #self.deletiondate = ""


class MediaItemDelegate(QItemDelegate):

    def __init__(self, parent=None):
        super(MediaItemDelegate, self).__init__(parent)
    
    def paint(self, painter, option, index):
        
        ppath = index.data()
        iicon = index.data(QFileSystemModel.FileIconRole)
        
        st1 = index.data()
        st = QStaticText(st1)
        
        painter.save()
        if option.state & QStyle.State_Selected:
            
            if ITEM_WIDTH > st.size().width():
                xpad = (ITEM_WIDTH - ICON_SIZE) / 2
            else:
                xpad = (st.size().width() - ICON_SIZE) / 2
            
            painter.setBrush(option.palette.color(QPalette.Highlight))
            painter.setPen(option.palette.color(QPalette.Highlight))
            painter.drawRoundedRect(QRect(option.rect.x()+xpad,option.rect.y(),ICON_SIZE,ICON_SIZE), 3.0, 3.0, Qt.AbsoluteSize)
        painter.restore()
        
        pixmap = iicon.pixmap(ICON_SIZE)
        
        if ITEM_WIDTH > st.size().width():
            xpad = (ITEM_WIDTH - ICON_SIZE) / 2
        else:
            xpad = (st.size().width() - ICON_SIZE) / 2
        
        painter.drawPixmap(option.rect.x() + xpad,option.rect.y(), -1,-1, pixmap,0,0,-1,-1)
        
        txpad = 0
        if ITEM_WIDTH > st.size().width():
            txpad = (ITEM_WIDTH - st.size().width()) / 2
        
        painter.drawStaticText(option.rect.x() + txpad, option.rect.y()+ICON_SIZE, st)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
    def sizeHint(self, option, index):
        dicon = ICON_SIZE
        st1 = index.data()
        st = QStaticText(st1)
        dtext = st.size()
        if ITEM_WIDTH > dtext.width():
            X = ITEM_WIDTH
        else:
            X = dtext.width()
        Y = ICON_SIZE + dtext.height()
        return QSize(int(X),int(Y))

class openDisks(QBoxLayout):
    def __init__(self, window, parent=None):
        super(openDisks, self).__init__(QBoxLayout.TopToBottom, parent)
        self.window = window
        self.selected_index = None
        self.setContentsMargins(QMargins(0,0,0,0))
        
        global TCOMPUTER
        if TCOMPUTER == 0:
            page = QWidget()
            #
            ilist = QListView()
            ilist.setViewMode(QListView.IconMode)
            ilist.setSpacing(50)
            ilist.setMovement(QListView.Static)
            ilist.setFlow(QListView.LeftToRight)
            # the background color
            if USE_BACKGROUND_COLOUR == 1:
                palette = ilist.palette()
                palette.setColor(QPalette.Base, QColor(ORED,OGREEN,OBLUE))
                ilist.setPalette(palette)
            
            ilist.clicked.connect(self.flist)
            ilist.doubleClicked.connect(self.flist2)
            
            self.addWidget(ilist, 0)
            
            ilist.setEditTriggers(QAbstractItemView.NoEditTriggers)
            ilist.setResizeMode(QListView.Adjust)
            self.model = QStandardItemModel(ilist)
            ilist.setModel(self.model)
            ilist.setItemDelegate(MediaItemDelegate())
            #
            obox = QBoxLayout(QBoxLayout.LeftToRight)
            obox.setContentsMargins(QMargins(5,5,5,5))
            self.insertLayout(1, obox)
            layout = QFormLayout()
            layout.setLabelAlignment(Qt.AlignRight)
            #
            self.label1 = QLabel("Name")
            self.label2 = QLabel("Type")
            self.label4 = QLabel("Media")
            self.label5 = QLabel("Size")
            self.label3 = QLabel("Trash")
            self.label6 = clabel()
            self.label7 = QLabel("")
            self.label9 = QLabel("")
            self.label10 = QLabel("")
            self.label8 = QLabel("")
            layout.addRow(self.label1, self.label6)
            layout.addRow(self.label2, self.label7)
            layout.addRow(self.label4, self.label9)
            layout.addRow(self.label5, self.label10)
            layout.addRow(self.label3, self.label8)
            #
            obox.insertLayout(1, layout, 1)
            box2 = QBoxLayout(QBoxLayout.TopToBottom)
            box2.setContentsMargins(QMargins(0,0,0,0))
            obox.insertLayout(1, box2, 0)
            #
            self.button1 = QPushButton("M")
            self.button1.setToolTip("Mount/Unmount the device")
            self.button1.clicked.connect(lambda:self.ftbutton1(self.selected_index))
            box2.addWidget(self.button1)
            #
            self.button2 = QPushButton("E")
            self.button2.setToolTip("Eject the device")
            self.button2.clicked.connect(lambda:self.ftbutton2(self.selected_index))
            box2.addWidget(self.button2)
            #
            self.button3 = QPushButton("P")
            self.button3.setToolTip("Turn off the device")
            self.button3.clicked.connect(lambda:self.ftbutton3(self.selected_index))
            box2.addWidget(self.button3)
            #
            self.button4 = QPushButton("Trash")
            self.button4.setToolTip("Recycle Bin")
            self.button4.clicked.connect(lambda:self.ftbutton4(self.selected_index))
            box2.addWidget(self.button4)

            self.button1.setEnabled(False)
            self.button2.setEnabled(False)
            self.button3.setEnabled(False)
            self.button4.setEnabled(False)

            self.window.mtab.addTab(page, "Media")

            page.setLayout(self)
            self.window.mtab.setCurrentIndex(self.window.mtab.count()-1)
            #
            TCOMPUTER = 1
            #
            list_cDisks = media_module.listcDisk().plist()
            self.fpopmodel(list_cDisks)
            
    def fpopmodel(self, list_cDisks):
        for ddev in list_cDisks:
            item = QStandardItem(15,1)
            ddevice = ddev.device
            drive_type = ddev.drive_type
            llabel = ddev.label
            dvendor = ddev.vendor
            dmodel = ddev.model
            if llabel:
                disk_name = llabel
            else:
                disk_name = dvendor + dmodel
            
            ssize = ddev.size
            ffilesystem = ddev.filesystem
            read_only = ddev.read_only
            mount_point = ddev.mount_point
            media_type = ddev.media_type
            can_eject = ddev.can_eject
            can_poweroff = ddev.can_poweroff
            connection_bus = ddev.connection_bus
            mdrive = ddev.drive

            item.setData(os.path.basename(disk_name), Qt.DisplayRole)
            item.setData(ddevice, Qt.UserRole)
            item.setData(drive_type, Qt.UserRole+1)
            item.setData(ssize, Qt.UserRole+2)
            item.setData(ffilesystem, Qt.UserRole+3)
            item.setData(read_only, Qt.UserRole+4)
            item.setData(mount_point, Qt.UserRole+5)
            item.setData(media_type, Qt.UserRole+6)
            item.setData(can_eject, Qt.UserRole+7)
            item.setData(can_poweroff, Qt.UserRole+8)
            item.setData(connection_bus, Qt.UserRole+9)
            item.setData(dvendor, Qt.UserRole+10)
            item.setData(dmodel, Qt.UserRole+11)
            item.setData(llabel, Qt.UserRole+12)
            item.setData(mdrive, Qt.UserRole+13)
            
            dicon = self.getDevice(media_type, drive_type, connection_bus)
            item.setIcon(QIcon(dicon))
            
            self.model.appendRow(item)

    def ftbutton1(self, index):
        if index == None:
            return
        ddevice = index.data(Qt.UserRole)
        ddev = ddevice.split("/")[-1]
        mount_point = media_module.getDevMounted(ddev).fgetdevmounted()

        if mount_point == "N":
            ret = media_module.mountDevice(ddev, 'Mount').fmount()
            if mount_point == -1:
                MyDialog("Info", "The device cannot be mounted.")
                return 
            #
            self.button1.setText("Unmount")
             
            self.button2.setEnabled(False)
            self.button3.setEnabled(False)
            if index.data(Qt.UserRole+4) == 1:
                self.label8.setText("Unavailable")
                self.button4.setEnabled(False)
            else:
                self.button4.setEnabled(True)
        else:
            ret = media_module.mountDevice(ddev, 'Unmount').fmount()
            
            if ret == -1:
                MyDialog("Info", "Device busy.")
                return
            
            self.button1.setText("Mount")
            
            can_eject = index.data(Qt.UserRole+7)
            if can_eject == 1:
                self.button2.setEnabled(True)
            
            self.button3.setEnabled(False)
            self.button4.setEnabled(False)

    def ftbutton2(self, index):
        if index == None:
            return
        mdrive = index.data(Qt.UserRole+13)
        ret = media_module.devEject(mdrive).fdeveject()
        if ret == -1:
            MyDialog("Error", "The device cannot be ejected.")
            return
        self.button1.setEnabled(False)
        self.button2.setEnabled(False)
        can_poweroff = index.data(Qt.UserRole+8)
        if can_poweroff:
            self.button3.setEnabled(True)
        
    def ftbutton3(self, index):
        if index == None:
            return
        mdrive = index.data(Qt.UserRole+13)
        ret = media_module.devPoweroff(mdrive).fdevpoweroff()
        if ret == -1:
            MyDialog("Error", "The device cannot be turned off.")
        self.button3.setEnabled(False)
        self.model.removeRow(index.row())

        num_model_row = self.model.rowCount()
        #
        for inx in range(num_model_row):
            iindex = self.model.index(inx, 0)
            ddrive = iindex.data(Qt.UserRole+13)
            if ddrive == mdrive:
                self.model.removeRow(iindex.row())

    def ftbutton4(self, index):
        if index == None:
            return
        ddevice = index.data(Qt.UserRole)
        ddev = ddevice.split("/")[-1]
        mount_point = media_module.getDevMounted(ddev).fgetdevmounted()

        if not mount_point == "N":
            #
            tlist = trash_module.ReadTrash(mount_point).return_the_list()
            if tlist == -1 or tlist == -2:
                return
            if isinstance(tlist, list):
                openTrash(self.window, mount_point)

    def getDevice(self, media_type, drive_type, connection_bus):

        if connection_bus == "usb" and drive_type == 0:
            return "icons/media-removable.svg"
        
        if "flash" in media_type:
            return "icons/media-flash.svg"
        elif "optical" in media_type:
            return "icons/media-optical.svg"
        
        if drive_type == 0:
            return "icons/drive-harddisk.svg"
        
        elif drive_type == 5:
            return "icons/media-optical.svg"
        
        return "icons/drive-harddisk.svg"

    def nameMedia(self, media_type, drive_type, ddevice):
        if "loop" in ddevice:
            return "Loop device"
        
        if "optical" in media_type:
            return "DVD/CD Rom"
        
        if drive_type == 0:
            return "Disk"
        elif drive_type == 5:
            return "DVD/CD Rom"
        
        return "Unknown Disk"

    def flist(self, index):
        
        self.selected_index = index
        if not index.data(Qt.UserRole+12):
            npart = index.data(Qt.UserRole).split("/")[-1]
            if index.data(Qt.UserRole+10) != "N" and index.data(Qt.UserRole+11) != "N":
                self.label6.setText(npart+" - "+index.data(Qt.UserRole+10)+" "+index.data(Qt.UserRole+11), self.window.width())
            else:
                self.label6.setText(npart, self.window.width())
        else:
            if index.data(Qt.UserRole+10) == "N" and index.data(Qt.UserRole+11) == "N":
                self.label6.setText(index.data(Qt.DisplayRole), self.window.width())
            else:
                self.label6.setText(index.data(Qt.DisplayRole)+" - "+index.data(Qt.UserRole+10)+" "+index.data(Qt.UserRole+11), self.window.width())
            
        iro = index.data(Qt.UserRole+4)
        if iro == 0:
            self.label7.setText(index.data(Qt.UserRole+3))
        elif iro == 1:
            self.label7.setText(index.data(Qt.UserRole+3)+" - "+"Read Only")
        mmedia = self.nameMedia(index.data(Qt.UserRole+6), index.data(Qt.UserRole+1), index.data(Qt.UserRole))
        self.label9.setText(mmedia)
        
        ssize = self.convert_size(index.data(Qt.UserRole+2))
        ddevice = index.data(Qt.UserRole)
        ddev = ddevice.split("/")[-1]
        mount_point = media_module.getDevMounted(ddev).fgetdevmounted()
        if mount_point != "N":
            if iro == 0:
                storageInfo = QStorageInfo(mount_point)
                sizeFree = storageInfo.bytesFree()
                self.label10.setText("{} - Free {}".format(ssize, self.convert_size(sizeFree)))
            else:
                self.label10.setText(ssize)
        else:
            self.label10.setText(ssize)
        
        is_trash_empty = trash_module.TrashIsEmpty(mount_point).isEmpty()
        if is_trash_empty == 0:
            if iro == 0:
                self.label8.setText("Empty")
            elif iro == 1:
                self.label8.setText("Unavailable")
        elif is_trash_empty == 1:
            self.label8.setText("Not empty")
        
        self.button1.setEnabled(True)
        self.button2.setEnabled(True)
        self.button3.setEnabled(True)
        self.button4.setEnabled(True)
        
        if mount_point == "N":
            self.button1.setText("Mount")
            can_eject = index.data(Qt.UserRole+7)
            list_ddrive = media_module.driveList().drlist()
            if can_eject == 1:
                
                ddev = index.data(Qt.UserRole).split("/")[-1]
                list_ddev = media_module.diskList().dlist()
                ddev_block = os.path.join('/org/freedesktop/UDisks2/block_devices', ddev[:-1])
                ddev_block1 = os.path.join('/org/freedesktop/UDisks2/block_devices', ddev)
                
                if ddev_block in list_ddev:
                    if not ddev_block1 in list_ddev:
                        self.button2.setEnabled(False)
                        can_poweroff = index.data(Qt.UserRole+8)
                        if can_poweroff:
                            self.button3.setEnabled(True)
                        else:
                            self.button3.setEnabled(False)
                    else:
                        self.button2.setEnabled(True)
                        self.button3.setEnabled(False)
                
                can_poweroff = index.data(Qt.UserRole+8)
                if can_poweroff == 0:
                    self.button3.setEnabled(False)
            else:
                self.button2.setEnabled(False)
                self.button3.setEnabled(False)
            
            self.button4.setEnabled(False)
        else:
            self.button1.setText("Unmount")
            self.button2.setEnabled(False)
            self.button3.setEnabled(False)
            if mount_point == "/" or mount_point == "/boot/efi" or mount_point[0:6] == "/home/":
                self.button1.setEnabled(False)
                self.button4.setEnabled(False)
            
            if iro == 1:
                self.label8.setText("Unavailable")
                self.button4.setEnabled(False)

    def flist2(self, index):

        ddevice = index.data(Qt.UserRole)
        ddev = ddevice.split("/")[-1]
        mount_point = media_module.getDevMounted(ddev).fgetdevmounted()
        read_only = index.data(Qt.UserRole+4)
        if mount_point != "N":
            if mount_point == "/" or mount_point == "/boot/efi" or mount_point[0:6] == "/home/":
                return
            else:
                if read_only == 0:
                    self.window.openDir(mount_point, 1)
                else:
                    self.window.openDir(mount_point, 2)
        else:
            MyDialog("Info", "This device is not mounted.")

    def convert_size(self, fsize2):
        
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        elif fsize2//1099511627776 == 0:
            sfsize = str(round(fsize2/1073741824, 3))+" GiB"
        else:
            sfsize = str(round(fsize2/1099511627776, 3))+" GiB"
        
        return sfsize              


class clabel(QLabel):
    
    def __init__(self, parent=None):
        super(clabel, self).__init__(parent)
    
    def setText(self, text, wWidth):
        
        boxWidth = wWidth-350*QApplication.instance().devicePixelRatio()
        font = self.font()
        metric = QFontMetrics(font)
        string = text
        ctemp = ""
        ctempT = ""
        for cchar in string:
            ctemp += str(cchar)
            width = metric.width(ctemp)
            if width < boxWidth:
                ctempT += str(cchar)
                continue
            else:
                ctempT += str(cchar)
                ctempT += "\n"
                ctemp = str(cchar)
        
        ntext = ctempT
        
        super(clabel, self).setText(ntext)


class thumbThread(threading.Thread):
    
    def __init__(self, fpath, fileModel, listview):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.fpath = fpath
        self.fileModel = fileModel
        self.listview = listview
    
    def run(self):
        list_dir = os.listdir(self.fpath)
        
        while not self.event.is_set():
            for iitem in list_dir:
                item_fpath = os.path.join(self.fpath, iitem)

                if os.path.exists(item_fpath):
                    
                    if stat.S_ISREG(os.stat(item_fpath).st_mode):
                        
                        hmd5 = "Null"
                        
                        imime = QMimeDatabase().mimeTypeForFile(iitem, QMimeDatabase.MatchDefault)
                        hmd5 = create_thumbnail(item_fpath, imime.name())

                        self.event.wait(0.05)
            
            self.event.set()
        
        self.fileModel.setIconProvider(IconProvider())
        self.listview.viewport().update()


# find the applications installed for a given mimetype
class getAppsByMime():
    def __init__(self, path):
        self.path = path
    
    def appByMime(self):
        listPrograms = []
        imimetype = QMimeDatabase().mimeTypeForFile(self.path, QMimeDatabase.MatchDefault).name()
        if imimetype != "application/x-zerosize":
            mimetype = imimetype
        else:
            mimetype = "text/plain"
        # the action for the mimetype also depends on the file mimeapps.list in the home folder 
        #lAdded,lRemoved,lDefault = self.addMime(mimetype)
        lAdded,lRemoved = self.addMime(mimetype)
        #
        for ddir in xdgDataDirs:
            applicationsPath = os.path.join(ddir, "applications")
            if os.path.exists(applicationsPath):
                desktopFiles = os.listdir(applicationsPath)
                for idesktop in desktopFiles:
                    if idesktop.endswith(".desktop"):
                        # skip the removed associations
                        if idesktop in lRemoved:
                            continue
                        desktopPath = os.path.join(ddir+"/applications", idesktop)
                        if mimetype in DesktopEntry(desktopPath).getMimeTypes():
                            mimeProg2 = DesktopEntry(desktopPath).getExec()
                            
                            if mimeProg2:
                                mimeProg = mimeProg2.split()[0]
                            else:
                                return
                            retw = shutil.which(mimeProg)
                            if retw is not None:
                                if os.path.exists(retw):
                                    listPrograms.append(retw)
                                    try:
                                        progName = DesktopEntry(desktopPath).getName()
                                        if progName != "":
                                            listPrograms.append(progName)
                                        else:
                                            listPrograms.append("None")
                                    except:
                                        listPrograms.append("None")
        # 
        # from the lAdded list
        for idesktop in lAdded:
            # skip the removed associations
            if idesktop in lRemoved:
                continue
            desktopPath = ""
            #
            # check if the idesktop is in xdgDataDirs - use it if any
            for ddir in xdgDataDirs:
                applicationsPath = os.path.join(ddir, "applications")
                if idesktop in os.listdir(applicationsPath):
                    desktopPath = os.path.join(applicationsPath, idesktop)
            #
            mimeProg2 = DesktopEntry(desktopPath).getExec()
            if mimeProg2:
                mimeProg = mimeProg2.split()[0]
            else:
                return
            retw = shutil.which(mimeProg)
            if retw is not None:
                if os.path.exists(retw):
                    listPrograms.append(retw)
                    try:
                        progName = DesktopEntry(desktopPath).getName()
                        if progName != "":
                            listPrograms.append(progName)
                        else:
                            listPrograms.append("None")
                    except:
                         listPrograms.append("None")
        #
        return listPrograms

    # function that return mimetypes added, removed in the mimeappss.list
    def addMime(self, mimetype):
        
        # mimeapps.list can have up to three not mandatory sectors
        intest = ["[Added Associations]","[Removed Associations]","[Default Applications]"]

        added = []
        removed = []
        default = []

        lista = []
        
        # load the file as list
        mimeappsPath = os.path.join(os.path.expanduser("~"),".config","mimeapps.list")
        # 
        if not os.path.exists(mimeappsPath):
            #return [],[],[]
            return [],[]
        with open(mimeappsPath, "r") as f:
            lista = f.readlines()
        
        # position in the list of each member of intest
        aIndex = -1
        rIndex = -1 
        dIndex = -1 

        if "[Added Associations]\n" in lista:
            aIndex = lista.index("[Added Associations]\n")
        if "[Removed Associations]\n" in lista:
            rIndex = lista.index("[Removed Associations]\n")
        if "[Default Applications]\n" in lista:
            dIndex = lista.index("[Default Applications]\n")

        # in list l if not -1 (means empty)
        l = []
        for el in [aIndex,rIndex,dIndex]:
            if el != -1:
                l.append(el)
        # sorting l
        l.sort()

        # it depends on the number of elements in l
        l1 = []
        l2 = []
        l3 = []
        if len(l) == 1:
            l1 = lista[l[0]:]
        elif len(l) == 2:
            l1 = lista[l[0]:l[1]]
            l2 = lista[l[1]:]
        elif len(l) == 3:
            l1 = lista[l[0]:l[1]]
            l2 = lista[l[1]:l[2]]
            l3 = lista[l[2]:]
        
        # lists of mimetypes added or removed
        lAdded = []
        lRemoved = []
        lDefault = []

        # search for the mimetype in the lists
        for el in l1:
            if mimetype in el:
                ret = self.popList(l1, mimetype)
                if ret[0] == "A":
                    lAdded = self.delNull(ret[1])
                elif ret[0] == "R":
                    lRemoved = self.delNull(ret[1])
                elif ret[0] == "D":
                    lDefault = self.delNull(ret[1])
        for el in l2:
            if mimetype in el:
                ret = self.popList(l2, mimetype)
                if ret[0] == "A":
                    lAdded = self.delNull(ret[1])
                elif ret[0] == "R":
                    lRemoved = self.delNull(ret[1])
                elif ret[0] == "D":
                    lDefault = self.delNull(ret[1])
        for el in l3:
             if mimetype in el:
                ret = self.popList(l3, mimetype)
                if ret[0] == "A":
                    lAdded = self.delNull(ret[1])
                elif ret[0] == "R":
                    lRemoved = self.delNull(ret[1])
                elif ret[0] == "D":
                    lDefault = self.delNull(ret[1])
        #
        #return lAdded,lRemoved,lDefault
        # lDefault is not necessary
        return lAdded,lRemoved

    # make the lists
    def popList(self, l, mimetype):
        # search for the mimetype in the lists
        for el in l:
            if mimetype in el:
                if l[0].strip("\n") == "[Added Associations]":
                    lAdded = el.replace(mimetype+"=","").strip("\n").split(";")
                    return ["A",lAdded]
                elif l[0].strip("\n") == "[Removed Associations]":
                    lRemoved = el.replace(mimetype+"=","").strip("\n").split(";")
                    return ["R",lRemoved]
                elif l[0].strip("\n") == "[Default Applications]":
                    lDefault = el.replace(mimetype+"=","").strip("\n").split(";")
                    return ["D",lDefault]
                else:
                    return "NONE"

    # skip the null elements in the list
    def delNull(self,e):
        return [i for i in e if i != ""]


# find the default application for a given mimetype if any
class getDefaultApp():
    
    def __init__(self, path):
        self.path = path
        
    def defaultApplication(self):
        ret = shutil.which("xdg-mime")
        if ret:
            imime = QMimeDatabase().mimeTypeForFile(self.path, QMimeDatabase.MatchDefault).name()
            #
            if imime in ["application/x-zerosize", "application/x-trash"]:
                mimetype = "text/plain"
            else:
                mimetype = imime
            #
            try:
                associatedDesktopProgram = subprocess.check_output([ret, "query", "default", mimetype], universal_newlines=False).decode()
            except Exception as E:
                return "None"
            
            if associatedDesktopProgram:

                for ddir in xdgDataDirs:
                    if ddir[-1] == "/":
                        ddir = ddir[:-1]
                    desktopPath = os.path.join(ddir+"/applications", associatedDesktopProgram.strip())
                    
                    if os.path.exists(desktopPath):
                        applicationName2 = DesktopEntry(desktopPath).getExec()
                        if applicationName2:
                            applicationName = applicationName2.split()[0]
                        else:
                            return "None"
                        applicationPath = shutil.which(applicationName)
                        if applicationPath:
                            if os.path.exists(applicationPath):
                                return applicationPath
                            else:
                                MyDialog("Error", "{} cannot be found".format(applicationPath))
                        else:
                            return "None"
                #
                # no apps found
                return "None"
            else:
                return "None"
        else:
            MyDialog("Error", "xdg-mime cannot be found")


class LView(QBoxLayout):
    
    def __init__(self, LVDIR, window, flag, parent=None):
        super(LView, self).__init__(QBoxLayout.TopToBottom, parent)
        self.window = window
        self.flag = flag
        self.setContentsMargins(QMargins(0,0,0,0))
        
        self.lvDir = ""
        self.lvFile = ""
        if os.path.isdir(LVDIR):
            self.lvDir = LVDIR
        else:
            self.lvDir = os.path.dirname(LVDIR)
            self.lvFile = os.path.basename(LVDIR)
        
        self.fmf = 0
        self.selection = None
        self.listview = MyQlist()

        self.listview.setViewMode(QListView.IconMode)
        
        # the background color
        if USE_BACKGROUND_COLOUR == 1:
            palette = self.listview.palette()
            palette.setColor(QPalette.Base, QColor(ORED,OGREEN,OBLUE))
            self.listview.setPalette(palette)
        
        self.listview.setSpacing(ITEM_SPACE)
        self.listview.setSelectionMode(self.listview.ExtendedSelection)
        self.listview.setResizeMode(QListView.Adjust)
        self.addWidget(self.listview, 1)
        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.System)
        self.listview.setModel(self.fileModel)
        self.listview.setItemDelegate(itemDelegate())
        self.fileModel.setIconProvider(IconProvider())
        #
        path = self.lvDir
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
        self.listview.clicked.connect(self.singleClick)
        self.listview.doubleClicked.connect(self.doubleClick)

        self.label1 = QLabel()
        self.label2 = QLabel()
        self.label3 = QLabel()
        self.label4 = QLabel()
        self.label5 = clabel()
        self.label5.setWordWrap(True)
        self.label5.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label6 = clabel()
        self.label6.setWordWrap(True)
        self.label6.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label7 = QLabel()
        self.label8 = QLabel()

        self.layout = QFormLayout()
        self.page1UI()

        self.listview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listview.customContextMenuRequested.connect(self.onRightClick)

        self.listview.selectionModel().selectionChanged.connect(self.lselectionChanged)
        
        self.tabLabels()
        
        if USE_TRASH:
            self.clickable2(self.listview).connect(self.itemsToTrash)
        elif USE_DELETE:
            self.clickable2(self.listview).connect(self.fdeleteAction)
        
        if USE_THUMB == 1:
            thread = thumbThread(self.lvDir, self.fileModel, self.listview)
            thread.start()
        
    def itemsToTrash(self):
        if self.selection:
            self.ftrashAction()
    
    def clickable2(self, widget):

        class Filter(QObject):
            
            clicked = pyqtSignal()
            
            def eventFilter(self, obj, event):
                if obj == widget:
                    if event.type() == QEvent.KeyRelease:
                        if event.key() == Qt.Key_Delete:
                            self.clicked.emit()
                
                return False
        
        filter = Filter(widget)
        widget.installEventFilter(filter)
        return filter.clicked
    
    def tabLabels(self):
        self.label1.setText("Path")
        self.label5.setText(self.lvDir, self.window.size().width())
        self.label2.setText("Items")
        num_items, hidd_items = self.num_itemh()
        self.label6.setText(str(num_items), self.window.size().width())
        self.label3.setText("Hiddens")
        self.label7.setText(str(hidd_items))
        self.label4.setText("")
        self.label8.setText("")

    def num_itemh(self):
        file_folder = os.listdir(self.lvDir)
        total_item = len(file_folder)
        for el in file_folder[:]:
            if el.startswith("."):
              file_folder.remove(el)
        visible_item = len(file_folder)
        hidden_item = total_item - visible_item
        return visible_item, hidden_item
    
    def page1UI(self):
        self.layout.setLabelAlignment(Qt.AlignRight)
        self.layout.addRow(self.label1, self.label5)
        self.layout.addRow(self.label2, self.label6)
        self.layout.addRow(self.label3, self.label7)
        self.layout.addRow(self.label4, self.label8)

        gbox = QBoxLayout(QBoxLayout.LeftToRight)
        gbox.setContentsMargins(QMargins(15,5,5,5))
        gbox.insertLayout(1, self.layout, 1)
        vbbox = QBoxLayout(QBoxLayout.TopToBottom)
        upbtn = QPushButton(QIcon.fromTheme("up"), "U")
        upbtn.setToolTip("go up")
        upbtn.clicked.connect(self.upButton)
        vbbox.addWidget(upbtn)
        invbtn = QPushButton("I")
        invbtn.clicked.connect(self.finvbtn)
        invbtn.setToolTip("Invert the selection")
        vbbox.addWidget(invbtn)
        hidbtn = QPushButton("H")
        hidbtn.clicked.connect(self.fhidbtn)
        hidbtn.setToolTip("Hidden Items")
        vbbox.addWidget(hidbtn)
        gbox.insertLayout(2, vbbox, 0)

        self.insertLayout(1, gbox)
    
    def singleClick(self, index):
        time.sleep(0.2)
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        file_info = QFileInfo(path)
        self.label1.setText("Name")
        self.label5.setText(file_info.fileName(), self.window.size().width())
        self.label2.setText("Path")
        
        if os.path.islink(path):
            if os.path.exists(os.path.realpath(path)):
                self.label6.setText("link to {}".format(os.path.realpath(path)), self.window.size().width())
            else:
                self.label6.setText("broken link to {}".format(os.readlink(path)), self.window.size().width())
        else:
            self.label6.setText(self.lvDir, self.window.size().width())
        
        self.label3.setText("Type")
        imime = QMimeDatabase().mimeTypeForFile(path, QMimeDatabase.MatchDefault)
        self.label7.setText(imime.name())
        
        if not os.path.exists(path):
            if os.path.islink(path):
                self.label4.setText("Size")
                self.label8.setText("(Broken Link)")
                return
            else:
                self.label4.setText("Size")
                self.label8.setText("Unrecognizable")
                return
        if os.path.isfile(path):
            self.label4.setText("Size")
            if os.access(path, os.R_OK):
                self.label8.setText(self.convert_size(file_info.size()))
            else:
                self.label8.setText("(Not readable)")
        elif os.path.isdir(path):
            self.label4.setText("Items")
            if os.access(path, os.R_OK):
                self.label8.setText(str(QDir(path).count()-2))
            else:
                self.label8.setText("(Not readable)")
        
        else:
            self.label4.setText("")
            self.label8.setText("")

    def doubleClick(self, index):
        global MMTAB
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        if os.path.isdir(path):
            if os.access(path, os.R_OK):
                try:
                    self.listview.clearSelection()
                    self.lvDir = path
                    MMTAB.setTabText(MMTAB.currentIndex(), os.path.basename(self.lvDir))
                    MMTAB.setTabToolTip(MMTAB.currentIndex(), self.lvDir)
                    self.listview.setRootIndex(self.fileModel.setRootPath(path))
                    self.tabLabels()
                    
                except Exception as E:
                    MyDialog("ERROR", str(E))
            else:
                MyDialog("ERROR", path+"\n\n   Not readable")
        elif os.path.isfile(path):
            perms = QFileInfo(path).permissions()
            if perms & QFile.ExeOwner:
                imime = QMimeDatabase().mimeTypeForFile(path, QMimeDatabase.MatchDefault).name()
                if imime == "application/x-sharedlib":
                    ret = execfileDialog(path, 1).getValue()
                else:
                    ret = execfileDialog(path, 0).getValue()
                
                if ret == 2:
                    try:
                        subprocess.Popen(path, shell=True)
                    except Exception as E:
                        MyDialog("Error", str(E))
                    finally:
                        return
                elif ret == -1:
                    return

            defApp = getDefaultApp(path).defaultApplication()
            
            if defApp != "None":
                try:
                    subprocess.Popen([defApp, path])
                except Exception as E:
                    MyDialog("Error", str(E))
            else:
                MyDialog("Error", "No programs found.")
     
    def lselectionChanged(self):
        self.selection = self.listview.selectionModel().selectedIndexes()
        if len(self.selection) == 1:
            return
        if self.selection == []:
            self.tabLabels()
        else:
            total_size = 0
            for iitem in self.selection:
                path = self.fileModel.fileInfo(iitem).absoluteFilePath()
                #
                if os.path.isfile(path):
                    total_size += QFileInfo(path).size()
                elif os.path.isdir(path):
                    total_size += self.folder_size(path)
            self.label1.setText("Selected Items")
            self.label5.setText(str(len(self.selection)), self.window.size().width())
            self.label2.setText("Size")
            self.label6.setText(str(self.convert_size(total_size)), self.window.size().width())
            self.label3.setText("")
            self.label7.setText("")
            self.label4.setText("")
            self.label8.setText("")
    
    # mouse right click on the pointed item
    def onRightClick(self, position):
        if self.flag == 0:
            return
        time.sleep(0.2)
        pointedItem = self.listview.indexAt(position)
        vr = self.listview.visualRect(pointedItem)
        pointedItem2 = self.listview.indexAt(QPoint(vr.x(),vr.y()))

        # the items
        if vr:
            itemName = self.fileModel.data(pointedItem2, Qt.DisplayRole)
            menu = QMenu("Menu", self.listview)
            menu.setFont(thefont)
            
            if self.selection != None:
                if len(self.selection) == 1:
                    if os.path.isfile(os.path.join(self.lvDir, itemName)):
                        subm_openwithAction= menu.addMenu("Open with...")
                        subm_openwithAction.setFont(thefont)
                        listPrograms = getAppsByMime(os.path.join(self.lvDir, itemName)).appByMime()
                        
                        ii = 0
                        defApp = getDefaultApp(os.path.join(self.lvDir, itemName)).defaultApplication()
                        progActionList = []
                        if listPrograms:
                            for iprog in listPrograms[::2]:
                                if iprog == defApp:
                                    progActionList.append(QAction("{} - {} (Default)".format(os.path.basename(iprog), listPrograms[ii+1]), self))
                                    progActionList.append(iprog)
                                else:
                                    progActionList.append(QAction("{} - {}".format(os.path.basename(iprog), listPrograms[ii+1]), self))
                                    progActionList.append(iprog)
                                ii += 2
                            ii = 0
                            for paction in progActionList[::2]:
                                paction.triggered.connect(lambda checked, index=ii:self.fprogAction(progActionList[index+1], os.path.join(self.lvDir, itemName)))
                                subm_openwithAction.addAction(paction)
                                ii += 2
                        subm_openwithAction.addSeparator()
                        otherAction = QAction("Other Program")
                        otherAction.triggered.connect(lambda:self.fotherAction(os.path.join(self.lvDir, itemName)))
                        subm_openwithAction.addAction(otherAction)
                        #
                        menu.addSeparator()
                    elif os.path.isdir(os.path.join(self.lvDir, itemName)):
                        newtabAction = QAction("Open in a new tab")
                        newtabAction.triggered.connect(lambda:self.fnewtabAction(os.path.join(self.lvDir, itemName), self.flag))
                        menu.addAction(newtabAction)
                        menu.addSeparator()
            
            copyAction = QAction("Copy", self)
            copyAction.triggered.connect(self.fcopyAction)
            menu.addAction(copyAction)

            if self.flag != 2:
                copyAction = QAction("Cut", self)
                copyAction.triggered.connect(self.fcutAction)
                menu.addAction(copyAction)

            if USE_TRASH:
                if self.flag != 2:
                    if isXDGDATAHOME:
                        trashAction = QAction("Trash", self)
                        trashAction.triggered.connect(self.ftrashAction)
                        menu.addAction(trashAction)
            
            # delete function
            if USE_DELETE:
                if self.flag != 2:
                    deleteAction = QAction("Delete", self)
                    deleteAction.triggered.connect(self.fdeleteAction)
                    menu.addAction(deleteAction)
            
            if self.flag != 2:
                if len(self.selection) == 1:
                    menu.addSeparator()
                    renameAction = QAction("Rename", self)
                    ipath = self.fileModel.fileInfo(self.selection[0]).absoluteFilePath()
                    renameAction.triggered.connect(lambda:self.frenameAction(ipath))
                    menu.addAction(renameAction)
            
            menu.addSeparator()
            subm_customAction = menu.addMenu("Custom Actions")
            subm_customAction.setFont(thefont)

            if len(list_custom_modules) > 0:
                listActions = []
                for el in list_custom_modules:
                    if el.mmodule_type(self) == 1 and len(self.selection) == 1:
                        icustomAction = QAction(el.mmodule_name(), self)
                        listActions.append(icustomAction)
                        listActions.append(el)
                        listActions.append(1)
                    elif el.mmodule_type(self) == 2 and len(self.selection) > 1:
                        icustomAction = QAction(el.mmodule_name(), self)
                        listActions.append(icustomAction)
                        listActions.append(el)
                        listActions.append(2)
                    elif el.mmodule_type(self) == 3 and len(self.selection) > 0:
                        icustomAction = QAction(el.mmodule_name(), self)
                        listActions.append(icustomAction)
                        listActions.append(el)
                        listActions.append(3)
                    elif el.mmodule_type(self) == 5:
                        icustomAction = QAction(el.mmodule_name(), self)
                        listActions.append(icustomAction)
                        listActions.append(el)
                        listActions.append(5)

                ii = 0
                for paction in listActions[::3]:
                    paction.triggered.connect(lambda checked, index=ii:self.ficustomAction(listActions[index+1], listActions[index+2]))
                    subm_customAction.addAction(paction)
                    ii += 3

            menu.addSeparator()
            if len(self.selection) == 1:
                ipath = self.fileModel.fileInfo(self.selection[0]).absoluteFilePath()
                if os.path.exists(ipath):
                    propertyAction = QAction("Property", self)
                    propertyAction.triggered.connect(lambda:self.fpropertyAction(ipath))
                    menu.addAction(propertyAction)
            #
            elif len(self.selection) > 1:
                propertyAction = QAction("Property", self)
                propertyAction.triggered.connect(self.fpropertyActionMulti)
                menu.addAction(propertyAction)
            #
            menu.exec_(self.listview.mapToGlobal(position))
        ## background
        else:
            self.listview.clearSelection()
            menu = QMenu("Menu", self.listview)
            menu.setFont(thefont)

            if self.flag != 2:
                newFolderAction = QAction("New Folder", self)
                newFolderAction.triggered.connect(self.fnewFolderAction)
                menu.addAction(newFolderAction)
                newFileAction = QAction("New File", self)
                newFileAction.triggered.connect(self.fnewFileAction)
                menu.addAction(newFileAction)

                if shutil.which("xdg-user-dir"):
                    templateDir = subprocess.check_output(["xdg-user-dir", "TEMPLATES"], universal_newlines=False).decode().strip()
                    if not os.path.exists(templateDir):
                        optTemplateDir = os.path.join(os.path.expanduser("~"), "Templates")
                        if os.path.exists(optTemplateDir):
                           templateDir = optTemplateDir
                        else:
                            templateDir = None

                    if templateDir:
                        if os.path.exists(templateDir):
                            menu.addSeparator()
                            subm_templatesAction= menu.addMenu("Templates")
                            subm_templatesAction.setFont(thefont)
                            listTemplate = os.listdir(templateDir)

                            progActionList = []
                            for ifile in listTemplate:
                                progActionList.append(QAction(ifile))
                                progActionList.append(ifile)
                            ii = 0
                            for paction in progActionList[::2]:
                                paction.triggered.connect(lambda checked, index=ii:self.ftemplateAction(progActionList[index+1]))
                                subm_templatesAction.addAction(paction)
                                ii += 2
            
            if self.flag != 2:
                menu.addSeparator()
                pastAction = QAction("Paste", self)
                pastAction.triggered.connect(self.fpastAction)
                menu.addAction(pastAction)
            
            if USE_PM:
                if self.flag != 2:
                    pasteNmergeAction = QAction("Paste and Merge", self)
                    pasteNmergeAction.triggered.connect(self.fpasteNmergeAction)
                    #pasteNmergeAction.setDisabled(True)
                    menu.addAction(pasteNmergeAction)

            menu.addSeparator()
            subm_customAction = menu.addMenu("Custom Actions")
            subm_customAction.setFont(thefont)

            if len(list_custom_modules) > 0:
                listActions = []
                for el in list_custom_modules:
                    if el.mmodule_type(self) == 4 or el.mmodule_type(self) == 5:
                        bcustomAction = QAction(el.mmodule_name(), self)
                        listActions.append(bcustomAction)
                        listActions.append(el)

                ii = 0
                for paction in listActions[::2]:
                    paction.triggered.connect(lambda checked, index=ii:self.fbcustomAction(listActions[index+1]))
                    subm_customAction.addAction(paction)
                    ii += 2
            #
            menu.exec_(self.listview.mapToGlobal(position))
    
    
    def fotherAction(self, itemPath):
        #
        ret = otherApp(itemPath).getValues()
        if ret == -1:
            return
        if shutil.which(ret):
            try:
                subprocess.Popen([ret, itemPath])
            except Exception as E:
                MyDialog("Error", str(E))
        else:
            MyDialog("Error", "The program\n"+ret+"\ncannot be found")
    
    
    def ftemplateAction(self, templateName):
        #
        if os.access(self.lvDir, os.W_OK): 
            ret = self.wrename3(templateName, self.lvDir)
            if ret != -1 or not ret:
                destPath = os.path.join(self.lvDir, ret)
                if not os.path.exists(destPath):
                    try:
                        iitem = open(destPath,'w')
                        iitem.close()
                    except Exception as E:
                        MyDialog("Error", str(E))
    
    
    def fprogAction(self, iprog, path):
        try:
            subprocess.Popen([iprog, path])
        except Exception as E:
            MyDialog("Error", str(E))
    
    
    def fnewtabAction(self, ldir, flag):
        #
        if os.access(ldir, os.R_OK):
            self.window.openDir(ldir, flag)
        else:
            MyDialog("Error", "Cannot open the folder: "+os.path.basename(ldir))

############# Paste and Merge section
    
    # add a suffix to the filename if the file exists at destination
    def faddSuffix(self, dest):
        if os.path.exists(dest):
            if USE_DATE == 1:
                z = datetime.datetime.now()
                #dY, dM, dD, dH, dm, ds, dms
                dts = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
                new_name = os.path.basename(dest)+dts
                dest = os.path.join(os.path.dirname(dest), new_name)
                
                return dest
            
            elif USE_DATE == 0:
                i = 1
                dir_name = os.path.dirname(dest)
                bname = os.path.basename(dest)
                dest = ""
                while i:
                    nn = bname+"_("+str(i)+")"
                    if os.path.exists(os.path.join(self.lvDir, nn)):
                        i += 1
                    else:
                        dest = os.path.join(dir_name, nn)
                        i = 0
                
                return dest
    
    def fnewList2(self, filePaths, dest_path):
        nlist = []
        # items not added
        items_skipped = ""
        for ditem in filePaths:
            # link and broken link
            if os.path.islink(ditem):
                nlist.append(ditem)
            # is file
            elif os.path.isfile(ditem):
                # can be read
                if os.access(ditem, os.R_OK):
                    nlist.append(ditem)
                else:
                    items_skipped += "{}\nNot readable.\n-----------\n".format(os.path.basename(ditem))
            # it is dir
            elif os.path.isdir(ditem):
                # can be read
                if os.access(ditem, os.R_OK):
                    nlist.append(ditem)
                else:
                    items_skipped += "{}\nNot readable.\n-----------\n".format(os.path.basename(ditem))
        
        if items_skipped != "":
            MyMessageBox("Info", "Items skipped", "", items_skipped)
        #
        return nlist

    # perform the past action: make a list and call copyItems2
    def fpasteAction2(self, atype):
        # check il the destination folder is writable
        if not os.access(self.lvDir, os.W_OK):
            MyDialog("Info", "This folder is not writable.")
            return
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData(QClipboard.Clipboard)
        
        got_quoted_data = []
        for f in mimeData.formats():
            #
            if f == "x-special/gnome-copied-files":
                data = mimeData.data(f)
                got_quoted_data = data.data().decode().split("\n")
                
                got_action = got_quoted_data[0]
                if got_action == "copy":
                    action = 1
                elif got_action == "cut":
                    action = 2
                filePaths = [unquote(x)[7:] for x in got_quoted_data[1:]]
                # a folder cannot be copied into itself or into a its subfolder
                for item in filePaths:
                    if os.path.isdir(item):
                        if item in self.lvDir:
                            MyMessageBox("Info", "A folder cannot copied into itself.\nRetry.","",item)
                            return
                #
                # html file needs its folder and viceversa
                for item in filePaths:
                    # if it is exists
                    if os.path.exists(item):
                        # if link pass
                        if os.path.islink(item):
                            continue
                        if stat.S_ISREG(os.stat(item).st_mode):
                            dir_name = os.path.dirname(item)
                            nroot, ext = os.path.splitext(os.path.basename(item))
                            if ext == ".html" or ext == ".htm":
                                fname = os.path.join(dir_name, nroot+"_files")
                                if os.path.exists(fname):
                                    if fname not in filePaths:
                                        if stat.S_ISDIR(os.stat(fname).st_mode) and os.access(fname, os.R_OK):
                                            filePaths.append(fname)
                        if stat.S_ISDIR(os.stat(item).st_mode):
                            dir_name = os.path.dirname(item)
                            base_name = os.path.basename(item)
                            nroot = base_name[:-6]
                            if not os.path.join(dir_name, nroot+".html") in filePaths:
                                if os.path.exists(os.path.join(dir_name, nroot+".html")):
                                    filePaths.append(os.path.join(dir_name, nroot+".html"))
                            if not os.path.join(dir_name, nroot+".htm") in filePaths:
                                if os.path.exists(os.path.join(dir_name, nroot+".htm")):
                                    filePaths.append(os.path.join(dir_name, nroot+".htm"))
                
                # only the selected items
                newList = self.fnewList2(filePaths, self.lvDir)
                # if cancel from the chosing dialogo do nothing
                if atype == -1:
                    MyDialog("Info", "Calcelled.")
                    return
                if newList:
                    # execute the copying copy/cut operations
                    copyItems2(action, newList, atype, self.lvDir)
    
    # the number of items to be copied with the same name at destination
    def fnumItemsSame(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData(QClipboard.Clipboard)
        for f in mimeData.formats():
            if f == "x-special/gnome-copied-files":
                data = mimeData.data(f)
                got_quoted_data = data.data().decode().split("\n")
                filePaths = [unquote(x)[7:] for x in got_quoted_data[1:]]
                # check if already present at destination
                itemsAtDest = []
                for item in filePaths:
                    tdest = os.path.join(self.lvDir, os.path.basename(item))
                    # the item exists at destination
                    if os.path.exists(tdest):
                        # it is a symlink
                        if os.path.islink(tdest):
                            # it is a link to folder
                            if os.path.isdir( str(PosixPath(tdest).absolute()) ):
                                continue
                            else:
                                itemsAtDest.append(item)
                        # it is a file or a link to file or a broken link
                        elif os.path.isfile(tdest):
                            itemsAtDest.append(item)
                        # it is a dir or a symlink to dir
                        elif os.path.isdir(tdest):
                            continue
                        # it is a different kind of item
                        else:
                            itemsAtDest.append(item)
                    # the item is a broken link
                    else:
                        if os.path.islink(tdest):
                            itemsAtDest.append(item)
                #
                return len(itemsAtDest)
                    
    # paste and merge function
    def fpasteNmergeAction(self):
        # number of items with the same name at destination
        isame = self.fnumItemsSame()
        # if the clipboard is empty
        if isame == None:
            return
        elif isame > 0:
            # ret: 1 skip - 2 overwrite - 3 new name - 4 automatic
            ret = pasteNmergeDialog(None, isame).getValue()
            #
            self.fpasteAction2(ret)
        # no items at destination when overwrite
        elif isame == 0:
            self.fpasteAction2(2)

#################
    
    def ftrashAction(self):
        if self.selection:
            list_items = []
            for item in self.selection:
                list_items.append(self.fileModel.fileInfo(item).absoluteFilePath())
            
            # if more than 30 items no list
            if len(self.selection) < ITEMSDELETED:
                dialogList = ""
                for item in list_items:
                    dialogList += os.path.basename(item)+"\n"
                ret = retDialogBox("Info", "Do you really want to move this item(s) to the trash?", "", dialogList)
            else:
                ret = retDialogBox("Info", "Do you really want to move this item(s) to the trash?", "", "Too many items.\n")
            #
            if ret.getValue():
                TrashModule(list_items)
        
    # bypass the trashcan
    def fdeleteAction(self):
        if self.selection:
            list_items = []
            for item in self.selection:
                list_items.append(self.fileModel.fileInfo(item).absoluteFilePath())
            
            # if more than 30 items no list
            if len(self.selection) < ITEMSDELETED:
                dialogList = ""
                for item in list_items:
                    dialogList += os.path.basename(item)+"\n"
                ret = retDialogBox("Info", "Do you really want to delete this item(s)?", "", dialogList)
            else:
                ret = retDialogBox("Info", "Do you really want to delete this item(s)?", "", "Too many items.\n")
            #
            if ret.getValue():
                self.fdeleteItems(list_items)
    
    
    def fdeleteItems(self, listItems):
        #
        # something happened with some items
        items_skipped = ""
        
        for item in listItems:
            time.sleep(0.1)
            if os.path.islink(item):
                try:
                    os.remove(item)
                except Exception as E:
                    items_skipped += os.path.basename(item)+"\n"+str(E)+"\n\n"
            elif os.path.isfile(item):
                try:
                    os.remove(item)
                except Exception as E:
                    items_skipped += os.path.basename(item)+"\n"+str(E)+"\n\n"
            elif os.path.isdir(item):
                try:
                    shutil.rmtree(item)
                except Exception as E:
                    items_skipped += os.path.basename(item)+"\n"+str(E)+"\n\n"
            # not regular files or folders 
            else:
                items_skipped += os.path.basename(item)+"\n"+"Only files and folders can be deleted."+"\n\n"
        #
        if items_skipped != "":
            MyMessageBox("Info", "Items not deleted:", "", items_skipped)
    
    def fnewFolderAction(self):
        if os.access(self.lvDir, os.W_OK): 
            ret = self.wrename3("New Folder", self.lvDir)
            if ret != -1 or not ret:
                destPath = os.path.join(self.lvDir, ret)
                if not os.path.exists(destPath):
                    try:
                        os.mkdir(destPath)
                    except Exception as E:
                        MyDialog("Error", str(E))
    
    
    def fnewFileAction(self):
        if os.access(self.lvDir, os.W_OK): 
            ret = self.wrename3("Text file.txt", self.lvDir)
            if ret != -1 or not ret:
                destPath = os.path.join(self.lvDir, ret)
                if not os.path.exists(destPath):
                    try:
                        iitem = open(destPath,'w')
                        iitem.close()
                    except Exception as E:
                        MyDialog("Error", str(E))
        
    
    def wrename3(self, ditem, dest_path):
        #
        ret = MyDialogRename3(ditem, self.lvDir).getValues()
        if ret == -1:
                return ret
        elif not ret:
            return -1
        else:
            return ret
    
    
    def frenameAction(self, ipath):
        ibasename = os.path.basename(ipath)
        idirname = os.path.dirname(ipath)
        inew_name = self.wrename2(ibasename, idirname)

        if inew_name != -1:
            try:
                shutil.move(ipath, inew_name)
            except Exception as E:
                MyDialog("Error", str(E))
    
    
    def fpropertyAction(self, ipath):
        propertyDialog(ipath)
    
    
    def fpropertyActionMulti(self):
        # size of all the selected items
        iSize = 0
        # number of the selected items
        iNum = len(self.selection)
        for iitem in self.selection:
            try:
                item = self.fileModel.fileInfo(iitem).absoluteFilePath()
                #
                if os.path.islink(item):
                    iSize += 512
                elif os.path.isfile(item):
                    iSize += QFileInfo(item).size()
                elif os.path.isdir(item):
                    iSize += self.folder_size(item)
                else:
                    QFileInfo(item).size()
            except:
                iSize += 0
        #
        propertyDialogMulti(self.convert_size(iSize), iNum)
    
    def ficustomAction(self, el, menuType):
        if menuType == 1:
            items_list = []
            items_list.append(self.fileModel.fileInfo(self.selection[0]).absoluteFilePath())
            el.ModuleCustom(self)
        elif menuType == 2:
            items_list = []
            for iitem in self.selection:
                items_list.append(self.fileModel.fileInfo(iitem).absoluteFilePath())
            el.ModuleCustom(self)
        elif menuType == 3:
            items_list = []
            for iitem in self.selection:
                items_list.append(self.fileModel.fileInfo(iitem).absoluteFilePath())
            el.ModuleCustom(self)
        elif menuType == 5:
            items_list = []
            for iitem in self.selection:
                items_list.append(self.fileModel.fileInfo(iitem).absoluteFilePath())
            el.ModuleCustom(self)
    
    
    def fbcustomAction(self, el):
        el.ModuleCustom(self)
    
    
    def wrename(self, ditem, dest_path):
        #
        dfitem = os.path.basename(ditem)
        ret = dfitem
        #
        ret = MyDialogRename(dfitem).getValues()
        if ret == -1 or ret == -2:
            return ret

        elif not ret:
            return -1
        else:
            return os.path.join(dest_path, ret)
    
    
    def wrename2(self, ditem, dest_path):
        ret = ditem
        ret = MyDialogRename2(ditem, dest_path).getValues()

        if ret == -1:
                return ret

        elif not ret:
            return -1
        else:
            return os.path.join(dest_path, ret)
    
    
    def fnewList(self, filePaths, dest_path):
        nlist = []
        items_skipped = ""
        for ditem in filePaths:
            # readable item or broken symlink
            if QFileInfo(ditem).isReadable() or os.path.islink(ditem):
                file_name = os.path.basename(ditem)
                dest_filePath = os.path.join(dest_path, file_name)
                if not os.path.exists(dest_filePath):
                    nlist.append(ditem)
                    nlist.append(dest_filePath)
                else:
                    ret = self.wrename(ditem, dest_path)
                    if ret == -2:
                        continue
                    elif ret == -1:
                        return -1
                    else:
                        nlist.append(ditem)
                        nlist.append(ret)
            else:
                items_skipped += "{}\n-----------\n".format(os.path.basename(ditem))
        if items_skipped != "":
            MyMessageBox("Info", "Items skipped because not readable", "", items_skipped)
        return nlist
    
    
    def fpastAction(self):
        #
        if not os.access(self.lvDir, os.W_OK):
            MyDialog("Info", "This folder is not writable.")
            return
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData(QClipboard.Clipboard)
        
        got_quoted_data = []
        for f in mimeData.formats():
            if f == "x-special/gnome-copied-files":
                data = mimeData.data(f)
                got_quoted_data = data.data().decode().split("\n")
                
                got_action = got_quoted_data[0]
                if got_action == "copy":
                    action = 1
                elif got_action == "cut":
                    action = 2
                filePaths = [unquote(x)[7:] for x in got_quoted_data[1:]]
                # a folder cannot be copied into itself or into a its subfolder
                for item in filePaths:
                    if os.path.isdir(item):
                        if item in self.lvDir:
                            MyMessageBox("Info", "A folder cannot copied into itself.\nRetry.","",item)
                            return
                # html file needs its folder
                for item in filePaths:
                    # if link pass
                    if os.path.islink(item):
                        continue
                    if stat.S_ISREG(os.stat(item).st_mode):
                        dir_name = os.path.dirname(item)
                        nroot, ext = os.path.splitext(os.path.basename(item))
                        if ext == ".html" or ext == ".htm":
                            fname = os.path.join(dir_name, nroot+"_files")
                            if os.path.exists(fname):
                                if fname not in filePaths:
                                    if stat.S_ISDIR(os.stat(fname).st_mode) and os.access(fname, os.R_OK):
                                        filePaths.append(fname)
                    if stat.S_ISDIR(os.stat(item).st_mode):
                        dir_name = os.path.dirname(item)
                        base_name = os.path.basename(item)
                        nroot = base_name[:-6]
                        if not os.path.join(dir_name, nroot+".html") in filePaths:
                            if os.path.exists(os.path.join(dir_name, nroot+".html")):
                                filePaths.append(os.path.join(dir_name, nroot+".html"))
                        if not os.path.join(dir_name, nroot+".htm") in filePaths:
                            if os.path.exists(os.path.join(dir_name, nroot+".htm")):
                                filePaths.append(os.path.join(dir_name, nroot+".htm"))
                
                newList = self.fnewList(filePaths, self.lvDir)
                if newList == -1:
                    return
                if newList:
                    copyItems(action, newList)
    
    
    def fcopyAction(self):
        #
        item_list = "copy\n"
        
        for iindex in self.selection:
            iname = iindex.data(QFileSystemModel.FileNameRole)
            iname_fp = os.path.join(self.lvDir, iname)
            #
            if os.access(iname_fp,os.R_OK) or os.path.islink(iname_fp):
                iname_quoted = quote(iname, safe='/:?=&')
                if iindex != self.selection[-1]:
                    iname_final = "file://{}\n".format(os.path.join(self.lvDir, iname_quoted))
                    item_list += iname_final
                else:
                    iname_final = "file://{}".format(os.path.join(self.lvDir, iname_quoted))
                    item_list += iname_final
        
        if item_list == "copy\n":
            clipboard = QApplication.clipboard()
            clipboard.clear()
            return
        
        clipboard = QApplication.clipboard()
        data = QByteArray()
        data.append(bytes(item_list, encoding="utf-8"))
        qmimdat = QMimeData()
        qmimdat.setData("x-special/gnome-copied-files", data)
        clipboard.setMimeData(qmimdat, QClipboard.Clipboard)
        
    
    def fcutAction(self):
        #
        item_list = "cut\n"
        
        for iindex in self.selection:
            iname = iindex.data(QFileSystemModel.FileNameRole)
            iname_fp = os.path.join(self.lvDir, iname)
            #
            if os.path.islink(iname_fp) or stat.S_ISREG(os.stat(iname_fp).st_mode) or stat.S_ISDIR(os.stat(iname_fp).st_mode):
                iname_quoted = quote(iname, safe='/:?=&')
                if iindex != self.selection[-1]:
                    iname_final = "file://{}\n".format(os.path.join(self.lvDir, iname_quoted))
                    item_list += iname_final
                else:
                    iname_final = "file://{}".format(os.path.join(self.lvDir, iname_quoted))
                    item_list += iname_final
            else:
                continue
        
        if item_list == "cut\n":
            clipboard = QApplication.clipboard()
            clipboard.clear()
            return
        
        clipboard = QApplication.clipboard()
        data = QByteArray()
        data.append(bytes(item_list, encoding="utf-8"))
        qmimdat = QMimeData()
        qmimdat.setData("x-special/gnome-copied-files", data)
        clipboard.setMimeData(qmimdat, QClipboard.Clipboard)
    
    
    def upButton(self):
        if self.lvDir != "/":
            self.listview.clearSelection()
            path = os.path.dirname(self.lvDir)
            self.lvDir = path
            global MMTAB
            MMTAB.setTabText(MMTAB.currentIndex(), os.path.basename(self.lvDir) or "ROOT")
            MMTAB.setTabToolTip(MMTAB.currentIndex(), self.lvDir)
            self.listview.setRootIndex(self.fileModel.setRootPath(path))
            
            self.tabLabels()
            
    
    def finvbtn(self):
        rootIndex = self.listview.rootIndex()
        first = rootIndex.child(0, 0)
        numOfItems = self.fileModel.rowCount(rootIndex)
        last = rootIndex.child(numOfItems - 1, 0)
        selection = QItemSelection(first, last)
        self.listview.selectionModel().select(selection, QItemSelectionModel.Toggle)

    
    def fhidbtn(self):
        if self.fmf == 0:
            self.fileModel.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.System | QDir.Hidden)
            self.fmf = 1
        else:
            self.fileModel.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.System)
            self.fmf = 0

    
    def convert_size(self, fsize2):
        
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize    

    
    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if os.path.islink(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size


class TrashModule():
    
    def __init__(self, list_items):
        self.list_items = list_items
        self.trash_path = self.find_trash_path(self.list_items[0])
        self.Tfiles = os.path.join(self.trash_path, "files")
        self.Tinfo = os.path.join(self.trash_path, "info")
        self.can_trash = 0
        self.Ttrash_can_trash()
        
        if self.can_trash:
            self.Tcan_trash(self.list_items)

    def find_trash_path(self, path):
        mount_point = ""
        while not os.path.ismount(path):
            path = os.path.dirname(path)
        mount_point = path
        #
        if mount_point == "/":
            trash_path = os.path.join(os.path.expanduser("~"), ".local/share/Trash")
        else:
            user_id = os.getuid()
            trash_path = os.path.join(mount_point, ".Trash-"+str(user_id))
        return trash_path

    def Ttrash_can_trash(self):
        if not os.path.exists(self.trash_path):
            if os.access(os.path.dirname(self.trash_path), os.W_OK):
                try:
                    os.mkdir(self.trash_path, 0o700)
                    os.mkdir(self.Tfiles, 0o700)
                    os.mkdir(self.Tinfo, 0o700)
                    self.can_trash = 1
                except Exception as E:
                    MyDialog("ERROR", str(E))
                    return
                finally:
                    return
            else:
                MyDialog("ERROR", "Cannot create the Trash.")
                return
        #
        if not os.access(self.Tfiles, os.W_OK):
            MyDialog("ERROR", "Cannot create the files folder.")
            return
        if not os.access(self.Tinfo, os.W_OK):
            MyDialog("ERROR", "Cannot create the info folder.")
            return
        #
        if os.access(self.trash_path, os.W_OK):
            if not os.path.exists(self.Tfiles):
                try:
                    os.mkdir(self.Tfiles, 0o700)
                except Exception as E:
                    MyDialog("ERROR", str(E))
                    return
            
            if not os.path.exists(self.Tinfo):
                try:
                    os.mkdir(self.Tinfo, 0o700)
                except Exception as E:
                    MyDialog("ERROR", str(E))
                    return
            
            self.can_trash = 1
            return
        
        else:
            MyDialog("ERROR", "The Trash folder has wrong permissions.")
            return
        
    def Tcan_trash(self, list_items):
        for item_path in list_items:
            item = os.path.basename(item_path)
            tnow = datetime.datetime.now()
            del_time = tnow.strftime("%Y-%m-%dT%H:%M:%S")
            item_uri = quote("file://{}".format(item_path), safe='/:?=&')[7:]
            if os.path.exists(os.path.join(self.Tinfo, item+".trashinfo")):
                basename, suffix = os.path.splitext(item)
                i = 2
                aa = basename+"."+str(i)+suffix+".trashinfo"

                while os.path.exists(os.path.join(self.Tinfo, basename+"."+str(i)+suffix+".trashinfo")):
                    i += 1
                else:
                    item = basename+"."+str(i)+suffix

            try:
                shutil.move(item_path, os.path.join(self.Tfiles, item))
            except Exception as E:
                MyDialog("ERROR", str(E))
                continue
            ifile = open(os.path.join(self.Tinfo, "{}.trashinfo".format(item)),"w")
            ifile.write("[Trash Info]\n")
            ifile.write("Path={}\n".format(item_uri))
            ifile.write("DeletionDate={}\n".format(del_time))
            ifile.close()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = MainWin()
    window.setFont(thefont)
    window.show()
    sys.exit(app.exec_())

