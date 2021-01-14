import numpy as np
import sqlite3
import DBase
from math import cos, pi, log10

# need to determine the correct number of loops to include in matrix
class Calc(object):
        
    def __init__(self, parent, cursr, db):
        self.parent = parent
        self.var_lst = set()
        self.coef_lst = set()
        self.cursr = cursr
        self.db = db

    def Node_Matrix(self):

        # these are to be the arrays used in numpy
        # used to solve the linear equations
        var_arry = []
        coef_arry = []
        # percentage variation in range of flow estimates
        # to calculate Q1 and Q2
        DeltaQ_Percent = .1
        gravity = 32.2  # ft/s^2
        Chw = 140
        for val in self.parent.nodes.values():
            # generate val=[('B', 0, 0), ('C', 0, 20.0), ('D', 1, 0)]
            # for each node in self.nodes
            for k, v1, v2 in val:
                if v2 == 0:
                    self.var_lst.add(k)
        # create a dictionary of lines used to define nodes and 
        # index them for matrix position
        # {'A': 0, 'B': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'I': 6, 'J': 7}
        self.var_dic = dict((v,k) for k,v in enumerate(sorted(self.var_lst)))
        
        # generate the matrix for each node
        for val in self.parent.nodes.values():
            if len(val) > 1:
                nd_matx = [0]*len(self.var_dic)
                coeff = 0
                for k, v1, v2 in val:
                    if v2 == 0:
                        nd_matx[self.var_dic[k]] = cos(pi*v1)*-1
                    else:
                        # specify the value for the coef array coresponding
                        # to the matrix in the variable array
                        # [20.0, 0, 0, 0]
                        coeff = v2 *cos(pi*v1)
                # collect the array of node coeficients
                # ie the value of any comsumption at the node
                coef_arry.append(coeff)
                # add the node matrix to the main variable array
                # [[0, -1.0, 1.0, 0, 0, 0, 0, 0],
                # [0, 0, -1.0, -1.0, 1.0, 0, -1.0, 0],
                # [0, 0, 0, 0, -1.0, -1.0, 0, 1.0],
                # [-1.0, 1.0, 0, 1.0, 0, 1.0, 0, 0]]
                var_arry.append(nd_matx)

        # the final array for the nodes removing the last node
        del var_arry[-1]
        del coef_arry[-1]

        # get all the Kt values from the various
        # tables and sum them for each line
        datatbls = ['General', 'ManVlv1', 'ManVlv2', 'ChkVlv',
                    'Fittings', 'WldElb', 'EntExt']
        n = 0
        dct = dict()
        for tbl in datatbls:
            qry = 'SELECT ID, Kt' + str(n) + ' FROM ' + tbl
            tbldata = DBase.Dbase(self).Dsqldata(qry)
            for ln, Kt in tbldata:
                dct.setdefault(ln, []).append(Kt)
            n += 1
        for ln in dct:
            dct[ln] = sum(dct[ln])

        # get the dimensional information for each line and
        # order data based on line label into a dictionary
        qry = 'SELECT ID, info1, info2, info3 FROM General'
        tbldata = DBase.Dbase(self).Dsqldata(qry)
        # tbldata = line lbl, dia", lgth', e"
        D_e={} # dimensional data
               # {line label:[dia", e", AR, ARL, Line_Length+Le]}
        for itm in tbldata:

            f = (1.14 - 2 * log10(itm[3]/itm[1]))**-2
            Le = dct[itm[0]] * (itm[1]/12) / f
            Lgth = Le + itm[2]
            K = (8.53E5 * Lgth) / (Chw**1.852 * itm[1]**4.87)
            AR = pi * (itm[1] / 12)**2 / 4  # ft^2 
            ARL = Lgth / (gravity * 2 * (itm[1] / 12) * AR**2)
            D_e[itm[0]] = [itm[1], itm[3], AR, ARL, Lgth]
            dct[itm[0]] = K
        # generates a dictionary of the sum Kt values for each line
        Kt_dict = dict(sorted(dct.items(),key=lambda item: item[0]))

        # reverse the points dictionary with the cordinates as the key
        # and the node label as the value
        inv_pts = {tuple(v):k for k,v in self.parent.pts.items()}
        # change the poly_pts dictionary cordinates
        # to the coresponding node label
        for num in self.parent.poly_pts:
            k_matx = [0]*len(self.var_dic)
            alpha_poly_pts = []
            for v in self.parent.poly_pts[num]:
                alpha_poly_pts.append(inv_pts[tuple(v)])

            # check the first line in the loop line list to see if the
            # first two points listed in the poly_pts corespond to it
            # if they do NOT then the line order needs to be changed
            if alpha_poly_pts[0] == 'origin':
                rst1 = ord(alpha_poly_pts[1])
            elif alpha_poly_pts[1] == 'origin':
                rst1 = ord(alpha_poly_pts[0])
            else:
                rst1 = ord(alpha_poly_pts[0]) + ord(alpha_poly_pts[1])
            # loop starting line is loop#[1][0]
            lns = self.parent.Loops[num][1]
            rst2 = sum(ord(i) for i in self.parent.runs[lns[0]][0] if i != 'origin')
            if rst1 != rst2:
                lns.append(lns.pop(0))

            # loop lines  ['E', 'F', 'D', 'C'] loop number 1
            for n, ln in enumerate(lns):
                nd1 = alpha_poly_pts[n]
                for val in self.parent.nodes[nd1]:
                    if ln in val:
                        k_matx[self.var_dic[ln]] = cos(pi*val[1]) *-1
            # run through the matrix of all the lines mapped
            # in the plot as specified as part of a node inorder to specify the
            # index location for the Kt vaiable in the loop equations
            # and combine the sign of the direction arrow with the
            # calculated Kt for the line
            for k,v in self.var_dic.items():
                if k in Kt_dict.keys():
                    if Kt_dict[k] != 0:
                        k_matx[v] = Kt_dict[k] * k_matx[v]
                    else:
                        k_matx[v] = 0.0
            var_arry.append(k_matx)
            coef_arry.append(0)

        Ar = np.array(var_arry)
        Cof = np.array(coef_arry)

        # Ar = np.array([[1.,1.,0.,0.,0.,0.,0.], [-1.,0.,0.,1.,0.,0.,0.],
        #  [0.,0.,0.,0.,-1.,0.,-1.], [ 0.,0.,1.,-1.,0.,-1.,0.],
        # [0.,0.,0.,0.,0.,1.,1.], [ 0.,-1.,-1.,0.,1.,0.,0.],
        # [-0.69903207,0.07807178,0.,-8.3197367,0.,0.,0.]])
        # Cof = np.array([4.45,-2.23,-3.34,-3.34,4.45,0.,0.])

        # put the flow and line labels into a dictionary
        # so positions can be controlled
        Q1 = np.linalg.solve(Ar, Cof)

        Flows = dict(zip(list(self.var_dic.keys()), Q1))

        Qsum = 0
        density = 62.37  # lbs/ft^3
        abs_vis = 1.1  # centipoise
        kin_vis = (abs_vis * .000672197) / density # ft^2/s
        ELOG = 9.35 * log10(2.71828183)

        i = 0  # track number of iterations
        for ln, flow in Flows.items():
            # start by using the 'flow' calculated in
            # the solution of linear equations
            # for the first iteration use;
            Calc_Flow = flow
            Avg_Flow = Calc_Flow
            # after the first iteration change values to:
            # where the 'Calc_Flow' is the iterated value for the flow
            if i > 1:
                Avg_Flow = (flow + Calc_Flow) / 2
                Qsum = Qsum + abs(flow - Calc_Flow)
            # upgrade the 'flow' value to the avg of the
            # latest iterated values, if it passes the iterations
            # then this will be the final line flow
            flow = Avg_Flow
            DeltaQ = Avg_Flow * DeltaQ_Percent
            Avg_Flow = abs(Avg_Flow)

            print('++++++++++++++++++++++')
            print("Line label = ", ln)
            Lgth = D_e[ln][4]
            AR = D_e[ln][2]
            ARL = D_e[ln][3]
            dia = D_e[ln][0]  # diameter in inches
            Dia = dia/12   # diameter in feet
            e = D_e[ln][1] / dia  # e/dia equivalent relative roughness

            # Crane 410 Eq 3-2   velocity = .408 * gpm / (PipeID")^2
            V1 = .408 * (Avg_Flow - DeltaQ) / dia**2
            if V1 < .001:
                V1 = .002
            V2 = .408 * (Avg_Flow + DeltaQ) / dia**2
            VE = .408 * Avg_Flow / dia**2
            print(f'Pipe Dia is {dia} and length is {Lgth}at a Velocity of {VE}')
            # Crane 410 Eq 3-3 Re = 50.6 * gpm * density / (PipeID" * abs_vis)
            RE1 = 50.6 * (Avg_Flow - DeltaQ) * density / (abs_vis * dia)
            RE2 = 50.6 * (Avg_Flow + DeltaQ) * density / (abs_vis * dia)

            if RE2 < 2100:
                F1 = 64 / RE1
                F2 = 64 / RE2
                EXPP = 1.0
                Kt0 = 64 * kin_vis * ARL / dia
                continue
            else:
                F = 1 / (1.14 - 2*log10(e))**2
                PAR =  VE *(.125 * F)**.5 * Dia * e / kin_vis
                if PAR <= 65:
                    RE = RE1
                    for MM in range(0,2):
                        MCT = 0
                        while True:
                            # Colebrook Friction Factor for turbulent flow
                            ARG = e + 9.35 / (RE * F**.5)
                            FF = (1 / F**.5) - 1.14 + 2 * log10(ARG)
                            DF = 1 / (2 * F * F**.5) + ELOG / (F * F**.5 * ARG * RE)
                            DIF = FF / DF
                            F = F + DIF
                            MCT += 1
                            if (abs(DIF) < .00001 or MCT > 15):
                                break
                        if MM != 1:
                            MM = 1
                            RE = RE2
                            F1 = F
                        F2 = F
                    print('F1 and F2 = ', F1, F2)
                    BE = (log10(F1) - log10(F2)) / (log10(Avg_Flow + DeltaQ) - log10(Avg_Flow - DeltaQ))
                    AE =  F1 * (Avg_Flow - DeltaQ)**BE
                    EP = 1 - BE
                    EXPP = EP + 1
                    print(f'b = {BE} , a = {AE}, n = {EXPP}')
                    Kt0 = AE * ARL * Avg_Flow**EP
                    print('Kt0 = ', Kt0)
                    Kt = F * Lgth / Dia
                    print(f'Piping Kt value = {Kt}')
                else:
                    Kt0 = F * ARL * Avg_Flow**2
                    EXPP = 2
                    print('Kt0 = ', Kt0)
            i += 1