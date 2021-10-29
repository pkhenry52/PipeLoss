import os
import shutil
import sqlite3
from ast import literal_eval
import string
import wx

import wx.grid as gridlib
import wx.lib.mixins.gridlabelrenderer as glr

from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import \
    NavigationToolbar2Wx as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.text import Text
import matplotlib.colors as mcolors
import numpy as np

import DBase
import Node_Frm
import Pipe_Frm
import Calc_Network
import Fluid_Frm
import DataOut
import Final_Rpt

class LftGrd(gridlib.Grid, glr.GridWithLabelRenderersMixin):
    def __init__(self, *args, **kw):
        gridlib.Grid.__init__(self, *args, **kw)
        glr.GridWithLabelRenderersMixin.__init__(self)


class RowLblRndr(glr.GridLabelRenderer):
    '''This function is needed to change the cell colors in the
    grid column labels after data has been saved'''
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor

    def Draw(self, grid, dc, rect, row):
        dc.SetBrush(wx.Brush(self._bgcolor))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        hAlgn, vAlgn = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlgn, vAlgn)


class InputForm(wx.Frame):
    '''The main entery form which contains the grid and the
    plot area for the piping configuration'''
    def __init__(self):

        super().__init__(None, wx.ID_ANY,
                         title='Plot Lines',
                         size=(1300, 840))

        # set up a list of dark colors suitable for the graph
        self.clrs = ['indianred', 'darkred', 'red',
                     'orangered', 'navy',
                     'chocolate', 'saddlebrown','brown',
                     'darkorange', 'orange','darkgreen', 'green',
                     'darkslategray', 'darkcyan',
                     'darkturquoise', 'darkkhaki', 'purple',
                     'darkblue', 'steelblue', 'mediumpurple',
                     'blueviolet', 'darkorchid', 'darkviolet'
                     ]

        self.colours = mcolors.CSS4_COLORS

        # inital file name to empty tring
        self.file_name = ''

        self.loop_pts = []
        self.cursr_set = False
        # list used to track changes in grid cell
        self.old_cell = []

        # set flags for deleting drawing elements
        self.dlt_loop = False
        self.dlt_line = False
        self.dlt_node = False
        self.dlt_pump = False

        # flags to indicate if warning message is to show
        self.show_line = False
        self.show_node = False
        self.show_loop = False
        self.show_pump = False

        # dictionary files for the lines and text plotted
        # used to remove specific items from plot
        self.plt_lines = {}
        # line labels
        self.plt_Txt = {}
        # node labels
        self.plt_txt = {}
        # loop circles
        self.crcl = {}
        # loop circle arrows
        self.arrw = {}
        # loop circle numbers
        self.plt_lpnum = {}
        # line direction arrows
        self.plt_arow = {}
        # pump dictionary
        self.plt_pump = {}
        # valve marked dictionary
        self.plt_vlv = {}
        self.plt_vlv_lbl = {}
        # plot lines and arrows for psuedo loops
        self.plt_pseudo = {}
        self.plt_psarow = {}

        # set dictionary of points; key node letter, value tuple of point,
        self.pts = {}
        # set dictionary of lines key line letter, value list of tuple start
        # point, end point and Boolean if first time end point is used
        self.runs = {}
	    # set dictionary of loops; key loop number, value list of centroid
        # point radius and list of all associated lines by key
        self.Loops = {}
        # dictionary for the tracking of the pseudo loops by number
        # with list of points and lines
        self.Pseudo = {}
        self.wrg_pt = ''
        # dictionary of the points moving around a given loop
        self.poly_pts = {}
        # dictionary of nodes indicating key as node and value lst indicating
        # line lbl and flow into (+) or out of node (-)
        self.nodes = {}
        # dictionary of the elevations fo the nodes
        # used in the Q energy equations
        self.elevs = {}
        # dictionary of the pump circuits
        # used in the Q energy equations
        self.pumps = {}
        # dictionary of the tank circuits
        # used in the Q energy equations
        self.tanks = {}
        # dictionary of the control valves circuits
        # used in the Q energy equations
        self.vlvs = {}

        # list of lines selected to form a loop
        self.Ln_Select = []
        # list of points in a specified direction defining the polygon loop
        self.Loop_Select = False
        # list of points redrawn
        self.redraw_pts = []

        mb = wx.MenuBar()

        fileMenu = wx.Menu()
        fileMenu.Append(103, '&Save To Database')
        fileMenu.Append(106, '&Open Database')
        fileMenu.Append(107, '&Reread Database')
        fileMenu.Append(101, '&Calculate')
        fileMenu.Append(105, '&View Report')
        fileMenu.AppendSeparator()
        fileMenu.Append(104, '&Exit')

        fluidMenu = wx.Menu()
        fluidMenu.Append(301, '&Fluid Properties')

        deleteMenu = wx.Menu()
        deleteMenu.Append(201, '&Node')
        deleteMenu.Append(202, '&Line')
        deleteMenu.Append(203, 'L&oop')
        deleteMenu.Append(204, '&Pump or Tank')

        mb.Append(fileMenu, 'File')
        mb.Append(fluidMenu, 'Fluid Data')
        mb.Append(deleteMenu, '&Delete Element')
        self.SetMenuBar(mb)

        self.Bind(wx.EVT_MENU, self.OnCalc, id=101)
        self.Bind(wx.EVT_MENU, self.OnExit, id=104)
        self.Bind(wx.EVT_MENU, self.OnView, id=105)
        self.Bind(wx.EVT_MENU, self.OnDB_Save, id=103)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=106)
        self.Bind(wx.EVT_MENU, self.OnReread, id=107)

        self.Bind(wx.EVT_MENU, self.OnFluidData, id=301)

        self.Bind(wx.EVT_MENU, self.OnDeleteNode, id=201)
        self.Bind(wx.EVT_MENU, self.OnDeleteLine, id=202)
        self.Bind(wx.EVT_MENU, self.OnDeleteLoop, id=203)
        self.Bind(wx.EVT_MENU, self.OnDeletePump, id=204)

        # create the form level sizer
        Main_Sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the sizer for the left side widgets
        sizerL = wx.BoxSizer(wx.VERTICAL)
        # add the grid and then set it to the left panel
        self.grd = LftGrd(self)
        # define the grid to be 3 columns and 26 rows
        self.grd.CreateGrid(26, 3)

        # set column widths
        for n in range(0, 3):
            self.grd.SetColSize(n, 80)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGING, self.OnCellChanging)

        # set the first column fonts and alignments
        attr = wx.grid.GridCellAttr()
        attr.SetTextColour(wx.BLACK)

        attr.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD))
        attr.SetAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grd.SetColAttr(0, attr)
        self.dflt_grd_clr = (211,211,211)

        #freeze the grid size
        self.grd.EnableDragGridSize(False)

        # set the column headers and format
        self.grd.SetColLabelAlignment(wx.ALIGN_CENTER_HORIZONTAL,
                                      wx.ALIGN_CENTER_VERTICAL)
        self.grd.SetColLabelValue(0, "Start\nPoint")
        self.grd.SetColLabelValue(1, "End\nX")
        self.grd.SetColLabelValue(2, "End\nY")
