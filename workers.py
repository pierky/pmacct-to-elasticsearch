import datetime
import json
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty
import threading

from errors import P2ESError
from es import *
from transformations import *

class BaseWriterThread(threading.Thread):

    def __init__(self, CONFIG, ts, queue, flush_size):
        threading.Thread.__init__(self)
        self.CONFIG = CONFIG
        self.ts = ts
        self.queue = queue
        self.done = False
        self.es_docs = []
        self.flush_size = flush_size

    def _flush(self, output):
        raise NotImplementedError()

    def _format_output(self):
        out = ''
        for dic in self.es_docs:
            out += '{"index":{}}' + '\n'
            out += json.dumps(dic) + '\n'
        return out

    def flush(self):
        self._flush(self._format_output())
        self.es_docs = []

    def run(self):
        while True:
            if self.done:
                print("Writer - Done")
                self.flush()
                return

            try:
                dic = self.queue.get(block=True, timeout=1)
                dic['@timestamp'] = self.ts
                self.es_docs.append(dic)
                if len(self.es_docs) >= self.flush_size:
                    self.flush()
            except Empty:
                print("Writer - Empty")
                pass
        print("Writer - Quitting")

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
            create_index(index_name, self.CONFIG["CONF_DIR"], self.CONFIG)
        except P2ESError as e:
            raise P2ESError(
                "Error while creating index {}: {}".format(
                    index_name, str(e)
                )
            )

    def _flush(self, output):
        send_to_es(self.CONFIG, self.index_name, output)

class PrintOnlyWriterThread(BaseWriterThread):

    def _flush(self, output):
        raise P2ESError("test")
        print(output)

class BaseReaderThread(threading.Thread):

    def __init__(self, idx, CONFIG, writer_queue):
        threading.Thread.__init__(self)
        self.idx = idx
        self.CONFIG = CONFIG
        self.queue = Queue()
        self.writer_queue = writer_queue
        self.done = False

    def run(self):
        while True:
            if self.done:
                print("Reader {} - Done".format(self.idx))
                return

            try:
                line = self.queue.get(block=True, timeout=1)
                self.writer_queue.put(self.parse(line))
            except Empty:
                print("Reader {} - Empty".format(self.idx))
                pass
        print("Reader {} - Quitting".format(self.idx))

    @staticmethod
    def expand_data_macros(s, dic):
        if "$" in s:
            res = s
            for k in dic:
                res = res.replace("${}".format(k), str(dic[k]))
            return res
        return s

    def apply_transformation(self, dic, tr):
        if not parse_conditions(tr['Conditions'], dic):
            return

        for action in tr['Actions']:
            action_type = action['Type']

            if action_type == 'AddField':
                new_val = self.expand_data_macros(action['Value'], dic)
                dic[action['Name']] = new_val

            elif action_type == 'AddFieldLookup':
                if action['LookupFieldName'] not in dic:
                    new_val = None

                    if str(dic[action['LookupFieldName']]) in action['LookupTable']:
                        new_val = action['LookupTable'][str(dic[action['LookupFieldName']])]
                    else:
                        if "*" in action['LookupTable']:
                            new_val = action['LookupTable']['*']

                    if new_val:
                        dic[action['Name']] = self.expand_data_macros(new_val, dic)
                                    
            elif action_type == 'DelField':
                if action['Name'] in dic:
                        del dic[action['Name']]

    def apply_transformations(self, dic):
        if 'Transformations' not in self.CONFIG:
            return

        for tr in self.CONFIG['Transformations']:
            self.apply_transformation(dic, tr)

    def parse(self, line):
        dic = self._parse(line)
        self.apply_transformations(dic)
        return dic

    def _parse(self, line):
        raise NotImplementedError()

class JSONReaderThread(BaseReaderThread):

    def _parse(self, line):
        return json.loads(line)
