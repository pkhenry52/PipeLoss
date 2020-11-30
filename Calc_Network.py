import numpy as np
import math
import sqlite3
import DBase


# need to remove the node equations for the end of line nodes,
# those which are consumption flows
# need to determine the correct number of loops to include in matrix

# ERROR the consumption nodes are still not loading properly

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
        coef_arry = [0]*len(self.parent.nodes)

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
        n = 0
        for val in self.parent.nodes.values():
            nd_matx = [0]*len(self.var_dic)
            for k, v1, v2 in val:
                if v2 == 0:
                    nd_matx[self.var_dic[k]] = math.cos(math.pi*v1)*-1
                else:
                    # specify the value for the coef array coresponding
                    # to the matrix in the variable array
                    # [20.0, 0, 0, 0]
                    coef_arry[n] = v2 * math.cos(math.pi*v1)
            n =+ 1
            # add the node matrix to the main variable array
            # [[0, -1.0, 1.0, 0, 0, 0, 0, 0],
            # [0, 0, -1.0, -1.0, 1.0, 0, -1.0, 0],
            # [0, 0, 0, 0, -1.0, -1.0, 0, 1.0],
            # [-1.0, 1.0, 0, 1.0, 0, 1.0, 0, 0]]
            var_arry.append(nd_matx)

        # get all the Kt values from the various
        # tables and sum them for each line
        datatbls = ['ManVlv1', 'ManVlv2', 'ChkVlv',
                    'Fittings', 'WldElb', 'EntExt']
        n = 0
        dct = dict()
        for tbl in datatbls:
            qry = 'SELECT ID, Kt' + str(n+1) + ' FROM ' + tbl
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
            # if they do not then the line order needs to be changed
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
            print('loop lines ', lns, 'loop number', num)
            # loop lines  ['E', 'F', 'D', 'C'] loop number 1
            for n, ln in enumerate(lns):
                nd1 = alpha_poly_pts[n]
                for val in self.parent.nodes[nd1]:
                    if ln in val:
                        k_matx[self.var_dic[ln]] = math.cos(math.pi*val[1]) *-1

            for k,v in self.var_dic.items():
                if Kt_dict[k] != 0:
                    k_matx[v] = Kt_dict[k] * k_matx[v]
                else:
                    k_matx[v] = 0.0
            
            var_arry.append(k_matx)
            coef_arry.append(0)

            Ar = np.array(var_arry)
            Cof = np.array(coef_arry)