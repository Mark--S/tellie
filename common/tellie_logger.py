#!/usr/bin/env python
#
# tellie_logger:
#
# TellieLogger
#
# Simple logging class.
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# History:
#
###########################################

import os
import time


class TellieLogger:
    """A logger, only ever one.
    """

    ## singleton instance
    _instance = None

    class SingletonHelper:

        def __call__(self, *args, **kw):
            if TellieLogger._instance is None:
                object = TellieLogger()
                TellieLogger._instance = object

            return TellieLogger._instance

    get_instance = SingletonHelper()

    def __init__(self):
        """Should always be called from the __main__ function
        of the master script.
        """
        if not TellieLogger._instance is None:
            raise Exception("Only one logger allowed")
        TellieLogger._instance = self
        self._debug_mode = False

    def set_debug_mode(self, debug_mode):
        self._debug_mode = debug_mode

    def log(self, message):
        print "LOG:" + message

    def debug(self, message):
        if self._debug_mode:
            print str(time.time()) + " DEBUG: " + message
