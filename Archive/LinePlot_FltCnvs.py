import os
import sqlite3
import random
import string
import wx
import wx.grid as gridlib
from copy import deepcopy
from wx.lib.floatcanvas import NavCanvas, FloatCanvas
import wx.lib.colourdb
from math import sin, log10, radians
import time

# this initializes the database and the cursor
def connect_db(filename):
    global cursr, db
    db = sqlite3.connect(filename)
    with db:
        cursr = db.cursor()
        cursr.execute('PRAGMA foreign_keys=ON')

def ScnFil(obj, colm1, colm2, colm3, num_row): #, rd_btns1=[], rd_btns2=[]):
    ''' this function loads all the information into the flex grid.
    The num_rows indicates how many rows will be used on the
    two columns of flex grids. In fact there is only on flex grid split
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

    return lst


class InputForm(wx.Frame):
    '''set up the form and draw axis'''
    def __init__(self):

        super(InputForm, self).__init__(None, wx.ID_ANY, title='Plot Lines', size=(1300, 830))

        # set a list of colors use dark values on light canvas
        self.colors = ['DARKSLATEGREY', 'NAVYBLUE', 'DARKTURQUOISE', 'CYAN',
                       'ORANGE', 'GOLDENROD', 'DARKOLIVEGREEN', 'OLIVEDRAB',
                       'DARKKHAKI', 'INDIANRED', 'DARKORANGE', 'VIOLETRED',
                       'PURPLE', 'DARKMAGENTA', 'DARKRED']

        # set the variables for placement of text box
        self.algn_V = ['t', 'c', 'b']
        self.algn_H = ['r', 'l', 'c']
        self.lns = []
        self.lop = []
        self.ends = []
        self.loop_pts = []
        self.cursr_set = False

        # set dictionary of points; key node letter, value tuple of point,
        self.pts = {}
        # set dictionary of lines key line letter, value list of tuple start point,
        # end point and Boolean if first time end point is used
        self.runs = {}
	    # set dictionary of loops; key loop number, value list of centroid point
        # radius and list of all associated lines by key
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
        
        mb = wx.MenuBar()

        fileMenu = wx.Menu() 
        fileMenu.Append(101, '&New')
        fileMenu.Append(102, '&Open')
        fileMenu.Append(103, '&Save')
        fileMenu.AppendSeparator()
        fileMenu.Append(104, '&Exit')

        mb.Append(fileMenu, 'File')
        self.SetMenuBar(mb)

        self.Bind(wx.EVT_MENU, self.OnExit, id=104)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=102)

        # create the form level sizer
        Main_Sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the sizer for the left side widgets
        sizerL = wx.BoxSizer(wx.VERTICAL)
        # add the grid and then set it ot he left panel
        self.grd = gridlib.Grid(self)
        # define the grid to be 3 columns and 26 rows
        self.grd.CreateGrid(26, 3)

        # set column widths
        for n in range(0, 3):
            self.grd.SetColSize(n, 80)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)

        # set the first column fonts and alignments
        attr = wx.grid.GridCellAttr()
        attr.SetTextColour(wx.BLACK)

        attr.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        attr.SetAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grd.SetColAttr(0, attr)

        #freeze the grid size
        self.grd.EnableDragGridSize(False)

        # set the column headers and format
        self.grd.SetColLabelAlignment(wx.ALIGN_CENTER_HORIZONTAL, wx.ALIGN_CENTER_VERTICAL)
        self.grd.SetColLabelValue(0, "Start\nPoint")
        self.grd.SetColLabelValue(1, "End\nX")
        self.grd.SetColLabelValue(2, "End\nY")

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

        # add the draw panel
        rght = NavCanvas.NavCanvas(self,
                                   ProjectionFun=None,
                                   Debug=0,
                                   BackgroundColor="LIGHT GREY",
                                   )
        self.Canvas = rght.Canvas

        self.InitCanvas()

        Main_Sizer.Add(sizerL, 0, wx.EXPAND)
        Main_Sizer.Add((10, 10))
        Main_Sizer.Add(rght, 1, wx.EXPAND)
        self.SetSizer(Main_Sizer)

    def InitCanvas(self):
        # add the x & y axis
        self.Canvas.AddLine([(0, 0), (0, 5)], LineWidth=2, LineColor='Yellow')
        self.Canvas.AddLine([(0, 0), (5, 0)], LineWidth=2, LineColor='Green')
        origin = self.Canvas.AddScaledTextBox('origin', (0, 0),
                                              Color='blue',
                                              Size=.5,
                                              PadSize=0,
                                              Width=None,
                                              LineColor=None,
                                              Family=wx.MODERN,
                                              Position='tr',
                                              Alignment='bottom',
                                              InForeground=True)
        
        origin.Bind(FloatCanvas.EVT_FC_LEFT_DOWN,
                    lambda evt, selctEnd='Origin':
                    self.OnLeftDown(evt, 'Origin'))

        wx.CallAfter(self.Canvas.ZoomToBB)

    def OnCellChange(self, evt):
        # get the row number the changes where made to
        row = evt.GetRow()
        try:
            self.DrawLine(*self.VarifyData(row))
            evt.Skip()
        except:
            evt.Skip()

    def VarifyData(self, row):
        points2 = []
        points1 = []
        points = []
        alpha_pts = []
        nd_pt1 = ''
        nd_pt2 = ''
        New_EndPt = True
        LnLbl = self.grd.GetRowLabelValue(row)

        # get the x,y values in column 1 & 2
        # designate them as points2
        for i in range(0, 3):
            pt = self.grd.GetCellValue(row, i)
            print(pt, row, i)
            # if a letter is entered in X or Y use its
            # end points for the start of the new line
            if pt != '':
                if pt.isdigit() is False:
                    # first step is to capitalize aplha characters
                    pt = pt.title()
                    self.grd.SetCellValue(row, i, pt.lower())
                    # if it is column 0 and origin is specified then
                    # start point is (0,0)
                    if i == 0:   # first column always start point1
                        if pt == 'Origin':
                            nd_pt1 = 'Origin'
                            self.pts[pt] = (0, 0)
                            # if 1st column has "Origin" as value
                            # then start point is (0,0)
                            points1 = (0, 0)
                        else:
                            # specify the end point for the entered alpha
                            new_row = ord(pt) - 65
                            for j in range(1, 3):
                                new_pt = self.grd.GetCellValue(new_row, j)
                                if new_pt == '':
                                    self.WarnData()
                                    self.grd.SetCellValue(row, 0, '')
                                    return
                                else:
                                    points1.append(int(new_pt))
                                    nd_pt1 = pt.lower()

                    else:  # these columns indicate the end point2
                        # if "Origin" is in 2nd or 3rd column then
                        # the end point is the origin
                        if pt == 'Origin':
                            points2 = (0, 0)
                            New_EndPt = False
                        else:
                            # use specified alpha character to determine end point
                            # first go to the corresponding row
                            New_EndPt = False
                            nd_pt2 = pt.lower()
                            new_row = ord(pt) - 65
                            for j in range(1, 3):
                                pt = self.grd.GetCellValue(new_row, j)
                                if pt == '':
                                    self.WarnData()
                                    self.grd.SetCellValue(row, j, '')
                                    # return
                                else:
                                    points2.append(int(pt))
                else:
                # this cell contains a letter which means
                # it can only be the end point as numeric
                # values are not allowed in the start column
                    New_EndPt = True
                    nd_pt2 = LnLbl.lower()
                    points2.append(int(pt))
            else:
                continue

        points.append(tuple(points1))
        points.append(tuple(points2))

        # get the row label for the line end point
        if len(points2) == 2 and nd_pt2 != '':
            if nd_pt2 not in self.pts:
                if points2 == [0, 0]:
                    nd_pt2 = 'Origin'
                    New_EndPt = False
                else:
                    self.pts[nd_pt2] = tuple(points2)

            alpha_pts.append((nd_pt1, nd_pt2))
            self.runs[LnLbl] = [alpha_pts, New_EndPt]
            print(points)
            return points, LnLbl, New_EndPt

    def DrawLine(self, points, LnLbl, New_EndPt):
        '''Draws the line object as specified in the VarifyData() function'''

        randposyV = random.randint(0, len(self.algn_V)-1)
        randposyH = random.randint(0, len(self.algn_H)-1)
        randposy = self.algn_V[randposyV] + self.algn_H[randposyH]

        randclr = random.randint(0, len(self.colors)-1)

        # label the end point of the line in lower case
        if New_EndPt is True:
            self.new_end = self.Canvas.AddScaledTextBox(LnLbl.lower(), tuple(points[1]),
                                                   Color='black',
                                                   Size=.5,
                                                   PadSize=.2,
                                                   Width=None,
                                                   LineColor=None,
                                                   Family=wx.MODERN,
                                                   Position=randposy,
                                                   Alignment='bottom',
                                                   InForeground=True)

            self.new_end.Bind(FloatCanvas.EVT_FC_LEFT_DOWN,
                         lambda evt, selctEnd=LnLbl.lower():
                         self.OnLeftDown(evt, selctEnd))

        # define the new line
        self.Canvas.AddLine(points, LineWidth=2, LineColor=self.colors[randclr])
        # add the new line to the list of lines

        self.Canvas.AddPoint(tuple(points[1]), 'black', 8)

        # locate the center of the new line for the label location
        lncntr = ((int(points[0][0])+int(points[1][0]))//2,
                  (int(points[0][1])+int(points[1][1]))//2)

        # place the new line lable
        new_line = self.Canvas.AddScaledTextBox(LnLbl, lncntr,
                                                Color=self.colors[randclr],
                                                Size=.5,
                                                PadSize=None,
                                                Width=None,
                                                LineColor=None,
                                                Family=wx.MODERN,
                                                Position=randposy,
                                                Alignment='bottom',
                                                InForeground=True)
        new_line.Name = LnLbl
        '''
        tic = time.perf_counter()
        new_line.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.ObjLeftDown)
        toc = time.perf_counter()
        print(f'time to execute BIND function for DrawLine line 399 = {toc-tic:0.2f}')
        '''
        wx.CallAfter(self.Canvas.ZoomToBB)

    def DrawLoop(self, Cx, Cy, r, num):

        self.Canvas.AddArc((Cx+r, Cy), (Cx, Cy-r), (Cx, Cy),
                           LineColor='black', LineWidth=2)
        self.Canvas.AddArrow((Cx+r, Cy), Length =10, Direction=180,
                             LineColor='black', LineWidth=2,
                             ArrowHeadSize=8, ArrowHeadAngle=30)

        new_loop = self.Canvas.AddScaledTextBox(str(num+1), (Cx, Cy),
                                                Color='black',
                                                Size=.5,
                                                PadSize=.2,
                                                Width=None,
                                                LineColor=None,
                                                Family=wx.MODERN,
                                                Position='cc',
                                                Alignment='center',
                                                InForeground=True)

        new_loop.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, lambda evt,
                      selctLp=str(num+1): self.OnLeftDown(evt, selctLp))

    def WarnData(self):
        dialog = wx.MessageDialog(self,
                                  "A node has been specified which is not defined.",
                                  'Node Error',
                                  wx.OK|wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def ObjLeftDown(self, object):
        '''States which object has been clicked on
        Additional code to follow'''
        lbl = object.Name

        try:
            int(lbl)
        except:
            if lbl == 'Origin':
                self.Node(lbl)

            elif 65 <= ord(lbl) <= 90:
                if self.Loop_Select:
                    # take line lbl and go to Loop function
                    self.Loop(lbl)
                else:
                    PipeFrm(self, 'Pipe & Fittings for ' + lbl)
            elif 97 <= ord(lbl) <= 122:
                self.Node(lbl)

    def OnLeftDown(self, evt, lbl):
        '''States which object has been clicked on
        Additional code to follow'''
        try:
            int(lbl)
        except:
            if lbl == 'Origin':
                self.Node(lbl)
            elif 65 <= ord(lbl) <= 90:
                if self.Loop_Select:
                    # take line lbl and go to Loop function
                     self.Loop(lbl)
                else:
                    PipeFrm(self, 'Pipe & Fittings for ' + lbl)
            elif 97 <= ord(lbl) <= 122:
                self.Node(lbl)

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

        for alpha_pt in self.runs[lbl][0]:
            for pt in alpha_pt:
                LnPts.append(self.pts[pt])

        if lbl in self.Ln_Select:
            # if line was previously selected, deselect it
            # remove line lbl from selected line list
            self.Ln_Select.remove(lbl)
            randclr = random.randint(0, len(self.colors)-1)
            self.Canvas.AddLine(LnPts, LineWidth=2,
                                LineColor=self.colors[randclr])
            # if line end point is in list remove it, if it is not in list
            # then it was common to another line and needs to be replaced
            for pt in LnPts:
                if pt in self.loop_pts:
                    self.loop_pts.remove(pt)
                else:
                    self.loop_pts.append(pt)
        else:  # a new line is selected
            self.Ln_Select.append(lbl)
            self.Canvas.AddLine(LnPts, LineWidth=2, LineColor='black')
            # add end points to loops list if they are not present
            # if it is common to another line then remove end point
            for pt in LnPts:
                if pt in self.loop_pts:
                    self.loop_pts.remove(pt)
                else:
                    self.loop_pts.append(pt)

        if not self.loop_pts:
            # confirm all end points have been duplicated and loop closed
            self.loop.SetLabel('Select\nLoop\nLines')
            self.Canvas.AddLine(LnPts, LineWidth=2, LineColor='black')

            loop_num = len(self.Loops) + 1

            # determine the centroid of the polygon and the distance to the
            # shortest to any ine line from the centroid
            # call it the radius for the circular arc
            Cx, Cy, r = self.centroid(self.AddLoop(loop_num))
          
            # Reassign the polygons points to the dictionary poly_pts
            # moving in a clockwise direction around the
            self.poly_pts[loop_num] = self.SetRotation(Cx, Cy, loop_num)

            self.Loops[loop_num] = [[Cx, Cy, r], self.Ln_Select]
            print('Dictionary of poly_pts clockwise = ', self.poly_pts)
            print('Dictionary of Loops lines in clockwise order', self.Loops)
            self.ReDraw()

        wx.CallAfter(self.Canvas.ZoomToBB)

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
        Ln_pts = list(self.runs[tmp_ln[0]][0][0])
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
                tmp_cord = list(self.runs[ln][0][0])
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
                for pt in alpha_pt:
                    poly_cord.append(self.pts[pt])

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
            # reduce radius to fit into polygon
            r = r * .5

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
        new_value = []
        new_key = []
        for key in self.runs:
            new_value.append(key)
            new_key.append(self.runs[key][0][0])

        new_dict = dict(zip(new_key, new_value))

        node_lines = [new_dict[key] for key in new_dict if lbl in key]
        Node_Frm(self, -1, lbl, node_lines, self.nodes)

    def OnReDraw(self, evt):
        self.ReDraw()

    def ReDraw(self):
        '''Redraws the lines and loops listed removing any changes'''
        self.Canvas.ClearAll()
        self.InitCanvas()

        # draw the lines and labels
        for key in self.runs:
            points = []
            New_EndPt = self.runs[key][1]
            for alpha_pt in self.runs[key][0]:
                for pt in alpha_pt:
                    points.append(self.pts[pt])

            self.DrawLine(points, key, New_EndPt)

        # draw the loop arcs and label
        for key in self.Loops:
            Cx, Cy, r = self.Loops[key][0]
            self.DrawLoop(Cx, Cy, r, key-1)

        self.Ln_Select = []
        self.Loop_Select = False

    def OnLoops(self, evt):
        pass

    def OnDelete(self, evt):
        '''field = Dbase().Dcolinfo(self.tblname)[1][1]
        val = "specify data field to delete"'''
        try:
            Dbase().TblDelete(self.tblname, val, field)
        except sqlite3.IntegrityError:
            wx.MessageBox('''This Record is associated with\nother tables
                           and cannot be deleted!''', "Cannot Delete",
                          wx.OK | wx.ICON_INFORMATION)

        # alternate delete method
        DeQuery = ("DELETE FROM " + self.PrtyTbl +
                    " WHERE Commodity_Property_ID = " +
                    str(self.ComdPrtyID) + " AND " +
                    self.tblID + " = " +
                    str(self.data[row][self.ID_col]))
        self.cursr.execute(query)
        self.db.commit()

    def OnUpdate(self, evt):
        # update data structure
        values[1] = 'REQUIRED'
        values[2] = new_value[1]
        values[3] = new_value[2]

        # if adding then do the following
        ValueList = []
        if type(values) == str:
            ValueList.append(values)
        else:
            ValueList = values

        UpQuery = ('INSERT INTO ' + self.tblname + ' VALUES (' +
                    "'" + "','".join(map(str, ValueList)) + "'" + ')')
        Dbase(self.tblname).TblEdit(UpQuery)

        # if updating data then do the following
        CurrentID = self.data[self.rec_num][0]
        realnames.remove('FastenerID')
        del ValueList[0]

        SQL_str = ','.join(["%s=?" % (name) for name in realnames])
        UpQuery = ('UPDATE ' + self.tblname + ' SET ' + SQL_str +
                    ' WHERE FastenerID = ' + str(CurrentID))
        Dbase().TblEdit(UpQuery, ValueList)

    def OnOpenFile(self, evt):
        currentDirectory = os.getcwd()
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=currentDirectory,
            defaultFile="",
            wildcard="SQLite file (*.db)|*.db",
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPaths()[0]
        print(currentDirectory, dlg.GetPaths(), self.path)
        dlg.Destroy()
        connect_db(self.path)
        self.cursr_set = True

    def OnExit(self, evt):
        if self.cursr_set is True:
            cursr.close()
            db.close
        self.Destroy()


class Node_Frm(wx.Frame):
    def __init__(self, parent, id, node, node_lst, node_dict):

        self.parent = parent
        self.rad_bt = []
        self.chk_bx = []
        self.txt_bxs = []
        self.nodes = node_dict
        self.node = node

        super(Node_Frm, self).__init__(parent,
                          title='Node "' + node + '" Flows',
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER |
                                                           wx.MAXIMIZE_BOX |
                                                           wx.MINIMIZE_BOX))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

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

        n = 7
        id_num = 0
        rbsizers = []

        for ln in node_lst:

            pos_rb = wx.RadioButton(self, id_num, label=('\t\tline "' + ln + '"'),
                                    pos=(20, 10*n),
                                    style=wx.RB_GROUP)
            neg_rb = wx.RadioButton(self, id_num+1, label='', pos=(180, 10*n))

            self.rad_bt.append(pos_rb)
            self.rad_bt.append(neg_rb)

            flow_chk = wx.CheckBox(self, id_num+2, label='', pos=(280, 10*n))
            self.chk_bx.append(flow_chk)

            txt_bx = wx.TextCtrl(self, id_num+3, value='',
                                 pos=(320, 10*n),
                                 size=(-1, 30))
            txt_bx.Enable(False)
            self.txt_bxs.append(txt_bx)

            rb_sizer = wx.BoxSizer(wx.HORIZONTAL)

            rb_sizer.Add(pos_rb, 0, wx.LEFT, 20)
            rb_sizer.Add(neg_rb, 0, wx.LEFT, 40)
            rb_sizer.Add(flow_chk, 0, wx.LEFT, 80)
            rb_sizer.Add(txt_bx, 0, wx.LEFT | wx.RIGHT, 20)

            rbsizers.append(rb_sizer)
            n += 5
            id_num += 4

        self.Bind(wx.EVT_CHECKBOX, self.OnChkBox)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadiogroup)

        for rbsizer in rbsizers:
            self.sizer.Add(rbsizer, 0)

        btn_lbls = ['Intersection of Multiple\nLines As List Above', 'Back Pressure Valve',
                    'Pressure Regulating Valve',
                    'Centrifugal Pump', 'Reservoir Supply']

        self.type_rbb = wx.RadioBox(self, 
                                    label=
                                    'The node point is one of the following;',
                                    style=wx.RA_SPECIFY_COLS,
                                    choices=btn_lbls,
                                    majorDimension=1)
        self.sizer.Add(self.type_rbb, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 30)

        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)

        # add these following lines since this is a call up form
        self.CenterOnParent()
        self.GetParent().Enable(False)
        self.Show(True)
        self.__eventLoop = wx.GUIEventLoop()
        self.__eventLoop.Run()

    def OnRadiogroup(self, evt): 
        rb = evt.GetEventObject()

    def OnChkBox(self, evt):
        ckBx = evt.GetEventObject()
        n = ckBx.GetId()
        i = int((n-2)/4)
        if ckBx.GetValue():
            self.txt_bxs[i].Enable()
        else:
            self.txt_bxs[i].ChangeValue('')
            self.txt_bxs[i].Enable(False)

    def PreClose(self):
        lst1 = []
        lst2 = []
        n = 1
        flow = 1
        for item in range(1, len(self.rad_bt), 2):
            dirct = 1
            flow = 1
            lst1.append(self.rad_bt[item-1].GetLabel()[-2])
            if self.chk_bx[item-n].GetValue() is True:
                flow = eval(self.txt_bxs[item-n].GetValue())
            if self.rad_bt[item].GetValue() == False:
                dirct = -1

            lst2.append(dirct*flow)
            n+=1

        ln_dirct = list((zip(lst1, lst2)))

        self.nodes[self.node] = ln_dirct
        print('Information from nodes form ', self.nodes)

    def OnClose(self, evt):
        self.PreClose()

        # add 2 lines for child parent form
        self.GetParent().Enable(True)
        self.__eventLoop.Exit()
        self.Destroy()


class Line_Frm(wx.Frame):
    def __init__(self, parent, id, line, line_data):

        self.parent = parent
        self.line_data = line_data

        super(Line_Frm, self).__init__(parent,
                          title='Pipe "' + line + '" Data',
                          size=(430, 400),
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER |
                                                           wx.MAXIMIZE_BOX |
                                                           wx.MINIMIZE_BOX))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

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
        hdrsizer.Add(hdr2, 1, wx.ALIGN_LEFT|wx.LEFT, 60)
        hdrsizer.Add(hdr3, 1, wx.ALIGN_LEFT|wx.LEFT, 40)
        hdrsizer.Add(hdr4, 1, wx.ALIGN_LEFT|wx.LEFT, 40)

        self.sizer.Add(hdrsizer, 1, wx.BOTTOM, 120)

        self.SetSizer(self.sizer)

        # add these following lines since this is a call up form
        self.CenterOnParent()
        self.GetParent().Enable(False)
        self.Show(True)
        self.__eventLoop = wx.GUIEventLoop()
        self.__eventLoop.Run()

    def PreClose(self):
        lst1 = []
        lst2 = []
        n = 1
        flow = 1
        for item in range(1, len(self.rad_bt), 2):
            dirct = 1
            lst1.append(self.rad_bt[item-1].GetLabel()[-2])
            if self.chk_bx[item-n].GetValue() is True:
                flow = eval(self.txt_bxs[item-n].GetValue())
            if self.rad_bt[item].GetValue() == False:
                dirct = -1

            lst2.append(dirct*flow)
            n+=1

        ln_dirct = list((zip(lst1, lst2)))

        self.nodes[self.node] = ln_dirct

    def OnClose(self, evt):
        self.PreClose()

        # add 2 lines for child parent form
        self.GetParent().Enable(True)
        self.__eventLoop.Exit()
        self.Destroy()


class PipeFrm(wx.Frame):

    def __init__(self, parent, title):
        super(PipeFrm, self).__init__(parent, title=title, size=(800, 930))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent

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
        self.K_calc(old, current_page)

    def K_calc(self, old, current_page):

        dia = 4
        e = .00197

        ff = (1.14 - 2 * log10(e / (dia/12)))**-2

        if current_page.Name == 'ManVlv1':
            K1 = [3, 340, 30, 55, 21, 150, 36, 55, 100, (45, 35, 25)]
            Kt1 = 0
            # set the value in the text box and check if it is
            # empty if so set it to zero
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                if bx_val == '':
                    bx_val = 0

                if bx == 9:
                    if dia <= 8:
                        Kt1 = int(bx_val) * K1[bx][0] * ff + Kt1
                    elif dia >= 10 and dia <= 14:
                        Kt1 = int(bx_val) * K1[bx][1] * ff + Kt1
                    elif dia >= 16 and dia <= 24:
                        Kt1 = int(bx_val) * K1[bx][2] * ff + Kt1
                else:
                    Kt1 = Kt1 +\
                        int(bx_val) * K1[bx] * ff
            print(Kt1)
        elif current_page.Name == 'ManVlv2':
            K2 = [8, 109, 43, 125, 214, 205, 1142, 1000, 300]
            Kt2 = 0
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                if bx_val == '':
                    bx_val = 0
                Kt2 = Kt2 + int(bx_val) * K2[bx] * ff
            print(Kt2)
        elif current_page.Name == 'ChkVlv':
            K3 = [600, 100, 55, 200, (80, 60, 40), 300, 100, 350, 50, 55, 55]
            Kt3 = 0
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                if bx_val == '':
                    bx_val = 0
                if bx == 4:
                    if dia <= 8:
                        Kt3 = int(bx_val) * K3[bx][0] * ff + Kt3
                    elif dia >= 10 and dia <= 14:
                        Kt3 = int(bx_val) * K3[bx][1] * ff + Kt3
                    elif dia >= 16 and dia <= 48:
                        Kt3 = int(bx_val) * K3[bx][2] * ff + Kt3
                else:
                    Kt3 = Kt3 +\
                        int(bx_val) * K3[bx] * ff
            print(Kt3)
        elif current_page.Name == 'Fittings':
            K4 = [30, 2, 16, 2, 50, 20, 13, 60, 72]
            Kt4 = 0
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                if bx_val == '':
                    bx_val = 0
                Kt4 = Kt4 + int(bx_val) * K4[bx] * ff
            print(Kt4)
        elif current_page.Name == 'WldElb':
            K5 = [20, 16, 10, 8, (24, 24, 30, 60), (12, 15)]
            Kt5 = 0
            for bx in range(len(self.nb.GetPage(old).pg_txt)):
                bx_val = self.nb.GetPage(old).pg_txt[bx].GetValue()
                if bx_val == '':
                    bx_val = 0
                if bx == 4:
                    for m in range(len(self.nb.GetPage(old).rdbtn1)):
                        Kt5 = K5[bx][m] *\
                            int(self.nb.GetPage(old).rdbtn1[m].GetValue()) *\
                            ff * int(bx_val) + Kt5
                elif bx == 5:
                    for m in range(len(self.nb.GetPage(old).rdbtn2)):
                        Kt5 = K5[bx][m] *\
                            int(self.nb.GetPage(old).rdbtn2[m].GetValue()) *\
                            ff * int(bx_val) + Kt5
                else:
                    Kt5 = Kt5 + int(bx_val) * K5[bx] * ff
            print(Kt5)
        elif current_page.Name == 'EntExt':
            K6 = [.78, 1, .5, .28, .24, .15, .09, .04]
            Kt6 = 0

            for bx in range(len(self.nb.GetPage(old).pg_chk)):
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
                    Kt6 = .8 * sin(radians(txt2/2)) * (1-(txt0/dia)**2) / \
                        (txt0/dia)**4 + Kt6
                elif txt2 <= 180 and txt2 > 45:
                    Kt6 = .5 * (1-(txt0/dia)**2) * \
                        (sin(radians(txt2/2)))**.5 / (txt0/dia)**4 + Kt6

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
                    Kt6 = 2.6 * sin(radians(txt3/2)) * (1-(dia/txt1)**2) / \
                        (dia/txt1)**4 + Kt6
                elif txt3 <= 180 and txt3 > 45:
                    Kt6 = (1-(dia/txt1)**2)**2 / (dia/txt1)**4 + Kt6
            print(Kt6, '\n\n')

    def OnClose(self, evt):
        # before closing make sure last page data is read
        # by triggering OnPageChanged
        pg = self.nb.GetSelection()

        if pg == 5:
            self.nb.SetSelection(0)
        else:
            self.nb.SetSelection(pg+1)

        self.Destroy()


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
        # flags to indicate if a check box (1), an blank space (0)
        # or a radiobutton (2) is to be used for input
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

    def PrptyDelete(self, query):
        self.cursr.execute(query)
        self.db.commit()

        # determine the required column width, name and primary status
    def Fld_Size_Type(self):
        # specified field type or size
        values = []
        auto_incr = True
        ColWdth = []
        n = 0

        # collect all the table information needed to build the grid
        # colinfo includes schema for each column: column number, name,
        # field type & length, is null , default value, is primary key
        for item in self.Dcolinfo(self.frmtbl):
            col_wdth = ''
            # check to see if field length is specified if so
            # use it to set grid col width
            for s in re.findall(r'\d+', item[2]):
                if s.isdigit():
                    col_wdth = int(s)
                    ColWdth.append(col_wdth)
            # check if it is a text string and primary key if it is then
            # it is not auto incremented develope a string of data based
            # on record field type for adding new row
            if item[5] == 1:
                pk = item[1]
                pk_col = n
                # if the primary key is not an interger then assign a text
                # value and indicate it is not auto incremented
                if 'INTEGER' not in item[2]:
                    values.append('Required')
                    auto_incr = False
                # it must be an integer and will be auto incremeted,
                # New_ID is assigned in AddRow routine
                else:
                    values.append('New_ID')
                    if col_wdth == '':
                        ColWdth.append(6)
            # remaining steps assing values to not
            # null fields otherwise leave empty
            elif 'INTEGER' in item[2] or 'FLOAT' in item[2]:
                if item[3]:
                    values.append(0)
                else:
                    values.append('')
                if col_wdth == '' and 'FLOAT' in item[2]:
                    ColWdth.append(10)
                elif col_wdth == '':
                    ColWdth.append(6)
            elif 'BLOB' in item[2]:
                if item[3]:
                    values.append('Required')
                else:
                    values.append('')
                if col_wdth == '':
                    ColWdth.append(30)
            elif 'TEXT' in item[2] or 'BOOLEAN' in item[2]:
                if item[3]:
                    values.append('Required')
                else:
                    values.append('')
                if col_wdth == '':
                    ColWdth.append(10)
            elif 'DATE' in item[2]:
                i = datetime.datetime.now()
                today = ("%s-%s-%s" % (i.month, i.day, i.year))
                if item[3]:
                    values.append(today)
                if col_wdth == '':
                    ColWdth.append(10)
            n += 1

        # the variables in FldInfo are;database column name for ID,
        # database number of ID column, if ID is autoincremented
        # (imples interger or stg), list of database specified column
        # width, a list of database column names,
        # a list of values to insert into none null fields
        FldInfo = [pk, pk_col, auto_incr, ColWdth, values]
        return FldInfo

    def ColNames(self):
        colnames = []
        for item in self.Dcolinfo(self.frmtbl):
            # modify the column names to remove
            # underscore and seperate words
            colname = item[1]
            if colname.find("ID", -2) != -1:
                colname = "ID"
            elif colname.find("_") != -1:
                colname = colname.replace("_", " ")
            else:
                colname = (' '.join(re.findall('([A-Z][a-z]*)', colname)))
            colnames.append(colname)
        return colnames

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
    frame = InputForm()
    # frame = StrUpFrm(None)
    frame.Center()
    frame.Show()
    app.MainLoop()
