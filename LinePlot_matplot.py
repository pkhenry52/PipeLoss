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
from matplotlib.lines import Line2D
from matplotlib.text import Text
import matplotlib.colors as mcolors
import numpy as np
from math import sin
from scipy.interpolate import interp1d, make_interp_spline
import DBase
import Node_Frm
import Pipe_Frm
import Calc_Network
import Fluid_Frm

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

        self.lns = []
        self.lop = []
        self.ends = []
        self.loop_pts = []
        self.cursr_set = False

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

        # set dictionary of points; key node letter, value tuple of point,
        self.pts = {}
        # set dictionary of lines key line letter, value list of tuple start
        # point, end point and Boolean if first time end point is used
        self.runs = {}
	    # set dictionary of loops; key loop number, value list of centroid
        # point radius and list of all associated lines by key
        self.Loops = {}
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
        fileMenu.Append(101, '&New')
        fileMenu.Append(103, '&Save To Database')
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

        self.Bind(wx.EVT_MENU, self.OnExit, id=104)
        self.Bind(wx.EVT_MENU, self.OnDB_Save, id=103)

        self.Bind(wx.EVT_MENU, self.OnFluidData, id=301)

        self.Bind(wx.EVT_MENU, self.OnDeleteNode, id=201)
        self.Bind(wx.EVT_MENU, self.OnDeleteLine, id=202)
        self.Bind(wx.EVT_MENU, self.OnDeleteLoop, id=203)
        self.Bind(wx.EVT_MENU, self.OnDeletePump, id=204)

        # create the form level sizer
        Main_Sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the sizer for the left side widgets
        sizerL = wx.BoxSizer(wx.VERTICAL)
        # add the grid and then set it ot he left panel
        self.grd = LftGrd(self)
        # define the grid to be 3 columns and 26 rows
        self.grd.CreateGrid(26, 3)

        # set column widths
        for n in range(0, 3):
            self.grd.SetColSize(n, 80)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)

        # set the first column fonts and alignments
        attr = wx.grid.GridCellAttr()
        attr.SetTextColour(wx.BLACK)

        attr.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD))
        attr.SetAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grd.SetColAttr(0, attr)

        #freeze the grid size
        self.grd.EnableDragGridSize(False)

        # set the column headers and format
        self.grd.SetColLabelAlignment(wx.ALIGN_CENTER_HORIZONTAL,
                                      wx.ALIGN_CENTER_VERTICAL)
        self.grd.SetColLabelValue(0, "Start\nPoint")
        self.grd.SetColLabelValue(1, "End\nX")
        self.grd.SetColLabelValue(2, "End\nY")
        self.default_color = self.grd.GetLabelBackgroundColour()
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
        drw = wx.Button(self, id=0, label="Redraw\nLines")
        self.loop = wx.Button(self, -1, "Select\nLoop\nLines")
        self.pseudo = wx.Button(self, id=1, label="Select\nPseudo\nLines")
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

        sizerL.Add((10, 20))
        sizerL.Add(self.grd, 0, wx.EXPAND)
        sizerL.Add(btnsizer, 1, wx.ALIGN_CENTER)

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
        self.Show()

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
        # the ReDraw function will addd the lines to the plot as well as
        # repopulate the plt_Txt, plt_lines and plt_txt dictionaries
        self.ReDraw()
        self.GrdLoad()
        self.Refresh()
        self.Update()

    def DBpts(self):
        # download the points information and place into the pts dictionary
        no_data = True
        data_sql = 'SELECT * FROM points'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.pts = {i[0]:literal_eval(i[1]) for i in tbl_data}
            no_data = False
        return no_data

    def DBlines(self):
        # download the lines information from the database and put it into
        # the runs dictionary
        data_sql = 'SELECT * FROM lines'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.runs = {i[0]:[tuple(literal_eval(i[1])), i[2]] for i in tbl_data}        

    def DBnodes(self):
        # download the data entered in the node_frm and put it into
        # the nodes dictionary
        data_sql = 'SELECT * FROM nodes'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.nodes = {i[0]:literal_eval(i[1]) for i in tbl_data}

    def DBelevs(self):
        # download the data entered in the node_frm and put it into
        # the elevs dictionary
        data_sql = 'SELECT * FROM elevs'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.elevs = {i[0]:[i[1],i[2]] for i in tbl_data}       

    def DBpumps(self):
        # download the data entered in the node_frm and put it into
        # the elevs dictionary
        data_sql = 'SELECT * FROM Pump'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.pumps = {i[0]:list(i[1:]) for i in tbl_data}

    def DBvalves(self):
        # download the data entered in the node_frm and put it into
        # the elevs dictionary
        data_sql = 'SELECT * FROM CVlv'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.vlvs = {i[0]:list(i[1:]) for i in tbl_data}

    def DBtanks(self):
        # download the data entered in the node_frm and put it into
        # the tanks dictionary
        data_sql = 'SELECT * FROM Tank'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.tanks = {i[0]:list(i[1:]) for i in tbl_data}        

    def DBloops(self):
        # enter the data base information for the loops and put it into
        # the Loops dictionaary
        pol_dc = {}
        data_sql = 'SELECT * FROM loops'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            self.Loops = {i[0]:[[i[1], i[2], i[3]], literal_eval(i[4])]
                        for i in tbl_data} 
            for k,v in self.Loops.items():
                self.Ln_Select = v[1]
                self.AddLoop(k)
                pol_dc[k] = self.SetRotation(v[0][0], v[0][1], k)
        self.Ln_Select = []

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
            node_lines = set([item[0] for item in run_tpl if lbl in item[1][0]])
            # for every line indicated color the coresponding grid cell
            for ltr in node_lines:
                if lbl == self.grd.GetCellValue(ord(ltr)-65, 0):
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            0, 'lightgreen')
                else:
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            1, 'lightgreen')
                    self.grd.SetCellBackgroundColour(ord(ltr)-65,
                                                            2, 'lightgreen')

        data_sql = 'SELECT ID, saved FROM General'
        tbl_data = DBase.Dbase(self).Dsqldata(data_sql)
        if tbl_data != []:
            for ln,saved in tbl_data:
                if saved == 1:
                    row = ord(ln) - 65
                    self.grd.SetRowLabelRenderer(row, RowLblRndr('lightgreen'))

    def add_toolbar(self):
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.toolbar.update()

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
            txt = self.ax.text(0, 0, 'origin', picker=True,
                               color=self.colours['purple'])
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
            else:
                continue

        points.append(points1)
        points.append(points2)

        # confirm that point2 has two values in tuple and
        # that it has a label associated with it
        if len(points2) == 2:
            if nd_pt2 == '':
                # this will provide the next available node letter
                nds = [*self.pts]
                # if end points have been specified as (0, 0) then
                # reset node label to 'origin' and New Line status to False
                if points2 == [0, 0]:
                    New_EndPt = False
                    nd_pt2 = 'origin'
                elif LnLbl.lower() in nds:
                    for i in range(97, 123):
                        if chr(i) not in nds:
                            nd_pt2 = chr(i)
                            break
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
        Txt = self.ax.text(x_mid, y_mid, LnLbl, picker=True,
                           color=self.colours[color_name])
        self.plt_Txt[LnLbl] = Txt

        # label the end point of the line in lower case
        # and populate the dictionay with the control information
        if New_EndPt is True:
            txt = self.ax.text(x[1], y[1], LnLbl.lower(),
                               picker=True, color=self.colours[color_name])
            self.plt_txt[LnLbl.lower()] = txt

        self.canvas.draw()

    def DrawPump(self, nd_lbl, pump):
        Cx, Cy = self.pts[nd_lbl]
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        # determine length of x and y axis'
        x_lg = xmax-xmin
        y_lg = ymax - ymin

        # set a percentage of the graph sizes for the pump radius
        rx = .05 * x_lg
        ry = .05 * y_lg
        r = max(rx, ry)

        if pump:
            # draw the pump
            an = np.linspace(0, 2 * np.pi, 100)
            pump = self.ax.plot(rx * r * np.cos(an) + Cx, ry * r * np.sin(an) + Cy,
                            color='k', picker=True)
 
        # determine the orientation of the tank
        xcord = xmax - x_lg / 2
        ycord = ymax - y_lg / 2
        if Cx > xcord and Cy > ycord:
            if pump:
                lp_pump = self.ax.text(Cx + ry * 1.02, Cy, 'Pump',
                                       color='k', picker=True)
            x_rect = [Cx + i * rx for i in [.7,.7,1.5,1.5,.7]]
            x_pipe = [Cx, Cx + .7 * rx]
            y_rect = [Cy + i * ry for i in [1.2,2.2,2.2,1.2,1.2]]
            y_pipe = [Cy, Cy + 1.2 * ry]
            lp_tank = self.ax.text(Cx + rx * 1.5, Cy + (2.2 + 1.2)/2 * ry, 'Tank',
                                   color='k')
        elif Cx > xcord and Cy <= ycord:
            if pump:
                lp_pump = self.ax.text(Cx - ry * 4, Cy, 'Pump',
                                       color='k', picker=True)
            x_rect = [Cx + i * rx for i in [.7,.7,1.5,1.5,.7]]
            x_pipe = [Cx, Cx + .7 * rx]
            y_rect = [Cy + i * ry for i in [-1.2,0,0,-1.2,-1.2]]
            y_pipe = [Cy, Cy - 1.2 * ry]
            lp_tank = self.ax.text(Cx + rx * 1.5, Cy - 1.2/2 * ry, 'Tank',
                                   color='k')          
        elif Cx <= xcord and Cy <= ycord:
            if pump:
                lp_pump = self.ax.text(Cx + ry * 1.02, Cy, 'Pump',
                                       color='k', picker=True)
            x_rect = [Cx + i * rx for i in [-.7,-1.5,-1.5,-.7,-.7]]
            x_pipe = [Cx, Cx - .7 * rx]
            y_rect = [Cy + i * ry for i in [-1.2,-1.2,0,0,-1.2]]
            y_pipe = [Cy, Cy - 1.2 * ry]
            lp_tank = self.ax.text(Cx - rx * .7, Cy - (.7 + 1.2)/2 * ry, 'Tank',
                                   color='k')
        else:
            if pump:
                lp_pump = self.ax.text(Cx - ry * 4, Cy, 'Pump',
                                       color='k', picker=True)
            x_rect = [Cx + i * rx for i in [-.7,-1.5,-1.5,-.7,-.7]]
            x_pipe = [Cx, Cx - .7 * rx]
            y_rect = [Cy + i * ry for i in [1.2,1.2,2.2,2.2,1.2]]
            y_pipe = [Cy, Cy + 1.2 * ry]
            lp_tank = self.ax.text(Cx - rx * .7, Cy + (1.2 + 2.2)/2 * ry, 'Tank',
                                   color='k')
            
        # draw the tank and pipe
        tank = self.ax.plot(x_rect, y_rect, color='k')
        pipe = self.ax.plot(x_pipe, y_pipe, color='k', picker=True)
        # save the plot information
        if pump:
            self.plt_pump[nd_lbl] = [pump, tank, pipe, lp_pump, lp_tank]
        else:
            self.plt_pump[nd_lbl] = [tank, pipe, lp_tank]

        self.canvas.draw()

    def DrawArrow(self, endpt1, endpt2, LnLbl):
        # get the end point coordinates
        x0, y0 = self.pts[endpt1]
        x1, y1 = self.pts[endpt2]
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

    def DrawValve(self, ln_lbl, loc, lg, typ):
        # initialized sent from the Pipe_frm
        # get the end points for the line
        pt_A = self.runs[ln_lbl][0][0]
        pt_B = self.runs[ln_lbl][0][1]
        # determine the direction of flow so up and
        # down stream flow can be determined
        for ln in self.nodes[pt_A]:
            if ln[0] == ln_lbl:
                # if the flow is into the first point then reverse
                # the X0 and X1
                print('direction of flow', ln[1])
                if ln[1] == 1:
                    x_0 = self.pts[pt_A][0]
                    x_1 = self.pts[pt_B][0]
                    y_0 = self.pts[pt_A][1]
                    y_1 = self.pts[pt_B][1]
                elif ln[1] == 0:
                    x_0 = self.pts[pt_B][0]
                    x_1 = self.pts[pt_A][0]
                    y_0 = self.pts[pt_B][1]
                    y_1 = self.pts[pt_A][1]
                # calulate the length of the line
                d = ((x_1 - x_0)**2 + (y_1 - y_0)**2)**.5
                # determine the ratio of the distance the
                # valve is along the line
                if typ == 0:
                    t = float(loc) / float(lg)
                else:
                    t = (float(lg)-float(loc)) / float(lg)
                # calulate the point location for the valve
                x = ((1 - t) * x_0 + t * x_1)
                y = ((1 - t) * y_0 + t * y_1)
                # plot a red diamond at the valve location
                vlv = self.ax.plot(x, y, c='red', markersize=10, marker='d')
                self.plt_vlv[ln_lbl] = vlv

                self.canvas.draw()
                break

    def DrawPseudo(self):

        '''
        pts = [(0,0), (0.3,-0.15), (2.5,-1.2), (1.9,0.1)]
        pseudo_pts = sorted(pts, key = lambda k:[k[0], k[1]])
        X, Y = map(list, zip(*pseudo_pts))
        '''

        gap = 0.05
        ln_1 = [(0, 0), (0.2 ,-0.2)]
        # calculate the slope of the lines
        m1 = (ln_1[1][1] - ln_1[0][1]) / (ln_1[1][0] - ln_1[0][0])

        # slope of line perpendicular to main line is -1/m therefore
        # the perpendicular line equation is Y = (-1/m) * X + Bp
        # calculate the intercept points at each end of the main line
        # with the new parallel line and the perpendicular
        delta_y = ((gap**2) / (1+m1**2))**.5
        ln1_y1 = ln_1[1][1] - delta_y
        # since line 1 end point is on perpendicular line then solve for Bp
        Bp1 = ln_1[1][1] - (-1/m1) * ln_1[1][0]
        # substitute into perpendicular equation and find x1
        ln1_x1 = (ln1_y1 - Bp1) / (-1/m1)
        # do the same for the other end of the main line
        ln1_y2 = ln_1[0][1] - delta_y
        Bp2 = ln_1[0][1] - (-1/m1) * ln_1[0][0]
        ln1_x2 = (ln1_y2 -Bp2) / (-1/m1)
        psln1 = self.ax.plot([ln1_x1, ln1_x2],
                             [ln1_y1, ln1_y2],
                             'black', linestyle='--', marker='')

        # repeat the above for line 2
        ln_2 = [(2.0, 0.2), (0.2, -0.2)]
        m2 = (ln_2[1][1] - ln_2[0][1]) / (ln_2[1][0] - ln_2[0][0])
        delta_y = delta_y = ((gap**2) / (1+m2**2))**.5
        ln2_y1 = ln_2[1][1] - delta_y
        Bp1 = ln_2[1][1] - (-1/m2) * ln_2[1][0]
        ln2_x1 = (ln2_y1 - Bp1) / (-1/m2)
        ln2_y2 = ln_2[0][1] - delta_y
        Bp2 = ln_2[0][1] - (-1/m2) * ln_2[0][0]
        ln2_x2 = (ln2_y2 -Bp2) / (-1/m2)
        psln2 = self.ax.plot([ln2_x1, ln2_x2],
                             [ln2_y1, ln2_y2],
                             'black', linestyle='--', marker='')

        self.canvas.draw()

    def RemoveVlv(self, ln_lbl):
        if ln_lbl in self.plt_vlv:
            self.plt_vlv.pop(ln_lbl)[0].remove()
        self.canvas.draw()
        self.Refresh()
        self.Update()

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

            self.grd.SetCellBackgroundColour(row, 1,
            self.grd.GetDefaultCellBackgroundColour())
            self.grd.SetCellBackgroundColour(row, 2,
            self.grd.GetDefaultCellBackgroundColour())
            if row != 0:
                self.grd.SetCellValue(row, 0, '')
                self.grd.SetCellBackgroundColour(row, 0,
                self.grd.GetDefaultCellBackgroundColour())

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
                        self.plt_txt.pop(nd).remove()
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
                    if nd in self.elevs:
                        del self.elevs[nd]

            # retrieve all the values from the loops dictionary
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

            # retrieve the valve data
            if lbl in self.plt_vlv:
                self.RemoveVlv(lbl)

            # revert the line cell color back to default
            self.grd.SetRowLabelRenderer(row, RowLblRndr(
                self.default_color))
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
            old_alpha = self.runs[ln][0][1]
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
                           color='k', picker=True)
        self.crcl[num] = crc
        # add the arrow head to circle
        arow = self.ax.plot(Cx-r, Cy, '^', ls='-', ms=mrk,
                            color='k', picker=True)
        self.arrw[num] = arow
        # number the loop circle
        lp_num = self.ax.text(Cx, Cy, num, color='k', picker=True)
        self.plt_lpnum[num] = lp_num
        self.Loop_Select = False
        self.canvas.draw()

    def RemoveLoop(self, num):
        # reset the delete warning flag
        self.dlt_loop = False

        # remove the graphics from the form
        self.plt_lpnum.pop(num, None).remove()
        self.arrw.pop(num, None)[0].remove()
        self.crcl.pop(num, None)[0].remove()
        self.canvas.draw()
        # remove the items from the appropriate lists and dictionaries
        self.Loops.pop(num, None)
        self.poly_pts.pop(num, None)

    def RemovePump(self, lbl):
        # reset the warning flag
        self.dlt_pump = False

        # remove the graphics elements
        self.plt_pump[lbl][0][0].remove()
        self.plt_pump[lbl][1][0].remove()
        self.plt_pump[lbl][2][0].remove()
        self.plt_pump[lbl][3].remove()
        self.plt_pump[lbl][4].remove()
        del self.plt_pump[lbl]
        self.canvas.draw()
        # remove the pump from the dictionary
        self.pumps.pop(lbl, None)

    def RemoveTank(self, lbl):
        # reset the warning flag
        self.dlt_pump = False

        # remove the graphics elements
        self.plt_pump[lbl][0][0].remove()
        self.plt_pump[lbl][1][0].remove()
        self.plt_pump[lbl][2].remove()
        del self.plt_pump[lbl]
        self.canvas.draw()
        # remove the pump from the dictionary
        self.pumps.pop(lbl, None)

    def OnLeftSelect(self, event):
        if isinstance(event.artist, Text):
            text = event.artist
            lbl = text.get_text()
            # if line label is selected do one of three things;
            # pull up the line specification form,
            # add the line to a loop
            # or delete the line
            if lbl.isupper():
                if self.Loop_Select:
                    # take line lbl and go to Loop function
                    self.Loop(lbl)
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
            '''
            elif lbl == 'Tank':
                print('you have selected a tank', text, lbl)
            elif lbl == 'Pump':
                print('you have selected a pump', text, lbl)
            '''

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
            if self.loop.GetLabel() == 'Select\nLoop\nLines':
                self.loop.SetLabel('Cancel\nLoop\nSelection')
                self.Loop_Select = True
                self.Ln_Select = []
            else:
                self.loop.SetLabel('Select\nLoop\nLines')
                self.Loop_Select = False
                self.Ln_Select = []
        else:
            if self.pseudo.GetLabel() == 'Select\nPseudo\nLines':
                self.pseudo.SetLabel('Cancel\nLoop\nSelection')
                self.Loop_Select = True
                self.Ln_Select = []
                msg = "The first selected line must connect\n \
to a tank, pump or control valve"
                dialog = wx.MessageDialog(self, msg, 'Line Selection', wx.OK|wx.ICON_INFORMATION)
                dialog.ShowModal()
                dialog.Destroy()
            else:
                self.pseudo.SetLabel('Select\nPseudo\nLines')
                self.Loop_Select = False
                self.Ln_Select = []

    def Loop(self, lbl):
        ''' build the loops made up of selected lines
        when all the end points have been duplicated the loop is closed'''
	    # temporary list of the points in a loop
        LnPts = []
        equip = False

        rnd = np.random.randint(len(self.clrs))
        color_name = self.clrs[rnd]
        for pt in self.runs[lbl][0]:
            if equip is False:
                LnPts.append(self.pts[pt])

        if lbl in self.Ln_Select:
            # if line was previously selected, deselect it
            # remove line lbl from selected line list
            self.Ln_Select.remove(lbl)
            self.plt_lines[lbl][0].set_color(self.colours[color_name])
        else:  # a new line is selected
            self.Ln_Select.append(lbl)
            self.plt_lines[lbl][0].set_color('k')

        # if line end point is in list remove it, if it is not in list
        # then it was common to another line and needs to be replaced
        for pt in LnPts:
            if pt in self.loop_pts:
                self.loop_pts.remove(pt)
            else:
                self.loop_pts.append(pt)

        self.canvas.draw()

        if not self.loop_pts:
            # confirm all end points have been duplicated and loop closed
            self.loop.SetLabel('Select\nLoop\nLines')

            key_lst = list(self.Loops.keys())
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
            if equip is False:
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
            else:
                self.DrawPseudo()

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

        for n in range(0, len(poly)-1):
            btm = poly[n+1][0] - poly[n][0]
            top = poly[n+1][1] - poly[n][1]
            if btm != 0:
                m = top / btm
            else:
                m = 0
            yL = m * (Cx - poly[n][0]) + poly[n][1]
            if yL > Cy:
                if (m < 0 and btm > 0) or (m > 0 and btm > 0):
                    rot += 1
                else:
                    rot -= 1
            elif yL < Cy:
                if (m < 0 and btm < 0) or (m > 0 and btm < 0):
                    rot += 1
                else:
                    rot -= 1
            elif m == 0:
                if top == 0:  # vertical line
                    if ((poly[n][0] > Cx and top < 0) or
                        (poly[n][0] < Cx and top > 0)):
                        rot += 1
                    else:
                        rot -= 1
                else:  # horizintal line
                    if ((poly[n][1] > Cy and btm > 0) or
                        (poly[n][1] < Cy and btm < 0)):
                        rot += 1
                    else:
                        rot -= 1
        # if the rotation is counter clockwise reverse the
        # points and the line order
        if rot < 0:
            poly = list(reversed(poly))
            self.Ln_Select = list(reversed(self.Ln_Select))

        poly.pop(-1)
        self.poly_pts[loop_num] = poly

        return poly

    def Node(self, nd_lbl):
        # collect data needed to initialize the node_frm
        run_tpl = list(self.runs.items())
        cord = self.pts[nd_lbl]
        node_lines = [item[0] for item in run_tpl if nd_lbl in item[1][0]]
        Node_Frm.NodeFrm(self, nd_lbl, cord, node_lines, self.nodes, self.elevs, self.pumps, self.tanks)

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
        # generate a list of all the node points excluding the origin
        redraw_pts = [*self.pts]
        redraw_pts.remove('origin')

        # draw the origin location on the chart
        txt = self.ax.text(0, 0, 'origin', picker=True,
                           color=self.colours['purple'])

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
            Txt = self.ax.text(x_mid, y_mid, key,
                               picker=True, color=self.colours[color_name])
            self.plt_Txt[key] = Txt
            # determin if the node point has already been labeled if so skip 
            if pt1 in redraw_pts:
                txt = self.ax.text(x1, y1, pt1, picker=True,
                                   color=self.colours[color_name])
                self.plt_txt[pt1] = txt
                redraw_pts.remove(pt1)

        for nd_lbl, lns in self.nodes.items():
            for ln in lns:
                if ln[0] not in self.plt_arow:
                    endpt1 = nd_lbl
                    if self.runs[ln[0]][0].index(endpt1) == 0:
                        endpt2 = self.runs[ln[0]][0][1]
                    else:
                        endpt2 = self.runs[ln[0]][0][0]
                    if ln[1] == 1:
                        tmp = endpt2
                        endpt2 = endpt1
                        endpt1 = tmp
                    self.DrawArrow(endpt1, endpt2, ln[0])
                    self.canvas.draw()

        # draw the loop arcs and label
        for key in self.Loops:
            Cx, Cy, r = self.Loops[key][0]
            self.DrawLoop(Cx, Cy, r, key)

        # draw the pumps and tanks
        for key in self.pumps:
            self.DrawPump(key, True)

        for key in self.tanks:
            self.DrawPump(key, False)

        for key in self.vlvs:
            dat = self.vlvs[key]
            print(dat)
            self.DrawValve(key, dat[2], dat[4], dat[0])
        
        self.DrawPseudo()
        
        self.Ln_Select = []
        self.Loop_Select = False

        self.canvas.draw()

    def OnDB_Save(self, evt):
        self.nodesDB()
        self.ptsDB()
        self.linesDB()
        self.loopsDB()
        self.pumpDB()
        self.tankDB()

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
        Insql = 'INSERT INTO Pump (pumpID, units, elev, flow1, flow2, flow3, tdh1, tdh2, tdh3) VALUES(?,?,?,?,?,?,?,?,?);'
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
        Insql = 'INSERT INTO Tank (CVlv_ID, typ, units, locate, set_press, length) VALUES(?,?,?,?,?,?);'
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
        Insql = 'INSERT INTO lines (lineID, ends, new_pt) VALUES(?,?,?);'
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

    def OnExit(self, evt):
        Calc_Network.Calc(self,self.cursr, self.db).Evaluation()
        if self.cursr_set is True:
            cursr.close()
            db.close
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
                             label='Open new data file:',
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
            shutil.copy(mt_file, self.filename)
            self.cont.Enable()
        evt.Skip()

    def OnClose(self, evt):
        self.EndModal(True)
        self.parent.Destroy()


# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frm = InputForm()
    app.MainLoop()