#        self.default_color = self.grd.GetLabelBackgroundColour()
        # set the left column lables alphabetic
        rowNum = 0
        for c in string.ascii_uppercase:
            self.grd.SetRowLabelValue(rowNum, c)
            rowNum += 1

        # default the first cell to the origin
        self.grd.SetCellValue(0, 0, "origin")
        self.grd.SetReadOnly(0, 0, True)

        editor = wx.grid.GridCellTextEditor()
        editor.SetParameters('10')
        self.grd.SetCellEditor(10, 2, editor)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        drw = wx.Button(self, -1, label="Redraw\nLines")
        self.loop = wx.Button(self, id=0, label="Select\nReal Loop")
        self.pseudo = wx.Button(self, id=1, label="Select\nPseudo Loop")
        xit = wx.Button(self, -1, "Exit")
        btnsizer.Add(drw, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        btnsizer.Add(self.loop, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        btnsizer.Add(self.pseudo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnReDraw, drw)
        self.Bind(wx.EVT_BUTTON, self.OnLoop, self.loop)
        self.Bind(wx.EVT_BUTTON, self.OnLoop, self.pseudo)
        self.Bind(wx.EVT_BUTTON, self.OnExit, xit)

#        sizerL.Add((10, 20))
        sizerL.Add(self.grd, 1, wx.EXPAND)
        sizerL.Add(btnsizer, 1, wx.ALIGN_CENTER, wx.EXPAND)

        sizerR = wx.BoxSizer(wx.VERTICAL)
        # add the draw panel
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ax = self.canvas.figure.axes[0]
        self.ax.grid()
        self.ax.set(xlabel='X Direction', ylabel='Y Direction',
                    title='General 2D Network layout')
        self.add_toolbar()
        self.figure.canvas.mpl_connect('pick_event', self.OnLeftSelect)

        sizerR.Add(self.canvas, 1, wx.EXPAND)
        sizerR.Add(self.toolbar)

        Main_Sizer.Add(sizerL, 0, wx.EXPAND)
        Main_Sizer.Add((10, 10))
        Main_Sizer.Add(sizerR, 1, wx.EXPAND)
        self.SetSizer(Main_Sizer)

        self.Center()
        self.Show(True)
        self.Maximize(True)

    def OnOpen(self,evt):
        self.grd.ClearGrid()

        for r in range(26):
            self.grd.SetRowLabelRenderer(r, RowLblRndr((245,245,245)))
            for c in range(3):
                self.grd.SetCellBackgroundColour(r,c,self.dflt_grd_clr)

        dlg = OpenFile(self)
        dlg.ShowModal()

        self.file_name = dlg.filename

        if isinstance(self.file_name, str):
            self.db = sqlite3.connect(self.file_name)
            with self.db:
                self.cursr = self.db.cursor()
                self.cursr.execute('PRAGMA foreign_keys=ON')

            if self.file_name.split(os.path.sep)[-1] != 'mt.db' and \
                self.file_name.split(os.path.sep)[-1] != "":
                self.Variable_Reset()
                self.DataLoad()

    def OnReread(self,evt):
        self.Variable_Reset()
        self.DataLoad()

    def DataLoad(self):
        # run through all the functions to retreive the data from the database
        no_data = self.DBpts()
        if no_data is True:
            return
        self.DBlines()
        self.DBnodes()
        self.DBelevs()
        self.DBpumps()
        self.DBtanks()
        self.DBvalves()
        self.DBloops()
        self.DBpseudo()
        # the ReDraw function will add the lines to the plot as well as
        # repopulate the plt_Txt, plt_lines and plt_txt dictionaries
        self.ReDraw()
        self.GrdLoad()
        self.Refresh()
        self.Update()

    def Variable_Reset(self):
        self.crcl = {}
        self.arrw = {}
        self.wrg_pt = ''
        self.poly_pts = {}

    def DBpts(self):
        # download the points information and place into the pts dictionary
        no_data = True
        self.pts = {}
        data_sql = 'SELECT * FROM points'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.pts = {i[0]:literal_eval(i[1]) for i in tbl_data}
            no_data = False
        return no_data

    def DBlines(self):
        # download the lines information from the database and put it into
        # the runs dictionary
        self.runs = {}
        data_sql = 'SELECT * FROM lines'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.runs = {i[0]:[tuple(literal_eval(i[1])), i[2]] for i in tbl_data}

    def DBnodes(self):
        # download the data entered in the node_frm and put it into
        # the nodes dictionary
        self.nodes = {}
        data_sql = 'SELECT * FROM nodes'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.nodes = {i[0]:literal_eval(i[1]) for i in tbl_data}

    def DBelevs(self):
        # download the data entered in the node_frm and put it into
        # the elevs dictionary
        self.elevs = {}
        data_sql = 'SELECT * FROM elevs'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.elevs = {i[0]:[i[1],i[2]] for i in tbl_data}

    def DBpumps(self):
        # download the data entered in the node_frm and put it into
        # the pumps dictionary
        self.pumps = {}
        data_sql = 'SELECT * FROM Pump'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.pumps = {i[0]:list(i[1:]) for i in tbl_data}

    def DBvalves(self):
        # download the data entered in the node_frm and put it into
        # the vlvs dictionary
        self.vlvs = {}
        data_sql = 'SELECT * FROM CVlv'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.vlvs = {i[0]:list(i[1:]) for i in tbl_data}

    def DBtanks(self):
        # download the data entered in the node_frm and put it into
        # the tanks dictionary
        self.tanks = {}
        data_sql = 'SELECT * FROM Tank'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.tanks = {i[0]:list(i[1:]) for i in tbl_data}        

    def DBloops(self):
        # enter the data base information for the loops and put it into
        # the Loops dictionaary
        self.Loops = {}
        data_sql = 'SELECT * FROM loops'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.Loops = {i[0]:[[i[1], i[2], i[3]], literal_eval(i[4])]
                          for i in tbl_data} 
            for k,v in self.Loops.items():
                self.Ln_Select = v[1]
                self.AddLoop(k)
#                self.SetRotation(v[0][0], v[0][1], k)
        self.Ln_Select = []

    def DBpseudo(self):
        # enter the data base information for the pseudo loops and put it into
        # the Pseudo dictionaary
        self.Pseudo = {}
        data_sql = 'SELECT * FROM pseudo'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.Pseudo = {i[0]:[literal_eval(i[1]),literal_eval(i[2])]
                           for i in  tbl_data}

    def GrdLoad(self):
        # load the points information into the grid against the
        # coresponding line label
        for k,v in self.runs.items():
            row = ord(k)-65
            end_pt = v[0][1]
            self.grd.SetCellValue(row, 0, v[0][0])
            if end_pt == k.lower():
                self.grd.SetCellValue(row, 1, str(self.pts[end_pt][0]))
                self.grd.SetCellValue(row, 2, str(self.pts[end_pt][1]))
            else:
                self.grd.SetCellValue(row, 1, end_pt)

        # color the cells which repesent defined nodes
        # get the nodes defined in the nodes dictionary
        nds = list(self.nodes.keys())
        # generate a list of all the points for the defined lines
        run_tpl = list(self.runs.items())
        # for each of the defined nodes generate a list of
        # lines in which they are an end point

        for lbl in nds:
#            bg_clr = 'green'
            bg_clr = (124,252,0)

            if len(self.nodes[lbl]) == 1 \
               and lbl not in self.pumps \
               and lbl not in self.tanks:
                row = ord(self.nodes[lbl][0][0]) - 65
                self.grd.SetRowLabelRenderer(row, RowLblRndr('yellow'))

            node_lines = set([item[0] for item in run_tpl
                              if lbl in item[1][0]])

            # high lite the cells containing nodes which are defined
            for ltr in node_lines:
                if lbl == self.grd.GetCellValue(ord(ltr)-65, 0):
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            0, bg_clr)
                else:
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            1, bg_clr)
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            2, bg_clr)

        # high lite the cells caontaining lines which are defined
        data_sql = 'SELECT ID, saved FROM General'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            for ln,saved in tbl_data:
                if saved == 1:
                    row = ord(ln) - 65
                    self.grd.SetRowLabelRenderer(row, RowLblRndr((124,252,0)))
