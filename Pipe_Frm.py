import wx
import DBase
import wx.lib.mixins.gridlabelrenderer as glr
import wx.grid as gridlib
from math import sin, log10, radians


class LftGrd(gridlib.Grid, glr.GridWithLabelRenderersMixin):
    def __init__(self, *args, **kw):
        gridlib.Grid.__init__(self, *args, **kw)
        glr.GridWithLabelRenderersMixin.__init__(self)

class RowLblRndr(glr.GridLabelRenderer):
    '''This function is needed to change the cell colors in the
    grid after data has been saved'''
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor

    def Draw(self, grid, dc, rect, row):
        dc.SetBrush(wx.Brush(self._bgcolor))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

def ScnFil(obj, colm1, colm2, colm3, num_row): #, rd_btns1=[], rd_btns2=[]):
    ''' this function loads all the information into the flex grid.
    The num_rows indicates how many rows will be used on the
    two columns of flex grids. In fact there is only one flex grid split
    to look like two separate grids each of 3 columns.  There is an
    additional column used as a spacer. So there is a total of 7 columns;
    3 with information, a spacer, and 3 more with information'''

    # lst is the actual list of tuples filling the flex grid
    lst = []
    # counters for the button arays if needed
    b = 0
    c = 0

    for n in range(num_row):
        for m in range(len(colm1)):
            # get header text for column 1 and column 5
            # if the spot is to be empty then use a
            # statictext box as a place holder
            if colm1[m][n] == 'Blank':
                col1 = (wx.StaticText(obj), 1, wx.EXPAND)
            else:
                col1 = (wx.StaticText(obj, label=colm1[m][n]), 1,
                        wx.ALIGN_RIGHT)
            lst.append(col1)

            # get image for column 2 and column 6
            # if the spot is to be empty then use a
            # statictext box as a place holder
            if colm2[m][n] == 'Blank':
                col2 = (wx.StaticText(obj), 1, wx.EXPAND)
            else:
                img1 = wx.Image(colm2[m][n], wx.BITMAP_TYPE_PNG)
                img = img1.Scale((img1.GetWidth())/3, (img1.GetHeight())/3)
                pic = wx.StaticBitmap(obj, -1, wx.Bitmap(img))
                col2 = (pic, 1, wx.EXPAND)
            lst.append(col2)

            # get input for column 3 and column 7
            # if the spot is to be empty then use a
            # statictext box as a place holder otherwise use a textctrl
            # or radiobutton array
            if colm3[m][n] == 1:
                img_txt = wx.TextCtrl(obj, value='0', size=(50, 30))
                obj.pg_txt.append(img_txt)
                col3 = (img_txt, 1)
            elif colm3[m][n] == 2:  # set if radiobutton is used
                # values of c and b are used to sync the array
                if m == 0:
                    col3 = (obj.rdbtn1[c], 1, wx.EXPAND)
                    c += 1
                elif m == 1:
                    col3 = (obj.rdbtn2[b], 1, wx.EXPAND)
                    b += 1
            elif colm3[m][n] == 3:  # this is set if a check box is needed
                img_chk = wx.CheckBox(obj, label=' ')
                obj.pg_chk.append(img_chk)
                col3 = (img_chk, 1)
            else:
                col3 = (wx.StaticText(obj), 1, wx.EXPAND)
            lst.append(col3)

            # this is the spacer column
            if m%2 == 0:
                col_spc = (wx.StaticText(obj, label='\t\t'), 1, wx.EXPAND)
                lst.append(col_spc)
    # returns a list consisting of the required
    # widgets to be loaded for the specified notebook page
    return lst

