class StreamHolder:
    name = ""
    def __init__(self, session):
        self._session = session
        self._msg = ""
    
    def write(self, msg):
        self._msg += "%s" % msg
    
    def flush(self):
        msg = "<pre>%s</pre>" % self._msg
        self._session.logger.info(msg, is_html=True)
        self._msg = ""  