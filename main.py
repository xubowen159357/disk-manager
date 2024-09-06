import os
import sys
import wmi
import time
import psutil
import os.path
import psutil._common
import win32api
import json as js
import tkinter as tk
import tkinter.messagebox as mess

from PIL import Image
from threading import Thread, Lock
from pystray import MenuItem, Icon, Menu

ICONP = 'icon.ico'
SETTINGP = 'setting.json'
LANGP = 'lang.json'

Recurse = [ICONP, SETTINGP, LANGP]



class disk_ifs:
    def __init__(self, disk:psutil._common.sdiskpart) -> None:
        self.device = disk.device
        self.fstype = disk.fstype
        self.mountpoint = disk.mountpoint
        self.opts = disk.opts.split(',')
        self.info = ''
        self.volume_name = ''
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
            self.volume_name = win32api.GetVolumeInformation(self.device)[0]

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
    
    def disk_info(self):
        name=self.volume_name
        if name == '':
            name = 'null'
        toptk = tk.Toplevel()
        toptk.title(LANG['title']['disk-info']% {'diskname': name, 'mountpoint': self.mountpoint})
        toptk.iconbitmap(ICONP)
        toptk.geometry('500x700')
        if self.volume_name:
            used = psutil.disk_usage(self.mountpoint)
            usedl = tk.Label(toptk, text=LANG['label']['disk_info']['use']% {'used': used.used, 'total': used.total, 'free': used.free})
        else:usedl = tk.Label(toptk, text=LANG['label']['disk_info']['use-cannt-get'])
        infol = tk.Label(toptk, text=LANG['label']['disk_info']['disk-info']% {'diskname': name, 'mountpoint': self.mountpoint, 'fstype': self.fstype, 'info': self.info, 'opts': self.opts, "wmi-enabled": WMIE})
        usedl.place(x=0, y=0)
        infol.place(x=0, y=100)
        toptk.mainloop()


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
    global NEW, DEL, TNEW, SETTING, LANGA, LANG, TIMESTEEP, WMIE, WMI
    SETTING = js.loads(open(SETTINGP, 'r').read())
    LANGA = js.loads(open(LANGP, 'r', encoding='utf-8').read())
    TNEW = None
    NEW, DEL = False, False
    LANG = LANGA['zh']
    TIMESTEEP = SETTING.get('time')
    if TIMESTEEP is None:
        TIMESTEEP = 0.1
    if SETTING.get('lang'):LANG = LANGA[SETTING.get('lang')]
    else:LANG = LANGA['zh']
    if not RE:
        mess.showinfo(LANG['title']['reload'], LANG['reload'])
    if SETTING.get('wmi-enabled'):WMIE=True;WMI=wmi.WMI()
    else:WMIE=False


