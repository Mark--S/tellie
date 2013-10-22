#!/usr/bin/env python
#
# fake_gui
#
# OrcaGui: the main GUI
# TellieOptions
# MessageField
# EllieField
#
# Mock GUI while we wait for Orca integration.
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# History:
#
###########################################

import os
import json
import time
import math
import optparse
import Tkinter
import tellie_comms
import comms_thread
import comms_thread_pool
from common import tellie_logger, parameters


class TellieOptions(object):
    """Class that contains all the options from the GUI.
    """

    def __init__(self):
        self.run_tkstr = Tkinter.StringVar()
        self.ch_tkstr = Tkinter.StringVar()
        self.ph_tkstr = Tkinter.StringVar()
        self.pw_tkstr = Tkinter.StringVar()
        self.pn_tkstr = Tkinter.StringVar()
        self.pr_tkstr = Tkinter.StringVar()
        self.td_tkstr = Tkinter.StringVar()
        self.fd_tkstr = Tkinter.StringVar()

    def check_options(self):
        """Check all required options have been set
        """
        if not self.get_run() or \
                not self.get_ch() or \
                not self.get_ph() or \
                not self.get_pw() or \
                not self.get_pn() or \
                not self.get_pr() or \
                not self.get_td() or \
                not self.get_fd():
            return True
        return False

    def check_int_options(self):
        try:
            int(self.get_run())
            int(self.get_ch())
            int(self.get_ph())
            int(self.get_pw())
            int(self.get_pn())
            int(self.get_pr())
            int(self.get_td())
            int(self.get_fd())
            return False
        except (ValueError, TypeError):
            return True

    def validate_options(self):
        """Check that the option fields are appropriate
        """
        message = None
        messages = []
        pn = int(self.get_pn())
        td = float(self.get_td())
        fd = float(self.get_fd())
        #ensure ability to pulse more than 65025 pulses
        n_max_pn, final_pn = self.get_pn_sequence(pn)
        adjusted_pn, actual_pn, _, _ = parameters.pulse_number(pn)
        total_pn = n_max_pn * parameters.max_pulse_number + actual_pn
        adjusted_td, actual_td, _ = parameters.trigger_delay(td)
        adjusted_fd, actual_fd, _ = parameters.fibre_delay(fd)
        if adjusted_pn is True:
            self.pn_tkstr.set()
            messages += ["Pulse number adjusted from %d to %s" % (pn, total_pn)]
        if adjusted_td is True:
            self.td_tkstr.set(actual_td)
            messages += ["Trigger delay adjusted from %s to %s" % (td, actual_td)]
        if adjusted_fd is True:
            self.fd_tkstr.set(actual_fd)
            messages += ["Fibre delay adjusted from %s to %s" % (fd, actual_fd)]
        if messages!=[]:
            message = ", ".join(m for m in messages)
        return message

    def get_pn_sequence(self, pn):
        """Get the number of pulses required
        """
        n_max_pn = int(pn / parameters.max_pulse_number)
        final_pn = pn % parameters.max_pulse_number
        return n_max_pn, final_pn

    def get_load_settings(self):
        """Return options for loading of settings
        """
        load_dict = {int(self.get_ch()): {
                "pulse_height": int(self.get_ph()),
                "pulse_width": int(self.get_pw()),
                "fibre_delay": float(self.get_fd())}}
        return load_dict

    def get_fire_settings(self):
        """Return options for firing settings
        """
        n_max_pn, final_pn = self.get_pn_sequence(int(self.get_pn()))
        basic_dict = {"channels": [self.get_ch()],
                      "pulse_delay": float(self.get_pd()),
                      "trigger_delay": int(self.get_td())}
        load_dicts = []
        for i in range(n_max_pn):
            load_dicts.append(basic_dict)
            load_dicts[i]["pulse_number"] = parameters.max_pulse_number
        load_dicts.append(basic_dict)
        load_dicts[len(load_dicts)-1]["pulse_number"] = final_pn
        return load_dicts

    def get_full_fire_settings(self):
        """Return options settings, ignoring the number of sequences required
        """
        lodf_dict = {"channels": [self.get_ch()],
                     "pulse_delay": float(self.get_pd()),
                     "trigger_delay": int(self.get_td()),
                     "pulse_number": int(self.get_pn())}
        return load_dict

    def get_run(self):
        return self.run_tkstr.get()

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
        delay_s = 1.0 / rate
        delay_ms = delay_s * 1000
        print delay_ms
        return str(delay_ms)

    def get_td(self):
        return self.td_tkstr.get()

    def get_fd(self):
        return self.fd_tkstr.get()


