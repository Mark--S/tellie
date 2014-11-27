#!/usr/bin/env python
#
# comms_thread.py
#
# CommsThread
# LoadFireThread
#
# Thread that handles communication with TELLIE.
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# History:
#
###########################################

import xmlrpclib
import time
import threading
from common import tellie_logger
from core import tellie_exception
import comms_thread_pool
import Tkinter


class CommsThread(threading.Thread):
    """The base class of the Orca->Tellie communications threads.
    """

    def __init__(self, name, unique=False):
        """Initialise a thread, unique=True if only one thread of this name should exist
        """
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        if unique is True and thread_pool.check_in_pool(name):
            print "CANNOT START NEW THREAD"
            raise tellie_exception.ThreadException("Cannot start this thread!")
        super(CommsThread, self).__init__(name=name)
        thread_pool.register_thread(self)
        self._in_pool = True
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def stopped(self):
        return self._stop_flag

    def shutdown_thread(self):
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        thread_pool.unregister_thread(self)


class LoadFireThread(CommsThread):
    """The threading class for any load/fire operations
    """

    def __init__(self, server, tellie_options, fire_button, message_field, ellie_field):
        try:
            super(LoadFireThread, self).__init__(name="LOADnFIRE", unique=True)
            self.logger = tellie_logger.TellieLogger.get_instance()
            self.fire_button = fire_button
            self.tellie_options = tellie_options
            self.message_field = message_field
            self.ellie_field = ellie_field
            self.server = server
        except tellie_exception.ThreadException, e:
            raise tellie_exception.ThreadException(e)
        try:
            import tellie_database
            self.database = tellie_database.TellieDatabase.get_instance()
        except ImportError:
            print "WARNING: cannot use TELLIE DB"
            self.database = None

    def attempt_stop(self):
        '''Try to stop the tellie server.
        '''
        try:
            server.stop()
        except xmlrpclib.Fault, e:
            # Really need some kind of big warning here!
            pass

    def run(self):
        """Expect two python dicts with settings.  Should calculate a
        reasonable time delay from which PINOUT reads should be called.
        """
        load_settings = self.tellie_options.get_load_settings()
        fire_settings = self.tellie_options.get_fire_settings()
        pin_readings = {}
        #first load the settings
        for chan in load_settings:
            try:
                # TODO: compact these and the fire settings into an init_channel call
                self.server.select_channel(chan)
                self.server.set_pulse_height(load_settings[chan]["pulse_height"])
                self.server.set_pulse_width(load_settings[chan]["pulse_width"])
                self.server.set_fibre_delay(load_settings[chan]["fibre_delay"])
            except xmlrpclib.Fault, e:
                self.attempt_stop()
                self.save_errors("COMMUNICATION ERROR: %s" % e.faultString)
                self.shutdown_thread(True, "COMMUNICATION ERROR: %s" % (e.faultString))
                return
        #now fire the channels
        rate = float(self.tellie_options.get_pr())
        #sequence mode, additional 200us delay
        pin_readings = []
        sub_pulses = []
        total_pulses = 0
        for fire in fire_settings:
            total_pulses += fire["pulse_number"]
            t_wait = fire["pulse_number"] * (1./rate + 200e-6)
            if self.stopped(): #check at before sending any commands
                self.attempt_stop()
                self.save_errors("CALLED STOP")
                self.shutdown_thread(True, "CALLED STOP!")
                return
            try:
                # TODO: add in handling of multiple channels
                self.server.select_channel(fire["channels"][0])
                self.server.set_pulse_number(fire["pulse_number"])
                self.server.set_pulse_delay(fire["pulse_delay"])
                self.server.set_trigger_delay(fire["trigger_delay"])
                self.server.fire_sequence()
                t_start = time.time()
            except xmlrpclib.Fault, e:
                self.attempt_stop()
                self.save_errors("COMMUNICATION ERROR: %s" % (e.faultString))
                self.shutdown_thread(True, "COMMUNICATION ERROR: %s" % (e.faultString))
                return
            t_now = time.time()
            while (t_now - t_start) < t_wait:
                self.ellie_field.show_running()
                time.sleep(0.1)
                if not self.stopped():
                    t_now = time.time()
                else:
                    self.attempt_stop()
                    self.save_errors("CALLED STOP")
                    self.shutdown_thread(True, "CALLED STOP!")
                    return
            try:
                pin_out, channel_list = self.server.read_pin_sequence()
            except xmlrpclib.Fault, e:
                self.attempt_stop()
                self.save_errors("READ ERROR: %s" % (e.faultString))
                self.shutdown_thread(True, "READ ERROR: %s" % (e.faultString))
                return
            while not pin_out:
                time.sleep(0.1)
                if self.stopped():
                    #Stop the thread here!
                    self.attempt_stop()
                    self.save_errors("CALLED STOP")
                    self.shutdown_thread(1, "CALLED STOP!")
                    return
                try:
                    pin_out, channel_list = self.server.read_pin_sequence()
                except xmlrpclib.Fault, e:
                    self.attempt_stop()
                    self.save_errors("READ ERROR: %s" % (e.faultString))
                    self.shutdown_thread(True, "READ ERROR: %s" % (e.faultString))
                    return
            pin_readings.append(pin_out)
            sub_pulses.append(fire["pulse_number"])

        self.ellie_field.show_waiting()
        self.save_results(sub_pulses, pin_readings)
        average_pin = {}
        for i, pins in enumerate(pin_readings):
            print "PINS", pin_readings
            for channel in pins:
                if channel not in average_pin:
                    average_pin[channel] = 0
                print "CH:", channel, type(channel)
                print "PI", pins
                print "FI", fire_settings
                print "TO", total_pulses
                average_pin[channel] += float(pins[channel] * fire_settings[i]["pulse_number"]) / float(total_pulses)
        self.shutdown_thread(message="Sequence complete, PIN: %s"%(average_pin))

    def shutdown_thread(self, error_flag=None, message=None):
        if error_flag:
            self.ellie_field.show_stopped()
            self.message_field.show_warning(message)
            self.logger.warn(message)
        else:
            self.ellie_field.show_waiting()
            if message:
                self.message_field.show_message(message)
                self.logger.debug(message)
            else:
                self.logger.debug("Thread shutdown called, no message")
        self.fire_button.config(state = Tkinter.NORMAL)
        super(LoadFireThread, self).shutdown_thread()

    def save_results(self, sub_pulses, pin_readings):
        if not self.database:
            return
        if not self.database.db:
            return
        results = {"pins": pin_readings}
        results["pulses"] = sub_pulses
        results["run"] = int(self.tellie_options.get_run())
        results["load_settings"] = self.tellie_options.get_load_settings()
        results["fire_settings"] = self.tellie_options.get_full_fire_settings()
        results["type"] = "run"
        # Should the timestamp come from the TELLIE machine?
        results["timestamp"] = time.time()
        self.database.save(results)

    def save_errors(self, message):
        if not self.database:
            return
        if not self.database.db:
            return
        results = {"errors": message}
        results["run"] = int(self.tellie_options.get_run())
        results["load_settings"] = self.tellie_options.get_load_settings()
        results["fire_settings"] = self.tellie_options.get_full_fire_settings()
        results["type"] = "run"
        self.database.save(results)
