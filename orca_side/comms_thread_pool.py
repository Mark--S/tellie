import threading

class CommsThreadPool:
    """A class for pooling threads - there should only ever be one thread pool.
    """
    ## singleton instance
    _instance = None

    class SingletonHelper:
        def __call__(self, *args, **kw):
            if CommsThreadPool._instance is None:
                object = CommsThreadPool()
                CommsThreadPool._instance = object

            return CommsThreadPool._instance

    get_instance = SingletonHelper()
    
    def __init__(self):
        if not CommsThreadPool._instance==None:
            raise Exception,"Only one thread pool allowed!"
        CommsThreadPool._instance=self
        self._threads = []
        self._thread_names = []

    def register_thread(self,thread):
        self._threads.append(thread)
        self._thread_names.append(thread.name)

    def unregister_thread(self,thread):
        print "REMOVE THREAD!"
        self._threads.remove(thread)
        self._thread_names.remove(thread.name)

    def get_thread_names(self):
        return self._thread_names

    def check_in_pool(self,name):
        return (name in self._thread_names)

    def get_thread_by_name(self,name):
        if self.check_in_pool(name):
            return self._threads[self._thread_names.index(name)]
        else:
            return None
            
