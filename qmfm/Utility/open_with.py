#!/usr/bin/env python3

from PyQt5.QtCore import (Qt,)
from PyQt5.QtWidgets import (QFileDialog, qApp, QBoxLayout, QPushButton, QApplication, QDialog, QMessageBox, QLineEdit, QWidget, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtGui import (QIcon,)

import sys
import os
import shutil
import subprocess
from xdg.DesktopEntry import *
#
from Utility import pop_menu

##########################

class listMenu(QWidget):
    
    def __init__(self, infile=None):
        super().__init__()
        self.infile = infile
        
        self.setWindowIcon(QIcon("icons/file-manager-red.svg"))
        self.setWindowTitle("Menu")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(600, 600)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        
        # treewidget
        self.TWD = QTreeWidget()
        self.TWD.setHeaderLabels(["Applications"])
        self.TWD.setAlternatingRowColors(False)
        self.TWD.itemClicked.connect(self.fitem)
        vbox.addWidget(self.TWD)

        # entry
        hbox2 = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox2)
        self.LE = QLineEdit()
        #self.LE.setReadOnly(True)
        hbox2.addWidget(self.LE)
        
        # select program
        self.buttonOF = QPushButton("Select...")
        self.buttonOF.clicked.connect(self.fOpenWith)
        hbox2.addWidget(self.buttonOF)
        
        ### buttons
        hbox = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox)
        button1 = QPushButton("Ok")
        hbox.addWidget(button1)
        button1.clicked.connect(self.fexecute)
        
        button2 = QPushButton("Cancel")
        hbox.addWidget(button2)
        button2.clicked.connect(self.fcancel)
        
        #### the menu
        # get the menu
        amenu = pop_menu.getMenu()
        self.menu = amenu.retList()[0]
        # get the categories
        categ = []
        for el in self.menu:
            if el[2] not in categ:
                categ.append(el[2])
        # sorting
        categ.sort()
        
        # populate the categories
        self.fpopMenu()
        
        self.Value = None
    
    #
    def fOpenWith(self):
        ret = QFileDialog.getOpenFileName(parent=None, caption="Select...", directory="/")
        if ret[0]:
            # set the text
            self.LE.setText(os.path.basename(ret[0]))
            # set the variable
            self.Value = ret[0]
    
    # create a menu of installed applications
    def fpopMenu(self):
        # extended categories
        development_extended_categories = ["Building","Debugger","IDE","GUIDesigner",
                                  "Profiling","RevisionControl","Translation",
                                  "Database","WebDevelopment"]

        office_extended_categories = ["Calendar","ContanctManagement","Office",
                             "Dictionary","Chart","Email","Finance","FlowChart",
                             "PDA","ProjectManagement","Presentation","Spreadsheet",
                             "WordProcessor","Engineering"]

        graphics_extended_categories = ["2DGraphics","VectorGraphics","RasterGraphics",
                               "3DGraphics","Scanning","OCR","Photography",
                               "Publishing","Viewer"]

        utility_extended_categories = ["TextTools","TelephonyTools","Compression",
                              "FileTools","Calculator","Clock","TextEditor",
                              "Documentation"]

        settings_extended_categories = ["DesktopSettings","HardwareSettings",
                               "Printing","PackageManager","Security",
                               "Accessibility"]

        network_extended_categories = ["Dialup","InstantMessaging","Chat","IIRCClient",
                              "FileTransfer","HamRadio","News","P2P","RemoteAccess",
                              "Telephony","VideoConference","WebBrowser"]

        # added "Audio" and "Video" main categories
        audiovideo_extended_categories = ["Audio","Video","Midi","Mixer","Sequencer","Tuner","TV",
                                 "AudioVideoEditing","Player","Recorder",
                                 "DiscBurning"]

        game_extended_categories = ["ActionGame","AdventureGame","ArcadeGame",
                           "BoardGame","BlockGame","CardGame","KidsGame",
                           "LogicGame","RolePlaying","Simulation","SportGame",
                           "StrategyGame","Amusement","Emulator"]

        education_extended_categories = ["Art","Construction","Music","Languages",
                                "Science","ArtificialIntelligence","Astronomy",
                                "Biology","Chemistry","ComputerScience","DataVisualization",
                                "Economy","Electricity","Geography","Geology","Geoscience",
                                "History","ImageProcessing","Literature","Math","NumericAnalysis",
                                "MedicalSoftware","Physics","Robots","Sports","ParallelComputing",
                                "Electronics"]

        system_extended_categories = ["FileManager","TerminalEmulator","FileSystem",
                             "Monitor","Core"]

        # main categories
        AudioVideo = []
        Development = []
        Education = []
        Game = []
        Graphics = []
        Network = []
        Office = []
        Settings = []
        System = []
        Utility = []
        Missed = []

        #
        for el in self.menu:
            cat = el[2]
            if cat == "AudioVideo" or cat in audiovideo_extended_categories:
                # category - label - path - executable
                AudioVideo.append(["AudioVideo",el[0],el[1],el[3]])
            elif cat == "Development" or cat in development_extended_categories:
                Development.append(["Development",el[0],el[1],el[3]])
            elif cat == "Education" or cat in education_extended_categories:
                Education.append(["Education",el[0],el[1],el[3]])
            elif cat == "Game" or cat in game_extended_categories:
                Game.append(["Game",el[0],el[1],el[3]])
            elif cat == "Graphics" or cat in graphics_extended_categories:
                Graphics.append(["Graphics",el[0],el[1],el[3]])
            elif cat == "Network" or cat in network_extended_categories:
                Network.append(["Network",el[0],el[1],el[3]])
            elif cat == "Office" or cat in office_extended_categories:
                Office.append(["Office",el[0],el[1],el[3]])
            elif cat == "Settings" or cat in settings_extended_categories:
                Settings.append(["Settings",el[0],el[1],el[3]])
            elif cat == "System" or cat in system_extended_categories:
                System.append(["System",el[0],el[1],el[3]])
            elif cat == "Utility" or cat in utility_extended_categories:
                Utility.append(["Utility",el[0],el[1],el[3]])
            else:
                Missed.append(["Missed",el[0],el[1],el[3]])
        #
        # adding the main categories
        for ell in [AudioVideo,Development,Education,Game,Graphics,Network,Office,Settings,System,Utility,Missed]:
            if ell:
                cat = ell[0][0]
                tl = QTreeWidgetItem([cat])
                self.TWD.addTopLevelItem(tl)
        #
        # populate the categories
        for ell in [AudioVideo,Development,Education,Game,Graphics,Network,Office,Settings,System,Utility,Missed]:
            if ell:
                # el: category - label - path - executable
                for el in ell:
                    # find the index of the category in the treeview
                    witem = self.TWD.findItems(el[0], Qt.MatchExactly, 0)[0]
                    idx = self.TWD.indexOfTopLevelItem(witem)
                    # add the item
                    tw_child = QTreeWidgetItem([el[1], el[2]])
                    witem.addChild(tw_child)


    # an item in the treewidget is clicked
    def fitem(self, item, col):
        # get the executable with full path
        appExec = DesktopEntry(item.text(1)).getExec().split()[0]
        # if the executable exists
        if shutil.which(appExec):
            # set the name of the program in the line edit widget
            self.LE.setText(item.text(0))
            # set the variable
            self.Value = appExec
        #
        else:
            # the program exists but cannot be executed
            if os.path.exists(appExec):
                self.fdialog("The program\n"+appExec+"\ncannot be executed.")
            # the program doesn't exist
            else:
                self.fdialog("The program\n"+appExec+"\ncannot be found.")
    
    # execute the program with the file as argument
    def fexecute(self):
        # program choosen from list or from dialog
        if self.Value:
            if shutil.which(self.Value):
                try:
                    subprocess.Popen([self.Value, self.infile])
                except Exception as E:
                    self.fdialog(str(E))
            else:
                self.fdialog("The program\n"+self.Value+"\ncannot be found.")
            self.close()
        # program written in the line edit widget directly
        else:
            if self.LE.text():
                if shutil.which(self.LE.text()):
                    try:
                        subprocess.Popen([self.LE.text(), self.infile])
                    except Exception as E:
                        self.fdialog(str(E))
                else:
                    self.fdialog("The program\n"+self.LE.text()+"\ncannot be found.")
                self.close()
    
    def fcancel(self):
        self.close()

    # dialog
    def fdialog(self, msg):
        dialog = QMessageBox()
        dialog.setWindowTitle("Info")
        dialog.setModal(True)
        dialog.setText(msg)
        dialog.exec()

###################
