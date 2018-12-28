import ScrolledText
from Tkinter import BOTH, END, LEFT
import threading
import time
import socket
import sys
import select
import pickle
import logging
import logging.handlers
import struct


class TextWindow(object):

    DELAY = 50
    TIMEOUT = 50000

    def read_log_record(self, client):
        chunk = client.recv(4)
        self.stext.insert(END, chunk)
        if len(chunk) < 4:
            return None
        slen = struct.unpack('>L', chunk)[0]
        chunk = client.recv(slen)
        if chunk == b"close":
            self.exit()
        elif chunk == b"hide":
            self.stext.winfo_toplevel().wm_attributes('-alpha', 0)
            return None
        elif chunk == b"show":
            self.stext.winfo_toplevel().wm_attributes('-alpha', 1)
            return None
        else:
            while len(chunk) < slen:
                chunk = chunk + client.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            return logging.makeLogRecord(obj)  

    def update_clock(self):
        #print(".")
        if self.connect_time > self.TIMEOUT:
            for client in self.clients:
                client.close()
            self.clients = []
            return
        try:
            (clientsocket, address) = self.sock.accept()
            if clientsocket:
                self.clients.append(clientsocket)
                print('Client connected from %s' % str(address))
        except socket.error as e:
                if e[0] == 10035:
                    sys.stdout.write('.')
                else:
                    raise

        if self.clients:
            ready_to_read, ready_to_write, in_error = select.select(
                    self.clients,
                    [],
                    [],
                    1)
            if ready_to_read:
                retries = 10
                for client in ready_to_read:
                    while retries > 0:
                        try:
                            data = self.read_log_record(client)
                            print(str(data))
                            if data:
                                self.display(data)
                                self.connect_time = 0
                        except socket.error as e:
                            if e[0] == 10035:
                                retries -= 1
                                time.sleep(self.DELAY//1000)
                                continue
                            print(str(e))
                            client.close()
                            self.clients.remove(client)
                            break

        self.stext.after(self.DELAY, threading.Thread(target=self.update_clock).start)

    def display(self, record):
        msg = self.formatter.format(record) + '\n'
        print(msg)
        self.stext.configure(state='normal')
        self.stext.insert(END, msg, record.levelname)
        self.stext.configure(state='disabled')
        self.stext.see("end")

    def __init__(self, log_format=None):
        print('Starting output window')
        self.formatter = logging.Formatter(log_format)
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind(('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT))
        self.sock.listen(1)
        self.stext = ScrolledText.ScrolledText(bg='white', height=20, state="disabled")
        self.stext.pack(fill=BOTH, side=LEFT, expand=True)
        self.stext.tag_config('INFO', foreground='black')
        self.stext.tag_config('DEBUG', foreground='gray')
        self.stext.tag_config('WARNING', foreground='orange')
        self.stext.tag_config('ERROR', foreground='red')
        self.stext.tag_config('CRITICAL', foreground='red', underline=1)
        self.stext.focus_set()
        self.stext.after(self.DELAY, self.update_clock)
        self.connect_time = 0
        print('Listening on test')
        self.stext.mainloop()    

    def exit(self):
        self.sock.close()
        self.stext.quit()

def run():
    print('run')
    TextWindow('%(asctime)-15s %(name)-15s %(levelname)-8s %(message)s')

if __name__ == "__main__":
    run()
