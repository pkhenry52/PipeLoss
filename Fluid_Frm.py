import wx
import DBase

class FluidFrm(wx.Dialog):

    def __init__(self, parent):

        ttl = 'Fluid Information.'

        super().__init__(parent, title=ttl, size = (1100, 240))

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.parent = parent

        self.InitUI()

    def InitUI(self):

        # put the buttons in a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        # density units reguired lb/ft^3
        chcs_1 = ['lb/ft^3', 'g/cm^3', 'kg/m^3']
        # kinematic viscosity units reguired ft^2/s
        chcs_2 = ['ft^2/s', 'cm^2/s\n(stokes)', 'centistokes']
        # dynamic viscosity units required centipoise
        chcs_3 = ['lbm/ft-sec', 'g/cm-s\n(poise)', 'centipoise']
        
        grd = wx.FlexGridSizer(4,9,5,5)
        
        # horizontal titles
        hrz1 = wx.StaticText(self, label = ' ')
        hrz2 = wx.StaticText(self, label = '\nDensity')
        hrz3 = wx.StaticText(self, label = '\nUnits')
        hrz4 = wx.StaticText(self, label = 'Kenimatic\nViscosity')
        hrz5 = wx.StaticText(self, label = '<= OR =>\nUnits')
        hrz6 = wx.StaticText(self, label = 'Dynamic\nViscosity')
        hrz7 = wx.StaticText(self, label = '\nUnits')
        hrz8 = wx.StaticText(self, label = 'Concentration\n% by Wt')
        hrz9 = wx.StaticText(self, label = 'Concentration\n% by Vol')
        
        # horizontal input row 1
        vrt1 = wx.StaticText(self, label = 'Homogenous Liquid (1)')
        self.density_1 = wx.TextCtrl(self, value='')
        self.unit_11 = wx.Choice(self, choices = chcs_1)
        self.kin_vis_1 = wx.TextCtrl(self, value='')
        self.unit_12 = wx.Choice(self, choices = chcs_2)
        self.dyn_vis_1 = wx.TextCtrl(self, value='')
        self.unit_13 = wx.Choice(self, choices = chcs_3)
        self.wgt_1 = wx.TextCtrl(self, value='')
        self.vol_1 = wx.TextCtrl(self, value='')

        # horizontal input row 2
        vrt2 = wx.StaticText(self, label = 'Homogenous Liquid (2)')
        self.density_2 = wx.TextCtrl(self, value='')
        self.unit_21 = wx.Choice(self, choices = chcs_1)
        self.kin_vis_2 = wx.TextCtrl(self, value='')
        self.unit_22 = wx.Choice(self, choices = chcs_2)
        self.dyn_vis_2 = wx.TextCtrl(self, value='')
        self.unit_23 = wx.Choice(self, choices = chcs_3)
        self.wgt_2 = wx.TextCtrl(self, value='')
        self.vol_2 = wx.TextCtrl(self, value='')

        # horizontal input row 3
        vrt3 = wx.StaticText(self, label = 'Solids')
        self.density_3 = wx.TextCtrl(self, value='')
        self.unit_31 = wx.Choice(self, choices = chcs_1)
        blk2 = wx.StaticText(self, label = ' ')
        blk3 = wx.StaticText(self, label = ' ')
        blk4 = wx.StaticText(self, label = ' ')
        blk5 = wx.StaticText(self, label = ' ')
        self.wgt_3 = wx.TextCtrl(self, value='')
        blk6 = wx.StaticText(self, label = ' ')

        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_11)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_12)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_13)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_21)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_22)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_23)
        self.Bind(wx.EVT_CHOICE, self.OnUnit11,self.unit_31)

        grd.AddMany([(hrz1), (hrz2), (hrz3), (hrz4), (hrz5), (hrz6),
                     (hrz7), (hrz8), (hrz9),
                     (vrt1), (self.density_1), (self.unit_11),
                     (self.kin_vis_1), (self.unit_12), (self.dyn_vis_1),
                     (self.unit_13), (self.wgt_1), (self.vol_1),
                     (vrt2), (self.density_2), (self.unit_21),
                     (self.kin_vis_2), (self.unit_22), (self.dyn_vis_2),
                     (self.unit_23), (self.wgt_2), (self.vol_2),
                     (vrt3), (self.density_3), (self.unit_31), (blk2), (blk3),
                     (blk4), (blk5), (self.wgt_3), (blk6)
                    ])

        sizer.Add(grd, proportion = 2, flag = wx.ALL|wx.EXPAND, border = 15)
        self.SetSizer(sizer)

        # if data exists for the fluid page fill in the boxes
        qry = 'SELECT * FROM Fluid'
        frm_data = DBase.Dbase(self.parent).Dsqldata(qry)

        if frm_data != []:
            data = frm_data[0]
            if data != []:
                self.density_1.SetValue(str(data[1]))
                self.unit_11.SetSelection(data[13])
                self.kin_vis_1.SetValue(str(data[2]))
                self.unit_12.SetSelection(data[14])
                self.dyn_vis_1.SetValue(str(data[3]))
                self.unit_13.SetSelection(data[15])
                self.wgt_1.SetValue(str(data[4]))
                self.vol_1.SetValue(str(data[5]))

                self.density_2.SetValue(str(data[6]))
                self.unit_21.SetSelection(data[16])
                self.kin_vis_2.SetValue(str(data[7]))
                self.unit_22.SetSelection(data[17])
                self.dyn_vis_2.SetValue(str(data[8]))
                self.unit_23.SetSelection(data[18])
                self.wgt_2.SetValue(str(data[9]))
                self.vol_2.SetValue(str(data[10]))

                self.density_3.SetValue(str(data[11]))
                self.unit_31.SetSelection(data[19])
                self.wgt_3.SetValue(str(data[12]))

        self.Center()
        self.Show()

    def Save_Data(self):
        ValueList = ['1']
        ValueList.append(self.density_1.GetValue())
        ValueList.append(self.kin_vis_1.GetValue())
        ValueList.append(self.dyn_vis_1.GetValue())
        ValueList.append(self.wgt_1.GetValue())
        ValueList.append(self.vol_1.GetValue())

        ValueList.append(self.density_2.GetValue())
        ValueList.append(self.kin_vis_2.GetValue())
        ValueList.append(self.dyn_vis_2.GetValue())
        ValueList.append(self.wgt_2.GetValue())
        ValueList.append(self.vol_2.GetValue())

        ValueList.append(self.density_3.GetValue())
        ValueList.append(self.wgt_3.GetValue())

        ValueList.append(self.unit_11.GetSelection())
        ValueList.append(self.unit_12.GetSelection())
        ValueList.append(self.unit_13.GetSelection())
        ValueList.append(self.unit_21.GetSelection())
        ValueList.append(self.unit_22.GetSelection())
        ValueList.append(self.unit_23.GetSelection())
        ValueList.append(self.unit_31.GetSelection())

        col_names = [name[1] for name in DBase.Dbase(self.parent).Dcolinfo('Fluid')]

        SQL_Chk = 'SELECT ID FROM Fluid'
        
        if DBase.Dbase(self.parent).Dsqldata(SQL_Chk) == []:
            num_vals = ('?,'*len(col_names))[:-1]
            UpQuery = 'INSERT INTO Fluid VALUES (' + num_vals + ')'
        else:
            col_names.remove('ID')
            del ValueList[0]
            SQL_str = ','.join(["%s=?" % (name) for name in col_names])
            UpQuery = 'UPDATE Fluid SET ' + SQL_str + ' WHERE ID = 1'

        DBase.Dbase(self.parent).TblEdit(UpQuery, ValueList)

    def OnUnit11(self, evt): 
        pass
    #    evt.Skip()

    def OnClose(self, evt):
        self.Save_Data()
        self.Destroy()


