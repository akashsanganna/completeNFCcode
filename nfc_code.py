import wx
import threading
import time
from smartcard.System import readers
from smartcard.util import toHexString
import ndef
from smartcard.CardConnection import CardConnection
from smartcard.CardMonitoring import CardMonitor, CardObserver
import os
import hashlib
import tkinter as tk
from tkinter import Text, Label, Button
from dotenv import load_dotenv



#  Set the correct UID in uppercase format
EXPECTED_UID = "1DD94F118D0000"
 #---------------------- Main Page (NFC Scan) ----------------------
class MainPage(wx.Frame):
    def __init__(self, parent, *args, **kw):
        super(MainPage, self).__init__(parent, *args, **kw)

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Top Bar
        top_bar = wx.Panel(panel, pos=(0, 0), size=(400, 40))
        top_bar.SetBackgroundColour('#1E3A8A')

        nfc_tool = wx.StaticText(top_bar, label="NFC Tool", pos=(10, 10))
        nfc_tool.SetForegroundColour('#FFFFFF')
        nfc_tool.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        version = wx.StaticText(top_bar, label="Version 1.0.9", pos=(300, 10))
        version.SetForegroundColour('#FFFFFF')

        self.label = wx.StaticText(panel, label="Device Not Found", pos=(150, 170))
        self.label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        vbox.Add(self.label, flag=wx.ALL | wx.CENTER, border=15)
        panel.SetSizer(vbox)

        self.SetSize((400, 200))
        self.Centre()

        #  Start NFC reading in a background thread
        self.nfc_thread = threading.Thread(target=self.read_nfc, daemon=True)
        self.nfc_thread.start()

    def read_nfc(self):
        """Continuously checks for NFC reader and tag."""
        while True:
            try:
                r = readers()
                if not r:
                    wx.CallAfter(self.show_message, " Device Not Found")
                else:
                    connection = r[0].createConnection()
                    connection.connect()

                    get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]

                    response, sw1, sw2 = connection.transmit(get_uid_command)
                    if sw1 == 0x90 and sw2 == 0x00:
                        uid = ''.join(f"{x:02X}" for x in response)
                        print(f" Detected UID: {uid}")

                        if uid == EXPECTED_UID:
                            wx.CallAfter(self.show_success)
                            break  # Stop scanning once the correct tag is found
                        else:
                            wx.CallAfter(self.show_message, " Incorrect NFC tag. Try again.")

                    else:
                        wx.CallAfter(self.show_message, "Unable to read tag.")
            
            except Exception as e:
                print(f" Error: {e}")
                wx.CallAfter(self.show_message, "Device Not Found")

            time.sleep(1)  # Delay to prevent high CPU usage

    def show_message(self, message):
        """Updates the label with a message."""
        self.label.SetLabel(message)
        self.Layout()  # Refresh UI to reflect changes

    def show_success(self):
        """Shows success message and opens the login page."""
        wx.MessageBox("Device Connected Successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        self.Close()
        LoginFrame(None, title="Login").Show()  # Show login page

# ---------------------- Login Page ----------------------

class LoginFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(LoginFrame, self).__init__(*args, **kw)
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        # Top Bar
        top_bar = wx.Panel(panel, pos=(0, 0), size=(400, 40))
        top_bar.SetBackgroundColour('#1E3A8A')

        nfc_tool = wx.StaticText(top_bar, label="NFC Tool", pos=(10, 10))
        nfc_tool.SetForegroundColour('#FFFFFF')
        nfc_tool.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        version = wx.StaticText(top_bar, label="Version 1.0.9", pos=(300, 10))
        version.SetForegroundColour('#FFFFFF')

        wx.StaticText(panel, label="Username:", pos=(50, 80))
        self.user_txt = wx.TextCtrl(panel, pos=(150, 80), size=(200, -1))

        wx.StaticText(panel, label="Password:", pos=(50, 120))
        self.pass_txt = wx.TextCtrl(panel, pos=(150, 120), size=(200, -1), style=wx.TE_PASSWORD)

        login_btn = wx.Button(panel, label="LOGIN", pos=(150, 170))
        login_btn.Bind(wx.EVT_BUTTON, self.OnLogin)

        self.SetSize((400, 250))
        self.Centre()

    def OnLogin(self, event):
        username = self.user_txt.GetValue()
        password = self.pass_txt.GetValue()

        if username == 'admin' and password == 'password123':
            wx.MessageBox('Login Successful!', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.Close()
            details = DetailsFrame(None)
            details.Show()
        else:
            wx.MessageBox('Invalid credentials!', 'Error', wx.OK | wx.ICON_ERROR)

# ---------------------- Details Page ----------------------

class DetailsFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(DetailsFrame, self).__init__(*args, **kw)
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)

        # Top Bar
        top_bar = wx.Panel(panel, pos=(0, 0), size=(400, 40))
        top_bar.SetBackgroundColour('#1E3A8A')

        nfc_tool = wx.StaticText(top_bar, label="NFC Tool", pos=(10, 10))
        nfc_tool.SetForegroundColour('#FFFFFF')
        nfc_tool.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        version = wx.StaticText(top_bar, label="Version 1.0.9", pos=(300, 10))
        version.SetForegroundColour('#FFFFFF')
        
        wx.StaticText(panel, label="Patient ID:", pos=(50, 50))
        self.patient_id_txt = wx.TextCtrl(panel, pos=(150, 50), size=(200, -1))

        wx.StaticText(panel, label="ZIP Code:", pos=(50, 90))
        self.zip_code_txt = wx.TextCtrl(panel, pos=(150, 90), size=(200, -1))

        wx.StaticText(panel, label="Device ID:", pos=(50, 130))
        self.device_id_txt = wx.TextCtrl(panel, pos=(150, 130), size=(200, -1))

        submit_btn = wx.Button(panel, label="SUBMIT", pos=(150, 170))
        submit_btn.Bind(wx.EVT_BUTTON, self.OnSubmit)

        self.SetSize((400, 250))
        self.Centre()

    def OnSubmit(self, event):
        patient_id = self.patient_id_txt.GetValue()
        zip_code = self.zip_code_txt.GetValue()
        device_id = self.device_id_txt.GetValue()

        if patient_id and zip_code and device_id:
            self.Close()
            nfc_write = WriteNFCFrame(None)  # ✅ Now creating NFCWriteFrame without arguments
            nfc_write.Show()
        else:
            wx.MessageBox('Please fill all the fields!', 'Error', wx.OK | wx.ICON_ERROR)

#---------------------------- write NFC -------------------------------

class WriteNFCFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="Write NFC Data", size=(400, 300))
        self.InitUI()  # Ensure this method exists


    EXPECTED_UID = "1DD94F118D0000"

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        vbox.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.write_button = wx.Button(panel, label="Write to NFC")
        vbox.Add(self.write_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        panel.SetSizer(vbox)

        

def create_ndef_record(data: str) -> bytes:
    """Encodes text into an NDEF message for NFC writing."""
    record = ndef.TextRecord(data)
    encoded_message = b''.join(ndef.message_encoder([record]))
    message_length = len(encoded_message)
    initial_message = b'\x03' + message_length.to_bytes(1, 'big') + encoded_message + b'\xFE'
    padding_length = -len(initial_message) % 4
    return initial_message + (b'\x00' * padding_length)

def write_ndef_message(connection, ndef_message: bytes) -> bool:
    """Writes the NDEF message to the NFC tag."""
    page = 4
    while ndef_message:
        block_data = ndef_message[:4]
        ndef_message = ndef_message[4:]
        WRITE_COMMAND = [0xFF, 0xD6, 0x00, page, 0x04] + list(block_data)
        response, sw1, sw2 = connection.transmit(WRITE_COMMAND)
        if sw1 != 0x90 or sw2 != 0x00:
            return False  # Failed to write
        page += 1
    return True  # Success

class WriteNFCFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="NFC Writer", size=(400, 300))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        top_bar = wx.Panel(panel, size=(-1, 40), style=wx.BORDER_SIMPLE)
        top_bar.SetBackgroundColour('#1E3A8A')  # Blue header background

        wx.StaticText(top_bar, label="NFC Tool", pos=(40, 10)).SetForegroundColour('#FFFFFF')

        version_label = wx.StaticText(top_bar, label="Version 1.0.9", pos=(300, 10))
        version_label.SetForegroundColour('#FFFFFF')

        # Text Entry
        self.text_label = wx.StaticText(panel, label="Enter text to write to NFC:")
        vbox.Add(self.text_label, flag=wx.ALL | wx.CENTER, border=10)

        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(300, 100))
        vbox.Add(self.text_ctrl, flag=wx.ALL | wx.CENTER, border=10)

        # Write Button
        self.write_button = wx.Button(panel, label="Write to NFC")
        vbox.Add(self.write_button, flag=wx.ALL | wx.CENTER, border=10)
        self.write_button.Bind(wx.EVT_BUTTON, self.OnWriteNFC)

        # Status Label
        self.status_label = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        vbox.Add(self.status_label, flag=wx.ALL | wx.CENTER, border=10)

        panel.SetSizer(vbox)

        # Start NFC Monitoring
        self.cardmonitor = CardMonitor()
        self.cardobserver = NTAG215Observer(self)
        self.cardmonitor.addObserver(self.cardobserver)

    def OnWriteNFC(self, event):
        """Triggered when 'Write to NFC' button is clicked."""
        data = self.text_ctrl.GetValue().strip()
        if not data:
            self.status_label.SetLabel("Please enter text to write.")
            return

        self.status_label.SetLabel("Waiting for NFC tag...")  # Waiting for tag detection

    def update_status(self, status):
        """Update the status label with a message."""
        self.status_label.SetLabel(status)