class MessageField(object):
    """Where messages get displayed.
    """

    def __init__(self, parent):
        self._message = Tkinter.StringVar()
        self._label = Tkinter.Label(parent, textvariable=self._message)
        self._parent = parent #keep track

    def set_pos(self, column, row, columnspan):
        self._label.grid(column=column, row=row, columnspan=columnspan)

    def clear_message(self):
        self._message.set("")
        self._label.config(bg="white", fg="black")
        self._parent.update()

    def show_message(self, message):
        self._message.set(message)
        self._label.config(bg="white", fg="black")
        self._parent.update()

    def show_warning(self, message):
        self._message.set(message)
        self._label.config(bg="white", fg="red")
        self._parent.update()


class EllieField(object):
    """Pink elephant!
    """

    def __init__(self, parent):
        self._running_img = []
        self._waiting_img = None
        self._stopped_img = None
        self._label = Tkinter.Label(parent)
        self._state = None
        self._run_ctr = None
        self._parent = parent #keep track

    def set_pos(self, column, row, rowspan):
        self._label.grid(column=column, row=row, rowspan=rowspan)

    def add_running_img(self, image):
        self._running_img.append(Tkinter.PhotoImage(file=image))

    def set_waiting_img(self, image):
        self._waiting_img = Tkinter.PhotoImage(file=image)

    def set_stopped_img(self, image):
        self._stopped_img = Tkinter.PhotoImage(file=image)

    def show_running(self):
        if self._state != "running":
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
    """The main GUI.
    """

    def __init__(self, parent, presets_file, channels_file):
        Tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self._presets_file = presets_file
        self._channels_file = channels_file
        self._presets = json.load(open(presets_file))
        self._channels = json.load(open(channels_file))
        self.initialise()
        self.lf_thread = None #will always point to a thread

    def initialise(self):
        self.grid()
        #default settings to load
        self.tellie_options = TellieOptions()
        #preset run options
        Tkinter.Label(self, text="Channel presets").grid(column=0, row=1, columnspan=1)
        self.preset_option_tkstr = Tkinter.StringVar()
        preset_option = Tkinter.Entry(self, textvariable=self.preset_option_tkstr)
        preset_option.grid(column=0, row=2, columnspan=1)
        preset_button = Tkinter.Button(self, text=u"Load preset",
                                       command=self.select_preset)
        self.preset_list_tkstr = Tkinter.StringVar()
        preset_list = Tkinter.OptionMenu(self, self.preset_list_tkstr,
                                         "100000",
                                         "10000",
                                         "1000")
        preset_list.grid(column=0, row=3, columnspan=1)
        preset_button.grid(column=0, row=4, columnspan=1)
        #the run
        run_label = Tkinter.Label(self, text="Run")
        run_entry = Tkinter.Entry(self, textvariable=self.tellie_options.run_tkstr)
        run_label.grid(column=2, row=0, padx=13)
        run_entry.grid(column=3, row=0)
        #editable fields (filled with presets)
        ch_label = Tkinter.Label(self, text="Channel")
        ph_label = Tkinter.Label(self, text="Height")
        pw_label = Tkinter.Label(self, text="Width")
        pn_label = Tkinter.Label(self, text="Number")
        pr_label = Tkinter.Label(self, text="Rate")
        td_label = Tkinter.Label(self, text="Trigger delay")
        fd_label = Tkinter.Label(self, text="Fibre delay")
        ch_entry = Tkinter.Entry(self, textvariable=self.tellie_options.ch_tkstr)
        ph_entry = Tkinter.Entry(self, textvariable=self.tellie_options.ph_tkstr)
        pw_entry = Tkinter.Entry(self, textvariable=self.tellie_options.pw_tkstr)
        pn_entry = Tkinter.Entry(self, textvariable=self.tellie_options.pn_tkstr)
        pr_entry = Tkinter.Entry(self, textvariable=self.tellie_options.pr_tkstr)
        td_entry = Tkinter.Entry(self, textvariable=self.tellie_options.td_tkstr)
        fd_entry = Tkinter.Entry(self, textvariable=self.tellie_options.fd_tkstr)
        Tkinter.Label(self, text="Channel settings").grid(column=2, row=1, columnspan=2)
        ch_label.grid(column=2, row=2, padx=13)
        ph_label.grid(column=2, row=3, padx=13)
        pw_label.grid(column=2, row=4, padx=13)
        fd_label.grid(column=2, row=5, padx=13)
        Tkinter.Label(self, text="Global settings").grid(column=2, row=6, columnspan=2)
        pn_label.grid(column=2, row=7, padx=13)
        pr_label.grid(column=2, row=8, padx=13)
        td_label.grid(column=2, row=9, padx=13)
        ch_entry.grid(column=3, row=2)
        ph_entry.grid(column=3, row=3)
        pw_entry.grid(column=3, row=4)
        fd_entry.grid(column=3, row=5)
        pn_entry.grid(column=3, row=7)
        pr_entry.grid(column=3, row=8)
        td_entry.grid(column=3, row=9)
        #fire button!
        self.fire_button = Tkinter.Button(self, text=u"Fire!", command=self.load_and_fire)
        self.fire_button.grid(column=0, row=10, columnspan=2)
        #stop button!
        self.stop_button = Tkinter.Button(self, text=u"Stop!", command=self.stop_fire)
        self.stop_button.grid(column=2, row=10, columnspan=2)
        #message section
        self.message_field = MessageField(self)
        self.message_field.set_pos(column=0, row=11, columnspan=4)
        #image
        self.ellie_field = EllieField(self)
        self.ellie_field.set_pos(column=4, row=0, rowspan=8)
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
        elif not self.preset_list_tkstr.get():
            self.message_field.show_message("Choose a run setting from list")
            self.clear_preset()
        else:
            chan = -1
            try:
                chan = int(self.preset_option_tkstr.get())
            except:
                pass
            if chan < 1 or chan > 96:
                self.message_field.show_message("Enter a valid channel number")
                self.clear_preset()
            else:
                nphoton = self.preset_list_tkstr.get()
                self.tellie_options.ch_tkstr.set(self.preset_option_tkstr.get())
                #channel parameters
                self.tellie_options.ph_tkstr.set(self._channels[self.tellie_options.get_ch()][nphoton]["pulse_height"])
                self.tellie_options.pw_tkstr.set(self._channels[self.tellie_options.get_ch()][nphoton]["pulse_width"])
                self.tellie_options.fd_tkstr.set(self._channels[self.tellie_options.get_ch()][nphoton]["fibre_delay"])
                #global parameters
                self.tellie_options.pn_tkstr.set(self._presets["run_list"][nphoton]["pulse_number"])
                self.tellie_options.pr_tkstr.set(self._presets["run_list"][nphoton]["pulse_rate"])
                self.tellie_options.td_tkstr.set(self._presets["run_list"][nphoton]["trigger_delay"])

    def clear_preset(self):
        self.tellie_options.ch_tkstr.set("")
        self.tellie_options.ph_tkstr.set("")
        self.tellie_options.pw_tkstr.set("")
        self.tellie_options.pn_tkstr.set("")
        self.tellie_options.pr_tkstr.set("")
        self.tellie_options.td_tkstr.set("")
        self.tellie_options.fd_tkstr.set("")

    def load_and_fire(self):
        self.message_field.clear_message()
        if self.tellie_options.check_options():
            self.message_field.show_message("Missing some settings, cannot run!")
        elif self.tellie_options.check_int_options():
            self.message_field.show_message("Some options are not ints, cannot run!")
        else:
            message = self.tellie_options.validate_options()
            if message:
                self.message_field.show_message(message)
            self.fire_button.config(state = Tkinter.DISABLED)
