import os
import json
import time
import optparse
import Tkinter
import orca_logger
import tellie_comms
import comms_thread
import comms_thread_pool

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
        rate = float(self.get_pr())
        delay = 1/rate
        delay_ms = int(delay*1000)
        delay_us_not = int((delay*1000 - delay_ms)*1000)
        delay_us = int((delay*1000 - delay_ms)*1000/4)
        print delay_ms
        print delay_us,delay_us_not
        delay_str = "{0:003d}".format(delay_ms)+"."+"{0:003d}".format(delay_us)
        return delay_str

class MessageField(object):
    def __init__(self,parent):
        self._message = Tkinter.StringVar()
        self._label = Tkinter.Label(parent,textvariable=self._message)
    def set_pos(self,column,row,columnspan):
        self._label.grid(column=0,row=6,columnspan=3)
    def clear_message(self):
        self._message.set("")
        self._label.config(bg="white",fg="black")
    def show_message(self,message):
        self._message.set(message)
        self._label.config(bg="white",fg="black")
    def show_warning(self,message):
        self._message.set(message)
        self._label.config(bg="white",fg="red")

class OrcaGui(Tkinter.Tk):
    def __init__(self,parent,presets_file):        
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self._presets_file = presets_file
        self._presets = json.load(open(presets_file))
        self.initialise()
    def initialise(self):
        self.grid()
        #default settings to load
        self.tellie_options = TellieOptions()
        #preset menu listings
        Tkinter.Label(self,text="Channel presets").grid(column=0,row=0)
        self.preset_option_tkstr = Tkinter.StringVar()
        preset_option = Tkinter.OptionMenu(self, self.preset_option_tkstr,
                                           1,2,3,4,5,6,7,8)
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

    def select_preset(self):
        self.message_field.clear_message()
        if not self.preset_option_tkstr.get():
            self.message_field.show_message("Select a preset from the list")
        else:
            self.tellie_options.ch_tkstr.set(self.preset_option_tkstr.get())        
            self.tellie_options.ph_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_height"])
            self.tellie_options.pw_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_width"])
            self.tellie_options.pn_tkstr.set(self._presets[self.tellie_options.get_ch()]["nb_pulses"])
            self.tellie_options.pr_tkstr.set(self._presets[self.tellie_options.get_ch()]["pulse_rate"])
        
    def load_and_fire(self):
        self.message_field.clear_message()
        if self.tellie_options.check_options():
            self.message_field.show_message("Missing some settings, cannot run!")
        else:
            self.fire_button.config(state = Tkinter.DISABLED)
            try:
                lf_thread = comms_thread.LoadFireThread(self.tellie_options,self.fire_button,self.message_field)
                lf_thread.start()
            except:
                print "Unable to start thread!"

    def stop_fire(self):        
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        if thread_pool.get_thread_by_name("LOADnFIRE"):
            #need to send a stop flag to the thread
            self.message_field.show_message("STOPPING...")
            thread_pool.get_thread_by_name("LOADnFIRE").stop()            
            check = True
            while check:
                check = thread_pool.get_thread_by_name("LOADnFIRE")
                print "..."
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
    logger = orca_logger.OrcaLogger.get_instance()
    logger.set_debug_mode(options.debug)
    app = OrcaGui(None,"orca_side/PRESETS.js")
    app.title = "TELLIE Control"
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.safe_exit()