#                    RowLblRndr('green'))

    def add_toolbar(self):
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.toolbar.update()

    def OnCellChanging(self, evt):
        row = evt.GetRow()
        x_val = self.grd.GetCellValue(row, 1)
        y_val = self.grd.GetCellValue(row, 2)

        self.old_cell = [x_val,y_val]

    def OnCellChange(self, evt):
        # provides the new row, col value after change
        # if value is unchanged nothing
        row = evt.GetRow()
        LnLbl = self.grd.GetRowLabelValue(row)

        # if one of the cells in col 1 or 2 has a value
        # check if it is an alpha value
        # a empty cell will return false
        x_val = self.grd.GetCellValue(row, 1)
        y_val = self.grd.GetCellValue(row, 2)

        if self.old_cell == [x_val, y_val]:
            return

        if x_val.isalpha() or y_val.isalpha() and \
                self.grd.GetCellValue(row, 0) != '':
            if LnLbl in self.runs:
                self.MoveNode(x_val + y_val, LnLbl)
            else:
                self.DrawLine(*self.VarifyData(row))
        # confirm data in all 3 cells then get points
        elif x_val != '' and y_val != '' and \
                self.grd.GetCellValue(row, 0) != '':
            if LnLbl in self.runs:
                nd = [float(x_val), float(y_val)]
                self.MoveNode(nd, LnLbl)
            else:
                self.DrawLine(*self.VarifyData(row))
        elif self.grd.GetCellValue(row, 0) not in [*self.pts] and \
            self.grd.GetCellValue(row, 0) != 'origin':
            self.WarnData()
            self.grd.SetCellValue(row, 0, '')
        # if data is not complete then return
        else:
            return

    def VarifyData(self, row):
        points2 = []
        points1 = []
        points = []
        alpha_pts = []
        nd_pt1 = ''
        nd_pt2 = ''
        New_EndPt = True
        LnLbl = self.grd.GetRowLabelValue(row)

        if self.pts=={}:
            self.pts['origin'] = [0, 0]
            txt=self.ax.annotate('origin',(0,0),
                    color=self.colours['purple'],
                    textcoords='offset points',
                    xytext=(3,3), ha='right',
                    picker=True)
            self.plt_txt['origin'] = txt

        # use the specified row and get the values for the 3
        for i in range(0, 3):
            pt = self.grd.GetCellValue(row, i)
            # if a letter is entered in X or Y use its
            # end points for the start of the new line
            if pt != '':
                if pt.isalpha():
                    # first step is to capitalize aplha characters
                    pt = pt.lower()
                    # change the grid value to lowercase
                    self.grd.SetCellValue(row, i, pt)

                    # first column always specifies the start point1
                    if i == 0:
                        # if origin is specified then
                        # point1 is (0,0)
                        if pt == 'origin':
                            nd_pt1 = 'origin'
                            # if 1st column has "origin" as value
                            # then start point is (0,0)
                            points1 = [0, 0]
                        else:
                            # use specified alpha character to determine point
                            # see if it exists in pts dictionary if so assign
                            # it to point1 else show warning dialog
                            nd_pt1 = pt
                            if nd_pt1 in list(self.pts.keys()) or \
                                    nd_pt1 == 'origin':
                                points1 = self.pts[nd_pt1]
                            else:
                                self.WarnData()
                                return

                    # get the x,y values in column 1 & 2
                    # designate them as points2
                    else:
                        New_EndPt = False
                        # if "origin" is in 2nd or 3rd column then
                        # the end point is the origin
                        if pt == 'origin':
                            points2 = [0, 0]
                            nd_pt2 = 'origin'
                        else:
                            # use specified alpha character to determine end
                            # point see if it exists if so assign it to point2
                            # else issue warning
                            nd_pt2 = pt
                            if nd_pt2 in list(self.pts.keys()):
                                points2 = self.pts[nd_pt2]
                            else:
                                self.WarnData()
                                return
                # this cell contains a digit which means
                # it can only be point2 as numeric
                else:
                    points2.append(float(pt))

        points.append(points1)
        points.append(points2)

        # confirm that point2 has two values in tuple and
        # that it has no label associated with it
        if len(points2) == 2:
            # create a reverse dictionary of self.pts to search by coordinates
            rev_pts = {}
            for k, v in self.pts.items():
                v = tuple(v)
                rev_pts[v] = k

            if nd_pt2 == '':
                # this will provide the next available node letter
                nds = [*self.pts]
                # if end points have been specified as (0, 0) then
                # reset node label to 'origin' and New Line status to False
                if points2 == [0, 0]:
                    New_EndPt = False
                    nd_pt2 = 'origin'
                # if the coordinates for an existing point are entered
                # into the grid then change to coordinates to that alpha point
                # and set New_EndPt to false so the point is not printed on
                # the graph twice
                elif tuple(points2) in rev_pts:
                    nd_pt2 = rev_pts[tuple(points2)]
                    New_EndPt = False
                    self.grd.SetCellValue(row, 1, nd_pt2)
                    self.grd.SetCellValue(row, 2, '')
                # if the node lable has already been used based on the
                # lowercase of the line lbl then find the next available letter
                elif LnLbl.lower() in nds:
                    for i in range(97, 123):
                        if chr(i) not in nds:
                            nd_pt2 = chr(i)
                            break
                # all else passed then use the line lbl lowercase
                # for the node label
                else:
                    nd_pt2 = LnLbl.lower()

            self.pts[nd_pt2] = points2
            # add the varified data to the lines dictionary self.runs
            alpha_pts.append(nd_pt1)
            alpha_pts.append(nd_pt2)
            self.runs[LnLbl] = [alpha_pts, New_EndPt]
            return points, LnLbl, New_EndPt

    def DrawLine(self, points, LnLbl, New_EndPt):
        # draw the plot lines and related label

        rnd = np.random.randint(len(self.clrs))
        color_name = self.clrs[int(rnd)]
        # draw the line based on points supplied
        # and populate the dictionay with the control information
        x = [i[0] for i in points]
        y = [i[1] for i in points]
        line = self.ax.plot(x, y, marker='.', markersize=10,
                            color=self.colours[color_name])
        self.plt_lines[LnLbl] = line

        # locate the center of the new line for the label location
        # and populate the dictionay with the control information
        x_mid, y_mid = ((x[0]+x[1])/2, (y[0]+y[1])/2)
        Txt=self.ax.annotate(LnLbl,(x_mid, y_mid),
                            color=self.colours[color_name],
                            textcoords='offset points',
                            xytext=(3,3), ha='left',
                            picker=True)
        self.plt_Txt[LnLbl] = Txt

        # label the end point of the line in lower case
        # and populate the dictionay with the control information
        if New_EndPt is True:
            txt = self.ax.annotate(LnLbl.lower(), (x[1], y[1]),
                                color=self.colours[color_name],
                                textcoords='offset points',
                                xytext=(3,3), ha='left',
                                picker=True)
            self.plt_txt[LnLbl.lower()] = txt

        self.canvas.draw()

    def DrawPump(self, nd_lbl, pump):
        Cx, Cy = self.pts[nd_lbl]
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        # determine length of x and y axis'
        x_lg = xmax - xmin
        y_lg = ymax - ymin

        # set a percentage of the graph sizes for the pump radius
        rx = .05 * x_lg
        ry = .05 * y_lg
        r = max(rx*5/x_lg, ry*5/y_lg)

        if pump:
            # draw the pump
            an = np.linspace(0, 2 * np.pi, 100)
            pump = self.ax.plot(rx * r * np.cos(an) + Cx, ry * r * np.sin(an) + Cy,
                            color='k')#, picker=True)
 
        # determine the orientation of the tank
        xcord = xmax - x_lg / 2
        ycord = ymax - y_lg / 2
        if Cx > xcord and Cy > ycord:
            if pump:
                lp_pump = self.ax.annotate('Pump', 
                                           (rx * r * np.cos(np.pi) + Cx,
                                            ry * r * np.sin(np.pi/2) + Cy),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(3,3), ha='right')
                                       
            x_rect = [Cx + i * rx for i in [.7,.7,1.5,1.5,.7]]
            x_pipe = [Cx, Cx + .7 * rx]
            y_rect = [Cy + i * ry for i in [1.2,2.2,2.2,1.2,1.2]]
            y_pipe = [Cy, Cy + 1.2 * ry]
            lp_tank = self.ax.annotate('Tank',
                                       (Cx + rx * 1.5,
                                        Cy + (2.2 + 1.2)/2 * ry),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(3,3), ha='left')

        elif Cx > xcord and Cy <= ycord:
            if pump:
                lp_pump = self.ax.annotate('Pump',
                                           (rx * r * np.cos(np.pi) + Cx,
                                            ry * r * np.sin(np.pi/2) + Cy),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(-5,-15), ha='right')
                                       
            x_rect = [Cx + i * rx for i in [.7,.7,1.5,1.5,.7]]
            x_pipe = [Cx, Cx + .7 * rx]
            y_rect = [Cy + i * ry for i in [-1.2,0,0,-1.2,-1.2]]
            y_pipe = [Cy, Cy - 1.2 * ry]
            lp_tank = self.ax.annotate('Tank',
                                       (Cx + rx * 1.5, Cy - 1.2/2 * ry),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(3,3), ha='left')
         
        elif Cx <= xcord and Cy <= ycord:
            if pump:
                lp_pump = self.ax.annotate('Pump', 
                                           (rx * r * np.cos(np.pi) + Cx,
                                            ry * r * np.sin(np.pi/2) + Cy),
                                           color='k',
                                           textcoords='offset points',
                                           xytext=(15,-15), ha='left')
             
            x_rect = [Cx + i * rx for i in [-.7,-1.5,-1.5,-.7,-.7]]
            x_pipe = [Cx, Cx - .7 * rx]
            y_rect = [Cy + i * ry for i in [-1.2,-1.2,0,0,-1.2]]
            y_pipe = [Cy, Cy - 1.2 * ry]
            lp_tank = self.ax.annotate('Tank',
                                       (Cx - rx * .7, Cy - (.7 + 1.2)/2 * ry),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(3,-8), ha='left')

        else:
            if pump:
                lp_pump = self.ax.annotate('Pump', (Cx - ry * 4, Cy),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(1,3), ha='center')

            x_rect = [Cx + i * rx for i in [-.7,-1.5,-1.5,-.7,-.7]]
            x_pipe = [Cx, Cx - .7 * rx]
            y_rect = [Cy + i * ry for i in [1.2,1.2,2.2,2.2,1.2]]
            y_pipe = [Cy, Cy + 1.2 * ry]
            lp_tank = self.ax.annotate('Tank',
                                       (Cx - rx * .7, Cy + (1.2 + 2.2)/2 * ry),
                                       color='k',
                                       textcoords='offset points',
                                       xytext=(3,3), ha='left')
            
        # draw the tank and pipe
        tank = self.ax.plot(x_rect, y_rect, color='k')
        pipe = self.ax.plot(x_pipe, y_pipe, color='k')#, picker=True)
        # save the plot information
        if pump:
            self.plt_pump[nd_lbl] = [pump, tank, pipe, lp_pump, lp_tank]
        else:
            self.plt_pump[nd_lbl] = [tank, pipe, lp_tank]

        self.canvas.draw()

    def DrawArrow(self, x0, y0, x1, y1, LnLbl):
        # use the grid size to determine proper arrow head length and width
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        hw = (ymax - ymin) / 70
        hl = (xmax - xmin) / 50
        
        # specify an arrow head location just off center of the line
        xa = .4 * x0 + .6 * x1
        ya = .4 * y0 + .6 * y1
        # specify the arrow head direction
        dx = (x0 - xa) * hl
        dy = (y0 - ya) * hl
        # draw the sucker
        arow = self.ax.arrow(xa, ya,
                             dx, dy,
                             fc='k', ec='k',
                             head_width=hw,
                             head_length=hl,
                             length_includes_head=True)
        # save the arrow head in a dictionary for later deletion if needed
        self.plt_arow[LnLbl] = arow

        self.canvas.draw()

    def DrawValve(self, ln_lbl, x, y, pt1):
        if self.vlvs[ln_lbl][0] == 1:
            txt_lbl = 'BPV'
        elif self.vlvs[ln_lbl][0] == 0:
            txt_lbl = 'PRV'

        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        hw = (ymax - ymin) / 70
        hl = (xmax - xmin) / 70

        # plot a red diamond at the valve location
        vlv = self.ax.plot(x, y, c='red', markersize=10, marker='d')
        self.plt_vlv[ln_lbl] = vlv

        vlv_lbl=self.ax.annotate(txt_lbl,(x-hl,y-hw),
                                 color='black',
                                 textcoords='offset points',
                                 xytext=(10,10), ha='left')

        self.plt_vlv_lbl[ln_lbl] = vlv_lbl
        self.canvas.draw()

    def DrawPseudo(self, num, lst_pts):
        self.plt_pseudo[num] = []
        self.plt_psarow[num] = []
        for n in range(len(lst_pts)-1):
            xmin, xmax = self.ax.get_xlim()
            ymin, ymax = self.ax.get_ylim()
            hw = (ymax - ymin) / 70
            hl = (xmax - xmin) / 50

            x0 = lst_pts[n][0] - hw
            x1 = lst_pts[n+1][0] - hw
            y0 = lst_pts[n][1] - hw
            y1 = lst_pts[n+1][1] - hw

            # draw thw lines parallel to the flow lines
            # if the line is vertical
            if x0 == x1:
                x1 = x0
            # if the line is horizontal
            elif y0 == y1:
                y1 = y0

            psln = self.ax.plot([x0, x1],
                                [y0, y1],
                                'magenta', linestyle=':', marker='')
            self.plt_pseudo[num].append(psln)

            # draw the arrow heads on the psuedo lines

            # specify an arrow head location just off center of the line
            xa = .4 * x1 + .6 * x0
            ya = .4 * y1 + .6 * y0
            # specify the arrow head direction
            dx = (x1 - xa) * hl
            dy = (y1 - ya) * hl
            # draw the sucker
            arow = self.ax.arrow(xa, ya,
                                dx, dy,
                                fc='magenta', ec='k',
                                head_width=hw,
                                head_length=hl,
                                length_includes_head=True)
            self.plt_psarow[num].append(arow)

            if n == int((len(lst_pts)-1) / 2):
                lp_num = self.ax.text(xa-hw, ya-hw, num, color='magenta', picker=True)
                self.plt_lpnum[num] = lp_num
        self.wrg_pt = ''
        self.Loop_Select = False
        self.canvas.draw()

    def RemoveVlv(self, ln_lbl):
        if ln_lbl in self.plt_vlv:
            self.plt_vlv.pop(ln_lbl)[0].remove()
            self.plt_vlv_lbl.pop(ln_lbl).remove()

        # for each pseudo loop see if the control valve is part of it
        for num in [*self.Pseudo]:
            # if the CV is present in a pseudo loop then the loop needs
            # to be removed if the vavle has changed or been deleted
            if ln_lbl in self.Pseudo[num][1]:
                self.RemoveLoop(num)
