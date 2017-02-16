# This code is Copyright 2014-2017 by Pier Carlo Chiodi.
# See full license in LICENSE file.

import json
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty

from transformations import *
from threads import P2ESThread
import sys

class BaseReaderThread(P2ESThread):

    def __init__(self, idx, CONFIG, errors_queue, writer_queue):
        P2ESThread.__init__(self, idx, CONFIG, errors_queue)
        self.queue = Queue()
        self.writer_queue = writer_queue

    def run(self):
        while True:
            line = None
            try:
                line = self.queue.get(block=True, timeout=1)
                if line is None:
                    return
                self.writer_queue.put(self.parse(line))
            except Empty:
                pass
            except Exception as e:
                self.errors_queue.put(str(e))
                if line is None:
                    return

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
                if action['LookupFieldName'] in dic:
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
    
class CSVReaderThread(BaseReaderThread):

    def set_headers(self, headers):
        self.headers = headers

    def _parse(self, line):
        fields = line.split(",")
        dic = {}
        for i in range(len(self.headers)):
            field_name = self.headers[i].lower()
            field_val = fields[i]
            dic[field_name] = field_val
        return dic

class BaseReader(object):

    HEADER = False

    def __init__(self, CONFIG, input_file, errors_queue, writer_queue):
        self.CONFIG = CONFIG

        self.input_file = input_file
    
        self.readers = []

        for thread_idx in range(CONFIG['ReaderThreads']):
            self.readers.append(
                self.READER_THREAD_CLASS(
                    "reader{}".format(thread_idx),
                    CONFIG,
                    errors_queue,
                    writer_queue
                )
            )

    def process_first_line(self, line):
        pass

    def start_threads(self):
        for thread in self.readers:
            thread.daemon = True
            thread.start()

    def process_input(self):
        self.start_threads()

        with open(self.input_file, "r") if self.input_file else sys.stdin as f:
            thread_idx = -1
            first_line_processed = False
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if not first_line_processed and self.HEADER:
                    self.process_first_line(line)
                    first_line_processed = True
                    continue

                thread_idx = (thread_idx + 1) % len(self.readers)
                self.readers[thread_idx].queue.put(line)

    def finalize(self):
        for thread in self.readers:
            thread.queue.put(None)

        for thread in self.readers:
            thread.join()

class JSONReader(BaseReader):

    READER_THREAD_CLASS = JSONReaderThread

class CSVReader(BaseReader):

    HEADER = True
    READER_THREAD_CLASS = CSVReaderThread

    def process_first_line(self, line):
        fields = line.split(",")
        for thread in self.readers:
            thread.set_headers(fields)
