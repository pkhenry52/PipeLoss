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
#from scipy.interpolate import make_interp_spline, BSpline
from scipy.interpolate import interp1d

class InputForm(wx.Frame):
    '''The main entery form which contains the grid and the
    plot area for the piping configuration'''
    def __init__(self):

        super().__init__(None, wx.ID_ANY,
                         title='Plot Lines',
                         size=(1300, 840))

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ax = self.canvas.figure.axes[0]
        self.ax.grid()
        self.ax.set(xlabel='X Direction', ylabel='Y Direction',
                    title='General 2D Network layout')

        # plot for horizontal z values
        x = np.array([0, 0.2, 2, 4.0, 4.6])
        y = np.array([0, -0.2, 0.2, -0.1, 0])
        model = interp1d(x, y, kind ='cubic')
        xs = np.linspace(x.min(),x.max(), 50)
        ys=model(xs)
        line = self.ax.plot(xs, ys)

        # for x running in vertical direction
        # switch x and y data then switch xs and ys in plot
        # this is actuall y x data points
        y = np.array([0, 0.2, 0.2, 0])
        # this is actually y data points
        x = np.array([0, -0.2, -1.2, -1.4])
        
        model = interp1d(x, y, kind ='cubic')
        xs = np.linspace(x.min(),x.max(), 50)
        ys=model(xs)
        # now switch everyting back by reversing xs and ys in plot
        line = self.ax.plot(ys, xs)

        self.canvas.draw()

        self.Center()
        self.Show()

# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frm = InputForm()
    app.MainLoop()