#                break

        self.canvas.draw()
        self.Refresh()
        self.Update()

        self.vlvs.pop(ln_lbl, None)

    def RemoveLine(self, set_lns):
        # reset the delete warning flag
        self.dlt_line = False
        for lbl in set_lns:
            # remove the lines and its label from the graphic
            if lbl in self.plt_lines:
                self.plt_lines.pop(lbl)[0].remove()
            if lbl in self.plt_Txt:
                self.plt_Txt.pop(lbl).remove()
            if lbl in self.plt_arow:
                self.plt_arow.pop(lbl).remove()
            # get row location based on row label
            row = ord(lbl) - 65
            # remove the points for the line from the grid
            self.grd.SetCellValue(row, 1, '')
            self.grd.SetCellValue(row, 2, '')
            # reset the effected cell colors

            self.grd.SetCellBackgroundColour(row, 1, self.dflt_grd_clr)
#            self.grd.GetDefaultCellBackgroundColour())
            self.grd.SetCellBackgroundColour(row, 2, self.dflt_grd_clr)
#            self.grd.GetDefaultCellBackgroundColour())
            if row != 0:
                self.grd.SetCellValue(row, 0, '')
                self.grd.SetCellBackgroundColour(row, 0, self.dflt_grd_clr)
#                self.grd.GetDefaultCellBackgroundColour())

            # remove the line node from the graphic if it is the only line present
            if len(self.runs) == 1:
                nd1, nd2 = self.runs.pop(lbl)[0]
                for nd in [nd1, nd2]:
                    if nd != 'origin':
                        self.pts.pop(nd)
                        self.plt_txt.pop(nd).remove()
            else:
                # remove the line from the runs dictionary
                # and save the line end points
                nd1, nd2 = self.runs.pop(lbl)[0]

                # turn runs dictionary into tuple of items
                # [('A', [('origin', 'a'), True]), ('B',[('origin','b'), True])]
                # get just the end points for each line
                # [('origin','a'),('origin','b')]
                nd_pts = [item[1][0] for item in list(self.runs.items())]
                # make a set of just the point labels {'a','origin','b'}
                lst_nds = set(item for l in nd_pts for item in l)

                for nd in [nd1, nd2]:
                    if nd not in lst_nds:
                        # remove the node from the list of displayed
                        # nodes if it is not used anywhere else
                        # ie it is a node with out a line
                        self.plt_txt.pop(nd).remove()
                        if nd in self.elevs:
                            del self.elevs[nd]
                        # delete point from dictionary of points
                        # if it is not origin
                        if nd != 'origin':
                            del self.pts[nd]
                    
                    # check to see if the line has been defined in
                    # the nodes dictionary if so delete the line tuple from
                    # the dictionary
                    if nd in self.nodes:
                        if len(self.nodes[nd]) == 1:
                            del self.nodes[nd]
                        else:
                            n = 0
                            for v in self.nodes[nd]:
                                if lbl == v[0]:
                                    self.nodes[nd].pop(n)
                                n += 1


            # retrieve all the values from the real loops dictionary
            set_loop = list(self.Loops.items())
            # get list of loops which are bordered by any of the lines
            for loup in set_loop:
                # find the common lines between the loops dictionary
                # line list and the lines intersection the node
                # if there are any lines common to both then they
                # represent a node associated with a loop
                loop_lns = set_lns.intersection(loup[1][1])
                if len(loop_lns) > 0:
                    self.RemoveLoop(loup[0])

            # retrieve all the values from the pseudo loops dictionary
            set_loop = list(self.Pseudo.items())
            # get list of loops which are bordered by any of the lines
            for loup in set_loop:
                # find the common lines between the loops dictionary
                # line list and the lines intersection the node
                # if there are any lines common to both then they
                # represent a node associated with a loop
                loop_lns = set_lns.intersection(loup[1][1])
                if len(loop_lns) > 0:
                    self.RemoveLoop(loup[0])

            # retrieve the valve data
            if lbl in self.plt_vlv:
                self.RemoveVlv(lbl)

            # revert the line cell color back to default
            self.grd.SetRowLabelRenderer(row, RowLblRndr(self.dflt_grd_clr))
