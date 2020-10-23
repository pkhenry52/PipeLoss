import wx


def ScnFil(obj, colm1, colm2, colm3, num_row): #, rd_btns1=[], rd_btns2=[]):
    ''' this function loads all the information into the flex grid'''
    # lst is the actual list of tuples filling the flex grid
    lst = []
    # counters for the btton arays if needed
    b = 0
    c = 0
    '''the num_rows indicates how amny rows will be used on the
    two columns of flex grids. In fact there is only on flex grid split
    to look like two separate grids each of 3 columns.  There is an
    additional column used as a spacer. So there is a total of 7 columns;
    3 with information, a spacer, and 3 more with information'''
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
                img_chk = wx.CheckBox(obj, label="")
                obj.pg_chk.append(img_chk)
                col3 = (img_chk, 1)
            else:
                col3 = (wx.StaticText(obj), 1, wx.EXPAND)
            lst.append(col3)

            # this is the spacer column
            if m%2 == 0:
                col_spc = (wx.StaticText(obj, label='\t\t'), 1, wx.EXPAND)
                lst.append(col_spc)

    return lst


class PipeFrm(wx.Frame):

    def __init__(self, parent, title):
        super(PipeFrm, self).__init__(parent, title=title, size=(800, 930))
        self.InitUI()

    def InitUI(self):
        '''This is the main frame holding the notebook pages'''
        self.nb = wx.Notebook(self)
        self.nb.AddPage(ManVlv1(self.nb),
                                'Ball, Butterfly,\nPlug, Globe Valves')
        self.nb.AddPage(ManVlv2(self.nb), 'Diaphragm,\nGate Valves')
        self.nb.AddPage(ChkVlv(self.nb), 'Check Valves')
        self.nb.AddPage(Fitting(self.nb), 'Fittings')
        self.nb.AddPage(WldElb(self.nb), 'Welded\nElbows')
        self.nb.AddPage(EntExt(self.nb), 'Entry\nExit Losses')

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        # menubar construction needs to be trimmed
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()

        fileMenu.AppendSeparator()

        fileMenu.AppendCheckItem(103, 'Checkable')

        radio1 = wx.MenuItem(fileMenu, 200,
                             text='Radio1', kind=wx.ITEM_RADIO)
        radio2 = wx.MenuItem(fileMenu, 300,
                             text='Radio2', kind=wx.ITEM_RADIO)

        fileMenu.Append(radio1)
        fileMenu.Append(radio2)

        newitem = wx.MenuItem(fileMenu, wx.ID_NEW, text='New',
                              kind=wx.ITEM_NORMAL)
        fileMenu.Append(newitem)

        fileMenu.Append(wx.ID_OPEN, '&Open')
        fileMenu.Append(wx.ID_SAVE, '&Save')
        fileMenu.Append(wx.ID_PRINT, '&Print\tCtrl+P')
        fileMenu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q')

        menubar.Append(fileMenu, '&File')

        editMenu = wx.Menu()
        copyItem = wx.MenuItem(editMenu, 100, text='copy',
                               kind = wx.ITEM_NORMAL)
        editMenu.Append(copyItem)

        cutItem = wx.MenuItem(editMenu, 101, text='cut',
                              kind = wx.ITEM_NORMAL)
        editMenu.Append(cutItem)

        pasteItem = wx.MenuItem(editMenu, 102, text='paste',
                                kind = wx.ITEM_NORMAL)
        editMenu.Append(pasteItem)

        menubar.Append(editMenu, '&Edit')
        self.Bind(wx.EVT_MENU, self.menuhandler)        

        self.SetMenuBar(menubar)
        self.Centre()
        self.Show(True)

    def menuhandler(self, event):
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.OnClose()
        elif menu_id == wx.ID_PRINT:
            pass
    
    def OnPageChanged(self, event):
        ''' once a notebook page is exited it is assumed it is completed and
        the data can be collected and calculations completed'''
        old = event.GetOldSelection()
        current_page = self.nb.GetPage(old)

        if current_page.Name == 'ManVlv1':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
        if current_page.Name == 'ManVlv2':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
        elif current_page.Name == 'ChkVlv':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
        elif current_page.Name == 'Fittings':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
        elif current_page.Name == 'WldElb':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
            for btn in self.nb.GetPage(old).rdbtn1:
                print(btn.GetValue())
            for btn in self.nb.GetPage(old).rdbtn2:
                print(btn.GetValue())
        elif current_page.Name == 'EntExt':
            for txt in self.nb.GetPage(old).pg_txt:
                print(txt.GetValue())
            for btn in self.nb.GetPage(old).rdbtn1:
                print(btn.GetValue())
            for chk in self.nb.GetPage(old).pg_chk:
                print(chk.GetValue())

        event.Skip()

    def OnClose(self):
        self.Close()


