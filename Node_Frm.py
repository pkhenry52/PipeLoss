import wx


class NodeFrm(wx.Dialog):
    def __init__(self, parent, node, cord, node_lst, node_dict):

        self.rad_bt = []
        self.chk_bx = []
        self.nd_bx = []
        self.txt_bxs = []
        self.chs_bxs = []

        self.cord = tuple(cord)    # coordinates for the selected node
        self.nodes = node_dict    # the dictionary of nodes
        self.node_lst = set(node_lst)  # set of the lines associated with node
        self.node = node    # the node label which has been selected
        self.saved = False
        self.type = 0
        self.parent = parent

        ttl = 'Node "' + node + ' ' + str(cord) + '" Flow Information.'

        super(NodeFrm, self).__init__(parent, title=ttl, style=wx.RESIZE_BORDER, size=(900,600))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.InitUI()

    def InitUI(self):
        new_data = True
        rdbtn = 0
        txtbx = 0
        ln_lst = set()
        d = {}  # a dictionary of line(key) and rdbtn1,flow(values)

        chcs_1 = ['US GPM', 'ft^3/s', 'm^3/hr']

        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self, label='Flow\nInto\nNode',
                             style=wx.ALIGN_LEFT)
        hdr2 = wx.StaticText(self, label='Flow\nOut Of\nNode',
                             style=wx.ALIGN_LEFT)
        hdr3 = wx.StaticText(self, label='External\nConsumption\nFlow',
                             style=wx.ALIGN_CENTER)
        hdr4 = wx.StaticText(self, label='Units\nfor\nFlow',
                             style=wx.ALIGN_CENTER)

        hdrsizer.Add(hdr1, 1, wx.LEFT, 20)
        hdrsizer.Add(hdr2, 1, wx.LEFT, 60)
        hdrsizer.Add(hdr3, 1, wx.LEFT, 35)
        hdrsizer.Add(hdr4, 1, wx.LEFT, 20)

        self.sizer.Add(hdrsizer, 1, wx.BOTTOM, 10)
        id_num = 0
        rbsizers = []

        ''' 
        There are 3 locations the node info needs to be checked;
        1) self.node_lst => a set of all the lines which intersect the node
        based on the information from the runs dictionary
        (what is shown in the plot)
        2) ln_lst => lines previously defined in the nodes dictionary,
        that may not represent the updated plot information
        3) any of the lines which may connect to the queried node but have
        been defined by the other line end point'''

        # check 2) see if queried node has already been defined,
        # if so get the needed info in ln_lst
        if self.node in self.nodes:
             # {'C': [1, 0], 'D': [0, 0], 'G': [0, 0]}
            for k, v1, v2, v3 in self.nodes[self.node]:
                d.setdefault(k, []).append(v1)
                d.setdefault(k, []).append(v2)
                d.setdefault(k, []).append(v3)
            ln_lst = set(d.keys())
        else:
            ln_lst = self.node_lst

        # convert self.runs into a tuple of (line lbl, endpoints, new line)
        # [('A', [('origin', 'a'), 1]), ('B', [('origin', 'b'), 1]),
        #  ('C', [('b', 'c'), 1]), ('D', [('c', 'd'), 1]), ... ]
        run_tpl = list(self.parent.runs.items())

        # step 3) getting any line which terminate
        # with the queried end point
        self.cmn_lns = {}
        # for each key value (node) in self.nodes
        # return the intersecting lines as node_lines
        for nd_lbl in self.nodes:
            # skip the node of interest
            if nd_lbl != self.node:
                node_lines = set([item[0] for \
                    item in run_tpl if nd_lbl in item[1][0]])
                # compare the list of lines for each node
                # with the lines list for the queried node
                # if there is a common line save it and the node (nd_lbl)
                if list(node_lines.intersection(ln_lst)) != [] and ln_lst != {}:
                    self.cmn_lns[list(node_lines.intersection
                                    (ln_lst))[0]] = nd_lbl

        n = 0
        # check each line located at the node as
        # specified from the self.runs dictionary
        for ln in self.node_lst:
            # if it is not an update (ie. there is no difference
            # between the self.nodes list and self.runs generated
            # list of lines) set the radio buttons
            # to default else use the saved dictionary values
            if ln in self.node_lst.difference(ln_lst) is False:
                rdbtn, txtbx, chsbx = d[ln]
                txt_lbl = ''
                new_data = False
            # check if line is part of the set
            # of lines listed at any other defined node
            elif ln in self.cmn_lns:
                txt_lbl = 'Specified\nat node "' + self.cmn_lns[ln] + '"'
                for i in self.nodes[self.cmn_lns[ln]]:                  
                    if i[0] == ln:
                        rdbtn = bool(i[1]-1)
                        txtbx = i[2]
                        chsbx = i[3]
            # if the line is not part of another defined node 
            # and it is in the self.node_lst list of lines
            # and it has been defined then use those values
            elif ln in d:
                rdbtn, txtbx, chsbx = d[ln]
                txt_lbl = 'Not Yet\nSpecified  '
            else:
                txt_lbl = 'Not Yet\nSpecified  '

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

            chs_bx = wx.Choice(self, id_num+4, choices=chcs_1, size=(-1, 30))
            chs_bx.Enable(False)

            if txtbx != 0:
                chs_bx.Enable()
                txt_bx.Enable()
                txt_bx.ChangeValue(str(txtbx))
                chs_bx.SetSelection(chsbx)
                flow_chk.SetValue(True)

            self.rad_bt.append(pos_rb)
            self.rad_bt.append(neg_rb)
            self.nd_bx.append(nd_txt)
            self.chk_bx.append(flow_chk)
            self.txt_bxs.append(txt_bx)
            self.chs_bxs.append(chs_bx)

            rb_sizer.Add(pos_rb, 0, wx.LEFT, 20)
            rb_sizer.Add(neg_rb, 0, wx.LEFT, 40)
            rb_sizer.Add(nd_txt, 0, wx.ALIGN_TOP)
            rb_sizer.Add(flow_chk, 0, wx.LEFT, 40)
            rb_sizer.Add(txt_bx, 0, wx.LEFT, 20)
            rb_sizer.Add(chs_bx, 0, wx.LEFT | wx.RIGHT, 20)

            rbsizers.append(rb_sizer)
            n += 5
            id_num += 4

        self.Bind(wx.EVT_CHECKBOX, self.OnChkBox)

        for rbsizer in rbsizers:
            self.sizer.Add((10,10))
            self.sizer.Add(rbsizer, 0)

        btn_lbls = ['Intersection of Multiple\nLines As List Above',
                    'Back Pressure Valve',
                    'Pressure Regulating Valve',
                    'Tank Supply',
                    'Centrifugal Pump\nTank']

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
            self.chs_bxs[i].Enable()
        else:
            self.txt_bxs[i].ChangeValue('')
            self.txt_bxs[i].Enable(False)
            self.chs_bxs[i].SetSelection(4)
            self.chs_bxs.Enable(False)

    def OnSave(self, evt):
        # if the first item in the node type is
        # selected as just an intercestion point
        if self.type == 0:
            self.SaveNode()

    def SaveNode(self):
        '''saves the data if the node is just
        specified as an intersection of lines'''
        lst1 = []
        lst2 = []
        lst3 = []
        lst4 = []
        # cycle through the radio buttons and get the value of in first row
        m = 1
        for item in range(1, len(self.rad_bt), 2):
            dirct = 1
            flow = 0
            unts = 4
            # get the line label from the radiobutton label
            ln_lbl = self.rad_bt[item-1].GetLabel()[-2]
            lst1.append(ln_lbl)
            if self.chk_bx[item-m].GetValue():
                if self.txt_bxs[item-m].GetValue() != '':
                    flow = float(self.txt_bxs[item-m].GetValue())
                    unts = self.chs_bxs[item-m].GetSelection()

            if self.rad_bt[item].GetValue() is False:
                dirct = 0
            m += 1

            # if the node data is saved for this node then the other nodes
            # with common lines need to relect the direction changes
            if ln_lbl in self.cmn_lns:
                n = 0
                tpl = []
                for tp in self.nodes[self.cmn_lns[ln_lbl]]:
                    if tp[0]==ln_lbl:
                        tpl.append(ln_lbl)
                        tpl.append(abs(dirct-1))
                        tpl.append(tp[2])
                        tpl.append(tp[3])
                        self.nodes[self.cmn_lns[ln_lbl]][n] = tuple(tpl)
                    n += 1
            lst2.append(dirct)
            lst3.append(flow)
            lst4.append(unts)

        # make a list containing the line label, flow direction and volume
        ln_dirct = list(zip(lst1, lst2, lst3, lst4))
        # add information to the nodes dictionary
        self.nodes[self.node] = ln_dirct
        if self.node in self.nodes:
            for ln in self.nodes[self.node]:
                if ln[0] in self.parent.plt_arow:
                    self.parent.plt_arow.pop(ln[0]).remove()
                endpt1 = self.node
                if self.parent.runs[ln[0]][0].index(endpt1) == 0:
                    endpt2 = self.parent.runs[ln[0]][0][1]
                else:
                    endpt2 = self.parent.runs[ln[0]][0][0]
                if ln[1] == 1:
                    tmp = endpt2
                    endpt2 = endpt1
                    endpt1 = tmp
                self.parent.DrawArrow(endpt1, endpt2, ln[0])

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
#        self.EndModal(True)
        self.Destroy()