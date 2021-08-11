import wx


class DataOutPut(wx.Dialog):

    def __init__(self, parent, Flows):

        super().__init__(parent,
                         title="Data Completed",
                         style=wx.DEFAULT_FRAME_STYLE &
                                ~(wx.RESIZE_BORDER |
                                wx.MAXIMIZE_BOX |
                                wx.MINIMIZE_BOX))


        self.parent = parent
        self.Flows = Flows
        self.InitUI()

    def InitUI(self):
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        col1 = list(self.Flows.keys())
        col2 = list(self.Flows.values())
        col1.insert(0,'Line\nLabel')
        col2.insert(0,'Flow\nft^3/s')

        grd = wx.FlexGridSizer(len(col1)+1, 2, 10, 10)

        n = 0
        for itm in col1:
            line=wx.StaticText(self, label=itm)
            flow=wx.StaticText(self, label=str(col2[n]))
            n += 1
            grd.AddMany([(line, 1, wx.EXPAND), (flow, 1, wx.EXPAND)])

        sve = wx.Button(self, -1, "Save Results")
        xit = wx.Button(self, -1, "Exit")
        grd.AddMany([(sve), (xit)])

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnSave, sve)
        self.Bind(wx.EVT_BUTTON, self.OnExit, xit)

        note_sizer = wx.BoxSizer(wx.VERTICAL)
        msg1 = 'The printed information includes;'
        msg2 = '\n\t-pump data\n\t-control valve data'
        msg3 = '\n\t-system data covering: \n\t\tflow,\n\t\tvelocity,'
        msg4 = '\n\t\theadloss,\n\t\tReynolds,'
        msg5 = '\n\t\tpressure at the nodes\n\t\tetc.'
        msg = msg1 + msg2 + msg3 + msg4 + msg5
        note1 = wx.StaticText(self, label=msg)
        msg6 = 'The pdf report file will be saved\nin'
        msg7 = ' the same location as the database,\n'
        msg8 = 'using the database file name.'
        msg = msg6 + msg7 + msg8
        note2 = wx.StaticText(self, label=msg)
        note_sizer.Add(note1, 1, wx.ALIGN_CENTER)
        note_sizer.Add((10,20))
        note_sizer.Add(note2,1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        self.SetSize(350,(250+40*len(col1)))
        self.sizer.Add(grd, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        self.sizer.Add((10,25))
        self.sizer.Add(note_sizer, 1, wx.ALIGN_CENTER)
        self.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

    def OnExit(self, evt):
        self.EndModal(False)
        self.Destroy()

    def OnSave(self, evt):
        self.EndModal(True)
        self.Destroy()