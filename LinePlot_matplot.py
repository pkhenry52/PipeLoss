
import os
import shutil
from ast import literal_eval
import sqlite3
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
from math import sin, log10, radians

# this initializes the database and the cursor
def connect_db(filename='mt.db'):
    global cursr, db
    db = sqlite3.connect(filename)
    with db:
        cursr = db.cursor()
        cursr.execute('PRAGMA foreign_keys=ON')

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


class InputForm(wx.Frame):
    '''The main entery form which contains the grid and the
    plot area for the piping configuration'''
    def __init__(self):

        super(InputForm, self).__init__(None, wx.ID_ANY, title='Plot Lines',
                                        size=(1300, 830))

        # set up a list of dark colors suitable for the graph
        self.clrs = ['rosybrown', 'indianred', 'brown', 'darkred', 'red',
                     'salmon', 'tomato', 'darksalmon', 'orangered', 'navy',
                     'olive', 'chocolate', 'saddlebrown', 'darkolivegreen',
                     'darkorange', 'burlywood', 'orange', 'goldenrod',
                     'darkseagreen', 'darkgreen', 'green', 'lawngreen',
                     'darkslategray', 'darkslategrey', 'teal', 'darkcyan',
                     'darkturquoise', 'darkkhaki', 'mediumorchid', 'purple',
                     'deepskyblue', 'skyblue', 'darkslateblue', 'darkblue',
                     'steelblue', 'dodgerblue', 'slategray', 'midnightblue',
                     'mediumslateblue', 'mediumpurple', 'rebeccapurple',
                     'blueviolet', 'darkorchid', 'darkviolet', 'royalblue'
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

        # flags to indicate if warning message is to show
        self.show_line = False
        self.show_node = False
        self.show_loop = False

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

        # list of lines selected to form a loop
        self.Ln_Select = []
        # list of points in a specified direction defining the polygon loop
        self.Loop_Select = False
        # list of points redrawn
        self.redraw_pts = []

        mb = wx.MenuBar()

        fileMenu = wx.Menu()
        fileMenu.Append(101, '&New')
        fileMenu.Append(103, '&Save Grid Data')
        fileMenu.AppendSeparator()
        fileMenu.Append(104, '&Exit')

        deleteMenu = wx.Menu()
        deleteMenu.Append(201, '&Node')
        deleteMenu.Append(202, '&Line')
        deleteMenu.Append(203, 'L&oop')

        mb.Append(fileMenu, 'File')
        mb.Append(deleteMenu, '&Delete Element')
        self.SetMenuBar(mb)

        self.Bind(wx.EVT_MENU, self.OnExit, id=104)
        self.Bind(wx.EVT_MENU, self.OnDB_Save, id=103)

        self.Bind(wx.EVT_MENU, self.OnDeleteNode, id=201)
        self.Bind(wx.EVT_MENU, self.OnDeleteLine, id=202)
        self.Bind(wx.EVT_MENU, self.OnDeleteLoop, id=203)

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
        drw = wx.Button(self, -1, "Redraw\nLines")
        self.loop = wx.Button(self, -1, "Select\nLoop\nLines")
        xit = wx.Button(self, -1, "Exit")
        btnsizer.Add(drw, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        btnsizer.Add(self.loop, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnReDraw, drw)
        self.Bind(wx.EVT_BUTTON, self.OnLoop, self.loop)
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
        file_name = dlg.filename
        '''
        if file_name.split(os.path.sep)[-1] != 'mt.db' and \
            file_name.split(os.path.sep)[-1] != "":
            self.DataLoad()'''
        self.DataLoad()

    def DataLoad(self):
        # run through all the functions to retreive the data from the database
        self.DBpts()
        self.DBnodes()
        self.DBlines()
        self.DBloops()
        # the ReDraw function will addd the lines to the plot as well as
        # repopulate the plt_Txt, plt_lines and plt_txt dictionaries
        self.ReDraw()
        self.GrdLoad()

    def DBpts(self):
        # download the points information and place into the pts dictionary
        data_sql = 'SELECT * FROM points'
        tbl_data = Dbase().Dsqldata(data_sql)
        self.pts = {i[0]:literal_eval(i[1]) for i in tbl_data}

    def DBlines(self):
        # download the lines information from the database and put it into
        # the runs dictionary
        data_sql = 'SELECT * FROM lines'
        tbl_data = Dbase().Dsqldata(data_sql)
        self.runs = {i[0]:[tuple(literal_eval(i[1])), i[2]] for i in tbl_data}        

    def DBnodes(self):
        # download the data entered in the node_frm and put it into
        # the nodes dictionary
        data_sql = 'SELECT * FROM nodes'
        tbl_data = Dbase().Dsqldata(data_sql)
        self.nodes = {i[0]:literal_eval(i[1]) for i in tbl_data}

    def DBloops(self):
        # enter the data base information for the loops and put it into
        # the Loops dictionaary
        pol_dc = {}
        data_sql = 'SELECT * FROM loops'
        tbl_data = Dbase().Dsqldata(data_sql)
        self.Loops = {i[0]:[[i[1], i[2], i[3]], literal_eval(i[4])]
                       for i in tbl_data} 
        for k,v in self.Loops.items():
            self.Ln_Select = v[1]
            self.AddLoop(k)
            pol_dc[k] = self.SetRotation(v[0][0], v[0][1], k)

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
                nd = [int(x_val), int(y_val)]
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
                    points2.append(int(pt))
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
        rnd = np.random.randint(len(self.clrs))
        color_name = self.clrs[rnd]

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

    def RemoveLine(self, set_lns):
        # reset the delete warning flag
        self.dlt_line = False
        for  lbl in set_lns:
            # remove the lines and its label from the graphic
            if lbl in self.plt_lines.keys():
                self.plt_lines.pop(lbl)[0].remove()
            if lbl in self.plt_Txt.keys():
                self.plt_Txt.pop(lbl).remove()
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
                        if len(self.nodes[nd][0]) == 1:
                            del self.nodes[nd]
                        else:
                            n = 0
                            for v in self.nodes[nd][0]:
                                if lbl == v[0]:
                                    self.nodes[nd][0].pop(n)
                                n += 1

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
        # remove the items from the appropriet lists and dictionaries
        self.Loops.pop(num, None)
        self.poly_pts.pop(num, None)

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
                    PipeFrm(self, lbl)
            # if node label is selected do one of two things;
            # pull up the node specification form,
            # or delete the line
            elif lbl.islower():
                if self.dlt_node:
                    self.RemoveNode(lbl)
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

    def OnDeleteLine(self, evt):
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveLine
        if self.show_line is False:
            dlg = DeleteWarning(None, 'line')
            self.dlt_line = dlg.ShowModal()
            self.show_line = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_line = True

    def OnDeleteNode(self, evt):
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveNode
        if self.show_node is False:
            dlg = DeleteWarning(None, 'node')
            self.dlt_node = dlg.ShowModal()
            self.show_node = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_node = True

    def OnDeleteLoop(self, evt):
        # this only calls up the warning dialog the actual deletion
        # is handled in teh OnLeftSelect function call and RemoveLoop
        if self.show_loop is False:
            dlg = DeleteWarning(None, 'loop')
            self.dlt_loop = dlg.ShowModal()
            self.show_loop = dlg.show_me
            dlg.Destroy()
        else:
            self.dlt_loop = True

    def OnLoop(self, evt):
        '''this set trigger as to what response is needed if a line is selected
        either open input screen or build loop'''
        if self.loop.GetLabel() == 'Select\nLoop\nLines':
            self.loop.SetLabel('Cancel\nLoop\nSelection')
            self.Loop_Select = True
            self.Ln_Select = []
        else:
            self.loop.SetLabel('Select\nLoop\nLines')
            self.Loop_Select = False
            self.Ln_Select = []

    def Loop(self, lbl):
        ''' build the loops made up of selected lines
        when all the end points have been duplicated the loop is closed'''
	    # temporary list of the points in a loop
        LnPts = []

        rnd = np.random.randint(len(self.clrs))
        color_name = self.clrs[rnd]
        for pt in self.runs[lbl][0]:
            LnPts.append(self.pts[pt])

        if lbl in self.Ln_Select:
            # if line was previously selected, deselect it
            # remove line lbl from selected line list
            self.Ln_Select.remove(lbl)
            self.plt_lines[lbl][0].set_color(self.colours[color_name])
            # if line end point is in list remove it, if it is not in list
            # then it was common to another line and needs to be replaced
            for pt in LnPts:
                if pt in self.loop_pts:
                    self.loop_pts.remove(pt)
                else:
                    self.loop_pts.append(pt)
        else:  # a new line is selected
            self.Ln_Select.append(lbl)
            self.plt_lines[lbl][0].set_color('k')
            # add end points to loops list if they are not present
            # if it is common to another line then remove end point
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
        poly = self.poly_pts[loop_num]

        # make a copy of the polygon points and add the start point to
        # the end of the list
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

    def Node(self, lbl):
        # collect data needed to initialize the node_frm
        run_tpl = list(self.runs.items())
        cord = self.pts[lbl]
        node_lines = [item[0] for item in run_tpl if lbl in item[1][0]]
        Node_Frm(self, lbl, cord, node_lines, self.nodes)

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

        # draw the loop arcs and label
        for key in self.Loops:
            Cx, Cy, r = self.Loops[key][0]
            self.DrawLoop(Cx, Cy, r, key)

        self.Ln_Select = []
        self.Loop_Select = False

        self.canvas.draw()

    def OnDB_Save(self, evt):
        self.nodesDB()
        self.ptsDB()
        self.linesDB()
        self.loopsDB()

    def nodesDB(self):
        # clear data from table
        Dsql = 'DELETE FROM nodes'
        Dbase().TblEdit(Dsql)
        # build the sql for multiple rows
        Insql = 'INSERT INTO nodes(node_ID, lines) VALUES(?,?);'
        # convert the list inside the dictionary to a string
        Indata = [(i[0], str(i[1])) for i in list(self.nodes.items())]
        Dbase().Daddrows(Insql, Indata)

    def ptsDB(self):
        # clear data from table
        Dsql = 'DELETE FROM points'
        Dbase().TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO points (pointID, pts) VALUES(?,?);'
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1])) for i in list(self.pts.items())]
        Dbase().Daddrows(Insql, Indata)

    def linesDB(self):
        # clear data from table
        Dsql = 'DELETE FROM lines'
        Dbase().TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO lines (lineID, ends, new_pt) VALUES(?,?,?);'
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1][0]), i[1][1])
                   for i in list(self.runs.items())]
        Dbase().Daddrows(Insql, Indata)

    def loopsDB(self):
        # clear data from table
        Dsql = 'DELETE FROM loops'
        Dbase().TblEdit(Dsql)
        # build sql to add rows to table
        Insql = '''INSERT INTO loops (loop_num, Cx, Cy, Rad, lines)
         VALUES(?,?,?,?,?);'''
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], i[1][0][0], i[1][0][1], i[1][0][2], str(i[1][1]))
                   for i in list(self.Loops.items())]
        Dbase().Daddrows(Insql, Indata)

    def OnExit(self, evt):
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
        connect_db(self.filename)
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
        
        dlg.Destroy()
        connect_db(self.filename)

        self.cont.Enable()

        evt.Skip()

    def OnClose(self, evt):
        self.EndModal(True)
        self.parent.Destroy()


