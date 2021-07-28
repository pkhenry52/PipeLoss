import wx


class DataOutPut(wx.Frame):

    def __init__(self, parent, Flows):
        super().__init__(parent,
                         title="Data Completed",
                         style=wx.DEFAULT_FRAME_STYLE |
                         wx.RESIZE_BORDER | wx.STAY_ON_TOP)

        self.Flows = Flows
        self.parent = parent

        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.InitUI()
        self.Centre()
        self.Show(True)

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

        prnt = wx.Button(self, -1, "Print Results")
        xit = wx.Button(self, -1, "Exit")
        grd.AddMany([(prnt), (xit)])

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnPrint, prnt)
        self.Bind(wx.EVT_BUTTON, self.OnExit, xit)

        note_sizer = wx.BoxSizer(wx.VERTICAL)
        msg1 = 'The printed information includes;'
        msg2 = '\n\t-pump data\n\t-control valve data'
        msg3 = '\n\t-system data covering: \n\t\tflow,\n\t\tvelocity,'
        msg4 = '\n\t\theadloss,\n\t\tReynolds,'
        msg5 = '\n\t\tpressure at the nodes\n\t\tetc.'
        msg = msg1+msg2+msg3+msg4+msg5
        note = wx.StaticText(self, label=msg)
        note_sizer.Add(note, 1, wx.ALIGN_CENTER)

        self.SetSize(350,(145+39*len(col1)))
        self.sizer.Add(grd, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        self.sizer.Add((10,25))
        self.sizer.Add(note_sizer, 1, wx.ALIGN_CENTER)
        self.SetSizer(self.sizer)

    def OnExit(self, evt):
        self.Destroy()

    def OnPrint(self, evt):
        self.Destroy()