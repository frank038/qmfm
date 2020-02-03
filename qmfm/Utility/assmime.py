#!/usr/bin/env python3

from PyQt5.QtCore import (QMargins,QEvent,QObject,Qt)
from PyQt5.QtWidgets import (QListWidgetItem, QListWidget, QTreeWidget, QTreeWidgetItem, qApp,QBoxLayout,QLabel,QPushButton,QApplication,QDialog,QMessageBox,QLineEdit,QTabWidget,QWidget,QListView)
from PyQt5.QtGui import (QPixmap,QFont)

import sys
import os
import shutil
import subprocess
from xdg.DesktopEntry import *
#
import pop_menu

WINW = 1200
WINH = 800

### mimetypes database
# system database
MIMETYPES = "/etc/mime.types"
## local database
#MIMETYPES2 = os.path.join(os.path.expanduser("~"), ".mime.types")

# where to look for the *.desktop files
xdgDataDirs = ['/usr/local/share', '/usr/share', os.path.expanduser('~')+"/.local/share"]

# full path of the mimeapps.list file
MIMEAPPSLIST = os.path.expanduser('~')+"/.config/mimeapps.list"


##############
ListMime = []

# create a category/extension database from the mime.types file
with open(MIMETYPES, "r") as f:
    for line in f:
        if line.strip(" ") != "\n":
            if not line.strip(" ")[0] == "#":
                lline = line.strip(" ").split("\t")
                mime = lline[0].strip("\n")
                ext = lline[-1].strip("\n")
                #
                if ext == mime:
                    ext = ""
                ListMime.append([mime,ext])

# the categories
ListCat = []

for el in ListMime:
    cat = el[0].split("/")[0]
    if not cat in ListCat:
        ListCat.append(cat)

##########################
### look for mimetypes added, removed in the mimeapps.list

# remove the null elements in the list
def delNull(e):
    return [i for i in e if i != ""]

# three list from mimeapps.list: association added and removed and default applications
lA = []
lR = []
lD = []
# function that return mimetypes added, removed in the mimeappss.list
def fillL123():
    # mimeapps.list can have up to three not mandatory sectors
    #["[Added Associations]","[Removed Associations]","[Default Applications]"]

    # lists of mimetypes added or removed - reset
    lAdded = []
    lRemoved = []
    lDefault = []
    lista = []
    
    # reset
    lA1 = []
    lR1 = []
    lD1 = []
    
    if not os.path.exists(MIMEAPPSLIST):
        return
    
    # all the file in lista: one row one item added to lista
    with open(MIMEAPPSLIST, "r") as f:
        lista = f.readlines()

    # marker
    x = ""
    for el in lista:
        if el == "[Added Associations]\n":
            x = "A"
        elif el == "[Removed Associations]\n":
            x = "R"
        elif el == "[Default Applications]\n":
            x = "D"
        #
        if el:
            if x == "A":
                lA1.append(el)
            elif x == "R":
                lR1.append(el)
            elif x == "D":
                lD1.append(el) 
    
    global lA
    lA = lA1
    global lR
    lR = lR1
    global lD
    lD = lD1
    

# function that return mimetypes added and removed (and default applications) in the mimeappss.list
def addMime(mimetype):
    # call the function
    fillL123()
    
    lAdded = []
    lRemoved = []
    lDefault = []

    for el in lA:
        if mimetype in el:
            # item is type list
            item = el.replace(mimetype+"=","").strip("\n").split(";")
            lAdded = delNull(item)
    #
    for el in lR:
        if mimetype in el:
            item = el.replace(mimetype+"=","").strip("\n").split(";")
            lRemoved = delNull(item)
    #
    for el in lD:
        if mimetype in el:
            item = el.replace(mimetype+"=","").strip("\n").split(";")
            lDefault = delNull(item)
    
    return lAdded,lRemoved#,lDefault
    

#### find the default application if any