class DeleteWarning(wx.Dialog):
    def __init__(self, parent, elem): 
        super(DeleteWarning, self).__init__(
                                            parent,
                                            title="Confirm Deletion",
                                            size=(480, 225),
                                            style=wx.DEFAULT_FRAME_STYLE &
                                                  ~(wx.RESIZE_BORDER |
                                                  wx.MAXIMIZE_BOX |
                                                  wx.MINIMIZE_BOX))
        self.elem = elem
        self.parent = parent
        self.InitUI()
        self.show_me = False

    def InitUI(self):
        # put the buttons in a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        if self.elem == 'line':
            msg = 'Deleting a line will result in the\ndeletion of' \
                    'all related loops.\n' \
                    'Select the corresponding\nline letter to proceed.'
        elif self.elem == 'node':
            msg = 'Deleting a node will result in the\ndeletion of ' \
                    'all intersecting lines and\ntheir related loops.' \
                    '\n\nSelect the corresponding node letter to delete.'
        elif self.elem == 'loop':
            msg = 'Deleting a loop will result in the\ndeletion of ' \
                    'all data related to the loop.\n' \
                    'Select the corresponding loop\nnumber to proceed.'

        hdrsizer = wx.BoxSizer(wx.HORIZONTAL)

        hdr1 = wx.StaticText(self,
                             label=msg,
                             style=wx.ALIGN_CENTER_HORIZONTAL)

        hdrsizer.Add(hdr1, 1, wx.LEFT, 20)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wrng_shw = wx.CheckBox(self,
                               label='Do not show this warning again.')

        ok = wx.Button(self, -1, "Ok")
        xit = wx.Button(self, -1, "Cancel")
        btnsizer.Add(self.wrng_shw, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 15)
        btnsizer.Add(ok, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        btnsizer.Add(xit, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, xit)

        self.sizer.Add(hdrsizer, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        self.sizer.Add((20, 10))
        self.sizer.Add(btnsizer, 1)
        self.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

    def OnOk(self, evt):
        self.EndModal(True)
        self.show_me = self.wrng_shw.GetValue()

    def OnCancel(self, evt):
        self.EndModal(False)
        self.show_me = self.wrng_shw.GetValue()


class Node_Frm(wx.Frame):
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

        super(Node_Frm, self).__init__(parent, title=ttl,
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


class PipeFrm(wx.Frame):

    def __init__(self, parent, lbl):

        self.lbl = lbl
        ttl = 'Pipe & Fittings for ' + self.lbl

        super(PipeFrm, self).__init__(parent, title=ttl, size=(850, 930))

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
        data = Dbase().Dsqldata(qry)[0]
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
        data = Dbase().Dsqldata(qry)
        if data != []:
            data = list(data[0])       
            del data[0]
            col_names = [name[1] for name in Dbase().Dcolinfo(
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
                Dbase().TblEdit(UpQuery, ValueList)
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
            Dbase().TblEdit(UpQuery, ValueList)

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
            Dbase().TblEdit(UpQuery, ValueList)

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
            Dbase().TblEdit(UpQuery, ValueList)

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
            Dbase().TblEdit(UpQuery, ValueList)

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
            Dbase().TblEdit(UpQuery, ValueList)

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
            Dbase().TblEdit(UpQuery, ValueList)

    def BldQuery(self, old_pg, new_data):
        col_names = [name[1] for name in Dbase().Dcolinfo(old_pg)]

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
        
        if Dbase().Dsqldata(SQL_Chk) == []:
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


class Dbase(object):
    '''DATABASE CLASS HANDLER'''
    # this initializes the database and opens the specified table
    def __init__(self, frmtbl=None):
        # this sets the path to the database and needs
        # to be changed accordingly
        self.cursr = cursr
        self.db = db
        self.frmtbl = frmtbl

    def Dcolinfo(self, table):
        # sequence for items in colinfo is column number, column name,
        # data type(size), not null, default value, primary key
        self.cursr.execute("PRAGMA table_info(" + table + ");")
        colinfo = self.cursr.fetchall()
        return colinfo

    def Dtbldata(self, table):
        # this will provide the foreign keys and their related tables
        # unknown,unknown,Frgn Tbl,Parent Tbl Link fld,
        # Frgn Tbl Link fld,action,action,default
        self.cursr.execute('PRAGMA foreign_key_list(' + table + ')')
        tbldata = list(self.cursr.fetchall())
        return tbldata

    def Dsqldata(self, DataQuery):
        # provides the actual data from the table based on the provided query
        self.cursr.execute(DataQuery)
        sqldata = self.cursr.fetchall()
        return sqldata

    def Daddrows(self, InQuery, Rcrds):
        self.cursr.executemany(InQuery, Rcrds)
        self.db.commit()

    def TblDelete(self, table, val, field):
        '''Call the function to delete the values in
        the database table.  Error trapping will occure
        in the call def delete_data'''

        if type(val) != str:
            DeQuery = ("DELETE FROM " + table + " WHERE "
                       + field + " = " + str(val))
        else:
            DeQuery = ("DELETE FROM " + table + " WHERE "
                       + field + " = '" + val + "'")
        self.cursr.execute(DeQuery)
        self.db.commit()

    def TblEdit(self, UpQuery, data_strg=None):
        if data_strg is None:
            self.cursr.execute(UpQuery)
        else:
            self.cursr.execute(UpQuery, data_strg)
        self.db.commit()

    def Search(self, ShQuery):
        self.cursr.execute(ShQuery)
        data = self.cursr.fetchall()
        if data == []:
            return False
        else:
            return data

    def Restore(self, RsQuery):
        self.cursr.execute(RsQuery)
        data = self.cursr.fetchall()
        # self.cursr.close()
        return data

    # close out the database
    def close_database(self):
        self.cursr.close()
        del self.cursr
        self.db.close()


# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frm = InputForm()
    # frame = StrUpFrm(None)
    app.MainLoop()