class ManVlv1(wx.Panel):
    def __init__(self, parent):
        super(ManVlv1, self).__init__(parent, name='ManVlv1')
        '''the first page of manual valves'''
        self.pg_txt=[]
        # the number of columns is common at 7, the number of rows varies
        # on the nmber of items to be entered
        num_row = 5
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # the list of headers for the two sides of the flexgrid
        # one list per side
        colm1 = [['Ball Valve\nFull Port', 'Reduced Port', 'Plug Valve\n2-Way',
                  '3-Way Straight', '3-Way Branch'], ['Globe Valve\nStraight',
                  'Y-Pattern', 'Right Angle', 'Blow-Down','Butterlfy Valve']]
        # the list of corespnding images if there is no image on that row
        # then specify "Blank"
        colm2 = [['Images/BlV1a.png', 'Blank', 'Images/PlV1a.png',
                  'Images/PlV2a.png', 'Images/PlV2b.png'], ['Images/GbV1a.png',
                  'Images/GbV2a.png', 'Images/GbV4a.png','Images/GbV3a.png',
                  'Images/BfV1a.png']]
        # flags to indicate if a check box (1), an blank space (0)
        # or a radiobutton (2) is to be used for input
        colm3 = [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1]]

        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 25, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class ManVlv2(wx.Panel):
    def __init__(self, parent):
        super(ManVlv2, self).__init__(parent, name='ManVlv2')

        self.pg_txt=[]
        num_row = 7
        num_col = 7

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Gate Valve', 'Full Open', '3/4 Open', '1/2 Open',
                  '1/4 Open', 'Blank', 'Basket\nStainer\tCv'],
                 ['Diaphragm Valve', 'Full Open', '3/4 Open',
                  '1/2 Open', '1/4 Open', 'Blank', 'Y-Strainer']]
        colm2 = [['Images/GtV1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Images/strainer2.png'],
                 ['Images/DpV1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Images/strainer.png']]
        colm3 = [[0, 1, 1, 1, 1, 0, 1], [0, 1, 1, 1, 1, 0, 1]]

        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 5, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class ChkVlv(wx.Panel):
    def __init__(self, parent): 
        super(ChkVlv, self).__init__(parent, name='ChkVlv')

        self.pg_txt=[]
        num_row = 5
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
        
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 30, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class Fitting(wx.Panel):
    def __init__(self, parent): 
        super(Fitting, self).__init__(parent, name='Fittings')

        self.pg_txt=[]
        num_row = 6
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
        
        obj = self

        fgs1 = wx.FlexGridSizer(num_row, num_col, 30, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)


class WldElb(wx.Panel):
    def __init__(self, parent):
        super(WldElb, self).__init__(parent, name='WldElb')

        self.pg_txt = []
        num_row = 11
        num_col = 7
        lst = []
        num_btns = 0
        self.rdbtn1 = []
        self.rdbtn2 = []

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Welded\nElbow', 'r/d = 1\nShort Radius', '90 Deg',
                  '45 Deg', 'Mitre 90 Deg\nElbow', 'Mitre Angle', '15 Deg',
                  '30 Deg', '45 Deg', '60 Deg', '90 Deg'],
                 ['Blank', 'r/d = 1.5\nLong Radius', '90 Deg', '45 Deg',
                  'Mitre 45 Deg\nElbow', 'Mitre Angle', '15 Deg',
                  '30 Deg', '45 Deg', 'Blank', 'Blank']]
        colm2 = [['Images/Elb1a.png', 'Blank', 'Blank',
                  'Blank', 'Images/Mitre1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank'],
                 ['Blank', 'Blank', 'Blank', 'Blank',
                  'Images/Mitre2a.png', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank']]
        colm3 = [[0, 0, 1, 1, 1, 0, 2, 2, 2, 2, 2],
                 [0, 0, 1, 1, 1, 0, 2, 2, 2, 0, 0]]
        
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
        num_row = 12
        num_col = 7
        lst = []
        self.rdbtn1 = []
        self.rdbtn2 = []
        num_btns = 0

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        grd_sizer = wx.BoxSizer(wx.HORIZONTAL)

        colm1 = [['Pipe Entry', 'Blank', 'r/d',
                  '0.0', '0.02', '0.04', '0.06', '0.10', '>= 0.15',
                  'Reducer', 'Small Dia.', 'Omega Angle'],
                 ['Pipe\nExit', 'Control\nValves', 'Cv', 'Cv', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank',
                  'Increaser', 'Large Dia.', 'Omega Angle']]
        colm2 = [['Images/Entr1a.png', 'Images/Entr2a.png', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Images/Rdcr1a.png', 'Blank', 'Blank'],
                 ['Images/Exit1a.png', 'Images/CntrlV1a.png', 'Blank', 'Blank',
                  'Blank', 'Blank', 'Blank', 'Blank', 'Blank',
                  'Images/Incr1a.png', 'Blank', 'Blank']]
        colm3 = [[2, 0, 0, 2, 2, 2, 2, 2, 2, 0, 1, 1],
                 [3, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1]]
        
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

        fgs1 = wx.FlexGridSizer(num_row, num_col, 15, 10)
        fgs1.AddMany(ScnFil(obj, colm1, colm2, colm3, num_row))
        grd_sizer.Add(fgs1, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 20)

        self.Sizer.Add(grd_sizer, 0, wx.ALIGN_LEFT|wx.TOP, 20)

app = wx.App(False)
frm = PipeFrm(None, 'Pipe & Fittings')
frm.Center()
frm.Show()
app.MainLoop()