class PipeFrm(wx.Frame):

    def __init__(self, parent, lbl):

        ttl = 'Pipe & Fittings for Line ' + lbl

        super().__init__(parent, title=ttl, size=(850, 930),
                         style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent

        self.InitUI(lbl)

    def InitUI(self, lbl):
        '''This is the main frame holding the notebook pages'''
        # The Pipe Frm is the only form which upadtes the
        # database as infomation is entered
        self.dia = 0
        self.ff = 0
        self.data_good = False
        self.lbl = lbl

        self.nb = wx.Notebook(self)

        self.nb.lbl = lbl
        self.nb.units = ['inches', 'feet', 'meters', 'centimeters', 'millimeters']
        self.nb.mtr = ['Plastic', 'A53 / A106', 'Concrete Smooth', 'Concrete Rough',
                       'Copper Tubing', 'Drawn Tube', 'Galvanized',
                       'Stainless Steel', 'Rubber Lined']

        self.nb.AddPage(General(self.nb), 'General Pipe\n Information')
        self.nb.AddPage(ManVlv1(self.nb),
                        'Ball, Butterfly,\nPlug, Globe Valves')
        self.nb.AddPage(ManVlv2(self.nb), 'Diaphragm,\nGate Valves')
        self.nb.AddPage(ChkVlv(self.nb), 'Check Valves')
        self.nb.AddPage(Fitting(self.nb), 'Fittings')
        self.nb.AddPage(WldElb(self.nb), 'Welded\nElbows')
        self.nb.AddPage(EntExt(self.nb), 'Entry\nExit Losses')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnBeforePgChg)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        # fileMenu.Append(wx.ID_OPEN, '&Open')
        # this will only change the grid cell color data 
        # has already been saved in the page changed function call to K_Cal
        fileMenu.Append(wx.ID_SAVE, '&Data Complete')
        # fileMenu.Append(wx.ID_PRINT, '&Print\tCtrl+P')
        fileMenu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q')
        menubar.Append(fileMenu, '&File')
        self.Bind(wx.EVT_MENU, self.menuhandler)

        # if data exists for the general page fill in the text boxes
        qry = 'SELECT * FROM General WHERE ID = "' + self.lbl + '"'
        frm_data = DBase.Dbase(self.parent).Dsqldata(qry)

        if frm_data != []:
            data = frm_data[0]
            if data != []:
                self.nb.GetPage(0).info1.SetValue(str(data[1]))
                self.nb.GetPage(0).unt1.SetSelection(data[6])
                self.nb.GetPage(0).info2.SetValue(str(data[2]))
                self.nb.GetPage(0).unt2.SetSelection(data[7])
                self.nb.GetPage(0).info3.SetValue(str(data[3]))
                self.nb.GetPage(0).unt3.SetSelection(data[8])
                self.data_good = data[4]
            else:
                self.nb.GetPage(0).unt1.SetSelection(0)
                self.nb.GetPage(0).unt2.SetSelection(1)
                self.nb.GetPage(0).unt3.SetSelection(0)

            if self.lbl in self.parent.vlvs:
                self.nb.typ, unt, loc, setpress, lg = self.parent.vlvs[self.lbl]
                self.nb.GetPage(0).pnl2.Show()
                self.nb.GetPage(0).set_press.SetValue(str(setpress))
                self.nb.GetPage(0).locate.SetValue(str(loc))
                self.nb.GetPage(0).unt_bx.SetSelection(unt)
                if self.nb.typ == 1:
                    self.nb.GetPage(0).bpv_chk.SetValue(True)
                    self.nb.GetPage(0).prv_chk.SetValue(False)
                    self.nb.GetPage(0).vlv_lbl.SetLabel('Upstream Pipe Length')
                elif self.nb.typ == 0:
                    self.nb.GetPage(0).bpv_chk.SetValue(False)
                    self.nb.GetPage(0).prv_chk.SetValue(True)
                    self.nb.GetPage(0).vlv_lbl.SetLabel('Downstream Pipe Length')
            else:
                self.nb.GetPage(0).unt_bx.SetSelection(2)
                self.nb.typ = None

        self.SetMenuBar(menubar)
        self.Centre()
        self.Show(True)

    def menuhandler(self, evt):
        menu_id = evt.GetId()
        if menu_id == wx.ID_EXIT:
            self.OnClose(None)
        elif menu_id == wx.ID_SAVE:
            self.data_good = True
            self.OnClose(None)

    def OnBeforePgChg(self, evt):
        # this called prior to a page change
        current = evt.GetSelection()
        self.Data_Load(current)

    def OnPageChanged(self, evt):
        ''' once a notebook page is exited it is assumed it is completed and
        the data can be collected and calculations completed'''
        old = evt.GetOldSelection()
        current = evt.GetSelection()

        if self.nb.GetPage(0).info1.GetValue() == '' or \
           self.nb.GetPage(0).info1.GetValue() == '0':
            if self.nb.GetPage(current).Name != 'General':
                self.nb.GetPage(current).Enable(False)
        else:
            self.nb.GetPage(current).Enable()

        self.K_calc(old)

    def Data_Load(self, current):
        # load the database data when the page is first called
        qry = ('SELECT * FROM ' + self.nb.GetPage(current).Name +
               ' WHERE ID = "' + self.lbl + '"')
        data = DBase.Dbase(self.parent).Dsqldata(qry)
        if data != []:
            # data is a list containing the tuple of the form's information
            # so change the tuple to just a list
            data = list(data[0])
            # remove the ID value from the list
            del data[0]
            # make list of the table column names and remove the ID name
            col_names = [name[1] for name in DBase.Dbase(self.parent).Dcolinfo(
                         self.nb.GetPage(current).Name)]
            del col_names[0]

            # database counter
            n = 0
            # checkbox counter
            cb = 0
            # radio button1 counter
            a = 0
            # radio button2 counter
            b = 0
            # text box counter
            t = 0
            for item in col_names:
                if item[0] == 'c':
                    self.nb.GetPage(current).pg_chk[cb].SetValue(data[n])
                    cb += 1
                elif item[0] == 'b':
                    self.nb.GetPage(current).pg_txt[t].SetValue(str(data[n]))
                    t += 1
                elif item[0] == 'r' and item[-1] == '1':
                    self.nb.GetPage(current).rdbtn1[a].SetValue(data[n])
                    a += 1
                elif item[0] == 'r' and item[-1] == '2':
                    self.nb.GetPage(current).rdbtn2[b].SetValue(data[n])
                    b += 1
                n += 1

    def K_calc(self, old):
        old_pg = self.nb.GetPage(old).Name

        if old_pg == 'General':

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            if self.nb.GetPage(old).info1.GetValue() != '':
                # convert the input diameter to inches
                unt = self.nb.GetPage(old).unt1.GetSelection()
                if unt == 1:
                    self.dia = float(self.nb.GetPage(old).info1.GetValue())
                elif unt == 0:
                    self.dia = float(self.nb.GetPage(old).info1.GetValue()) * 12
                elif unt == 2:
                    self.dia = float(self.nb.GetPage(old).info1.GetValue()) * 39.37
                elif unt == 3:
                    self.dia = float(self.nb.GetPage(old).info1.GetValue()) / 2.54
                else:
                    self.dia = float(self.nb.GetPage(old).info1.GetValue()) / 25.4

                # specify the coresponding e value in inches for the selected material
                unt = self.nb.GetPage(old).unt3.GetSelection()
                if unt == 1:
                    e = float(self.nb.GetPage(old).info3.GetValue())
                elif unt == 0:
                    e = float(self.nb.GetPage(old).info3.GetValue()) * 12
                elif unt == 2:
                    e = float(self.nb.GetPage(old).info3.GetValue()) * 39.37
                elif unt == 3:
                    e = float(self.nb.GetPage(old).info3.GetValue()) / 2.54
                else:
                    e = float(self.nb.GetPage(old).info3.GetValue()) / 25.4

                # define what this equation for pipe friction loss is.
                self.ff = (1.14 - 2 * log10(e / (self.dia/12)))**-2

                # save the General page data
                Kt0 = 0
                UpQuery = self.BldQuery(old_pg, new_data)
                ValueList.append(str(self.nb.GetPage(old).info1.GetValue()))
                ValueList.append(self.nb.GetPage(old).info2.GetValue())
                ValueList.append(self.nb.GetPage(old).info3.GetValue())
                ValueList.append(self.data_good)
                ValueList.append(Kt0)
                ValueList.append(self.nb.GetPage(old).unt1.GetSelection())
                ValueList.append(self.nb.GetPage(old).unt2.GetSelection())
                ValueList.append(self.nb.GetPage(old).unt3.GetSelection())
                DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)
                '''
                if self.nb.GetPage(old).prv_chk.GetValue() or \
                self.nb.GetPage(old).bpv_chk.GetValue():
                    if self.nb.GetPage(0).prv_chk.GetValue() is True:
                    # selected valve is PRV
                        vlv_typ = 0
                    else:
                    # selected valve is BPV
                        vlv_typ = 1
                    CVlv_list = []
                    CVlv_list.append(self.lbl)
                    CVlv_list.append(vlv_typ)
                    CVlv_list.append(self.nb.GetPage(old).unt_bx.GetSelection())
                    locate = self.nb.GetPage(old).locate.GetValue()
                    CVlv_list.append(float(locate))
                    set_press = self.nb.GetPage(old).set_press.GetValue()
                    CVlv_list.append(float(set_press))
                    lgth = self.nb.GetPage(old).info2.GetValue()
                    CVlv_list.append(float(lgth))

                    SQL_Chk = 'SELECT CVlv_ID FROM CVlv WHERE CVlv_ID = "' + self.lbl + '"'
                    if DBase.Dbase(self.parent).Dsqldata(SQL_Chk) == []:
                        UpQuery = 'INSERT INTO CVlv VALUES (?,?,?,?,?,?)'
                        DBase.Dbase(self.parent).TblEdit(UpQuery, CVlv_list)
                    else:
                        UpQuery = 'UPDATE CVlv SET typ=?, units=?, locate=?, set_press=?, length=? WHERE CVlv_ID = "' + self.lbl + '"'
                        DBase.Dbase(self.parent).TblEdit(UpQuery, CVlv_list[1:])'''
            else:
                return

        if old_pg == 'ManVlv1':
            K1 = [3, 340, 30, 55, 18, 150, 30, 55, 90, (45, 35, 25)]
            Kt1 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            # get the value in the text box and check if it is
            # empty if so set it to zero
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                ValueList.append(bx_val)
                if bx_val == '':
                    bx_val = 0
                if bx == 9:
                    if self.dia <= 8:
                        Kt1 = float(bx_val) * K1[bx][0] * self.ff + Kt1
                    elif self.dia >= 10 and self.dia <= 14:
                        Kt1 = float(bx_val) * K1[bx][1] * self.ff + Kt1
                    elif self.dia >= 16 and self.dia <= 24:
                        Kt1 = float(bx_val) * K1[bx][2] * self.ff + Kt1
                else:
                    Kt1 = Kt1 + float(bx_val) * K1[bx] * self.ff

            ValueList.append(Kt1)
            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

        elif old_pg == 'ManVlv2':
            K2 = [8, 109, 43, 125, 214, 205, 1142, 1000, 300]
            Kt2 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                ValueList.append(bx_val)
                if bx_val == '':
                    bx_val = 0
                Kt2 = Kt2 + float(bx_val) * K2[bx] * self.ff

            ValueList.append(Kt2)
            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

        elif old_pg == 'ChkVlv':
            K3 = [600, 400, 55, 200, (80, 60, 40), 300, 100, 350, 50, 55, 55]
            Kt3 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                ValueList.append(bx_val)
                if bx_val == '':
                    bx_val = 0
                if bx == 4:
                    if self.dia <= 8:
                        Kt3 = float(bx_val) * K3[bx][0] * self.ff + Kt3
                    elif self.dia >= 10 and self.dia <= 14:
                        Kt3 = float(bx_val) * K3[bx][1] * self.ff + Kt3
                    elif self.dia >= 16 and self.dia <= 48:
                        Kt3 = float(bx_val) * K3[bx][2] * self.ff + Kt3
                else:
                    Kt3 = Kt3 + float(bx_val) * K3[bx] * self.ff

            ValueList.append(Kt3)
            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

        elif old_pg == 'Fittings':
            K4 = [30, 2, 16, 2, 50, 20, 13, 60, 72]
            Kt4 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                ValueList.append(bx_val)
                if bx_val == '':
                    bx_val = 0
                Kt4 = Kt4 + float(bx_val) * K4[bx] * self.ff

            ValueList.append(Kt4)
            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

        elif old_pg == 'WldElb':
            K5 = [20, 16, 10, 8, (24, 24, 30, 60), (12, 15)]
            Kt5 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                ValueList.append(bx_val)
                if bx_val == '':
                    bx_val = 0
                if bx == 4:
                    for m in range(len(self.nb.GetPage(old).rdbtn1)):
                        Kt5 = K5[bx][m] *\
                            int(self.nb.GetPage(old).rdbtn1[m].GetValue()) *\
                            self.ff * int(bx_val) + Kt5
                elif bx == 5:
                    for m in range(len(self.nb.GetPage(old).rdbtn2)):
                        Kt5 = K5[bx][m] *\
                            int(self.nb.GetPage(old).rdbtn2[m].GetValue()) *\
                            self.ff * int(bx_val) + Kt5
                else:
                    Kt5 = Kt5 + int(bx_val) * K5[bx] * self.ff

            # locate the index of the radiobuttons which are selected
            rdbtn1_true = [c for c, rb in enumerate(self.nb.GetPage(old).rdbtn1) \
                if int(rb.GetValue()) == 1]
            rdbtn2_true = [c for c, rb in enumerate(self.nb.GetPage(old).rdbtn2) \
                if int(rb.GetValue()) == 1]

            # add the radiobutton and Kt value to the list
            ValueList.append(rdbtn1_true[0])
            ValueList.append(rdbtn2_true[0])
            ValueList.append(Kt5)

            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

        elif old_pg == 'EntExt':
            K6 = [.78, 1, .5, .28, .24, .15, .09, .04]
            Kt6 = 0

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            for bx in range(len(self.nb.GetPage(old).pg_chk)):
                ValueList.append(int(self.nb.GetPage(old).pg_chk[bx].GetValue()))
                Kt6 = K6[bx] * int(self.nb.GetPage(old).pg_chk[bx].GetValue())\
                    + Kt6

            txt0 = self.nb.GetPage(old).pg_txt[0].GetValue()
            if txt0 == '':
                txt0 = 0
            txt2 = self.nb.GetPage(old).pg_txt[2].GetValue()
            if txt2 == '':
                txt2 = 0
            txt0 = float(txt0)
            txt2 = float(txt2)
            if txt0 != 0 and txt2 != 0:
                if txt2 <= 45:
                    Kt6 = .8 * sin(radians(txt2/2)) * (1-(txt0/self.dia)**2) / \
                        (txt0/self.dia)**4 + Kt6
                elif txt2 <= 180 and txt2 > 45:
                    Kt6 = .5 * (1-(txt0/self.dia)**2) * \
                        (sin(radians(txt2/2)))**.5 / (txt0/self.dia)**4 + Kt6

            txt1 = self.nb.GetPage(old).pg_txt[1].GetValue()
            if txt1 == '':
                txt1 = 0
            txt3 = self.nb.GetPage(old).pg_txt[3].GetValue()
            if txt3 == '':
                txt3 = 0
            txt3 = float(txt3)
            txt1 = float(txt1)
            if txt1 != 0 and txt3 != 0:
                if txt3 <= 45:
                    Kt6 = 2.6 * sin(radians(txt3/2)) * (1-(self.dia/txt1)**2) / \
                        (self.dia/txt1)**4 + Kt6
                elif txt3 <= 180 and txt3 > 45:
                    Kt6 = (1-(self.dia/txt1)**2)**2 / (self.dia/txt1)**4 + Kt6

            # add the text boxes and Kt6 values to the list
            ValueList.append(txt0)
            ValueList.append(txt1)
            ValueList.append(txt2)
            ValueList.append(txt3)
            ValueList.append(Kt6)

            UpQuery = self.BldQuery(old_pg, new_data)
            DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

    def BldQuery(self, old_pg, new_data):
        col_names = [name[1] for name in DBase.Dbase(self.parent).Dcolinfo(old_pg)]

        if new_data is False:
            col_names.remove('ID')
            SQL_str = ','.join(["%s=?" % (name) for name in col_names])
            return 'UPDATE ' + old_pg + ' SET ' + SQL_str + \
        ' WHERE ID = "' + self.lbl + '"'
        else:
            num_vals = ('?,'*len(col_names))[:-1]
            return 'INSERT INTO ' + old_pg + ' VALUES (' + num_vals + ')'

    def Data_Exist(self, old_pg):
        SQL_Chk = 'SELECT ID FROM ' + old_pg + ' WHERE ID = "' + self.lbl + '"'
        
        if DBase.Dbase(self.parent).Dsqldata(SQL_Chk) == []:
            new_data = True
            ValueList = [self.lbl]
        else:
            new_data = False
            ValueList = []

        return ValueList, new_data

    def OnClose(self, evt):
        # before closing make sure last page data is read
        # by triggering OnPageChanged
        pg = self.nb.GetSelection()

        if pg == 6:
            self.nb.SetSelection(0)
        else:
            self.nb.SetSelection(pg+1)

        # if the data entered is completed
        if self.data_good is True:
            # color the line label on the grid line cell green
            row = ord(self.lbl) - 65
            self.parent.grd.SetRowLabelRenderer(row, RowLblRndr('lightgreen'))
            # check to see if a BPV or PRV has been added or removed if so
            # pass along to parent form to add or delete valve
            if self.nb.GetPage(0).add_vlv is True:
                loc = self.nb.GetPage(0).locate.GetValue()
                lg = self.nb.GetPage(0).info2.GetValue()
                if self.nb.GetPage(0).prv_chk.GetValue() is True:
                    # selected valve is PRV
                    vlv_typ = 0
                elif self.nb.GetPage(0).bpv_chk.GetValue() is True:
                    # selected valve is BPV
                    vlv_typ = 1
                unts = self.nb.GetPage(0).unt_bx.GetSelection()
                press = self.nb.GetPage(0).set_press.GetValue()
                # if a CV is added or changed on a line then remove
                # any pseudo loop associated with that line
                # and any pre-existing valve
                if self.nb.GetPage(0).vlv_chg is True:
                    self.parent.RemoveVlv(self.lbl)
                self.parent.vlvs[self.lbl] = [vlv_typ, unts, loc, press, lg]
                self.parent.DrawValve(self.lbl, *self.parent.vlv_pts(self.lbl))
            elif self.nb.GetPage(0).add_vlv is False and \
                 self.nb.GetPage(0).vlv_chg is True:
                self.parent.RemoveVlv(self.lbl)

        self.Destroy()