class NTAG215Observer(CardObserver):
    def __init__(self, app):
        self.app = app

    def update(self, observable, actions):
        """Handles the NFC card detection and writing process."""
        addedcards, _ = actions
        for card in addedcards:
            try:
                connection = card.createConnection()
                connection.connect()

                # Read NFC tag UID
                uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                response, sw1, sw2 = connection.transmit(uid_command)
                tag_uid = toHexString(response).replace(" ", "").upper()

                if tag_uid != EXPECTED_UID:
                    self.app.update_status("Wrong NFC tag! Access Denied.")
                    return

                # Get text from the text box
                data = self.app.text_ctrl.GetValue().strip()
                if not data:
                    self.app.update_status("No text entered. Please enter text.")
                    return

                # Convert text to NDEF message
                ndef_message = create_ndef_record(data)

                # Write to NFC tag
                if write_ndef_message(connection, ndef_message):
                    self.app.update_status("Data written successfully!")
                else:
                    self.app.update_status("Failed to write to NFC tag.")

            except Exception as e:
                self.app.update_status(f"Error: {e}")

def main():
    root = tk.Tk()
    app = NFCApp(root)
    root.mainloop()

if __name__ == "__main__":
    app = wx.App(False)  # Create the app
    frame = MainPage(None, title="NFC Scanner")  # Start with the MainPage
    frame.Show()
    app.MainLoop()  # Run the event loop
 