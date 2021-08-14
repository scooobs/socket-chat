import socket
import select
import headers
import sys
import time
import colors
import signal
from threading import Thread, Timer

TIMEOUT = 1
HEADERSIZE = 10
MESSAGE_START = 10
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'


class Handler:
    def __init__(self):
        self._valid = False
        self._name = None
        self._header = None

    def change_name(self, name):
        self._name = name
    
    def change_valid(self, valid):
        self._valid = valid

    def change_header(self, header):
        self._header = header

    def clear_header(self):
        self._header = None


def handle_server(server_socket: socket.socket, handler: Handler):
    new_msg = True
    full_msg = ''
    # Wait for server to send username response
    while True:

        try:
            msg = server_socket.recv(16)

            if new_msg:
                header = int(msg[:HEADERSIZE].strip())
                if header == headers.HEADERS["NAME_PROMPT"]:
                    handler.change_header(header)
                    full_msg = ''
                    msg = ''
                elif header == headers.HEADERS["NAME_INVALID"]:
                    #TODO: remove
                    handler.change_header(header)
                    server_socket.send(bytes(create_special_header(headers.HEADERS["CLIENT_REQUEST_NEW_NAME"]), "utf-8"))
                    full_msg = ''
                    msg = ''
                elif header == headers.HEADERS["NAME_SUCCESS"]:

                    handler.change_valid(True)
                    handler.clear_header()
                    full_msg = ''
                    msg = ''
                else:

                    size = header
                    new_msg = False

            if msg:

                full_msg += msg.decode("utf-8")


            if len(full_msg) - HEADERSIZE == size:
                print(full_msg[HEADERSIZE:])
                new_msg = True
                full_msg = ''
        except socket.timeout:
            continue
        except:
            break
    return


def create_special_header(header):
    return f'{header:<{HEADERSIZE}}'


def create_normal_header(message):
    return f'{len(message):<{HEADERSIZE}}' + message


def client_side_message(message, name):
    return f'{colors.CYAN}{f"{name} >":<{MESSAGE_START}}{colors.CLEAR}' + message

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('localhost', 1234))

    handler = Handler()

    server_thread = Thread(target=handle_server, args=(s, handler))
    server_thread.setDaemon(True)
    server_thread.start()

    # Read from stdin
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            msg = sys.stdin.readline()
            if msg:
                header = handler._header
                if header:
                    if (header == headers.HEADERS["NAME_PROMPT"]):
                        if msg:
                            if msg.rstrip() == 'quit()':
                                s.send(bytes(create_special_header(
                                    headers.HEADERS["CLIENT_QUIT"]), "utf-8"))
                                s.shutdown(socket.SHUT_RDWR)
                                s.close()
                                exit()
                            name = msg.rstrip()
                            handler.change_name(name)
                            handler.clear_header()
                            s.send(bytes(create_normal_header(msg), "utf-8"))
                    elif (header == ["NAME_SUCCESS"]):
                        handler.clear_header()
                else:
                    if msg:
                        if msg.rstrip() == 'quit()':
                            s.send(bytes(create_special_header(
                                headers.HEADERS["CLIENT_QUIT"]), "utf-8"))
                            s.shutdown(socket.SHUT_RDWR)
                            s.close()
                            exit()
                        elif handler._valid:
                            sys.stdout.write(CURSOR_UP_ONE)
                            sys.stdout.write(ERASE_LINE)
                            print(client_side_message(
                                msg.rstrip(), handler._name))
                            s.send(bytes(create_normal_header(
                                client_side_message(msg.rstrip(), handler._name)), "utf-8"))
                        else:
                            print(client_side_message(msg.rstrip(), "Anon"))
                            s.send(bytes(create_normal_header(
                                client_side_message(msg.rstrip(), "Anon")), "utf-8"))
            else:
                s.send(bytes(create_special_header(
                    headers.HEADERS["CLIENT_QUIT"]), "utf-8"))
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                exit()


if __name__ == "__main__":
    main()