class General(wx.Panel):
    def __init__(self, parent):
        super(General, self).__init__(parent, name='General')

        self.parent = parent
        self.add_vlv = False
        self.vlv_chg = False

        chcs_1 = self.parent.units
        row_lst = [['Plastics', '0.0015', '0.00006'],
                   ['A53\nA106', '0.0610', '0.00240'],
                   ['Concrete\nSmooth', '0.0400', '0.00157'],
                   ['Concrete\nRough', '2.00', '0.07874'],
                   ['Copper\nTube', '0.6100', '0.02402'],
                   ['Drawn\nTube', '0.0015', '0.00006'],
                   ['Galvanized', '0.1500','0.00591'],
                   ['Stainless\nSteel', '0.0020', '0.00008'],
                   ['Rubber\nLined', '0.0100', '0.039']]

        # one sizer to fit them all
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # top outer sizer for top2 and grd1
        top1_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # top inner sizer for grd and static text box
        top2_sizer = wx.BoxSizer(wx.VERTICAL)
        grd = wx.FlexGridSizer(3,3,10,10)

        hdr1 = wx.StaticText(self, label='Diameter',
                             style=wx.ALIGN_LEFT)
        hdr2 = wx.StaticText(self, label='Length',
                             style=wx.ALIGN_LEFT)
        hdr3 = wx.StaticText(self, label='Absolute\nRoughness',
                             style=wx.ALIGN_CENTER)

        self.info1 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.unt1 = wx.Choice(self, choices=chcs_1)
        self.unt1.SetSelection(0)
        self.info2 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.unt2 = wx.Choice(self, choices=chcs_1)
        self.unt2.SetSelection(1)
        self.info3 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.unt3 = wx.Choice(self, choices=chcs_1)
        self.unt3.SetSelection(0)

        grd.AddMany([(hdr1), (self.info1), (self.unt1),
                     (hdr2), (self.info2), (self.unt2),
                     (hdr3), (self.info3), (self.unt3)])

        msg1 = 'This table shows suggested design values for the Absolute\n'
        msg2 = ' or Specific roughness, for various pipe materials.\n'
        msg3 = ' These values are sited from;\n\n'
        msg4 = ' \t- The Hydraulic Institute, Engineering Data Book.\n'
        msg5 = ' \t- Various vendor data compiled by SAIC, 1998\n'
        msg6 = ' \t- F.M. White, Fluid Mechanics, 7th edition'
        msg = msg1 + msg2 + msg3 + msg4 + msg5 + msg6
        info_txt = wx.StaticText(self, label = msg,
                                 style = wx.ALIGN_LEFT)

        top2_sizer.Add(grd, 0, wx.LEFT, 20)
        top2_sizer.Add((10,50))
        top2_sizer.Add(info_txt, 0, wx.LEFT, 20)

        # build the information grid for absolute roughness
        grd1 = gridlib.Grid(self, -1)
        grd1.CreateGrid(9, 3)
        grd1.EnableEditing(False)
        grd1.SetRowLabelSize(1)

        grd1.SetColLabelValue(0, "Pipe\nMaterial")
        grd1.SetColLabelValue(1, "mm")
        grd1.SetColLabelValue(2, "inch")
        
        grd_row = 0
        for items in row_lst:
            grd1.SetRowSize(grd_row, 40)
            grd_col = 0
            for item in items:
                grd1.SetColSize(grd_col, 90)
                grd1.SetCellAlignment(grd_row, grd_col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                grd1.SetCellValue(grd_row, grd_col, item)
                grd_col += 1
            grd_row += 1

        top1_sizer.Add(grd1, 0, wx.LEFT, 35)
        top1_sizer.Add(top2_sizer, 0, wx.LEFT, 20)

        chk_sizer = wx.BoxSizer(wx.VERTICAL)
        self.prv_chk = wx.CheckBox(self, id=1, label='Add a Pressure Relief Valve',
                                   style=wx.ALIGN_RIGHT)
        self.bpv_chk = wx.CheckBox(self, id=2, label='or Back Pressure Valve',
                                   style=wx.ALIGN_RIGHT)
        self.prv_chk.SetValue(False)
        self.bpv_chk.SetValue(False)

        self.Bind(wx.EVT_CHECKBOX, self.Onvlv)

        chk_sizer.Add(self.prv_chk, 0, wx.ALIGN_LEFT| wx.LEFT, 30)
        chk_sizer.Add((10, 5))
        chk_sizer.Add(self.bpv_chk, 0, wx.ALIGN_LEFT | wx.LEFT, 30)

        self.pnl2 = wx.Panel(self)
        pnl2_sizer = wx.BoxSizer(wx.VERTICAL)
        unt_chcs = ['psig',
                    'KPa',
                    'feet water']

        unt_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hrz2 = wx.StaticText(self.pnl2, label = 'Valve Set Pressure')
        self.set_press = wx.TextCtrl(self.pnl2, value='')
        unt_lbl = wx.StaticText(self.pnl2, label='Units')
        self.unt_bx = wx.Choice(self.pnl2, choices=unt_chcs, size=(-1, 30))
        self.unt_bx.SetSelection(2)
        unt_sizer.Add(hrz2, 0, wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, 25)
        unt_sizer.Add(self.set_press, 0, wx.LEFT, 10)
        unt_sizer.Add(unt_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        unt_sizer.Add(self.unt_bx, 0, wx.LEFT, 10)

        vlv_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vlv_lbl = wx.StaticText(self.pnl2, label=' ')
        self.locate = wx.TextCtrl(self.pnl2, value='')
        vlv_sizer.Add(self.vlv_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 25)
        vlv_sizer.Add(self.locate, 0, wx.LEFT, 15)

        pnl2_sizer.Add(unt_sizer, 0, wx.ALIGN_CENTRE)
        pnl2_sizer.Add((10,20))
        pnl2_sizer.Add(vlv_sizer, 0, wx.ALIGN_CENTER)
        self.pnl2.Hide()
        self.pnl2.SetSizer(pnl2_sizer)

        self.sizer.Add((5, 50))
        self.sizer.Add(top1_sizer, border=15)
        self.sizer.Add((10, 25))
        self.sizer.Add(chk_sizer)
        self.sizer.Add(self.pnl2, 0, wx.TOP, 30)

        self.SetSizer(self.sizer)

    def Onvlv(self, evt):
        self.add_vlv = False
        self.vlv_chg = False
        print(self.parent.typ)
        if evt.GetEventObject().GetId() == 1:   # PRV
            self.bpv_chk.SetValue(False)
            if self.parent.typ == 0:
                if self.prv_chk.GetValue() is False:
                    if self.bpv_chk.GetValue() is False:
                        self.add_vlv = False
                        self.vlv_chg = True
                    elif self.bpv_chk.GetValue() is True:
                        self.add_vlv = True
                        self.vlv_chg = True
            elif self.parent.typ == 1:
                if self.prv_chk.GetValue() is True:
                    self.add_vlv = True
                    self.vlv_chg = True
                if self.prv_chk.GetValue() is False:
                    self.add_vlv = False
                    self.vlv_chg = True
            elif self.parent.typ is None:
                if self.prv_chk.GetValue() is True:
                    self.add_vlv = True
                    self.vlv_chg = False

        else:   # BPV
            self.prv_chk.SetValue(False)
            if self.parent.typ == 1:
                if self.bpv_chk.GetValue() is False:
                    if self.prv_chk.GetValue() is False:
                        self.add_vlv = False
                        self.vlv_chg = True
                    elif self.prv_chk.GetValue() is True:
                        self.add_vlv = True
                        self.vlv_chg = True
            elif self.parent.typ == 0:
                if self.bpv_chk.GetValue() is True:
                    self.add_vlv = True
                    self.vlv_chg = True
                if self.bpv_chk.GetValue() is False:
                    self.add_vlv = False
                    self.vlv_chg = True
            elif self.parent.typ is None:
                if self.bpv_chk.GetValue() is True:
                    self.add_vlv = True
                    self.vlv_chg = False

        if self.prv_chk.GetValue() or self.bpv_chk.GetValue():
            self.pnl2.Show()
            if self.prv_chk.GetValue() is False:
                self.vlv_lbl.SetLabel('Upstream Pipe Length')
            else:
                self.vlv_lbl.SetLabel('Downstream Pipe Length')
        else:
            self.pnl2.Hide()

        # if a new valve is being added then check to see
        # if there are any closed loops involved if there
        # are they need to be deleted if the valve is added
        # this applies to closed and pseudo loops
        if self.vlv_chg is False and self.add_vlv is True:
            lp_num = []
            for num in wx.GetTopLevelParent(self.parent).parent.Loops:
                if self.parent.lbl in wx.GetTopLevelParent(self.parent).parent.Loops[num][1]:
                    lp_num.append(num)
            if lp_num != []:
                msg1 = 'Placing a control valve on this line will\n'
                msg2 = 'remove all closed loops ' + str(lp_num) + ' associated with the line.'
                dlg = wx.MessageDialog(self, msg1 + msg2, 'Valve Implications',
                        wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
                rslt = dlg.ShowModal()
                if rslt == wx.ID_CANCEL:
                    self.add_vlv = False
                    if self.parent.typ == 0:
                        self.bpv_chk.SetValue(False)
                        self.prv_chk.SetValue(True)
                        self.pnl2.Show()
                    elif self.parent.typ == 1:
                        self.bpv_chk.SetValue(True)
                        self.prv_chk.SetValue(False)
                        self.pnl2.Show()
                    elif self.parent.typ in None:
                        self.bpv_chk.SetValue(False)
                        self.prv_chk.SetValue(False)
                        self.pnl2.Hide()
                elif rslt == wx.ID_OK:
                    for num in lp_num:
                        wx.GetTopLevelParent(self.parent).parent.RemoveLoop(num)
                dlg.Destroy()
        
        print('PRV = 1, BPV = 2', evt.GetEventObject().GetId())
        print(f'add valve = {self.add_vlv} and change valve = {self.vlv_chg}')
        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Refresh()


class ManVlv1(wx.Panel):
    def __init__(self, parent):
        super(ManVlv1, self).__init__(parent, name='ManVlv1')
        '''the first page of manual valves'''
        self.pg_txt = []
        # the number of columns is common at 7, the number of rows varies
        # on the nmber of items to be entered
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # the list of headers for the two sides of the flexgrid
        # one list per side
        colm1 = [['Ball Valve\nFull Port', 'Reduced Port', 'Plug Valve\n2-Way',
                  '3-Way Straight', '3-Way Branch'],
                 ['Globe Valve\nStraight', 'Y-Pattern', 'Right Angle',
                  'Blow-Down', 'Butterlfy Valve']]
        # the list of corespnding images if there is no image on that row
        # then specify "Blank"
        colm2 = [['Images/BlV1a.png', 'Blank', 'Images/PlV1a.png',
                  'Images/PlV2a.png', 'Images/PlV2b.png'],
                 ['Images/GbV1a.png','Images/GbV2a.png', 'Images/GbV4a.png',
                  'Images/GbV3a.png', 'Images/BfV1a.png']]
        # flags to indicate if a check box (1), an blank space (0),
        # a radiobutton (2) or checkbox (3) is to be used for input
        colm3 = [[1, 1, 1, 1, 1],
                 [1, 1, 1, 1, 1]]
        num_row = len(colm3[0])
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 25, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class ManVlv2(wx.Panel):
    def __init__(self, parent):
        super(ManVlv2, self).__init__(parent, name='ManVlv2')

        self.pg_txt = []
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Gate Valve', 'Full Open', '3/4 Open', '1/2 Open',
                  '1/4 Open', 'Blank', 'Blank'],
                 ['Diaphragm Valve', 'Full Open', '3/4 Open',
                  '1/2 Open', '1/4 Open', 'Blank', 'Y-Strainer']]
        colm2 = [['Images/GtV1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank'],
                 ['Images/DpV1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Images/strainer.png']]
        colm3 = [[0, 1, 1, 1, 1, 0, 0], [0, 1, 1, 1, 1, 0, 1]]
        num_row = len(colm3[0])
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 5, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class ChkVlv(wx.Panel):
    def __init__(self, parent): 
        super(ChkVlv, self).__init__(parent, name='ChkVlv')

        self.pg_txt = []
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Lift Check', 'Lift Check', 'Tilt Disc\nCheck',
                  'Swing\nCheck', 'Swing\nCheck', 'Blank'],
                 ['Globe-Stop\nCheck', 'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank']]
        colm2 = [['Images/LfCV1a.png', 'Images/LfCV2a.png',
                  'Images/TtCV1a.png', 'Images/SwCV1a.png',
                  'Images/SwCV2a.png', 'Blank'],
                 ['Images/SpCV1a.png', 'Images/SpCV1b.png',
                  'Images/SpCV2a.png', 'Images/SpCV2b.png',
                  'Images/SpCV3a.png', 'Images/SpCV3b.png']]
        colm3 = [[1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 1, 1]]
        num_row = len(colm3[0])
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 30, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class Fitting(wx.Panel):
    def __init__(self, parent): 
        super(Fitting, self).__init__(parent, name='Fittings')

        self.pg_txt = []
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Thread/SW\n90 Deg Elbow', '45 Deg Elbow', '180 Deg Return',
                  'Tee', 'Flow Through\n Run', 'Branch'],
                 ['Union\n(Thd/SW)', 'Coupling\n(Thd/SW)', 'Blank', 'Weld Tee',
                  'Flow Through\nRun', 'Branch']]
        colm2 = [['Images/Elb2a.png', 'Images/Elb3a.png', 'Images/Retrn1a.png',
                  'Images/Tee1a.png', 'Blank', 'Blank'],
                 ['Images/Union.png', 'Images/couple.png', 'Blank',
                  'Images/tee.png', 'Blank', 'Blank']]
        colm3 = [[1, 1, 1, 0, 1, 1], [1, 1, 0, 0, 1, 1]]
        num_row = len(colm3[0])
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 30, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class WldElb(wx.Panel):
    def __init__(self, parent):
        super(WldElb, self).__init__(parent, name='WldElb')

        self.pg_txt = []
        num_col = 7
        lst = []
        num_btns = 0
        self.rdbtn1 = []
        self.rdbtn2 = []

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Welded\nElbow', 'r/d = 1\nShort Radius', '90 Deg',
                  '45 Deg', 'Mitre 90 Deg\nElbow', 'Mitre Angle', '15 Deg',
                  '30 Deg', '45 Deg', '90 Deg'],
                 ['Blank', 'r/d = 1.5\nLong Radius', '90 Deg', '45 Deg',
                  'Mitre 45 Deg\nElbow', 'Mitre Angle', '15 Deg',
                  '45 Deg', 'Blank', 'Blank']]
        colm2 = [['Images/Elb1a.png', 'Blank', 'Blank',
                  'Blank', 'Images/Mitre1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank'],
                 ['Blank', 'Blank', 'Blank', 'Blank',
                  'Images/Mitre2a.png', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank']]
        colm3 = [[0, 0, 1, 1, 1, 0, 2, 2, 2, 2],
                 [0, 0, 1, 1, 1, 0, 2, 2, 0, 0]]
        num_row = len(colm3[0])
        # if buttons are to be used then button arrays are used, here the
        # arrays are built based on the number of button flags (2) in the
        # above specifed lists for colm3
        num_btns = len([i for i, val in enumerate(colm3[0]) if val==2])
        if num_btns > 0:
            self.rdbtn1.append(wx.RadioButton(self, style=wx.RB_GROUP))
            for i in range(1, num_btns):
                self.rdbtn1.append(wx.RadioButton(self))

        num_btns = 0
        num_btns = len([i for i, val in enumerate(colm3[1]) if val==2])
        if num_btns > 0:
            self.rdbtn2.append(wx.RadioButton(self, style=wx.RB_GROUP))
            for i in range(1, num_btns):
                self.rdbtn2.append(wx.RadioButton(self))

        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 30, 5)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)

