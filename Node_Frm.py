import wx


class NodeFrm(wx.Frame):
    def __init__(self, parent, node, cord, node_lst, node_dict):

        self.rad_bt = []
        self.chk_bx = []
        self.txt_bxs = []
        self.cord = tuple(cord)
        self.nodes = node_dict
        self.node_lst = set(node_lst)
        self.node = node
        self.saved = False
        self.type = 0

        ttl = 'Node "' + node + ' ' + str(cord) + '" Flow Information.'

        super(NodeFrm, self).__init__(parent, title=ttl,
                                       style=wx.DEFAULT_FRAME_STYLE &
                                       ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX |
                                         wx.MINIMIZE_BOX))

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent

        self.InitUI()

    def InitUI(self):
        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self, label='Flow\nInto\nNode',
                             style=wx.ALIGN_LEFT)
        hdr2 = wx.StaticText(self, label='Flow\nOut Of\nNode',
                             style=wx.ALIGN_LEFT)
        hdr3 = wx.StaticText(self, label='\nExternal Flow',
                             style=wx.ALIGN_CENTER)
        hdrsizer.Add(hdr1, 1, wx.LEFT, 20)
        hdrsizer.Add(hdr2, 1, wx.LEFT, 60)
        hdrsizer.Add(hdr3, 1, wx.LEFT, 40)

        self.sizer.Add(hdrsizer, 1, wx.BOTTOM, 10)
        id_num = 0
        rbsizers = []

        ln_lst = set()
        if self.node in self.nodes.keys():
            d = {}
            for k , v1, v2 in self.nodes[self.node][0]:
                d.setdefault(k, []).append(v1)
                d.setdefault(k, []).append(v2)
            ln_lst = set(d.keys())

        n = 0
        for ln in self.node_lst:
            if ln in self.node_lst.difference(ln_lst):
                rdbtn = 0
                txtbx = 0
                new_data = True
            else:
                rdbtn, txtbx = d[ln]
                new_data = False

            rb_sizer = wx.BoxSizer(wx.HORIZONTAL)
            pos_rb = wx.RadioButton(self, id_num,
                                    label=('\t\tline "' + ln + '"'),
                                    pos=(20, 10*n),
                                    style=wx.RB_GROUP)
            neg_rb = wx.RadioButton(self, id_num+1, label='', pos=(180, 10*n))
            neg_rb.SetValue(bool(rdbtn))

            flow_chk = wx.CheckBox(self, id_num+2, label='', pos=(280, 10*n))

            txt_bx = wx.TextCtrl(self, id_num+3, value='',
                                 pos=(320, 10*n),
                                 size=(-1, 30))
            txt_bx.Enable(False)

            if txtbx != 0:
                txt_bx.Enable()
                txt_bx.ChangeValue(str(txtbx))
                flow_chk.SetValue(True)

            self.rad_bt.append(pos_rb)
            self.rad_bt.append(neg_rb)
            self.chk_bx.append(flow_chk)
            self.txt_bxs.append(txt_bx)

            rb_sizer.Add(pos_rb, 0, wx.LEFT, 20)
            rb_sizer.Add(neg_rb, 0, wx.LEFT, 40)
            rb_sizer.Add(flow_chk, 0, wx.LEFT, 80)
            rb_sizer.Add(txt_bx, 0, wx.LEFT | wx.RIGHT, 20)

            rbsizers.append(rb_sizer)
            n += 5
            id_num += 4

        self.Bind(wx.EVT_CHECKBOX, self.OnChkBox)

        for rbsizer in rbsizers:
            self.sizer.Add(rbsizer, 0)

        btn_lbls = ['Intersection of Multiple\nLines As List Above',
                    'Back Pressure Valve',
                    'Pressure Regulating Valve',
                    'Centrifugal Pump', 'Reservoir Supply']

        self.type_rbb = wx.RadioBox(self, 
                                    label=
                                    'The node point is one of the following;',
                                    style=wx.RA_SPECIFY_COLS,
                                    choices=btn_lbls,
                                    majorDimension=1)

        if new_data is False:
            self.type_rbb.SetSelection(self.nodes[self.node][1])

        self.Bind(wx.EVT_RADIOBOX, self.OnRadioBx, self.type_rbb)

        self.sizer.Add(self.type_rbb, 0,
                       wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 30)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        xit = wx.Button(self, -1, "Exit")
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnClose, xit)

        self.sizer.Add(btnsizer, 0)

        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

    def OnRadioBx(self, evt): 
        rb = evt.GetEventObject()
        rb.GetSelection()
        self.type = rb.GetSelection()

    def OnChkBox(self, evt):
        ckBx = evt.GetEventObject()
        n = ckBx.GetId()
        i = int((n-2)/4)
        if ckBx.GetValue():
            self.txt_bxs[i].Enable()
        else:
            self.txt_bxs[i].ChangeValue('')
            self.txt_bxs[i].Enable(False)

    def OnSave(self):
        lst1 = []
        lst2 = []
        lst3 = []
        n = 1
        flow = 0
        for item in range(1, len(self.rad_bt), 2):
            dirct = 1
            flow = 0
            lst1.append(self.rad_bt[item-1].GetLabel()[-2])
            if self.chk_bx[item-n].GetValue():
                if self.txt_bxs[item-n].GetValue() != '':
                    flow = eval(self.txt_bxs[item-n].GetValue())
            if self.rad_bt[item].GetValue() is False:
                dirct = 0
            lst2.append(dirct)
            lst3.append(flow)
            n += 1

        # make a list containing the line label, flow direction and volume
        ln_dirct = [list((zip(lst1, lst2, lst3))), self.type]
        # add information to the nodes dictionary
        self.nodes[self.node] = ln_dirct
        # change the grid cell color to green to indicate data is complete
        for ltr in self.node_lst:
            if self.node == self.parent.grd.GetCellValue(ord(ltr)-65, 0):
                self.parent.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                        0, 'lightgreen')
            else:
                self.parent.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                        1, 'lightgreen')
                self.parent.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                        2, 'lightgreen')

    def OnClose(self, evt):
        self.OnSave()
        self.Destroy()