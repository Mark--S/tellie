import os
import json
import time
import optparse
import Tkinter
import tellie_comms
import comms_thread
import comms_thread_pool
from common import tellie_logger

class TellieOptions(object):
    def __init__(self):
        self.ch_tkstr = Tkinter.StringVar()
        self.ph_tkstr = Tkinter.StringVar()
        self.pw_tkstr = Tkinter.StringVar()
        self.pn_tkstr = Tkinter.StringVar()
        self.pr_tkstr = Tkinter.StringVar()
    def check_options(self):
        """Check all required options have been set
        """
        if not self.get_ch() or \
                not self.get_ph() or \
                not self.get_pw() or \
                not self.get_pn() or \
                not self.get_pr():
            return True
        return False
    def get_load_settings(self):
        """Return options for loading of settings
        """
        load_dict = {int(self.get_ch()):{"pulse_height":int(self.get_ph()),
                                         "pulse_width":int(self.get_pw())}}
        return load_dict
    def get_fire_settings(self):
        """Return options for firing settings
        """
        load_dict = {int(self.get_ch()):{"pulse_number":int(self.get_pn()),
                                         "pulse_delay":float(self.get_pd())}}
        return load_dict
    def get_ch(self):
        return self.ch_tkstr.get()
    def get_ph(self):
        return self.ph_tkstr.get()
    def get_pw(self):
        return self.pw_tkstr.get()
    def get_pn(self):
        return self.pn_tkstr.get()
    def get_pr(self):
        return self.pr_tkstr.get()
    def get_pd(self):
        rate = float(self.get_pr())#Hz
        delay_s = 1/rate
        delay_ms = delay_s * 1000
        print delay_ms
        return str(delay_ms)

class MessageField(object):
    def __init__(self,parent):
        self._message = Tkinter.StringVar()
        self._label = Tkinter.Label(parent,textvariable=self._message)
        self._parent = parent #keep track
    def set_pos(self,column,row,columnspan):
        self._label.grid(column=column,row=row,columnspan=columnspan)
    def clear_message(self):
        self._message.set("")
        self._label.config(bg="white",fg="black")
        self._parent.update()
    def show_message(self,message):
        self._message.set(message)
        self._label.config(bg="white",fg="black")
        self._parent.update()
    def show_warning(self,message):
        self._message.set(message)
        self._label.config(bg="white",fg="red")
        self._parent.update()

class EllieField(object):
    def __init__(self,parent):#,running,waiting,stopped):
        self._running_img = []
        self._waiting_img = None
        self._stopped_img = None
        self._label = Tkinter.Label(parent)
        self._state = None
        self._run_ctr = None
        self._parent = parent #keep track
    def set_pos(self,column,row,rowspan):
        self._label.grid(column=column,row=row,rowspan=rowspan)
    def add_running_img(self,image):
        self._running_img.append(Tkinter.PhotoImage(file=image))
    def set_waiting_img(self,image):
        self._waiting_img = Tkinter.PhotoImage(file=image)
    def set_stopped_img(self,image):
        self._stoppped_img = Tkinter.PhotoImage(file=image)
    def show_running(self):
        if self._state!="running":
            self._run_ctr = 0
            self._run_num = len(self._running_img)
            self._state = "running"
        counter = self._run_ctr % self._run_num
        self._label.configure(image=self._running_img[counter])
        self._label.image = self._running_img[counter]
        self._run_ctr += 1
        self._parent.update()
    def show_waiting(self):
        self._state = "waiting"
        self._label.configure(image=self._waiting_img)
        self._label.image = self._waiting_img
        self._parent.update()
    def show_stopped(self):
        self._state = "stopped"
        self._label.configure(image=self._stopped_img)
        self._label.image = self._stopped_img
        self._parent.update()