class EntExt(wx.Panel):
    def __init__(self, parent):
        super(EntExt, self).__init__(parent, name='EntExt')

        self.pg_txt = []
        self.pg_chk = []
        num_col = 7
        lst = []
        self.rdbtn1 = []
        self.rdbtn2 = []
        num_btns = 0

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Pipe Entry', 'Blank', 'r/d',
                  '0.0', '0.02', '0.04', '0.06', '0.10', '>= 0.15',
                  'Blank', 'Reducer', 'Small Dia.', 'Omega Angle'],
                 ['Pipe\nExit', 'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Increaser', 'Large Dia.', 'Omega Angle']]
        colm2 = [['Images/Entr1a.png', 'Images/Entr2a.png', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Images/Rdcr1a.png',
                  'Blank', 'Blank'],
                 ['Images/Exit1a.png', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Images/Incr1a.png', 'Blank', 'Blank']]
        colm3 = [[3, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 1, 1],
                 [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]]
        num_row = len(colm3[0])
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 15, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        # bind the checkboxes so they can interact like radio buttons
        self.Bind(wx.EVT_CHECKBOX, self.OnChkBox)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)

    def OnChkBox(self, evt):
        ckBx = evt.GetEventObject()
        lst_indx = self.pg_chk.index(ckBx)

        # this check box is independant of other checkboxes
        if lst_indx != 1:
            # if anyother check box is checked all other boxes must unchecked
            for indx in range(len(self.pg_chk)):
                # again ignore this checkbox if other boxes change
                if indx == 1:
                    continue
                if indx != lst_indx:
                    self.pg_chk[indx].SetValue(False)
