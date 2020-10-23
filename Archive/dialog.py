import wx
import shutil
import os


class DeleteWarning(wx.Frame):
    def __init__(self, parent): 
        super(DeleteWarning, self).__init__(
                                            parent,
                                            title = "Confirm Deletion",
                                            size = (425,225),
                                            style=wx.DEFAULT_FRAME_STYLE &
                                                  ~(wx.RESIZE_BORDER |
                                                  wx.MAXIMIZE_BOX |
                                                  wx.MINIMIZE_BOX))

        self.InitUI()

    def InitUI(self):
        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(
            self, 
            label='Deleting a node will result in the\ndeletion of ' \
                  'all intersecting lines and\ntheir related loops.' \
                  '\n\nSelect the corresponding node letter to delete.',
            style=wx.ALIGN_CENTER_HORIZONTAL)
        hdrsizer.Add(hdr1, 1, wx.LEFT, 20)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        wrng_shw = wx.CheckBox(self, 
                               label='Show this warning\nbefore deleting element')


        ok = wx.Button(self, -1, "Ok")
        xit = wx.Button(self, -1, "Cancel")
        btnsizer.Add(wrng_shw, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 15)
        btnsizer.Add(ok, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
    #    self.Bind(wx.EVT_BUTTON, self.OnReDraw, ok)
    #    self.Bind(wx.EVT_BUTTON, self.OnExit, xit)

        self.sizer.Add(hdrsizer, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        self.sizer.Add((20, 10))
        self.sizer.Add(btnsizer, 1)
        self.SetSizer(self.sizer)


class OpenFile(wx.Frame):
    def __init__(self, parent): 
        super(OpenFile, self).__init__(
                                       parent,
                                       title="Open Data File",
                                       size=(600, 225),
                                       style=wx.DEFAULT_FRAME_STYLE &
                                               ~(wx.RESIZE_BORDER |
                                                 wx.MAXIMIZE_BOX |
                                                 wx.MINIMIZE_BOX))

        self.parent = parent
        self.InitUI()

    def InitUI(self):

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self,
                             label='Open an existing data file:',
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        self.file_name = wx.FilePickerCtrl(self,
                                           message='',
                                           style=wx.FLP_OPEN |
                                           wx.FLP_FILE_MUST_EXIST |
                                           wx.FLP_USE_TEXTCTRL,
                                           size=(400, 25))

        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.Selected, self.file_name)

        sizer1.Add(hdr1, 0, wx.TOP | wx.LEFT, 20)
        sizer1.Add(self.file_name, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hdr2 = wx.StaticText(self,
                             label='Open new data file:',
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        yup = wx.Button(self, -1, "Specify\nNew File")
        self.Bind(wx.EVT_BUTTON, self.OnDialog, yup)
        sizer2.Add(hdr2, 0, wx.LEFT | wx.TOP, 20)
        sizer2.Add(yup,0, wx.LEFT, 20)

        self.sizer.Add(sizer1, 1)
        self.sizer.Add((10, 10))
        self.sizer.Add(sizer2, 1)
        self.SetSizer(self.sizer)

    def Selected(self, evt):
        print(self.file_name.GetPath())
        evt.Skip()

    def OnDialog(self, evt):
        with wx.FileDialog(self, "Save data file", wildcard="db files (*.db)|*.db",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            if pathname[-3:] != '.db':
                pathname = pathname + '.db'

            shutil.copyfile(os.getcwd() + '/mt.db', pathname)
        evt.Skip()


if __name__ == "__main__":
    app = wx.App(False)
    frame = OpenFile(None)
    frame.Show()
    frame.CenterOnScreen()
    app.MainLoop()