# get the default progam associated to a given mimetype
def getDefaultApp(imime):
    ret = shutil.which("xdg-mime")
    if ret:
        if imime in ["application/x-zerosize", "application/x-trash"]:
            mimetype = "text/plain"
        else:
            mimetype = imime
        #
        try:
            associatedDesktopProgram = subprocess.check_output([ret, "query", "default", mimetype], universal_newlines=False).decode()
        except Exception as E:
            return "None"
        #
        return associatedDesktopProgram


#### DESKTOP FILES
# list: program name - exec - mimetypes - desktop file
ListProg = []

## desktop files
for ddir in xdgDataDirs:
    applicationsPath = os.path.join(ddir, "applications")
    #
    if os.path.exists(applicationsPath):
        desktopFiles = os.listdir(applicationsPath)
        for idesktop in desktopFiles:
            if idesktop.endswith(".desktop"):
                desktopPath = os.path.join(ddir+"/applications", idesktop)
                #
                mimeTypes = DesktopEntry(desktopPath).getMimeTypes()
                mimeProg2 = DesktopEntry(desktopPath).getExec()
                #
                if mimeProg2:
                   mimeProg = mimeProg2.split()[0]
                retw = shutil.which(mimeProg)
                if retw is not None:
                    pass
                #
                progName = DesktopEntry(desktopPath).getName()
                ListProg.append([progName,mimeProg,mimeTypes,idesktop])

