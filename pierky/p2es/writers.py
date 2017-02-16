# This code is Copyright 2014-2017 by Pier Carlo Chiodi.
# See full license in LICENSE file.

import datetime
import json
try:
    from queue import Empty
except:
    from Queue import Empty

from errors import P2ESError
from es import *
from threads import P2ESThread

class BaseWriterThread(P2ESThread):

    def __init__(self, idx, CONFIG, errors_queue, ts, queue, flush_size):
        P2ESThread.__init__(self, idx, CONFIG, errors_queue)
        self.ts = ts
        self.queue = queue
        self.es_docs = []
        self.flush_size = flush_size
        self.done = False

    def _flush(self, output):
        raise NotImplementedError()

    def _format_output(self):
        out = ''
        for dic in self.es_docs:
            out += '{"index":{}}' + '\n'
            out += json.dumps(dic) + '\n'
        return out

    def flush(self):
        if self.es_docs:
	    try:
	        output = self._format_output()
	        self._flush(output)
            finally:
                self.es_docs = []

    def run(self):
        while True:
            dic = None
            try:
                dic = self.queue.get(block=True, timeout=1)

                if dic is None:
                    #self.flush()
		    break
                    #return

                dic['@timestamp'] = self.ts
                self.es_docs.append(dic)
                if len(self.es_docs) >= self.flush_size:
                    self.flush()
            except Empty:
                pass
            except Exception as e:
                self.errors_queue.put(str(e))
        self.flush()

class ESWriterThread(BaseWriterThread):

    def __init__(self, *args, **kwargs):
        BaseWriterThread.__init__(self, *args, **kwargs)

        # Preparing for HTTP authentication
        prepare_for_http_auth(self.CONFIG)

        # Creating index
        self.index_name = datetime.datetime.now().strftime(
            self.CONFIG['ES_IndexName']
        )
        try:
            create_index(self.index_name, self.CONFIG)
        except P2ESError as e:
            raise P2ESError(
                "Error while creating index {}: {}".format(
                    self.index_name, str(e)
                )
            )

    def _flush(self, output):
        send_to_es(self.CONFIG, self.index_name, output)

class PrintOnlyWriterThread(BaseWriterThread):

    def _flush(self, output):
        print(output)
