import numpy as np
# import math
import sqlite3
import DBase
from math import cos, pi, log10


# need to remove the node equations for the end of line nodes,
# those which are consumption flows
# need to determine the correct number of loops to include in matrix

# ERROR the consumption nodes are still not loading
# properly in the nodes form and/or nodes dictionary

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
        gravity = 9.8

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

        # get the dimensional information for each line and
        # order data based on line label into a dictionary
        qry = 'SELECT ID, info1, info2, info3 FROM General'
        tbldata = DBase.Dbase(self).Dsqldata(qry)
        D_e={} # dimensional data {line label:[diameter, e, AR, ARL]}
        for itm in tbldata:
            # ==== where .0254 and .3048 are conversion factors ====
            AR = pi / 4 * (itm[1] * .0254)**2
            ARL = (itm[2] * .3048) / (gravity * 2 * itm[1] * AR**2)
            D_e[itm[0]] = [itm[1],itm[3],AR,ARL]

        Qsum = 0
        Q = [0]*len(self.var_dic)
        VIS = 1.0
        ELOG = 9.35 * log10(2.71828183)

        i = 0
        for ln, flow in Flows.items():
            Calc_Flow = flow
            Avg_Flow = Calc_Flow
            if i > 1:
                Avg_Flow = (flow + Calc_Flow) / 2
                Qsum = Qsum + abs(flow + Calc_Flow)

            flow = Avg_Flow
            DeltaQ = Avg_Flow * DeltaQ_Percent
            Avg_Flow = abs(Avg_Flow)

            AR = D_e[ln][2]
            ARL = D_e[ln][3]
            Dia = D_e[ln][0] * .0254
            e = D_e[ln][1] * .0254

            V1 = (Avg_Flow - DeltaQ) / AR
            if V1 < .001:
                V1 = .002
            V2 = (Avg_Flow + DeltaQ) / AR
            VE = Avg_Flow /AR
            RE1 = V1 * Dia / VIS
            RE2 = V2 * Dia / VIS
            if RE2 < 2100:
                F1 = 64 / RE1
                F2 = 64 / RE2
                EXPP = 1.0
                Kt0 = 64 * VIS * ARL / Dia
            else:
                MM = 0
                F = 1 / (1.14 -2*log10(e))**2
                PAR =  VE *(.125 * F)**.5 * Dia * e / VIS
                if PAR < 65:
                    RE = RE1
# LOOP 2
                    MCT = 0
# LOOP 1 REPEAT THIS CODE UNTIL abs(DIF) > .00001 AND MCT < 15
                    FS = F**.5
                    FZ =.5 / (F * FS)
                    ARG = e + 9.35 / (RE *FS)
                    FF = 1 / FS - 1.14 + 2 * log10(ARG)
                    DF = FZ + ELOG * FZ / (ARG *RE)
                    DIF = FF / DF
                    F = F + DIF
                    MCT += 1
# END OF LOOP 1
                    if MM != 1:
                        MM = 1
                        RE = RE2
                        F1 = F
                    else:
                        break
# END OF LOOP 2
                    F2 = F
                    BE = (log10(F1) - log10(F2)) / (log10(Avg_Flow + DeltaQ) - log10(Avg_Flow - DeltaQ))
                    AE =  F1 * ( Avg_Flow - DeltaQ)**BE
                    EP = 1 - BE
                    EXPP = EP + 1
                    Kt0 = AE * ARL * Avg_Flow**EP
                else:
                    Kt0 = F * ARL * Avg_Flow**2
                    EXPP = 2
            print(ln, Kt0)
            i += 1
        NCT += 1
