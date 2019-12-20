#!/usr/bin/env python3

import dbus
import subprocess
import os
import sys

class mountDevice():
    def __init__(self, ddev, operation):
        self.ddev = ddev
        self.operation = operation
        self.progname = 'org.freedesktop.UDisks2'
        objpath = os.path.join('/org/freedesktop/UDisks2/block_devices', self.ddev)
        self.objpath  = objpath
        self.intfname = 'org.freedesktop.UDisks2.Filesystem'
    
    def fmount(self):
        try:
            bus = dbus.SystemBus()
            methname = self.operation
            obj  = bus.get_object(self.progname, self.objpath)
            intf = dbus.Interface(obj, self.intfname)
            ret = intf.get_dbus_method(methname, dbus_interface='org.freedesktop.UDisks2.Filesystem')([])
        except:
            return -1
        
class devEject():
    def __init__(self, mddev):
        self.mddev = mddev
        self.progname = 'org.freedesktop.UDisks2'
        self.objpath  = self.mddev
        self.intfname = 'org.freedesktop.UDisks2.Drive'
    
    def fdeveject(self):
        try:
            bus = dbus.SystemBus()
            methname = 'Eject'
            obj  = bus.get_object(self.progname, self.objpath)
            intf = dbus.Interface(obj, self.intfname)
            ret = intf.get_dbus_method(methname, dbus_interface='org.freedesktop.UDisks2.Drive')([])
            return ret
        except:
            return -1

class devPoweroff():
    def __init__(self, mddev):
        self.mddev = mddev
        self.progname = 'org.freedesktop.UDisks2'
        self.objpath  = self.mddev
        self.intfname = 'org.freedesktop.UDisks2.Drive'
    
    def fdevpoweroff(self):
        try:
            bus = dbus.SystemBus()
            methname = 'PowerOff'
            obj  = bus.get_object(self.progname, self.objpath)
            intf = dbus.Interface(obj, self.intfname)
            ret = intf.get_dbus_method(methname, dbus_interface='org.freedesktop.UDisks2.Drive')([])
            return ret
        except:
            return -1

class ManagedObjects():
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.obj = self.bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")
        self.iface = dbus.Interface(self.obj, 'org.freedesktop.DBus.ObjectManager')

    def mo(self):
        mobject = self.iface.GetManagedObjects()
        return mobject

class cDisk():
    device = ""
    drive_type = 0
    label = ""
    size = 0
    filesystem = ""
    read_only = 0
    drive = ""
    mount_point = ""
    media_type = ""
    can_eject = 0
    can_poweroff = 0
    connection_bus = ""
    vendor = ""
    model = ""

class diskList():
    def __init__(self):
        self.disk_list = []

    def dlist(self):
        mobject = ManagedObjects().mo()
        for k,v in mobject.items():
            if "/org/freedesktop/UDisks2/block_devices" in k:
                self.disk_list.append(str(k))
        return self.disk_list

class driveList():
    def __init__(self):
        self.dlist = []
        
    def drlist(self):
        mobject = ManagedObjects().mo()
        for k in mobject:
            mount_paths = []
            device = mobject[k]
            
            fs = "org.freedesktop.UDisks2.Filesystem"
            bl = "org.freedesktop.UDisks2.Block"
            
            if fs in device:
                if "org.freedesktop.UDisks2.Partition" in device:
                    drive = "".join(map(str,device["org.freedesktop.UDisks2.Partition"]["Table"]))
                    l = [drive, str(k)]
                    self.dlist.append(l)
                elif "org.freedesktop.UDisks2.Loop" in device:
                    res = "".join(map(str,device["org.freedesktop.UDisks2.Loop"]["BackingFile"]))
                    ddev = ""
                    for arr in res:
                        point = "".join(map(str,arr))
                        ddev = (ddev + point).replace("\x00","")
                    l = [ddev, str(k)]
                    self.dlist.append(l)
                else:
                    self.dlist.append(["", str(k)])
        return self.dlist

