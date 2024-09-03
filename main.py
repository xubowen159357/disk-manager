import os
import sys
import time
import psutil
import os.path
import win32api
import json as js
import tkinter.messagebox as mess

from PIL import Image
from threading import Thread, Lock
from pystray import MenuItem, Icon, Menu

ICONP = 'icon.ico'
SETTINGP = 'setting.json'
LANGP = 'lang.json'

Recurse = [ICONP, SETTINGP, LANGP]


class disk_ifs:
    def __init__(self, device: str = None, fstype: str = None, opts: str = '') -> None:
        self.device = device
        self.fstype = fstype
        self.opts = opts.split(',')
        self.info = ''
        self.volume_info = ''
        if self.device:
            self.init()

    def init(self):
        if self.fstype == '':
            self.info += '未挂载;'
            self.fstype = 'null'
        if len(self.opts) == 1:
            pass
        if 'r' in self.opts:
            self.info += '只读;'
        else:
            self.info += '可写;'
        if 'fixed' in self.opts:
            self.info += '本地磁盘;'
        elif 'removable' in self.opts:
            self.info += '可移动盘;'
        elif 'cdrom' in self.opts:
            self.info += '光驱;'
        if self.fstype != 'null':
            self.volume_info = win32api.GetVolumeInformation(self.device)[0]

    def save(self):
        return {'device': self.device, 'fstype': self.fstype, 'opts': self.opts}

    def load(self, data: str | dict):
        if isinstance(data, str):
            data = js.loads(data)
        self.device = data['device']
        self.fstype = data['fstype']
        self.opts = data['opts']
        self.init()
        return self

    def open(self):
        if self.fstype != 'null':
            win32api.ShellExecute(0, 'open', self.device, '', '', 1)
        else:
            mess.showinfo('Error', f'{self.device}|未挂载')


for i in Recurse:
    if not os.path.exists(i) and (i != ICONP or i != SETTINGP):
        with open(i, 'w') as file:
            file.write('{\n}')
    elif not os.path.exists(i):
        mess.showinfo('Error', 'RecursionError')
        sys.exit()

ICON = Image.open(ICONP)
RE = True



def reload():
    global NEW, DEL, TNEW, SETTING, LANGA, LANG, TIMESTEEP
    SETTING = js.loads(open(SETTINGP, 'r').read())
    LANGA = js.loads(open(LANGP, 'r', encoding='utf-8').read())
    TNEW = None
    NEW, DEL = False, False
    LANG = LANGA['zh']
    TIMESTEEP = SETTING.get('time')
    if TIMESTEEP is None:
        TIMESTEEP = 0.1
    if '-lang=en' in sys.argv:
        LANG = LANGA['en']
    if not RE:
        mess.showinfo(LANG['title']['reload'], LANG['reload'])


class Background:
    def __init__(self) -> None:
        self.RUN = True
        self.Disks = psutil.disk_partitions()
        self.Elocaldisk = [disk_ifs(disk.device, disk.fstype, disk.opts)
                           for disk in self.Disks]
        self.nowdisk = {disk.device: disk for disk in self.Elocaldisk}
        self.lock = Lock()

    def run(self):
        self.m = Thread(target=self.main, daemon=True)
        self.m.start()

    def main(self):
        global NEW, DEL, TNEW
        while self.RUN:
            with self.lock:
                ldisk = psutil.disk_partitions()
                if len(self.Disks) < len(ldisk):
                    self.Elocaldisk = [disk_ifs(disk.device, disk.fstype, disk.opts)
                                       for disk in ldisk]
                    NEW = True
                    TNEW = [new for new in self.Elocaldisk if new.device not in self.nowdisk]
                    self.nowdisk = {disk.device: disk for disk in self.Elocaldisk}
                elif len(self.Disks) > len(ldisk):
                    self.Elocaldisk = [disk_ifs(disk.device, disk.fstype, disk.opts)
                                       for disk in ldisk]
                    self.nowdisk = {disk.device: disk for disk in self.Elocaldisk}
                    DEL = True
                self.Disks = ldisk
            time.sleep(TIMESTEEP)  # Add a small sleep to prevent excessive CPU usage

    def stop(self):
        self.RUN = False


class UI:
    def __init__(self, icon: Image.Image):
        self.icon = icon
        self.ui = Icon('Disk Manager', self.icon, 'Disk Manager')
        self.um()
        self.lock = Lock()

    def run(self):
        self.uiMU = Thread(target=self.updatemune, daemon=True)
        self.uiMU.start()
        self.ui.run()

    def exit(self):
        if mess.askokcancel(LANG['title']['exit'], LANG['exit']):
            self.ui.stop()
            bk.stop()

    def reboot(self):
        global RE
        if mess.askokcancel(LANG['title']['reboot'], LANG['reboot']):
            self.ui.stop()
            bk.stop()
        RE = True

    def newdisk(self, disk: list[disk_ifs]):
        for new in disk:
            if os.path.exists(new.device):
                if mess.askokcancel('New Disk', f'新磁盘 {new.volume_info} {new.device} 你想打开他吗？'):
                    new.open()

    def info(self):
        from data import version_, author_, scrurl_
        mess.showinfo(LANG['title']['about'], LANG['about'] % {'version': version_, 'author': author_, 'srcurl': scrurl_})

    def um(self):
        m = []
        for disk in bk.nowdisk:
            info = ''
            if SETTING.get('showinfo'):
                info += f'\tinfo:{bk.nowdisk[disk].info}'
            m.append(MenuItem(disk+f'    {bk.nowdisk[disk].volume_info}'+info, bk.nowdisk[disk].open))
        m.append(MenuItem(LANG['title']['about'], self.info))
        m.append(MenuItem(LANG['title']['reload'], reload))
        m.append(MenuItem(LANG['title']['reboot'], self.reboot))
        m.append(MenuItem(LANG['title']['exit'], self.exit))
        self.ui.menu = Menu(*m)
        self.ui.update_menu()

    def updatemune(self):
        global NEW, DEL
        while bk.RUN:
            if NEW or DEL:
                with self.lock:
                    self.um()
                if NEW and SETTING.get('new-disk-open'):
                    Thread(target=self.newdisk, args=(TNEW,)).start()
                NEW = False
                DEL = False
            time.sleep(TIMESTEEP)  # Add a small sleep to prevent excessive CPU usage


while RE:
    reload()
    RE = False
    bk = Background()
    bk.run()
    ui = UI(ICON)
    ui.run()