class OrcaGui(Tkinter.Tk):
    def __init__(self,parent,presets_file):        
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self._presets_file = presets_file
        self._presets = json.load(open(presets_file))
        self.initialise()
        self.lf_thread = None #will always point to a thread
    def initialise(self):
        self.grid()
        #default settings to load
        self.tellie_options = TellieOptions()
        #preset menu listings
        Tkinter.Label(self,text="Channel presets").grid(column=0,row=0)
        self.preset_option_tkstr = Tkinter.StringVar()
        preset_option = Tkinter.Entry(self,textvariable=self.preset_option_tkstr)
        #preset_option = Tkinter.OptionMenu(self, self.preset_option_tkstr,
        #                                   1,2,3,4,5,6,7,8)
        preset_option.grid(column=0,row=1)
        preset_button = Tkinter.Button(self,text=u"Load preset",
                                       command=self.select_preset)
        preset_button.grid(column=0,row=2)
        #editable fields (filled with presets)
        ch_label = Tkinter.Label(self,text="Channel")
        ph_label = Tkinter.Label(self,text="Height")
        pw_label = Tkinter.Label(self,text="Width")
        pn_label = Tkinter.Label(self,text="Number")
        pr_label = Tkinter.Label(self,text="Rate")
        ch_entry = Tkinter.Entry(self,textvariable=self.tellie_options.ch_tkstr)
        ph_entry = Tkinter.Entry(self,textvariable=self.tellie_options.ph_tkstr)
        pw_entry = Tkinter.Entry(self,textvariable=self.tellie_options.pw_tkstr)
        pn_entry = Tkinter.Entry(self,textvariable=self.tellie_options.pn_tkstr)
        pr_entry = Tkinter.Entry(self,textvariable=self.tellie_options.pr_tkstr)
        ch_label.grid(column=1,row=0,padx=13)
        ph_label.grid(column=1,row=1,padx=13)
        pw_label.grid(column=1,row=2,padx=13)
        pn_label.grid(column=1,row=3,padx=13)
        pr_label.grid(column=1,row=4,padx=13)
        ch_entry.grid(column=2,row=0)
        ph_entry.grid(column=2,row=1)
        pw_entry.grid(column=2,row=2)
        pn_entry.grid(column=2,row=3)
        pr_entry.grid(column=2,row=4)
        #fire button!
        self.fire_button = Tkinter.Button(self,text=u"Fire!",command=self.load_and_fire)
        self.fire_button.grid(column=0,row=5,columnspan=1)
        #stop button!
        self.stop_button = Tkinter.Button(self,text=u"Stop!",command=self.stop_fire)
        self.stop_button.grid(column=2,row=5,columnspan=1)
        #message section
        self.message_field = MessageField(self)
        self.message_field.set_pos(column=0,row=6,columnspan=3)
        #image
        self.ellie_field = EllieField(self)
        self.ellie_field.set_pos(column=3,row=0,rowspan=6)
        self.ellie_field.add_running_img('orca_side/img/ellie_blue.gif')
        self.ellie_field.add_running_img('orca_side/img/ellie_turquoise.gif')
        self.ellie_field.add_running_img('orca_side/img/ellie_green.gif')
        self.ellie_field.add_running_img('orca_side/img/ellie_magenta.gif')
        self.ellie_field.set_waiting_img('orca_side/img/ellie_wait.gif')
        self.ellie_field.set_stopped_img('orca_side/img/ellie_stop.gif')
        self.ellie_field.show_waiting()

    def select_preset(self):
        self.message_field.clear_message()
        if not self.preset_option_tkstr.get():
            self.message_field.show_message("Enter a channel to load presets")
            self.clear_preset()
        else:
            chan = -1
            try:
                chan = int(self.preset_option_tkstr.get())
            except:
                pass
            if chan<1 or chan>92:
                self.message_field.show_message("Enter a valid channel number")                
                self.clear_preset()
            else:
                self.tellie_options.ch_tkstr.set(self.preset_option_tkstr.get())        
                self.tellie_options.ph_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_height"])
                self.tellie_options.pw_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_width"])
                self.tellie_options.pn_tkstr.set(self._presets[self.tellie_options.get_ch()]["nb_pulses"])
                self.tellie_options.pr_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_rate"])

    def clear_preset(self):
        self.tellie_options.ch_tkstr.set("")        
        self.tellie_options.ph_tkstr.set("")
        self.tellie_options.pw_tkstr.set("")
        self.tellie_options.pn_tkstr.set("")
        self.tellie_options.pr_tkstr.set("")
        
    def load_and_fire(self):
        self.message_field.clear_message()
        if self.tellie_options.check_options():
            self.message_field.show_message("Missing some settings, cannot run!")
        else:
            self.fire_button.config(state = Tkinter.DISABLED)
            try:
                self.lf_thread = comms_thread.LoadFireThread(self.tellie_options,self.fire_button,self.message_field)
                self.lf_thread.start()
            except:
                print "Unable to start thread!"

    def stop_fire(self):
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        if thread_pool.get_thread_by_name("LOADnFIRE"):
            #need to send a stop flag to the thread
            self.message_field.show_message("STOPPING...")
            self.lf_thread.stop()
            ctr = 1
            while thread_pool.get_thread_by_name("LOADnFIRE"):
                ctr+=1
                if ctr>100000:#large number...
                    break
            print "THREADS:",thread_pool._threads
        #send a stop command, just in case
        error_state,response = tellie_comms.send_stop_command()
        if error_state:
            self.message_field.show_warning("ERROR ON STOP COMMAND!")
        else:
            self.message_field.show_message("STOPPED")            
                            
    def safe_exit(self):
        self.stop_fire()
        self.destroy()

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d",dest="debug",action="store_true",default=False,help="Debug mode")
    (options, args) = parser.parse_args()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(options.debug)
    app = OrcaGui(None,"orca_side/PRESETS.js")
    app.title = "TELLIE Control"
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.safe_exit()