class listcDisk():
    def __init__(self):
        self.list_cDisks = []

    def plist(self):
        dlist = driveList().drlist()
        dlist.sort()
        for item in dlist:
            cD = cDisk()
            bus = dbus.SystemBus()
            bd = bus.get_object('org.freedesktop.UDisks2', item[1])
            try:
                try:
                    pdevice = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
                    pdevice = bytearray(pdevice).replace(b'\x00', b'').decode('utf-8')
                    if pdevice:
                        pass
                    else:
                        device = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
                        device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                    cD.device = pdevice
                except:
                    cD.device = "N"
                
                if item[0]:
                    ddev = item[0].split("/")[-1]
                else:
                    ddev = item[1].split("/")[-1]
                if ddev:
                    if "loop" in pdevice:
                        pass
                    else:
                        try:
                            if os.access("/sys/block/{}/device/type".format(ddev), os.R_OK):
                                dtype = subprocess.check_output(["cat", "/sys/block/{}/device/type".format(ddev)], universal_newlines=False)
                                ltype = int(dtype.decode().strip())
                                if ltype == 0:
                                    cD.type_media = "disk"
                                elif ltype == 5:
                                    cD.type_media = "rom"
                                else:
                                    cD.type_media = "N"
                        except:
                            cD.type_media = "N"
                
                try:
                    label = bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.label = label
                except:
                    cD.label = "N"
                
                try:
                    size = bd.Get('org.freedesktop.UDisks2.Block', 'Size', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.size = size
                except:
                    cD.size = "N"
                
                try:
                    file_system =  bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.filesystem = file_system
                except:
                    cD.filesystem = "N"
                
                try:
                    read_only = bd.Get('org.freedesktop.UDisks2.Block', 'ReadOnly', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.read_only = read_only
                except:
                    cD.read_only = "N"
                
                try:
                    drive = bd.Get('org.freedesktop.UDisks2.Block', 'Drive', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.drive = drive
                except:
                    cD.drive = "N"

                try:
                    mountpoint = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
                    if mountpoint:
                        mountpoint = bytearray(mountpoint[0]).replace(b'\x00', b'').decode('utf-8')
                        cD.mount_point = mountpoint
                    else:
                        cD.mount_point = "N"
                except:
                    cD.mount_point = "N"

                bd2 = bus.get_object('org.freedesktop.UDisks2', drive)
                
                try:
                    type_media = bd2.Get('org.freedesktop.UDisks2.Drive', 'Media', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.media_type = type_media
                except:
                    cD.media_type = "N"
                
                try:
                    can_eject = bd2.Get('org.freedesktop.UDisks2.Drive', 'Ejectable', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.can_eject = can_eject
                except:
                    cD.can_eject = "N"
                
                try:
                    can_poweroff = bd2.Get('org.freedesktop.UDisks2.Drive', 'CanPowerOff', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.can_poweroff = can_poweroff
                except:
                    cD.can_poweroff = "N"
                
                try:
                    conn_bus = bd2.Get('org.freedesktop.UDisks2.Drive', 'ConnectionBus', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.connection_bus = conn_bus
                except:
                    cD.connection_bus = "N"
                
                try:
                    vendor = bd2.Get('org.freedesktop.UDisks2.Drive', 'Vendor', dbus_interface='org.freedesktop.DBus.Properties')
                    model = bd2.Get('org.freedesktop.UDisks2.Drive', 'Model', dbus_interface='org.freedesktop.DBus.Properties')
                    cD.vendor = vendor
                    cD.model = model
                except:
                    cD.vendor = "N"
                    cD.model = "N"

            except:
                pass

            self.list_cDisks.append(cD)

        return self.list_cDisks

class getDevMounted():
    def __init__(self, ddev):
        self.ddev = ddev
        path = os.path.join('/org/freedesktop/UDisks2/block_devices/', self.ddev)
        self.bus = dbus.SystemBus()
        self.bd = self.bus.get_object('org.freedesktop.UDisks2', path)
        
    def fgetdevmounted(self):
        try:
            mountpoint = self.bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
            if mountpoint:
                mountpoint = bytearray(mountpoint[0]).replace(b'\x00', b'').decode('utf-8')
                return mountpoint
            else:
                return "N"
        except:
            return "N"
