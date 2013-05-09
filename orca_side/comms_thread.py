
import time
import threading
from common import comms_flags, tellie_logger
import comms_thread_pool
import tellie_comms
import Tkinter

class CommsThread(threading.Thread):
    """The base class of the Orca->Tellie communications threads.
    """
    def __init__(self,name,unique=False):
        """Initialise a thread, unique=True if only one thread of this name should exist
        """
        thread_pool = comms_thread_pool.CommsThreadPool.get_instance()
        if unique==True and thread_pool.check_in_pool(name):
            print "CANNOT START NEW THREAD"
            raise Exception,"Cannot start this thread!"
        super(CommsThread,self).__init__(name=name)
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
    def __init__(self,tellie_options,fire_button,message_field):
        try:
            super(LoadFireThread,self).__init__(name="LOADnFIRE",unique=True)
            self.logger = tellie_logger.TellieLogger.get_instance()
            self.fire_button = fire_button
            self.tellie_options = tellie_options
            self.message_field = message_field
        except:
            raise Exception,"Cannot start this thread"
    def run(self):
        """Expect two python dicts with settings.  Should calculate a 
        reasonable time delay from which PINOUT reads should be called.
        """
        load_settings = self.tellie_options.get_load_settings()
        fire_settings = self.tellie_options.get_fire_settings()
        pin_readings = {}
        if len(load_settings)!=1 or len(fire_settings)!=1:
            #Can only operate with on channel currently
            #No current plans to implement more!
            print "Only one channel at a time! WILL NOT FIRE"
            raise Exception
        for chan in load_settings:
            n_fire = fire_settings[chan]["pulse_number"]
            rate = float(self.tellie_options.get_pr())
            t_wait = n_fire/rate
            t_start = time.time()
            if self.stopped(): #check at before sending any commands
                self.shutdown_thread(1,"CALLED STOP!")
                return
            error_state,response = tellie_comms.send_init_command(load_settings)
            if error_state:
                self.shutdown_thread(error_state,"COMMUNICATION ERROR: %s"%(response))
                return
            if self.stopped(): #check at before sending any commands
                self.shutdown_thread(1,"CALLED STOP!")
                return
            error_state,response = tellie_comms.send_fire_command(fire_settings)
            if error_state:
                self.shutdown_thread(error_state,"COMMUNICATION ERROR: %s"%(response))
                return
            t_now = time.time()
            while (t_now - t_start) < t_wait:
                time.sleep(0.1)
                if not self.stopped():
                    t_now = time.time()
                else:
                    #Stop the thread here!
                    self.shutdown_thread(1,"CALLED STOP!")
                    return
            error_state,response = tellie_comms.send_read_command()
            if error_state:
                self.shutdown_thread(error_state,"READ ERROR: %s"%(response))
                return
            while response == comms_flags.tellie_notready:
                time.sleep(0.1)
                error_state,response = tellie_comms.send_read_command()
                if self.stopped():
                    #Stop the thread here!
                    self.shutdown_thread(1,"CALLED STOP!")
                    return
                if error_state:
                    self.shutdown_thread(error_state,"READ ERROR: %s"%(response))
                    return
            try:
                pin_readings[chan] = response.split("|")[1]
            except IndexError:
                self.shutdown_thread(1,"PIN READ ERROR: %s"%response)
                return
        self.shutdown_thread(message="Sequence complete, PIN: %s"%(pin_readings))
    def stop(self):
        super(LoadFireThread,self).stop()
    def stopped(self):
        return super(LoadFireThread,self).stopped()
    def shutdown_thread(self,error_flag=None,message=None):
        if error_flag:
            self.message_field.show_warning(message)
        else:
            if message:
                self.message_field.show_message(message)                
        self.fire_button.config(state = Tkinter.NORMAL)
        super(LoadFireThread,self).shutdown_thread()
