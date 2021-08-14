import socket
import colors
import headers
import time
from threading import Thread

HEADERSIZE = 10
MESSAGE_START = 10

SERVER_NAME = f'{colors.BRRED}{"SERVER >":<{MESSAGE_START}}{colors.CLEAR}'
WELCOME_MESSAGE = f"Welcome to Conal's Chat Test"

client_sockets = []

# (addr) -> name
client_names = {}


def create_special_header(header):
    return f'{header:<{HEADERSIZE}}'


def create_normal_header(message):
    return f"{len(message):<{HEADERSIZE}}" + message


def create_server_message(message):
    return create_normal_header(SERVER_NAME + message)


def send_all_clients(message):
    for socket in client_names.keys():
        socket.send(bytes(message, 'utf-8'))


def send_client_message(sender_socket, message):
    for socket in client_names.keys():
        if socket != sender_socket:
            socket.send(bytes(message, 'utf-8'))


def handle_client(client_socket: socket.socket, addr):
    named = False
    # Send the client a welcome message and ask them for their name
    client_socket.send(bytes(create_server_message(WELCOME_MESSAGE), "utf-8"))
    time.sleep(0.5)
    client_socket.send(bytes(create_server_message(
        "What would you like your username to be?"), "utf-8"))
    time.sleep(0.5)
    client_socket.send(
        bytes(create_special_header(headers.HEADERS["NAME_PROMPT"]), "utf-8"))

    new_msg = True
    full_msg = ''
    # Wait for client to send username response
    while True:
        try:
            msg = client_socket.recv(16)

            if new_msg:
                header = int(msg[:HEADERSIZE].strip())
                if header == headers.HEADERS["CLIENT_QUIT"]:
                    if named:
                        leaver_name = client_names[client_socket]
                        print(f"{leaver_name} has disconnected")
                        del client_names[client_socket]
                        client_sockets.remove(client_socket)
                        send_all_clients(create_server_message(f"{colors.CYAN}{leaver_name}{colors.CLEAR} has disconnected"))
                        return
                    else:
                        print(f'{addr} has disconnected')
                        client_sockets.remove(client_socket)
                        return
                else:
                    size = header
                    new_msg = False

            full_msg += msg.decode("utf-8")

            if len(full_msg) - HEADERSIZE == size:
                name = full_msg[HEADERSIZE:].strip()
                if name in client_names.values():
                    client_socket.send(bytes(create_server_message("That username is taken, please enter another"), "utf-8"))
                    time.sleep(0.5)
                    client_socket.send(bytes(create_special_header(headers.HEADERS["NAME_PROMPT"]), "utf-8"))
                    full_msg = ''
                    new_msg = True
                else:
                    print(f'Recieved name "{name}" from {addr}')
                    time.sleep(1)
                    client_socket.send(bytes(
                        create_special_header(headers.HEADERS["NAME_SUCCESS"]), "utf-8"))

                    time.sleep(1)
                    send_all_clients(create_server_message(f"{colors.CYAN}{name}{colors.CLEAR} has connected"))
                    client_socket.send(bytes(
                      create_server_message(f"You're ready to start chatting {colors.CYAN}{name}{colors.CLEAR}"),"utf-8"))
                    client_names[client_socket] = name
                    named = True
                    new_msg = True
                    full_msg = ''
                    break
        except socket.timeout:
            continue
        except:
            return

    # Handle all futher messages the client sends
    new_msg = True
    full_msg = ''
    while True:
        try:
            msg = client_socket.recv(16)
            if new_msg:
                header = int(msg[:HEADERSIZE].strip())
                if header == headers.HEADERS["CLIENT_QUIT"]:
                    if named:
                        leaver_name = client_names[client_socket]
                        print(f"{leaver_name} has disconnected")
                        del client_names[client_socket]
                        client_sockets.remove(client_socket)
                        send_all_clients(create_server_message(f"{colors.CYAN}{leaver_name}{colors.CLEAR} has disconnected"))
                        return
                    else:
                        print(f'{addr} has disconnected')
                        client_sockets.remove(client_socket)
                        return
                else:
                    size = header
                    new_msg = False

            full_msg += msg.decode("utf-8")

            if len(full_msg) - HEADERSIZE == size:
                #TODO: Log messages
                send_client_message(client_socket, full_msg)
                new_msg = True
                full_msg = ''
        except socket.timeout:
            continue
        except:
            return


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # We set timeouts to allow exceptions to break while loops to check if a thread should be killed
    s.settimeout(5)
    s.bind(('localhost', 1234))
    s.listen(3)

    # listen for new connections
    while True:
        try:
            client_socket, addr = s.accept()
            print(f"Connection from {addr} has been accepted")

            client_sockets.append(client_socket)
            client_socket.settimeout(5)
            # spin up a thread to handle the new client
            client_thread = Thread(target=handle_client,
                                   args=(client_socket, addr))
            # This should handle killing the thread once the proper exception is thrown inside handle_client()
            client_thread.setDaemon(True)
            client_thread.start()

        except socket.timeout:
            continue
        except:
            # Error occured, let's pack up
            break

    return


if __name__ == '__main__':
    main()