class Background:
    def __init__(self) -> None:
        self.RUN = True
        self.Disks = psutil.disk_partitions()
        self.Elocaldisk = [disk_ifs(disk)
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
                    self.Elocaldisk = [disk_ifs(disk)
                                       for disk in ldisk]
                    NEW = True
                    TNEW = [new for new in self.Elocaldisk if new.device not in self.nowdisk]
                    self.nowdisk = {disk.device: disk for disk in self.Elocaldisk}
                elif len(self.Disks) > len(ldisk):
                    self.Elocaldisk = [disk_ifs(disk)
                                       for disk in ldisk]
                    self.nowdisk = {disk.device: disk for disk in self.Elocaldisk}
                    DEL = True
                self.Disks = ldisk
            time.sleep(TIMESTEEP)  # Add a small sleep to prevent excessive CPU usage

    def stop(self):
        self.RUN = False


class UI:
    def __init__(self, icon: Image.Image):
        self.tk=tk.Tk()
        self.tk.wm_withdraw()
        self.icon = icon
        self.ui = Icon('Disk Manager', self.icon, 'Disk Manager')
        self.um()
        self.lock = Lock()
        self.diskinfok=None

    def run(self):
        self.uiMU = Thread(target=self.updatemune, daemon=True)
        self.uiMU.start()
        self.ui.run()

    def exit(self):
        if mess.askokcancel(LANG['title']['exit'], LANG['exit']):
            self.tk.destroy()
            self.ui.stop()
            bk.stop()

    def reboot(self):
        global RE
        if mess.askokcancel(LANG['title']['reboot'], LANG['reboot']):
            self.tk.destroy()
            self.ui.stop()
            bk.stop()
        RE = True

    def newdisk(self, disk: list[disk_ifs]):
        for new in disk:
            if os.path.exists(new.device):
                if mess.askokcancel('New Disk', LANG['info']['new-disk']%{'mountpoint': new.mountpoint, "diskname": new.volume_name}):
                    new.open()

    def info(self):
        from data import version_, author_, scrurl_
        mess.showinfo(LANG['title']['about'], LANG['about'] % {'version': version_, 'author': author_, 'srcurl': scrurl_})

    def profile_edit(self):
        def save():
            sSETTING={}
            sSETTING['time'] = timesetting.get()
            sSETTING['showinfo'] = showinfotk.get()
            sSETTING['lang'] = lang.get()
            sSETTING['new-disk-open'] = newdiskopen.get()
            sSETTING['wmi'] = wmi.get()
            if not (lang.get() == 'en' or lang.get() == 'zh'):mess.showerror(LANG['title']['profile-edit'], LANG['error']['profile-edit']['lang']);return None
            f=open('setting.json','w',encoding='utf-8')
            f.write(js.dumps(sSETTING, ensure_ascii=False, indent=4))
            f.close()
            mess.showinfo('info','Saved !')
        toptk = tk.Toplevel()
        toptk.title(LANG['title']['profile-edit'])
        toptk.resizable(False, False)
        toptk.iconbitmap(ICONP)
        toptk.geometry('500x400')
        timesetting = tk.IntVar(value=SETTING.get('time'));timesetting2 = tk.Label(toptk, text=LANG['label']['profile-edit']['time'])
        showinfotk = tk.BooleanVar(value=SETTING.get('showinfo'));showinfotk2 = tk.Label(toptk, text=LANG['label']['profile-edit']['showinfo'])
        lang = tk.StringVar(value=SETTING.get('lang'));lang2 = tk.Label(toptk, text=LANG['label']['profile-edit']['lang'])
        newdiskopen = tk.BooleanVar(value=SETTING.get('new-disk-open'));newdiskopen2 = tk.Label(toptk, text=LANG['label']['profile-edit']['new-disk-open'])
        timesettingtk = tk.Spinbox(toptk, from_=1, to=100, textvariable=timesetting, width=10)
        showinfotktk = tk.Checkbutton(toptk, textvariable=showinfotk, variable=showinfotk)
        langtk = tk.Spinbox(toptk, textvariable=lang)
        newdiskopentk = tk.Checkbutton(toptk, textvariable=newdiskopen, variable=newdiskopen)
        savebutton = tk.Button(toptk, text=LANG['label']['profile-edit']['save'], command=save)
        wmi = tk.BooleanVar(value=SETTING.get('wmi'))
        wmitk = tk.Checkbutton(toptk, textvariable=wmi, variable=wmi);wmi2 = tk.Label(toptk, text=LANG['label']['profile-edit']['wmi'])
        timesetting2.place(relx=0.1, rely=0.1)
        showinfotk2.place(relx=0.1, rely=0.3)
        lang2.place(relx=0.1, rely=0.5)
        newdiskopen2.place(relx=0.1, rely=0.7)
        timesettingtk.place(relx=0.5, rely=0.1)
        showinfotktk.place(relx=0.5, rely=0.2)
        langtk.place(relx=0.5, rely=0.3)
        newdiskopentk.place(relx=0.5, rely=0.4)
        wmitk.place(relx=0.5, rely=0.5)
        wmi2.place(relx=0.1, rely=0.5)
        savebutton.place(relx=0.4, rely=0.9)
        toptk.mainloop()

    def um(self):
        m = []
        for disk in bk.nowdisk:
            info = ''
            if SETTING.get('showinfo'):
                info += f'\tinfo:{bk.nowdisk[disk].info}'
            m.append(MenuItem(disk+f'    {bk.nowdisk[disk].volume_name}'+info, bk.nowdisk[disk].open))
        mc = [MenuItem(LANG['title']['profile-edit'], self.profile_edit), \
              MenuItem(LANG['title']['reboot'], self.reboot)]
        m.append(MenuItem(LANG['title']['disk_info'], Menu(*[MenuItem(bk.nowdisk[disk].mountpoint, bk.nowdisk[disk].disk_info) for disk in bk.nowdisk])))
        m.append(MenuItem(LANG['title']['more-config'], Menu(*mc)))
        m.append(MenuItem(LANG['title']['about'], self.info))
        m.append(MenuItem(LANG['title']['reload'], reload))
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
