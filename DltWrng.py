import wx


class DeleteWarning(wx.Dialog):

    def __init__(self, parent, elem): 
        super(DeleteWarning, self).__init__(
                                            parent,
                                            title="Confirm Deletion",
                                            size=(480, 225),
                                            style=wx.DEFAULT_FRAME_STYLE &
                                                  ~(wx.RESIZE_BORDER |
                                                  wx.MAXIMIZE_BOX |
                                                  wx.MINIMIZE_BOX))
        self.elem = elem
        self.parent = parent
        self.InitUI()
        self.show_me = False

    def InitUI(self):
        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        if self.elem == 'line':
            msg = 'Deleting a line will result in the\ndeletion of' \
                    'all related loops.\n' \
                    'Select the corresponding\nline letter to proceed.'
        elif self.elem == 'node':
            msg = 'Deleting a node will result in the\ndeletion of ' \
                    'all intersecting lines and\ntheir related loops.' \
                    '\n\nSelect the corresponding node letter to delete.'
        elif self.elem == 'loop':
            msg = 'Deleting a loop will result in the\ndeletion of ' \
                    'all data related to the loop.\n' \
                    'Select the corresponding loop\nnumber to proceed.'

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)

        hdr1 = wx.StaticText(self,
                             label=msg,
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        hdrsizer.Add(hdr1, 1, wx.LEFT, 20)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wrng_shw = wx.CheckBox(self,
                               label='Do not show this warning again.')

        ok = wx.Button(self, -1, "Ok")
        xit = wx.Button(self, -1, "Cancel")
        btnsizer.Add(self.wrng_shw, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 15)
        btnsizer.Add(ok, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, xit)

        self.sizer.Add(hdrsizer, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        self.sizer.Add((20, 10))
        self.sizer.Add(btnsizer, 1)
        self.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

    def OnOk(self, evt):
        self.EndModal(True)
        self.show_me = self.wrng_shw.GetValue()

    def OnCancel(self, evt):
        self.EndModal(False)
        self.show_me = self.wrng_shw.GetValue()