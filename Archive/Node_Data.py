import wx


class Node_Frm(wx.Frame):
    def __init__(self):

        node_lst = ['A', 'E', 'F', 'H']
        node = 'a'

        wx.Frame.__init__(self, None, wx.ID_ANY,
                          'Node "' + node + '" Flows',
                          size=(250, 400),
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER |
                                                           wx.MAXIMIZE_BOX |
                                                           wx.MINIMIZE_BOX))

        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self, label='Flow\nInto\nNode',
                             style = wx.ALIGN_LEFT)
        hdr2 = wx.StaticText(self, label='Flow\nOut Of\nNode',
                             style = wx.ALIGN_LEFT)
        hdrsizer.Add(hdr1, 1, wx.ALIGN_LEFT|wx.LEFT, 20)
        hdrsizer.Add(hdr2, 1, wx.ALIGN_LEFT|wx.LEFT, 60)

        self.sizer.Add(hdrsizer, 1, wx.BOTTOM, 120)
        
        n = 7
        id_num = 1
        rbsizers = []
        rad_bt = []
        for ln in node_lst:
            pos_rb = wx.RadioButton(self, id_num, label=('\t\tline "' + ln + '"'),
                                    pos=(20, 10*n),
                                    style=wx.RB_GROUP)
            neg_rb = wx.RadioButton(self, id_num+1, label='', pos=(180, 10*n))

            rad_bt.append(pos_rb)
            rad_bt.append(neg_rb)

            rb_sizer = wx.BoxSizer(wx.HORIZONTAL)
            rbsizers.append(rb_sizer)
            n += 5
            id_num += 2

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadiogroup)

        for rbsizer in rbsizers:
            self.sizer.Add(rbsizer, 0)

        self.SetSizer(self.sizer)

    def OnRadiogroup(self, evt): 
        rb = evt.GetEventObject()
        print(evt.GetId())
        print(rb.GetLabel(),' is clicked from Radio Group')

    def Close(self, evt):
        self.Close(True)


if __name__ == "__main__":
    app = wx.App(False)
    frame = Node_Frm()
    frame.Show()
    frame.CenterOnScreen()
    app.MainLoop()