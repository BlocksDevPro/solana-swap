import time


class Group:
    def __init__(self, username, timeout):
        self.username = username
        self.timeout = timeout
        self.last_reponse = None
    
    @property 
    def is_timeout(self):
        return (not self.last_reponse or (self.last_reponse + self.timeout) < time.time())
    
    @property
    def set_timeout(self):
        self.last_reponse = time.time()
        return self.last_reponse