#            try:
            if True:
                self.lf_thread = comms_thread.LoadFireThread(self.tellie_options, self.fire_button, self.message_field, self.ellie_field)
                self.lf_thread.start()
#            except:
#                print "Unable to start thread!"
        self.ellie_field.show_waiting()

    def stop_fire(self):
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        if thread_pool.get_thread_by_name("LOADnFIRE"):
            #need to send a stop flag to the thread
            self.message_field.show_message("STOPPING...")
            self.lf_thread.stop()
            ctr = 1
            while thread_pool.get_thread_by_name("LOADnFIRE"):
                ctr += 1
                if ctr > 100000:#large number...
                    break
            print "THREADS:", thread_pool._threads
        #send a stop command, just in case
        error_state, response = tellie_comms.send_stop_command()
        if error_state:
            self.message_field.show_warning("ERROR ON STOP COMMAND!")
        else:
            self.message_field.show_message("STOPPED")

    def safe_exit(self):
        self.stop_fire()
        self.destroy()


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d", dest="debug", action="store_true", default=False, help="Debug mode")
    parser.add_option("-a", dest="address", default=None, help="Server address (default 127.0.0.1)")
    parser.add_option("-p", dest="port", default=None, help="Server port (default 50050)")
    parser.add_option("-l", dest="usedb", action="store_true", help="Upload results to database")
    (options, args) = parser.parse_args()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(options.debug)
    database = None
    if options.usedb:
        try:
            import tellie_database
            database = tellie_database.TellieDatabase.get_instance()
            database.login("http://127.0.0.1:5984", "tellie")
        except ImportError:
            print "WARNING: cannot use TELLIE DB"
    app = OrcaGui(None, "orca_side/PRESETS.js", "orca_side/CHANNELS.js")
    app.title = "TELLIE Control"
    if options.address:
        tellie_comms.HOST = options.address
    if options.port:
        tellie_comms.PORT = int(options.port)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.safe_exit()
