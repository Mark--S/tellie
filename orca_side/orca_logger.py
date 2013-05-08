import os

class OrcaLogger:
    """A logger, only ever one.
    """
    ## singleton instance
    _instance = None

    class SingletonHelper:
        def __call__(self, *args, **kw):
            if OrcaLogger._instance is None:
                object = OrcaLogger()
                OrcaLogger._instance = object

            return OrcaLogger._instance

    get_instance = SingletonHelper()

    def __init__(self):
        """Should always be called from the __main__ function
        of the master script.
        """
        if not OrcaLogger._instance==None:
            raise Exception,"Only one logger allowed"
        OrcaLogger._instance=self
        self._debug_mode = False

    def set_debug_mode(self,debug_mode):
        self._debug_mode = debug_mode

    def log(self,message):
        print "LOG:"+message

    def debug(self,message):
        if self._debug_mode:
            print "DEBUG:"+message
