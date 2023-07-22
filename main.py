import tkinter
import tkinter.messagebox
import tkinter.ttk
import winsound
import psutil
from time import sleep
import time
import pystray
import PIL.Image
import ctypes
import os
import configparser
import threading

STIME = 10
MINP = 5
MAXP = 95
BPDUR = 650
BPFRMIN = 3000
BPFRMAX = 1000
ICON = "logo.png"

def sgn(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    else:
        return 0

def apply(offset, minp, maxp):
    global STIME
    global MINP
    global MAXP
    STIME = int(offset)
    MINP = int(minp)
    MAXP = int(maxp)

def is_ru():
    u = ctypes.windll.LoadLibrary("user32.dll")
    pf = getattr(u, "GetKeyboardLayout")
    return hex(pf(0)) == '0x4190419'

def key_handler(e):
    if is_ru():
        ctrl = (e.state & 0x4) != 0
        if e.keycode == 67 and ctrl:
            e.widget.event_generate("<<Copy>>")
        elif e.keycode == 86 and ctrl:
            e.widget.event_generate("<<Paste>>")
        elif e.keycode == 65 and ctrl:
            e.widget.event_generate("<<SelectAll>>")
        elif e.keycode == 88 and ctrl:
            e.widget.event_generate("<<Cut>>")

def check(offset, minp, maxp, is_run):
    is_warned = 0
    prevVol = -1
    prevTime = -1
    urgency = 1.0
    while is_run():
        offN = offset()
        minN = minp()
        maxN = maxp()
        btr = psutil.sensors_battery()
        if not btr.power_plugged:
            if is_warned == 1:
                is_warned = 0
            if btr.percent <= minN and not is_warned:
                winsound.Beep(BPFRMIN, BPDUR)
                tkinter.messagebox.showerror(title="Minimum is reached!", message="Connect the charger.")
                is_warned = -1
        elif btr.power_plugged:
            if is_warned == -1:
                is_warned = 0
            if btr.percent >= maxN and not is_warned:
                winsound.Beep(BPFRMAX, BPDUR)
                tkinter.messagebox.showerror(title="Maximum is reached!", message="Disconnect the charger.")
                is_warned = 1
        if btr.secsleft < 0:
            urgency = 1
        elif prevVol > 0:
            diff = btr.secsleft - prevVol + (time.time() - prevTime)
            urgency = (abs(diff/offN)+1)**(-sgn(diff))
        prevVol = btr.secsleft
        prevTime = time.time()
        sleep(offN/urgency)

def settings():
    def save(offset: str, minp: str, maxp: str):
        if not (offset.isdigit() and minp.isdigit() and maxp.isdigit()):
            tkinter.messagebox.showerror(title="Error", message="Enter whole numbers.")
            return
        apply(offset, minp, maxp)
        config = configparser.ConfigParser()
        config['DEFAULT'] = {'offset': offset, 'min': minp, 'max': maxp}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        tkinter.messagebox.showinfo(title="Ready!", message="Settings are saved.")

    root = tkinter.Tk()
    root.title('Battery checker settings')
    root.iconphoto(False, tkinter.PhotoImage(file=ICON))
    root.eval('tk::PlaceWindow . center')
    root.bind('<Key>', key_handler)

    frm = tkinter.ttk.Frame(root, padding=50)
    frm.grid()

    tkinter.ttk.Label(frm, text="Offset").grid(column=0, row=0, sticky=tkinter.W)
    offsetForm = tkinter.ttk.Entry(frm, width=15)
    offsetForm.grid(column=0, row=1)

    tkinter.ttk.Label(frm, text="Minimum").grid(column=0, row=2, sticky=tkinter.W)
    minForm = tkinter.ttk.Entry(frm, width=15)
    minForm.grid(column=0, row=3)

    tkinter.ttk.Label(frm, text="Maximum").grid(column=0, row=4, sticky=tkinter.W)
    maxForm = tkinter.ttk.Entry(frm, width=15)
    maxForm.grid(column=0, row=5)

    tkinter.ttk.Button(frm, text="Save", command=lambda: save(offsetForm.get(), minForm.get(), maxForm.get()), width=10).grid(column=0, row=6)

    if os.path.exists('./config.ini'):
        config = configparser.ConfigParser()
        config.read('config.ini')
        offsetForm.insert(0, config['DEFAULT']['offset'])
        minForm.insert(0, config['DEFAULT']['min'])
        maxForm.insert(0, config['DEFAULT']['max'])
        apply(config['DEFAULT']['offset'], config['DEFAULT']['min'], config['DEFAULT']['max'])
    else:
        offsetForm.insert(0, str(STIME))
        minForm.insert(0, str(MINP))
        maxForm.insert(0, str(MAXP))

    root.mainloop()

if __name__ == '__main__':
    def close():
        global is_run
        icon.stop()
        is_run = False
        t.join()
    is_run = True
    icon = pystray.Icon('Battery checker', PIL.Image.open(ICON), menu=pystray.Menu(
        pystray.MenuItem('Settings', settings),
        pystray.MenuItem('Close', close)
    ))
    if os.path.exists('./config.ini'):
        config = configparser.ConfigParser()
        config.read('config.ini')
        apply(config['DEFAULT']['offset'], config['DEFAULT']['min'], config['DEFAULT']['max'])
    t = threading.Thread(target=check, args=(lambda: STIME, lambda: MINP, lambda: MAXP, lambda: is_run))
    t.start()
    icon.run()