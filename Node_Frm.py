import wx


class NodeFrm(wx.Dialog):
    def __init__(self, parent, node, cord, node_lst, node_dict):

        self.rad_bt = []
        self.chk_bx = []
        self.nd_bx = []
        self.txt_bxs = []
        self.cord = tuple(cord)    # coordinates for the selected node
        self.nodes = node_dict    # the dictionary of nodes
        self.node_lst = set(node_lst)  # set of the lines associated with node
        self.node = node    # the node label which has been selected
        self.saved = False
        self.type = 0

        ttl = 'Node "' + node + ' ' + str(cord) + '" Flow Information.'

        super().__init__(parent, title=ttl,
                         style=wx.DEFAULT_FRAME_STYLE &
                         ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX |
                           wx.MINIMIZE_BOX) | wx.STAY_ON_TOP)

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
        # see if node has already been defined
        # the following will check to see if node
        # has been changed since last save
        # to the database or dictionary
        if self.node in self.nodes:
            d = {}  # a dictionary of line(key) and rdbtn1,flow(values)
            for k, v1, v2 in self.nodes[self.node][0]:
                d.setdefault(k, []).append(v1)
                d.setdefault(k, []).append(v2)
            ln_lst = set(d.keys())

        # convert elf.runs into a tuple of (line lbl, endpoints, new line)
        run_tpl = list(self.parent.runs.items())

        # for each of the defined nodes generate a list of
        # lines with the specified endpoint 'node'
        self.cmn_lns = {}
        # if there not any nodes defined skip this step
#        if self.nodes != {}:
        # for each key value (node) in self.nodes
        # return the intersecting lines
        # skip repeating the node of interest
        for nd_lbl in self.nodes:
            if nd_lbl != self.node:
                node_lines = set([item[0] for \
                    item in run_tpl if nd_lbl in item[1][0]])
                # if there are other nodes already defined with
                # lines ending in the node of interest then collect
                # this as a common line already defined
                if list(node_lines.intersection(ln_lst)) != []:
                    self.cmn_lns[list(node_lines.intersection
                                    (ln_lst))[0]] = nd_lbl
        n = 0
        # get each line located at the node as
        # specified on the current node dictionary
        for ln in self.node_lst:
            # check if line exists in set of all
            # lines intersecting defined nodes
            # if it is an update set the radio buttons
            # to default else use the saved dictionary values
            if ln in self.node_lst.difference(ln_lst):
                rdbtn = 0
                txtbx = 0
                new_data = True
            else:
                rdbtn, txtbx = d[ln]
                new_data = False

            if ln in self.cmn_lns:
                txt_lbl = 'Specified\nat node "' + self.cmn_lns[ln] + '"'
                for i in self.nodes[self.cmn_lns[ln]][0]:
                    if i[0] == ln:
                        rdbtn = bool(i[1]-1)
                        txtbx = i[2]
            else:
                txt_lbl = ''

            rb_sizer = wx.BoxSizer(wx.HORIZONTAL)
            pos_rb = wx.RadioButton(self, id_num,
                                    label='\t\tline "' + ln + '"',
                                    pos=(20, 10*n),
                                    style=wx.RB_GROUP)
            neg_rb = wx.RadioButton(self, id_num+1, label='', pos=(180, 10*n))
            neg_rb.SetValue(bool(rdbtn))

            nd_txt = wx.StaticText(self, id_num, label=txt_lbl)
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
            self.nd_bx.append(nd_txt)
            self.chk_bx.append(flow_chk)
            self.txt_bxs.append(txt_bx)

            rb_sizer.Add(pos_rb, 0, wx.LEFT, 20)
            rb_sizer.Add(neg_rb, 0, wx.LEFT, 40)
            rb_sizer.Add(nd_txt, 0, wx.ALIGN_TOP)
            rb_sizer.Add(flow_chk, 0, wx.LEFT, 40)
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

        self.Bind(wx.EVT_RADIOBOX, self.OnRadioBx)

        self.sizer.Add(self.type_rbb, 0,
                       wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 30)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        xit = wx.Button(self, -1, "Exit")
        sve = wx.Button(self, -1, "Save")
        btnsizer.Add(sve, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnSave, sve)
        self.Bind(wx.EVT_BUTTON, self.OnClose, xit)

        self.sizer.Add(btnsizer, 0)

        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

    def OnRadioBx(self, evt):
        rb = evt.GetEventObject()
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

    def OnSave(self, evt):
        lst1 = []
        lst2 = []
        lst3 = []

        # cycle through the radio buttons and get the value of in first row
        m = 1
        for item in range(1, len(self.rad_bt), 2):
            dirct = 1
            flow = 0
            # get the line label from the radiobutton label
            ln_lbl = self.rad_bt[item-1].GetLabel()[-2]
            lst1.append(ln_lbl)
            if self.chk_bx[item-m].GetValue():
                if self.txt_bxs[item-m].GetValue() != '':
                    flow = float(self.txt_bxs[item-m].GetValue())
            if self.rad_bt[item].GetValue() is False:
                dirct = 0
            m += 1

            # if the node data is saved for this node then the other nodes
            # with common lines need to relect the direction changes
            if ln_lbl in self.cmn_lns:
                n = 0
                tpl = []
                for tp in self.nodes[self.cmn_lns[ln_lbl]][0]:
                    if tp[0]==ln_lbl:
                        tpl.append(ln_lbl)
                        tpl.append(abs(dirct-1))
                        tpl.append(tp[2])
                        self.nodes[self.cmn_lns[ln_lbl]][0][n] = tuple(tpl)
                    n += 1
            lst2.append(dirct)
            lst3.append(flow)

        # make a list containing the line label, flow direction and volume
        ln_dirct = [list(zip(lst1, lst2, lst3)), self.type]
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
        self.EndModal(True)
        self.Destroy()