#                self.default_color))
        self.canvas.draw()
        self.Refresh()
        self.Update()

    def RemoveNode(self, lbl):
        # reset the delete warning flag
        self.dlt_node = False

        # build a list of all the lines at this node
        lns = [k for k, v in self.runs.items() if lbl in v[0]]
        # remove any duplicates found in the line list
        set_lns = set(lns)

        self.RemoveLine(set_lns)

    def MoveNode(self, nd, ln):

        effect_loops = []
        if type(nd) is list:
            alpha_nd = self.runs[ln][0][1]
            self.pts[alpha_nd] = nd
        elif type(nd) is str:
            alpha_nd = nd
            '''if it is a string value then a node letter has
            been changed and the line end point is different
            the original node coordinates have not changed.'''

        # list of lines associated with the changed node
        lns = [k for k, v in self.runs.items() if alpha_nd in v[0]]
        set_lns = set(lns)
        set_loop = list(self.Loops.items())
        # get list of loops which are bordered by any of the lines
        for loup in set_loop:
            loop_lns = set_lns.intersection(loup[1][1])
            if len(loop_lns) > 0:
                effect_loops.append(loup[0])

        # determine the new Cx, Cy and r values for the
        # loop based on the new line location and redefine the loops
        for loop_id in effect_loops:
            self.Ln_Select = self.Loops[loop_id][1]
            Cx, Cy, r = self.centroid(self.AddLoop(loop_id))
            self.poly_pts[loop_id] = self.SetRotation(Cx, Cy, loop_id)
            self.Loops[loop_id] = [[Cx, Cy, r], self.Ln_Select]

        # redraw the loops lines and node labels
        self.ReDraw()

    def DrawLoop(self, Cx, Cy, r, num):
        an = np.linspace(0, 2 * np.pi, 100)
        mrk = 8
        if r>10:
            mrk = 15
        # plot the circle
        crc = self.ax.plot(r * np.cos(an)+Cx, r * np.sin(an)+Cy,
                           color='k')#, picker=True)
        self.crcl[num] = crc

        # add the arrow head to circle
        arow = self.ax.plot(Cx-r, Cy, '^', ls='-', ms=mrk,
                            color='k')#, picker=True)
        self.arrw[num] = arow

        # number the loop circle
        lp_num = self.ax.text(Cx, Cy, num, color='k', picker=True)
        self.plt_lpnum[num] = lp_num

        self.Loop_Select = False
        self.canvas.draw()

    def RemoveLoop(self, num):
        # reset the delete warning flag
        self.dlt_loop = False
        if num in self.Loops:
            # remove the graphics from the form
            self.plt_lpnum.pop(num, None).remove()
            self.arrw.pop(num, None)[0].remove()
            self.crcl.pop(num, None)[0].remove()
            self.canvas.draw()
            # remove the items from the appropriate lists and dictionaries
            self.Loops.pop(num, None)
            self.poly_pts.pop(num, None)
        elif num in self.Pseudo:
            # remove the graphics from the form
            self.plt_lpnum.pop(num, None).remove()
            for n in range(len(self.plt_psarow[num])):
                self.plt_psarow[num][n].remove()
                self.plt_pseudo[num][n][0].remove()
            self.plt_psarow.pop(num, None)
            self.plt_pseudo.pop(num, None)
            self.canvas.draw()
            # remove the items from the appropriate lists and dictionaries
            self.Pseudo.pop(num, None)

    def RemovePump(self, lbl):
        # reset the warning flag
        self.dlt_pump = False

        if lbl in self.pumps:
            # remove the graphics elements
            self.plt_pump[lbl][0][0].remove()
            self.plt_pump[lbl][1][0].remove()
            self.plt_pump[lbl][2][0].remove()
            self.plt_pump[lbl][3].remove()
            self.plt_pump[lbl][4].remove()
            del self.plt_pump[lbl]
            # remove the pump from the dictionary
            self.pumps.pop(lbl, None)
        else:
            # remove the graphics elements
            self.plt_pump[lbl][0][0].remove()
            self.plt_pump[lbl][1][0].remove()
            self.plt_pump[lbl][2].remove()
            del self.plt_pump[lbl]
            # remove the tank from the dictionary
            self.tanks.pop(lbl, None)
        
        for l in self.runs:
            # locate the line which connects to the
            # pump or tank
            if lbl in self.runs[l][0]:
                break

        # remove the line data from the Kt database tables
        # i.e General, Fitting, ManVlv1 etc
        for tbl in ['ChkVlv', 'General', 'Fittings', 'EntExt',
                    'ManVlv1', 'ManVlv2', 'WldElb']:
            DBase.Dbase(self).TblDelete(tbl, l, 'ID')

        self.canvas.draw()

    def OnLeftSelect(self, evt):
        if isinstance(evt.artist, Text):
            text = evt.artist
            lbl = text.get_text()
            # if line label is selected do one of three things;
            # pull up the line specification form,
            # add the line to a loop
            # or delete the line
            if lbl.isupper():
                if self.Loop_Select:
                    # take line lbl and go to Loop function
                    self.Loop(lbl) #, self.wrg_pt)
                elif self.dlt_line:
                    self.RemoveLine(set(lbl))
                else:
                    Pipe_Frm.PipeFrm(self, lbl)
            # if node label is selected do one of two things;
            # pull up the node specification form,
            # or delete the line
            elif lbl.islower():
                if self.dlt_node:
                    self.RemoveNode(lbl)
                elif self.dlt_pump:
                    self.RemovePump(lbl)
                else:
                    self.Node(lbl)
            # if a number has been selected it must be a loop,
            # only action is to delete the loop provided delete flag is set
            elif lbl.isdigit():
                if self.dlt_loop:
                    self.RemoveLoop(int(lbl))

    def WarnData(self):
        msg = "A node has been specified which is not defined."
        dialog = wx.MessageDialog(self, msg, 'Node Error', wx.OK|wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnFluidData(self, evt):
        Fluid_Frm.FluidFrm(self)

    def OnDeleteLine(self, evt):
        import DltWrng
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveLine
        if self.show_line is False:
            dlg = DltWrng.DeleteWarning(None, 'line')
            self.dlt_line = dlg.ShowModal()
            self.show_line = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_line = True

    def OnDeleteNode(self, evt):
        import DltWrng
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveNode
        if self.show_node is False:
            dlg = DltWrng.DeleteWarning(None, 'node')
            self.dlt_node = dlg.ShowModal()
            self.show_node = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_node = True

    def OnDeleteLoop(self, evt):
        import DltWrng
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveLoop
        if self.show_loop is False:
            dlg = DltWrng.DeleteWarning(None, 'loop')
            self.dlt_loop = dlg.ShowModal()
            self.show_loop = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_loop = True

    def OnDeletePump(self, evt):
        import DltWrng
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveLoop
        if self.show_pump is False:
            dlg = DltWrng.DeleteWarning(None, 'pump')
            self.dlt_pump = dlg.ShowModal()
            self.show_pump = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_pump = True

    def OnLoop(self, evt):
        '''this set trigger as to what response is needed if a line is selected
        either open input screen or build loop'''
        btn = evt.GetId()
        if btn == 0:
            if self.loop.GetLabel() == 'Select\nReal Loop\nLines':
                self.loop.SetLabel('Cancel\nReal Loop\nSelection')
                self.Loop_Select = True
                self.Ln_Select = []
            else:
                self.loop.SetLabel('Select\nReal Loop\nLines')
                self.loop_pts = []
                self.Loop_Select = False
                self.Ln_Select = []
        else:
            if self.pseudo.GetLabel() == 'Select\nPseudo Loop\nLines':
                self.pseudo.SetLabel('Cancel\nPseudo Loop\nSelection')
                self.Loop_Select = True
                self.Ln_Select = []
                msg = "The first selected line must connect\n \
to a tank, pump or contain a control valve"
                dialog = wx.MessageDialog(self, msg, 'Line Selection',
                                          wx.OK|wx.ICON_INFORMATION)
                dialog.ShowModal()
                dialog.Destroy()
            else:
                self.pseudo.SetLabel('Select\nPseudo Loop\nLines')
                self.Loop_Select = False
                self.wrg_pt = ''
                self.Ln_Select = []

    def Loop(self, lbl):  # , wrg_pt):
        ''' build the loops made up of selected lines
        when all the end points have been duplicated the loop is closed'''
	    # temporary list of the points in a loop
        LnPts = []
        rnd = np.random.randint(len(self.clrs))
        color_name = self.clrs[rnd]

        if 'C' in self.loop.GetLabel():
            # selected to develop real loop
            loop_typ = 0
        else:
            # selected to develop pseudo loop
            loop_typ = 1

        # if this is a closed loop confirm that the
        # selected line does not contain a control valve
        if loop_typ == 0 and (lbl in self.vlvs):
            msg1 = 'A closed or real loop cannot have a '
            msg2 = '\nline containing a control valve.'
            self.WarnLoop(lbl, msg1 + msg2, 'real')
            for lbl in self.Ln_Select:
                self.plt_lines[lbl][0].set_color(self.colours[color_name])
            self.Ln_Select = []
            self.wrg_pt = ''
            return

        for pt in self.runs[lbl][0]:
            if pt in self.tanks or pt in self.pumps:
                # if the end point of the line is the point
                # at which the pump or tank is located do not
                # add it to the list of points LnPts
                continue
            if (pt == self.wrg_pt and len(self.nodes[pt]) <= 2) or \
               (pt == self.wrg_pt and len(self.Ln_Select) <= 1):
                msg1 = 'The line selected approaches the '
                msg2 = '\ncontrol valve from the wrong side.'
                self.WarnLoop(lbl, msg1 + msg2, 'pseudo')
                for lbl in self.Ln_Select:
                    self.plt_lines[lbl][0].set_color(self.colours[color_name])
                self.Ln_Select = []
                self.wrg_pt = ''
                return            

            if lbl in self.vlvs:
                # check to see if the selected line flow is into
                # or out of the upstream node
                for ln in self.nodes[pt]:
                # find the selected line in the nodes list
                    if ln[0] == lbl:
                        if (ln[1] == 1 and self.vlvs[lbl][0] == 1) or \
                        (ln[1] == 0 and self.vlvs[lbl][0] == 0):
                            # this is the case where the flow is out
                            # of the node toward a BPV
                            # OR
                            # this is the case where the flow is into
                            # the node away from a PRV
                            if self.Ln_Select == []:
                                msg = 'Next line selected must intersect at node ' + pt
                                dialog = wx.MessageDialog(self, msg, 'Next Line',
                                                        wx.OK | wx.ICON_INFORMATION)
                                dialog.ShowModal()
                                dialog.Destroy()
                        elif (ln[1] == 0 and self.vlvs[lbl][0] == 1) or \
                        (ln[1] == 1 and self.vlvs[lbl][0] == 0):
                            self.wrg_pt = pt
                            if self.wrg_pt in self.loop_pts:
                                msg1 = 'The line selected approaches the '
                                msg2 = '\ncontrol valve from the wrong side.'
                                self.WarnLoop(lbl, msg1 + msg2, 'pseudo')
                                for lbl in self.Ln_Select:
                                    self.plt_lines[lbl][0].set_color(self.colours[color_name])
                                self.Ln_Select = []
                                self.wrg_pt = ''
                                return
            # build a list of all the selected line end points
            # do not include any point which designate a tank or pump
            if pt == self.wrg_pt and \
              len(self.nodes[pt]) > 2 and \
              len(self.Ln_Select) > 1:
                LnPts.append(pt)
            elif pt != self.wrg_pt:
                LnPts.append(pt)

        if lbl in self.Ln_Select:
            # if line was previously selected, deselect it
            # remove line lbl from selected line list
            self.Ln_Select.remove(lbl)
            self.plt_lines[lbl][0].set_color(self.colours[color_name])
            if lbl in self.vlvs:
                self.wrg_pt = ''
        else:  # a new line is selected
            self.Ln_Select.append(lbl)
            self.plt_lines[lbl][0].set_color('k')

        self.canvas.draw()

        # if line end points are in the list of line points already selected
        # remove it, if it is not add it to the list
        for pnt in LnPts:
            if pnt in self.loop_pts:
                self.loop_pts.remove(pnt)
            else:
                self.loop_pts.append(pnt)

        # if the pseudo loop ends with a PRV then remove the wrg_pt
        if len(self.Ln_Select) > 1 and \
           (self.wrg_pt in self.loop_pts) and \
           lbl in self.vlvs:
            self.loop_pts.remove(self.wrg_pt)

        # confirm all end points have been duplicated and loop closed
        if len(self.loop_pts) == 0:
            # determine which type of loop is being drawn
            if loop_typ == 0:
                self.loop.SetLabel('Select\nReal Loop\nLines')
            else:
                self.pseudo.SetLabel('Select\nPseudo Loop\nLines')

            key_lst = list(self.Loops.keys()) + list(self.Pseudo.keys())
            # check for any missing loop numbers in Loops dictionary
            if key_lst == []:
                loop_num = 1
            else:
                loop_num = [x for x in
                            range(1, key_lst[-1]+1) if x not in key_lst]
                if loop_num == []:
                    loop_num = max(key_lst) + 1
                else:
                    loop_num = loop_num[0]

            # from this point on all lines have been selected
            # code is concerned with the completed list of lines Ln_Select

            # first part of if loop is for the real loop drawing
            if loop_typ == 0:

                # determine the centroid of the polygon and the distance to the
                # shortest to any ine line from the centroid
                # call it the radius for the circular arc
                Cx, Cy, r = self.centroid(self.AddLoop(loop_num))

                # Reassign the polygons points to the dictionary poly_pts
                # moving in a clockwise direction around the
                self.poly_pts[loop_num] = self.SetRotation(Cx, Cy, loop_num)

                self.Loops[loop_num] = [[Cx, Cy, r], self.Ln_Select]
                # once the loop is closed and selection is done then return
                # the lines to ramdon colors
                for  ln in self.Ln_Select:
                    rnd = np.random.randint(len(self.clrs))
                    color_name = self.clrs[rnd]
                    self.plt_lines[ln][0].set_color(self.colours[color_name])

                self.DrawLoop(Cx, Cy, r, loop_num)

            # second part of if loop is for pseudo loops
            else:
                lst_pts = []
                # starting with the first line in Ln_Select
                # to specify the start points
                new_lns = [self.Ln_Select[0]]
                pt1, pt2 = self.runs[self.Ln_Select.pop(0)][0]

                # set the node point of the tank or pump as the
                # first point in the loop pt1 and
                # pt2 is the start point for the next line
                if pt1 in self.tanks or pt1 in self.pumps:
                    lst_pts.append(self.pts[pt1])
                    lst_pts.append(self.pts[pt2])
                elif pt2 in self.tanks or pt2 in self.pumps:
                    lst_pts.append(self.pts[pt2])
                    lst_pts.append(self.pts[pt1])
                    pt2 = pt1

                # confirm that the line is in the list of valves
                if new_lns[0] in self.vlvs:
                    # find the coordinates for the valve
                    for ln in self.nodes[pt1]:
                        if ln[0] == new_lns[0]:
                            x, y, pt2 = self.vlv_pts(new_lns[0])
                            break
                    # the valve point needs to be saved as coordinates
                    lst_pts.append([x, y])
                    # the end point of the line either
                    # upstream for BPV or downstream
                    # for PRV needs to be specified as pt1
                    lst_pts.append(self.pts[pt2])

                # cycle through the lines selected and
                # add the new end points to the point list
                flag = False
                while len(self.Ln_Select) > 0:
                    for l in self.Ln_Select:
                        # locate the line which connects to the
                        # last point
                        if pt2 in self.runs[l][0]:
                            # if the point pt2 defines a line containing a
                            # valve it must be the last line in the loop
                            if l in self.vlvs:
                                x, y, pt2 = self.vlv_pts(l)
                                new_lns.append(l)
                                lst_pts.append([x, y])
                                self.Ln_Select.remove(l)
                                flag = True
                                break
                            # determine if the pt is first or second in the
                            # line cordinates then select the other node
                            # to append to lst_pts
                            if flag is True:
                                break
                            idx = int(np.cos(self.runs[l][0].index(pt2)
                                        *(np.pi/2)))
                            pt2 = self.runs[l][0][idx]
                            self.Ln_Select.remove(l)
                            lst_pts.append(self.pts[self.runs[l][0][idx]])
                            new_lns.append(l)
                self.Pseudo[loop_num] = [lst_pts, new_lns]
                for  ln in new_lns:
                    rnd = np.random.randint(len(self.clrs))
                    color_name = self.clrs[rnd]
                    self.plt_lines[ln][0].set_color(self.colours[color_name])
                self.DrawPseudo(loop_num, lst_pts)
                self.wrg_pt = ''

    def WarnLoop(self, lbl, msg, typ):
        dialog = wx.MessageDialog(self, msg, 'Faulty Line Selection',
                                wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()
        dialog.Destroy()
        # add the line now and delete it from Ln_Select
        # after exiting FOR loop
        self.Ln_Select.append(lbl)
        for  ln in self.Ln_Select:
            rnd = np.random.randint(len(self.clrs))
            color_name = self.clrs[rnd]
            self.plt_lines[ln][0].set_color(self.colours[color_name])
        self.canvas.draw()
        if typ == 'real':
            self.loop.SetLabel('Select\nReal Loop\nLines')
        elif typ == 'pseudo':
            self.pseudo.SetLabel('Select\nPseudo Loop\nLines')
        self.Loop_Select = False
        for  ln in self.Ln_Select:
            rnd = np.random.randint(len(self.clrs))
            color_name = self.clrs[rnd]
            self.plt_lines[ln][0].set_color(self.colours[color_name])
        self.loop_pts = []
        self.Ln_Select = []
        self.wrg_pt = ''

    def AddLoop(self, loop_num):
        '''generate the consecutive list of points making up the polygon
        in a clockwise or counterclockwise direction'''
        new_ln_list = []
        # make a copy of the lines making up the polygon
        poly_lns = self.Ln_Select[:]
        # number of line in polygon
        num_lns = len(poly_lns)
        # start with the first line in the polygon
        tmp_ln = poly_lns[0]
        new_ln_list.append(tmp_ln)
        # get the end nodes of the line
        Ln_pts = list(self.runs[tmp_ln[0]][0])
        # remove the line from the list of polygon lines
        poly_lns.remove(tmp_ln)
        # use the last node in the line as a search
        test_pt = Ln_pts[-1]
        # go through all the polylines until you find one
        # with the node matching the test node then
        # remove the line from the list of poly lines and add
        # the second line node to the list of polygon
        # nodes and use it as the test for the next line
        for i in range(num_lns):
            for ln in poly_lns:
                tmp_cord = list(self.runs[ln][0])
                if test_pt in tmp_cord:
                    tmp_cord.remove(test_pt)
                    poly_lns.remove(ln)
                    new_ln_list.append(ln)
                    if tmp_cord[0] not in Ln_pts:
                        Ln_pts.append(tmp_cord[0])
                    test_pt = tmp_cord[0]
                    break
        # change the list of nodes into x,y cordinates
        final_pts = [self.pts[cord] for cord in Ln_pts]
        self.poly_pts[loop_num] = final_pts
        self.Ln_Select = new_ln_list
        return(final_pts)

    def centroid(self, poly):
        '''Gets the centroid of the polygon and uses it to specify the center
        of the graphic loop'''
        centroid_total = []
        poly_cord = []
        rad = []
        # Calculate the centroid from the weighted average of the polygon's
        # constituent triangles
        area_total = 0
        centroid_total = [float(poly[0][0]), float(poly[0][1])]
        for i in range(0, len(poly) - 2):
            # Get points for triangle ABC
            a, b, c = poly[0], poly[i+1], poly[i+2]
            # Calculate the signed area of triangle ABC
            area = ((a[0] * (b[1] - c[1])) +
                    (b[0] * (c[1] - a[1])) +
                    (c[0] * (a[1] - b[1]))) / 2.0
            # If the area is zero, the triangle's line segments are
            # colinear so we should skip it
            if area == 0:
                continue
            # The centroid of the triangle ABC is the average of its three
            # vertices
            centroid = [(a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0]
            # Add triangle ABC's area and centroid to the weighted average
            centroid_total[0] = ((area_total * centroid_total[0]) +
                                 (area * centroid[0])) / (area_total + area)
            centroid_total[1] = ((area_total * centroid_total[1]) +
                                 (area * centroid[1])) / (area_total + area)
            area_total += area

        # determine the radius of arc around centroid
        for Ln in self.Ln_Select:
            Cx = centroid_total[0]
            Cy = centroid_total[1]
            for alpha_pt in self.runs[Ln][0]:
                poly_cord.append(self.pts[alpha_pt])
            p0 = poly_cord[0]
            p1 = poly_cord[1]
            tN = ((p0[0] - Cx)**2 + (p0[1] - Cy)**2)**.5
            tD = ((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)**.5
            t = tN / tD
            # if t is greater than 1 then centroid is to right of end of line
            # and distance is taken to end point,
            # if t is less than 0 centroid is to the left of end of line
            # and distance is taken to end point,
            # else centroid can have a perpendicular distance to line
            if t < 0:
                r = (abs((p0[0]-Cx)**2 - (p0[1] - Cy)**2))**.5
            elif t > 1:
                r = (abs((p1[0]-Cx)**2 - (p1[1] - Cy)**2))**.5
            else:
                rN = abs(((p0[1] - p1[1]) * Cx + (p1[0] - p0[0]) * Cy +
                            (p0[0] * p1[1] - p1[0] * p0[1])))
                rD = (abs((p1[0] - p0[0])**2 + (p1[1] - p0[1])**2))**.5
                r = rN / rD

            # safe all the calculated radi &
            # reduce radius to fit into polygon
            rad.append(r * .5)
            # reset the poly_cord points for next calculation
            poly_cord = []
        # use the smallest of the distances between
        # the lines as the circle radius
        r = min(rad)
        return [Cx, Cy, r]

    def SetRotation(self, Cx, Cy, loop_num):
        ''' set direction of lines around loop as clockwise'''
        # add plus one for clockwise rotation
        rot = 0
        # make a copy of the polygon points and add the start point to
        # the end of the list
        poly = self.poly_pts[loop_num]
        poly.append(poly[0])

        for n in range(len(poly)-1):
            btm = poly[n+1][0] - poly[n][0]
            top = poly[n+1][1] - poly[n][1]
            if btm == 0:
                xL = poly[n][0]
                if xL > Cx and top > 0:
                    rot -= 1
                elif xL > Cx and top < 0:
                    rot += 1
                elif xL < Cx and top > 0:
                    rot += 1
                elif xL < Cx and top < 0:
                    rot -= 1
            else:
                m = top / btm
                if m == 0:
                    yL = poly[n][1]
                else:
                    yL = m * (Cx - poly[n][0]) + poly[n][1]

                if yL > Cy and btm < 0:
                    rot += 1
                elif yL > Cy and btm < 0:
                    rot -= 1
                elif yL < Cy and btm > 0:
                    rot -= 1
                elif yL < Cy and btm < 0:
                    rot += 1                    

        # if the rotation is counter clockwise reverse the
        # points and the line order
        if rot < 0:
            poly = list(reversed(poly))
            self.Ln_Select = list(reversed(self.Ln_Select))
        poly.pop(-1)
        self.poly_pts[loop_num] = poly
        return poly

    def vlv_pts(self, ln_lbl):
        dat = self.vlvs[ln_lbl]
        loc = dat[2]
        lg = dat[4]
        typ = dat[0]
        # initialized sent from the Pipe_frm
        # get the end points for the line
        pt1, pt2 = self.runs[ln_lbl][0]
        # determine the direction of flow so up and
        # down stream flow can be determined
        for ln in self.nodes[pt1]:
            if ln[0] == ln_lbl:
                # if the flow is into the first point then reverse
                # the X0 and X1
                # selected valve is BPV
                if ln[1] == 1:
                    x_0 = self.pts[pt1][0]
                    x_1 = self.pts[pt2][0]
                    y_0 = self.pts[pt1][1]
                    y_1 = self.pts[pt2][1]
#                    if typ == 0:
#                        pt1 = pt2
                # selected valve is PRV
                elif ln[1] == 0:
                    x_0 = self.pts[pt2][0]
                    x_1 = self.pts[pt1][0]
                    y_0 = self.pts[pt2][1]
                    y_1 = self.pts[pt1][1]
                    if typ == 1:
                        pt1 = pt2
                # calculate the length of the line
                x_mid = (x_0 + x_1) / 2
                d = ((x_1 - x_0)**2 + (y_1 - y_0)**2)**.5
                # determine the ratio of the distance the
                # valve is along the line
                if typ == 0:   # PRV
                    t = float(loc) / float(lg)
                else:    # BPV
                    t = (float(lg)-float(loc)) / float(lg)
                # calculate the point location for the valve
                # if the location is the middle of the line
                # than it will conflict with the line arrow and lable
                x = ((1 - t) * x_0 + t * x_1)
                y = ((1 - t) * y_0 + t * y_1)
                if x == x_mid:
                    x = ((1 - t/1.2) * x_0 + t/1.2 * x_1)
                    y = ((1 - t/1.2) * y_0 + t/1.2 * y_1)

        return(x, y, pt1)

    def Node(self, nd_lbl):
        # collect data needed to initialize the node_frm
        run_tpl = list(self.runs.items())
        cord = self.pts[nd_lbl]
        node_lines = [item[0] for item in run_tpl if nd_lbl in item[1][0]]
        Node_Frm.NodeFrm(self, nd_lbl, cord, node_lines,
                         self.nodes, self.elevs,
                         self.pumps, self.tanks)

    def OnReDraw(self, evt):
        self.ReDraw()

    def ReDraw(self):
        '''Redraws the lines and loops listed removing any changes'''
        self.axes.clear()
        self.ax.grid()
        self.ax.set(xlabel='X Direction', ylabel='Y Direction',
                    title='General 2D Network layout')
        self.plt_lines = {}
        self.plt_txt = {}
        self.plt_Txt = {}
        self.plt_arow = {}

        self.plt_lpnum = {}
        self.plt_pump = {}
        self.plt_vlv = {}
        self.plt_vlv_lbl = {}
        self.plt_pseudo = {}
        self.plt_psarow = {}

        max = len(self.nodes)
        if max >= 1:
            count = 0
            prg_dlg = wx.ProgressDialog("Loading Data and Graphics",
                                        '',
                                        maximum = max,
                                        parent=self,
                                        style= 0 | wx.PD_APP_MODAL
                                        )

        # generate a list of all the node points excluding the origin
        redraw_pts = [*self.pts]
        redraw_pts.remove('origin')

        # draw the origin location on the chart
        txt = self.ax.annotate('origin', (0,0),
                                color=self.colours['purple'],
                                textcoords='offset points',
                                xytext=(3,3), ha='right',
                                picker=True)

        # redraw the lines and labels
        # step through the line list
        for key in self.runs:
            rnd = np.random.randint(len(self.clrs))
            color_name = self.clrs[rnd]
            # get the alpha designation for the line end points
            pt0, pt1 = self.runs[key][0]
            # get the coordinates for the end points
            x0, y0 = self.pts[pt0]
            x1, y1 = self.pts[pt1]
            # draw the specified line
            line = self.ax.plot([x0, x1], [y0, y1], marker='.',
                                markersize=10, color=self.colours[color_name])
            self.plt_lines[key] = line
            # determine the mid point of the line and
            # lable it with the key
            x_mid, y_mid = [(x0+x1)/2, (y0+y1)/2]
            Txt=self.ax.annotate(key,(x_mid, y_mid),
                                color=self.colours[color_name],
                                textcoords='offset points',
                                xytext=(3,3), ha='left',
                                picker=True)
            self.plt_Txt[key] = Txt
            # determine if the node point has already been labeled if so skip 
            if pt1 in redraw_pts:
                txt = self.ax.annotate(pt1, (x1, y1),
                                       color=self.colours[color_name],
                                       textcoords='offset points',
                                       xytext=(3,3), ha='left',
                                       picker=True)
                self.plt_txt[pt1] = txt
                redraw_pts.remove(pt1)

        # add arrow heads to the lines for each node
        for nd_lbl, lns in self.nodes.items():

            count += 1
            if count < max:
                prg_dlg.Update(count)
            elif count >= max:
                prg_dlg.Destroy()

            # lns is the list of line data at the intersection of node nd_lbl
            for ln in lns:
                # check if line has already plotted arrow head
                if ln[0] not in self.plt_arow:
                    # assume line start point is at node
                    endpt1 = nd_lbl
                    # if self.runs[ln_lbl] = (endpt1, endpt2) then if is satisfied 
                    if self.runs[ln[0]][0].index(endpt1) == 0:
                        endpt2 = self.runs[ln[0]][0][1]
                    # if self.runs[ln_lbl] = (endpt2, endpt1) then this follows
                    else:
                        endpt2 = self.runs[ln[0]][0][0]

                    # if flow is out of node reverse the arrow direction
                    if ln[1] == 1:
                        tmp = endpt2
                        endpt2 = endpt1
                        endpt1 = tmp

                    x0, y0 = self.pts[endpt1]
                    x1, y1 = self.pts[endpt2]

                    self.DrawArrow(x0, y0, x1, y1, ln[0])

        # draw the loop arcs and label
        for key in self.Loops:
            Cx, Cy, r = self.Loops[key][0]
            self.DrawLoop(Cx, Cy, r, key)

        # draw the pumps and tanks
        for key in self.pumps:
            self.DrawPump(key, True)
        for key in self.tanks:
            self.DrawPump(key, False)

        for ln_lbl in self.vlvs:
            self.DrawValve(ln_lbl, *self.vlv_pts(ln_lbl))

        for key in self.Pseudo:
            dat = self.Pseudo[key]
            self.DrawPseudo(key, dat[0])

        self.Ln_Select = []
        self.Loop_Select = False
        self.canvas.draw()
        self.canvas.Update()

    def OnDB_Save(self, evt):
        self.nodesDB()
        self.ptsDB()
        self.linesDB()
        self.loopsDB()
        self.pseudoDB()
        self.pumpDB()
        self.tankDB()
        self.valveDB()

    def nodesDB(self):
        # clear data from table
        Dsql = 'DELETE FROM nodes'
        DBase.Dbase(self).TblEdit(Dsql)
        # build the sql for multiple rows
        Insql = 'INSERT INTO nodes(node_ID, lines) VALUES(?,?);'
        # convert the list inside the dictionary to a string
        Indata = [(i[0], str(i[1])) for i in list(self.nodes.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

        # clear data from table
        Dsql = 'DELETE FROM elevs'
        DBase.Dbase(self).TblEdit(Dsql)
        # build the sql for multiple rows
        Insql = 'INSERT INTO elevs(nodeID, elev, units) VALUES(?,?,?);'
        # convert the list inside the dictionary to a string
        Indata = [(i[0], str(i[1][0]), str(i[1][1])) for i in list(self.elevs.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def pumpDB(self):
        # clear data from table
        Dsql = 'DELETE FROM Pump'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = ('''INSERT INTO Pump (pumpID, units, fluid_elev, flow1, flow2, flow3,
        tdh1, tdh2, tdh3) VALUES(?,?,?,?,?,?,?,?,?);''')
        Indata = []
        for k, v in self.pumps.items():
            ls = list(v)
            ls.insert(0, k)
            Indata.append(tuple(ls))
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def tankDB(self):
        # clear data from table
        Dsql = 'DELETE FROM Tank'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO Tank (tankID, fluid_elev, units) VALUES(?,?,?);'
        Indata = []
        for k, v in self.tanks.items():
            ls = list(v)
            ls.insert(0, k)
            Indata.append(tuple(ls))
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def valveDB(self):
        # clear data from table
        Dsql = 'DELETE FROM CVlv'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO CVlv (CVlv_ID, typ, units, locate, set_press, length) VALUES(?,?,?,?,?,?);'
        Indata = []
        for k, v in self.vlvs.items():
            ls = list(v)
            ls.insert(0, k)
            Indata.append(tuple(ls))
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def ptsDB(self):
        # clear data from table
        Dsql = 'DELETE FROM points'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO points (pointID, pts) VALUES(?,?);'
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1])) for i in list(self.pts.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def linesDB(self):
        # clear data from table
        Dsql = 'DELETE FROM lines'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO lines (lineID, ends, typ) VALUES(?,?,?);'
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1][0]), i[1][1])
                   for i in list(self.runs.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def loopsDB(self):
        # clear data from table
        Dsql = 'DELETE FROM loops'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = '''INSERT INTO loops (loop_num, Cx, Cy, Rad, lines)
         VALUES(?,?,?,?,?);'''
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], i[1][0][0], i[1][0][1], i[1][0][2], str(i[1][1]))
                   for i in list(self.Loops.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def pseudoDB(self):
        # clear data from table
        Dsql = 'DELETE FROM pseudo'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = '''INSERT INTO pseudo (loop_num, points, lines)
         VALUES(?,?,?);'''
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1][0]), str(i[1][1]))
                   for i in list(self.Pseudo.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def OnCalc(self, evt):
        Qs, D_e, density, kin_vis = Calc_Network.Calc(self, self.cursr, self.db).Evaluation()
        if Qs != {}:
            dlg = DataOut.DataOutPut(None, Qs)
            self.data_save = dlg.ShowModal()
            dlg.Destroy()
            if self.data_save:
                Final_Rpt.Report_Data(self, self.file_name, Qs, D_e, density, kin_vis).tbl_data()

                msg1 = "The report data has been saved as\n"
                msg2 = self.file_name[:-2] + 'pdf'
                msg3 = '\nand can be viewed using the view command in\n'
                msg4 = 'the File drop down menu.'
                msg = msg1 + msg2 + msg3 + msg4
                dialog = wx.MessageDialog(self, msg, 'Report Completed',
                                        wx.OK|wx.ICON_INFORMATION)
                dialog.ShowModal()
                dialog.Destroy()

    def OnView(self, evt):
        if self.file_name == '':
            PDFFrm(self)
        else:
            PDFFrm(self, self.file_name)

    def OnExit(self, evt):
        if self.cursr_set is True:
            self.cursr.close()
            self.db.close
        self.Destroy()


class OpenFile(wx.Dialog):
    def __init__(self, parent):
        super(OpenFile, self).__init__(parent,
                                       title="Open Data File",
                                       size=(600, 225),
                                       style=wx.DEFAULT_FRAME_STYLE &
                                             ~(wx.RESIZE_BORDER |
                                               wx.MAXIMIZE_BOX |
                                               wx.MINIMIZE_BOX))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent
        self.InitUI()
        self.filename = ''

    def InitUI(self):

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hdr1 = wx.StaticText(self,
                             label='Open an existing data file:',
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        self.file_name = wx.FilePickerCtrl(self,
                                           message='',
                                           style=wx.FLP_OPEN |
                                           wx.FLP_FILE_MUST_EXIST |
                                           wx.FLP_USE_TEXTCTRL,
                                           size=(400, 25))

        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.Selected, self.file_name)

        sizer1.Add(hdr1, 0, wx.TOP | wx.LEFT, 20)
        sizer1.Add(self.file_name, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hdr2 = wx.StaticText(self,
                             label='Start new file:',
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        yup = wx.Button(self, -1, "Specify\nNew File")
        self.Bind(wx.EVT_BUTTON, self.OnNew, yup)
        sizer2.Add(hdr2, 0, wx.LEFT | wx.TOP, 20)
        sizer2.Add(yup, 0, wx.LEFT, 20)

        self.cont = wx.Button(self, wx.ID_OK, "Continue")
        self.cont.Enable(False)

        self.sizer.Add(sizer1, 1)
        self.sizer.Add((10, 10))
        self.sizer.Add(sizer2, 1)
        self.sizer.Add(self.cont, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 10)
        self.SetSizer(self.sizer)

    def Selected(self, evt):
        self.filename = self.file_name.GetPath()
        if isinstance(self.filename, str):
            self.cont.Enable()
        self.parent.cursr_set = True
        evt.Skip()

    def OnNew(self, evt):
        currentDirectory = os.getcwd()
        dlg = wx.FileDialog(
            self, message="Save data file",
            defaultDir=currentDirectory,
            defaultFile=" ",
            wildcard="SQLite file (*.db)|*.db",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPaths()[0]
        if self.filename[-3:] != '.db':
            self.filename = self.filename + '.db'

        mt_dir = os.getcwd()
        mt_file = os.path.join(mt_dir, 'mt.db')

        if isinstance(self.filename, str):
            self.file_name.SetPath(self.filename)
            shutil.copy(mt_file, self.filename)
            self.cont.Enable()
        evt.Skip()

    def OnClose(self, evt):
        self.EndModal(True)
        self.parent.Destroy()


class PDFFrm(wx.Frame):
    def __init__(self, parent, filename=''):
        wx.Frame.__init__(self, parent)
        from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel
        self.Maximize(True)

        self.filename = filename
#        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrm)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.buttonpanel = pdfButtonPanel(self,  wx.ID_ANY,
                                          wx.DefaultPosition,
                                          wx.DefaultSize, 0)
        vsizer.Add(self.buttonpanel, 0,
                   wx.GROW | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.viewer = pdfViewer(self,  wx.ID_ANY, wx.DefaultPosition,
                                wx.DefaultSize, wx.HSCROLL |
                                wx.VSCROLL | wx.SUNKEN_BORDER)
        vsizer.Add(self.viewer, 1, wx.GROW | wx.LEFT | wx.RIGHT |
                   wx.BOTTOM, 5)
        loadbutton = wx.Button(self,  wx.ID_ANY, "Load PDF file",
                               wx.DefaultPosition, wx.DefaultSize, 0)
        loadbutton.SetForegroundColour((255, 0, 0))
        vsizer.Add(loadbutton, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        hsizer.Add(vsizer, 1, wx.GROW | wx.ALL, 5)
        self.SetSizer(hsizer)
        self.SetAutoLayout(True)

        # introduce buttonpanel and viewer to each other
        self.buttonpanel.viewer = self.viewer
        self.viewer.buttonpanel = self.buttonpanel

        self.Bind(wx.EVT_BUTTON, self.OnLoadButton, loadbutton)

        self.CenterOnParent()
        self.GetParent().Enable(False)
        self.Show(True)
        self.__eventLoop = wx.GUIEventLoop()
        self.__eventLoop.Run()
    
    def OnLoadButton(self, event):
        try:
            pdf_file = self.filename[:-2] + 'pdf'
            self.viewer.LoadFile(pdf_file)
        except FileNotFoundError:
            dlg = wx.FileDialog(self, wildcard="*.pdf")
            if dlg.ShowModal() == wx.ID_OK:
                wx.BeginBusyCursor()
                self.viewer.LoadFile(dlg.GetPath())
                wx.EndBusyCursor()
            dlg.Destroy()

    def OnCloseFrm(self, evt):
        self.GetParent().Enable(True)
        self.__eventLoop.Exit()
        self.Destroy()


# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frm = InputForm()
    app.MainLoop()