##########################
# main class
class MainWin(QWidget):
    
    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        
        self.resize(int(WINW), int(WINH))
        self.setWindowTitle("Mimetypes")
        
        self.imime = ""
        
        # top container
        self.obox = QBoxLayout(QBoxLayout.LeftToRight)
        self.obox.setContentsMargins(QMargins(2,2,2,2))
        self.setLayout(self.obox)
        
        # left container
        self.vbox1 = QBoxLayout(QBoxLayout.TopToBottom)
        self.obox.addLayout(self.vbox1)
        
        # right container
        self.vbox2 = QBoxLayout(QBoxLayout.TopToBottom)
        self.obox.addLayout(self.vbox2)
        
        ############ widgets in right container
        
        self.extLabel1 = QLabel("Extension(s)")
        self.vbox2.addWidget(self.extLabel1)
        self.extLabel2 = QLineEdit()
        self.extLabel2.setReadOnly(True)
        self.vbox2.addWidget(self.extLabel2)
        
        # label
        self.execLabel = QLabel("Executable(s)")
        self.vbox2.addWidget(self.execLabel)
        
        #### List
        self.plist = QListWidget()
        self.vbox2.addWidget(self.plist)
        
        #### buttons
        self.buttonBox = QBoxLayout(QBoxLayout.LeftToRight)
        
        self.b1 = QPushButton("Make default")
        self.b1.clicked.connect(self.fb1)
        self.buttonBox.addWidget(self.b1)
        
        self.b2 = QPushButton("Add")
        self.b2.clicked.connect(self.fb2)
        self.buttonBox.addWidget(self.b2)
        
        self.b3 = QPushButton("Remove")
        self.b3.clicked.connect(self.fb3)
        self.buttonBox.addWidget(self.b3)
        
        self.vbox2.addLayout(self.buttonBox)
        
        
        ########### treeview
        
        self.TW = QTreeWidget()
        self.TW.setHeaderLabels(["Mimetypes", "ext"])
        self.TW.setColumnHidden(1, True)
        self.TW.setAlternatingRowColors(True)
        # fill the commans list on the right by clicking the item 
        self.TW.itemClicked.connect(self.fitem)
        self.vbox1.addWidget(self.TW)
        
        ########### items
        # add the toplevels categories
        for el in ListCat:
            tl = QTreeWidgetItem([el])
            self.TW.addTopLevelItem(tl)
        
        # adding the items in each category - ListMime
        for el in ListMime:
            item = el[0].split("/")
            # 
            cat1 = item[0]
            cat2 = item[1]
            # find the index of the category in the treeview
            witem = self.TW.findItems(cat1, Qt.MatchExactly, 0)[0]
            idx = self.TW.indexOfTopLevelItem(witem)
            # add the item
            tw_child = QTreeWidgetItem([cat2, el[1]])
            witem.addChild(tw_child)
            
        ## close application button
        self.closeBtn = QPushButton("Close")
        self.vbox1.addWidget(self.closeBtn)
        self.closeBtn.clicked.connect(self.close)

    # the three list in mimeapps.list
    def threeList(self):
        # the lists in mimeapps.list - resorted
        self.lDA = lD
        self.lAA = lA
        self.lRA = lR

    # when an item in the treelist is been clicked
    def fitem(self, item, col):
        ##### find the index of the item in the category
        p = item.parent()
        if p:
            # clear the plist
            self.plist.clear()
            #
            self.extLabel2.setText(item.text(1))
            self.imime = p.text(0)+"/"+item.text(0)
            defApp = getDefaultApp(self.imime).strip("\n")
            # from the mimeapps.list
            lAdded,lRemoved = addMime(self.imime)
            #
            ### update the three list from mimeapps.list
            self.threeList()
            #
            for el in ListProg:
                # search for the mimetype
                if self.imime in el[2]:
                    if el[3] == defApp:
                        item = QListWidgetItem()
                        item.setText(el[1]+" (*)")
                    elif el[3] in lRemoved:
                        item = QListWidgetItem()
                        item.setText(el[1]+" (-)")
                    else:
                        item = QListWidgetItem()
                        item.setText(el[1])
                    if item:
                        self.plist.addItem(item)
                #
            # mimeapps.list: added associations
            # lAdded can have more than one item
            for eapp in lAdded:
                # se is default application
                if eapp == defApp:
                    item = QListWidgetItem()
                    # 
                    for edir in xdgDataDirs:
                        if eapp in os.listdir(os.path.join(edir,"applications")):
                            df = os.path.join(edir,"applications",eapp)
                            dfapp = DesktopEntry(df).getExec().split()[0]
                            item.setText(dfapp+" (+*)")
                            self.plist.addItem(item)
                else:
                    item = QListWidgetItem()
                    for edir in xdgDataDirs:
                        if eapp in os.listdir(os.path.join(edir,"applications")):
                            df = os.path.join(edir,"applications",eapp)
                            dfapp = DesktopEntry(df).getExec().split()[0]
                            item.setText(dfapp+" (+)")
                            self.plist.addItem(item)

    # make the application the default one
    def fb1(self, w):
        # selected item of plist
        itemSelected = self.plist.currentItem()
        if itemSelected:
            if itemSelected.text()[-2:] != "*)":
                dret = commDialog("Confirm Make default?", 3).getValue()
                # 2 means Execute
                if dret == 2:
                    # check if the mimetype is already in the Default Applications list
                    for el in self.lDA:
                        if self.imime in el:
                            self.lDA.remove(el)
                    #
                    ## add the new
                    # selected item of plist
                    itemSelected = self.plist.currentItem()
                    ret = self.findDesktop(itemSelected.text())
                    # 
                    if ret == 0:
                        return
                    newItem = os.path.basename(ret)
                    self.lDA.insert(1, self.imime+"="+newItem+";\n")
                    
                    try:    
                        ## update the file
                        with open(MIMEAPPSLIST, 'w') as f:
                            for ell in [self.lDA,self.lAA,self.lRA]:
                                # not empty
                                if ell:
                                    for el in ell:
                                        f.write(el)
                    except Exception as E:
                        commDialog("Error with the file mimeapps.list.\nReload this application.", 5)

                    # reload qlist
                    self.fitem(self.TW.currentItem(), 0)
                      
                    
    # find the desktop file of the executable
    def findDesktop(self, item):
        a = pop_menu.getMenu()
        menu = a.retList()[0]
        #
        for el in menu:
            if item.replace(" (+)","") in el:
                return el[1]
        return 0

    
    # add an application
    def fb2(self, w):
        #
        if self.imime:
            ret = listMenu().getValue()
            # add the desktop file to the list
            if ret == -1 or ret == None:
                return 
            toAdd = self.imime+"="+os.path.basename(ret)+";\n"
            if toAdd not in self.lAA:
                elFound = 0
                # check whether the mimetypes is already in the list
                for el in self.lAA[:]:
                    if self.imime in el:
                        elFound = el
                        break
                # if found or not
                if elFound:
                    self.lAA.remove(el)
                    self.lAA.append(el.replace("\n","")+os.path.basename(ret)+";\n")
                else:
                    self.lAA.insert(1, toAdd)
                # write the file
                try:    
                    ## update the file
                    with open(MIMEAPPSLIST, 'w') as f:
                        for ell in [self.lDA,self.lAA,self.lRA]:
                            # not empty
                            if ell:
                                for el in ell:
                                    f.write(el)
                except Exception as E:
                    commDialog("Error with the file mimeapps.list.\nReload this application.", 5)
                #
                # reload qlist
                self.fitem(self.TW.currentItem(), 0)
                
   
    # remove the association
    def fb3(self, w):
        # selected item of plist
        itemSelected = self.plist.currentItem()
        if itemSelected:
            # find the item in the lists self.lDA and self.lAA
            ret = self.findItemInLista(itemSelected)
            # confirmation dialog
            if ret:
                dret = commDialog("Confirm Delete?", 3).getValue()
                # 2 means Execute
                if dret == 2:
                    itemName = itemSelected.text()
                    # if the application is marked as added and as default removes as default
                    if itemName[-5:] == " (+*)":
                        for el in self.lDA[:]:
                            if self.imime+"=" in el and itemName[:-5] in el:
                                self.lDA.remove(el)
                    # if the application is marked as added removes as added
                    elif itemName[-4:] == " (+)":
                        for el in self.lAA[:]:
                            if self.imime+"=" in el and itemName[:-4] in el:
                                self.lAA.remove(el)
                    #if the application is marked as removed removes as removed
                    elif itemName[-4:] == " (-)":
                        for el in self.lRA[:]:
                            if self.imime+"=" in el and itemName[:-4] in el:
                                self.lRA.remove(el)
                    
                    ## update the mimeapps.list file
                    try:
                        with open(MIMEAPPSLIST, 'w') as f:
                            for ell in [self.lDA,self.lAA,self.lRA]:
                                if ell:
                                    for el in ell:
                                        f.write(el)
                    except Exception as E:
                        commDialog("Error with the file mimeapps.list.\nReload this application.", 5)
                    
                    # qlist
                    self.fitem(self.TW.currentItem(), 0)
                    

    # find the item in the lists l1,l2,l3
    def findItemInLista(self, item):
        i = 0
        # 
        for ell in [self.lDA, self.lAA, self.lRA]:
            if ell:
                for el in ell:
                    if self.imime+"=" in el and item.text().split(" ")[0] in el:
                        i += 1
        #
        return i

