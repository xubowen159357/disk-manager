import subprocess
import os
import re
import psutil
import json as js


"""
def sh(command, print_msg=True):
    p = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('gbk')
    if print_msg:
        print(result)
    return result


def usbpath():
    if os.name == 'nt':
        disks = sh("wmic logicaldisk get deviceid, description",
                   print_msg=False).split('\n')
        for disk in disks:
            if 'Removable' in disk:
                return re.search(r'\c:', disk).group()
    elif os.name == 'posix':
        return sh('ll -a /media')[-1].strip()
    else:
        return sh('ls /Volumes')[-1].strip()


print(usbpath())

class disk_ifs:
    def __init__(self, device:str=None, mountpoint:str=None, fstype:str=None, opts:str=None) -> None:
        self.device=device
        self.mountpoint=mountpoint
        self.fstype=fstype
        self.opts=opts.split(',')[0]
        self.info=''
        if self.device and self.mountpoint and self.fstype and self.opts:
            self.init()
    
    def init(self):
        if not self.fstype:
            self.info='未挂载;'
            self.fstype=='null'
        if self.opts[0]=='r':
            self.info+='只读;'
        else:
            self.info+='可写;'
        if self.opts[1]=='fixed':
            self.info+='本地磁盘;'
        elif self.opts[1]=='removable':
            self.info+='可移动盘;'
    
    def save(self):
        return {'device':self.device,'mountpoint':self.mountpoint,'fstype':self.fstype,'opts':self.opts}
    
    def load(self, data:str):
        data=js.loads(data)
        self.device=data['device']
        self.mountpoint=data['mountpoint']
        self.fstype=data['fstype']
        self.opts=data['opts']
        self.init()

print(js)"""

print("%(message)s%(deny)s"%{'message':'hello','deny':'world'})



