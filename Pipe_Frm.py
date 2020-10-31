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

        self.lbl = lbl
        ttl = 'Pipe & Fittings for ' + self.lbl

        super().__init__(parent, title=ttl, size=(850, 930))

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent

        self.InitUI()

    def InitUI(self):
        '''This is the main frame holding the notebook pages'''
        self.dia = 0
        self.ff = 0
        self.data_good = False

        self.nb = wx.Notebook(self)
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
        # menubar construction needs to be trimmed
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
        data = DBase.Dbase().Dsqldata(qry)[0]
        if data != []:
            self.nb.GetPage(0).info1.SetValue(str(data[1]))
            self.nb.GetPage(0).info2.SetValue(str(data[2]))
            self.nb.GetPage(0).info3.SetValue(str(data[3]))
            self.nb.GetPage(0).info4.SetValue(str(data[4]))

        self.SetMenuBar(menubar)
        self.Centre()
        self.Show(True)

    def menuhandler(self, event):
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.OnClose(None)
        elif menu_id == wx.ID_SAVE:
            self.data_good = True
            self.OnClose(None)

    def OnBeforePgChg(self, evt):
        old = evt.GetOldSelection()
        current = evt.GetSelection()
        self.Data_Load(current)

    def OnPageChanged(self, evt):
        ''' once a notebook page is exited it is assumed it is completed and
        the data can be collected and calculations completed'''
        old = evt.GetOldSelection()
        current = evt.GetSelection()

        if self.nb.GetPage(0).info1.GetValue() == '':
            if self.nb.GetPage(current).Name != 'General':
                self.nb.GetPage(current).Enable(False)
        else:
            self.nb.GetPage(current).Enable()

        self.K_calc(old)

    def Data_Load(self, current):
        qry = ('SELECT * FROM ' + self.nb.GetPage(current).Name +
               ' WHERE ID = "' + self.lbl + '"')
        data = DBase.Dbase().Dsqldata(qry)
        if data != []:
            data = list(data[0])       
            del data[0]
            col_names = [name[1] for name in DBase.Dbase().Dcolinfo(
                        self.nb.GetPage(current).Name)]
            del col_names[0]
            n = 0
            a = 0
            b = 0
            t = 0
            for item in col_names:
                if item[0] == 'c':
                    self.nb.GetPage(current).pg_chk[n].SetValue(data[n])
                    n += 1
                elif item[0] == 'b':
                    self.nb.GetPage(current).pg_txt[t].SetValue(str(data[n]))
                    t += 1
                elif item[0] == 'r' and item[-1] == '1':
                    self.nb.GetPage(current).rdbtn1[a].SetValue(data[n])
                    a += 1
                elif item[0] == 'r' and item[-1] == '2':
                    self.nb.GetPage(current).rdbtn2[b].SetValue(data[n])
                    b += 1

    def K_calc(self, old):
        old_pg = self.nb.GetPage(old).Name

        if old_pg == 'General':

            # check to see if this a new record or an update
            ValueList, new_data = self.Data_Exist(old_pg)

            length = self.nb.GetPage(old).info2.GetValue()
            matr = self.nb.GetPage(old).info3.GetValue()
            elev = self.nb.GetPage(old).info4.GetValue()

            if self.nb.GetPage(old).info1.GetValue() != '':
                self.dia = float(self.nb.GetPage(old).info1.GetValue())
                e = .00197
                self.ff = (1.14 - 2 * log10(e / (self.dia/12)))**-2
                UpQuery = self.BldQuery(old_pg, new_data)
                ValueList.append(str(self.dia))
                ValueList.append(length)
                ValueList.append(matr)
                ValueList.append(elev)
                DBase.Dbase().TblEdit(UpQuery, ValueList)
            else:
                return

        if old_pg == 'ManVlv1':
            K1 = [3, 340, 30, 55, 21, 150, 36, 55, 100, (45, 35, 25)]
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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

        elif old_pg == 'ChkVlv':
            K3 = [600, 100, 55, 200, (80, 60, 40), 300, 100, 350, 50, 55, 55]
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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

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
            DBase.Dbase().TblEdit(UpQuery, ValueList)

    def BldQuery(self, old_pg, new_data):
        col_names = [name[1] for name in DBase.Dbase().Dcolinfo(old_pg)]

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
        
        if DBase.Dbase().Dsqldata(SQL_Chk) == []:
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

        # if the data entered is completed then color grid line cell
        if self.data_good is True:
            row = ord(self.lbl) - 65
            self.parent.grd.SetRowLabelRenderer(row, RowLblRndr('lightgreen'))

        self.Destroy()


class General(wx.Panel):
    def __init__(self, parent):
        super(General, self).__init__(parent, name='General')

        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self, label='Diameter (inch)',
                             style=wx.ALIGN_LEFT)
        hdr2 = wx.StaticText(self, label='Length (feet)',
                             style=wx.ALIGN_LEFT)
        hdr3 = wx.StaticText(self, label='Material',
                             style=wx.ALIGN_CENTER)
        hdr4 = wx.StaticText(self, label='Delta Elevation',
                             style=wx.ALIGN_CENTER)

        hdrsizer.Add(hdr1, 1, wx.ALIGN_LEFT|wx.LEFT, 20)
        hdrsizer.Add(hdr2, 1, wx.ALIGN_LEFT|wx.LEFT, 70)
        hdrsizer.Add(hdr3, 1, wx.ALIGN_LEFT|wx.LEFT, 30)
        hdrsizer.Add(hdr4, 1, wx.ALIGN_LEFT|wx.LEFT, 50)

        infosizer = wx.BoxSizer(wx.HORIZONTAL)
        self.info1 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.info2 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.info3 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        self.info4 = wx.TextCtrl(self, value='', style=wx.TE_RIGHT)
        infosizer.Add(self.info1, 1, wx.ALIGN_LEFT|wx.LEFT, 20)
        infosizer.Add(self.info2, 1, wx.ALIGN_LEFT|wx.LEFT, 60)
        infosizer.Add(self.info3, 1, wx.ALIGN_LEFT|wx.LEFT, 40)
        infosizer.Add(self.info4, 1, wx.ALIGN_LEFT|wx.LEFT, 40)
        
        self.sizer.Add(hdrsizer, 0)
        self.sizer.Add(infosizer, 0)

        self.SetSizer(self.sizer)


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