#
class listMenu(QDialog):
    def __init__(self, parent=None):
        super(listMenu, self).__init__(parent)
        
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
        
        # buttons
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
        a = pop_menu.getMenu()
        self.menu = a.retList()[0]
        # get the categories
        categ = []
        for el in self.menu:
            if el[2] not in categ:
                categ.append(el[2])
        # sorting
        categ.sort()
        
        ## populate the categories
        self.fpopMenu()
        
        self.Value = None
        self.exec_()

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
        self.Value = item.text(1)
    
    def getValue(self):
        return self.Value
    
    def fexecute(self):
        self.close()
    
    def fcancel(self):
        self.Value = -1
        self.close()


# generic dialog
class commDialog(QDialog):
    def __init__(self, text, flag, parent=None):
        super(commDialog, self).__init__(parent)
        self.text = text
        self.flag = flag
        #
        self.setWindowTitle("Info")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(600, 100)
        #
        vbox = QBoxLayout(QBoxLayout.TopToBottom)
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        #
        label1 = QLabel("{}".format(self.text))
        vbox.addWidget(label1)
        hbox = QBoxLayout(QBoxLayout.LeftToRight)
        vbox.addLayout(hbox)
        #
        if self.flag == 0:
            button1 = QPushButton("Open")
            hbox.addWidget(button1)
            button1.clicked.connect(self.fopen)
        elif self.flag == 1:
            button1 = QPushButton("OK")
            hbox.addWidget(button1)
            button1.clicked.connect(self.fopen)
        elif self.flag == 3:
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


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = MainWin()
    window.show()
    sys.exit(app.exec_())