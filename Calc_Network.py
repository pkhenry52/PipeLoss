import numpy as np
import sqlite3
import DBase
from math import cos, pi, log10

# need to determine the correct number of loops to include in matrix
class Calc(object):
        
    def __init__(self, parent, cursr, db):
        self.parent = parent
        self.coef_lst = set()
        self.cursr = cursr
        self.db = db

        # these are to be the arrays used in numpy
        # used to solve the linear equations
        self.var_arry = []
        self.coef_arry = []
        
        # {line label:[dia", e", AR, ARL, Line_Length, Le]}
        self.D_e = {}
        # {line label:[Kp values and exponent n]}
        self.K = {}

        # get all the Kt values from the various
        # tables and sum them for each line
        datatbls = ['General', 'ManVlv1', 'ManVlv2', 'ChkVlv',
                    'Fittings', 'WldElb', 'EntExt']
        n = 0
        self.dct = dict()
        for tbl in datatbls:
            qry = 'SELECT ID, Kt' + str(n) + ' FROM ' + tbl
            tbldata = DBase.Dbase(self).Dsqldata(qry)
            for ln, Kt in tbldata:
                self.dct.setdefault(ln, []).append(Kt)
            n += 1
        for ln in self.dct:
            self.dct[ln] = sum(self.dct[ln])

    def Evaluation(self):
        Q_old = {}

        # STEP 1 is to define the node matrices
        # these do not change during the calculations
        self.node_matrix()

        # STEP 2 use the Hazen-Williams equation
        # to determine an initial Kp values once the Q's are calculated
        # then a new Kp will be calculated using the friction factors
        self.Kp_Le()

        # use the preliminary Kp values to determine the loop energy equations
        self.loop_matrix()

        # Array values for the lines ['B', 'D', 'E', 'F', 'G', 'H', 'I']
        # Ar = np.array([
        # [1.,1.,0.,0.,0.,0.,0.],
        # [-1.,0.,0.,1.,0.,0.,0.],
        # [0.,0.,0.,0.,-1.,0.,-1.],
        # [0.,0.,1.,-1.,0.,-1.,0.],
        # [0.,0.,0.,0.,0.,1.,1.],
        # [-0.26819644, 4.57925996, -0.40396739, -1.30345388, 0., 0., 0.]        ]
        # [ 0., 0., 0.40396739, 0., 1.50099963, 3.09127342, -9.41131546]
        # ])
        Ar = np.array(self.var_arry)

        # Cof = np.array([4.45,-2.23,-3.34,-3.34,4.45,0.,0.])
        # convert gpm to ft^3/sec
        Cof = np.array(self.coef_arry) / 448.8

        # STEP 3 solve for the initial flow values
        Q1 = np.linalg.solve(Ar, Cof)

        # put the flow and line labels into a dictionary
        Flows = dict(zip(list(self.var_dic.keys()), Q1))
        # flows in ft^3/sec
        # Flows dictionary {'B': 3.679435757336772,
        # 'D': 0.7768922284029779, 'E': 1.185590835521604,
        # 'F': 1.4512717644668973, 'G': 1.962483063924582,
        # 'H': 3.0765650603595196, 'I': 1.3797629253802302}

        # STEP 4 and 5 calculate the Velocity, Re, f and new Kp values
        self.Iterate_Flow(Flows)

        # STEP 6 use the newest Kp values to generate
        # a new set of energy equations
        #++++++++ the number of rows to be removed from
        # var_arry needs to be set by the number of loop
        # equations used ++++++++++++
        self.var_arry = self.var_arry[:-2]
        self.loop_matrix()
        Ar = np.array(self.var_arry)
        Q1 = np.linalg.solve(Ar, Cof)
        # STEP 7 calculate the new flow values
        # put the flow and line labels into a dictionary
        Flows = dict(zip(list(self.var_dic.keys()), Q1))

        # and calculate the new Velocity, Re, f and new Kp values
        self.Iterate_Flow(Flows)
        K_old = self.K.copy()
        Q_old = Flows.copy()
        self.var_arry = self.var_arry[:-2]
        self.loop_matrix()
        Ar = np.array(self.var_arry)
        Q1 = np.linalg.solve(Ar, Cof)
        Flows = dict(zip(list(self.var_dic.keys()), Q1))

        Q_avg = {}
        for k, v in Flows.items():
            Avg = (Flows[k] + Q_old[k]) / 2
            Q_avg[k] = Avg

        # use the first set of Q1, Kp and n
        # to find new coef for the energy equation
        # based on the equation K = Ki * Qi ^ (ni - 1)
        self.Kp_Iterated(Q_avg)
        self.var_arry = self.var_arry[:-2]
        self.loop_matrix()
        Ar = np.array(self.var_arry)
        Q1 = np.linalg.solve(Ar, Cof)
        Flows = dict(zip(list(self.var_dic.keys()), Q1))

        for iters in range(5):
            # and calculate the new Velocity, Re, f and new Kp values
            self.Iterate_Flow(Q_avg)
            Q_old = Flows.copy()
            self.var_arry = self.var_arry[:-2]
            self.loop_matrix()
            Ar = np.array(self.var_arry)
            Q1 = np.linalg.solve(Ar, Cof)
            Flows = dict(zip(list(self.var_dic.keys()), Q1))

            Q_avg = {}
            for k, v in Flows.items():
                Avg = (Flows[k] + Q_old[k]) / 2
                Q_avg[k] = Avg

            # use the first set of Q1, Kp and n
            # to find new coef for the energy equation
            # based on the equation K = Ki * Qi ^ (ni - 1)
            self.Kp_Iterated(Q_avg)
            self.var_arry = self.var_arry[:-2]
            self.loop_matrix()
            Ar = np.array(self.var_arry)
            Q1 = np.linalg.solve(Ar, Cof)
            Flows = dict(zip(list(self.var_dic.keys()), Q1))
            # test the variation of the flows if the next iteration
            # does not change then the last values are valid
            sigma = self.Iterate_Test(Flows, Q_old)

            if sigma <= .01:
                completed = True
                break
            else:
                completed = False
                Q_avg = {}
                for k, v in Flows.items():
                    Avg = (Flows[k] + Q_old[k]) / 2
                    Q_avg[k] = Avg

        if completed is True:
            density = 62.37  # lbs/ft^3
            gravity = 32.2
            abs_vis = 1.1  # centipoise
            kin_vis = (abs_vis * .000672197) / density # ft^2/s
            ELOG = 9.35 * log10(2.71828183)
            # calculate these for each pipe flow
            for ln, Q in Q_old.items():
                gpm = Q * 448.8
                dia = self.D_e[ln][0]
                Dia = dia / 12
                lgth = (self.D_e[ln][4] + self.D_e[ln][5])
                e = self.D_e[ln][1] / dia
                vel = .408 * gpm / dia**2
                Re = 123.9 * dia * vel * density / abs_vis
                if Re <= 2100:
                    f = 64 / Re
                    hL = .0962 * abs_vis * lgth * vel / (dia**2 * density)
                    delta_P = (.000668 * abs_vis * lgth * vel / dia**2)
                else:
                    f = 1 / (1.14 - 2*log10(e))**2
                    PAR =  vel *(.125 * f)**.5 * Dia * e / kin_vis
                    if PAR <= 65:
                        MCT = 0
                        while True:
                            # Colebrook Friction Factor for turbulent flow
                            ARG = e + 9.35 / (Re * f**.5)
                            FF = (1 / f**.5) - 1.14 + 2 * log10(ARG)
                            DF = 1 / (2 * f * f**.5) + ELOG / 2 * (f * f**.5 * ARG * Re)
                            DIF = FF / DF
                            f = f + DIF
                            MCT += 1
                            if (abs(DIF) < .00001 or MCT > 15):
                                break
                    hL = .1863 * f * lgth * vel**2 / dia
                    delta_P = .001294 * f * lgth * density * vel**2 / dia

                print('\n+++++++++++++++++++++')
                print('Line Label = ', ln,)
                print('Pipe Dia (inches) = ',dia)
                print('Equivalent Length (ft) = ', lgth)
                print('Flow rate (gpm) = ', gpm, '  (ft^3/s) = ', Q)
                print("Head Loss (ft of fluid) = ", hL)
                print('Pressure Drop (psi) = ', delta_P)
                print('Renolds Number = ', Re)
                print('Friction Factor = ', f)
                print('Flow Velocity (ft/sec) = ', vel)
        else:
            print('Unable to iterate network to a solution')

    def node_matrix(self):
        var_lst = set()

        for val in self.parent.nodes.values():
            # generate val=[('B', 0, 0), ('C', 0, 20.0), ('D', 1, 0)]
            # for each node in self.nodes
            for k, v1, v2 in val:
                if v2 == 0:
                    # make a list of all the pipes itersecting nodes
                    # excluding consumption flows
                    var_lst.add(k)

        # sort them then index them for matrix position
        # {'B': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'H': 5, 'I': 6}
        self.var_dic = dict((v,k) for k,v in enumerate(sorted(var_lst)))

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
                self.coef_arry.append(coeff)
                # add the node matrix to the main variable array
                # [[0, -1.0, 1.0, 0, 0, 0, 0, 0],
                # [0, 0, -1.0, -1.0, 1.0, 0, -1.0, 0],
                # [0, 0, 0, 0, -1.0, -1.0, 0, 1.0],
                # [-1.0, 1.0, 0, 1.0, 0, 1.0, 0, 0]]
                self.var_arry.append(nd_matx)
    
        # +++++ Note this code to be changed to delete
        # specific node if solution is not found after first iteration+++++
        # the final array for the nodes removing the last node
        del self.var_arry[-1]
        del self.coef_arry[-1]

    def Kp_Le(self, FF=None):
        gravity = 32.2  # ft/s^2
        Chw = 120

        # get the dimensional information for each line and
        # order data based on line label into a dictionary
        qry = 'SELECT ID, info1, info2, info3 FROM General'
        tbldata = DBase.Dbase(self).Dsqldata(qry)
        # tbldata = line lbl, dia", lgth', e"
        for lbl, dia, Lgth, e in tbldata:
            Dia = dia / 12
            AR = pi * Dia**2 / 4  # ft^2 
            n_exp = 0

            if FF is None:
                # first calculation of f is based on fully turbulent flow
                f = (1.14 - 2 * log10(e/dia))**-2
            else:
                # after first iteration use the calculated average f value
                f = FF[lbl]

            Le = self.dct[lbl] * Dia / f
            ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)
            Kp = (4.73 * (Lgth + Le)) / (Chw**1.852 * Dia**4.87)

            self.D_e[lbl] = [dia, e, AR, ARL, Lgth, Le]
            self.K[lbl] = [Kp, n_exp]

#        self.K = {'D':[4.71,1.96], 'E':[.402,1.85],'F':[1.37,1.90],'B':[.264,1.95],'G':[1.14,1.95],'I':[11.30,1.97],'H':[3.35,1.98]}

    def loop_matrix(self):
        # reverse the key and values in the points dictionary
        # with the cordinates as the key
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
            # in the plot as specified as part of a node in order to specify
            # the index location for the Kp vaiable in the loop equations
            # and combine the sign of the direction arrow with the
            # calculated Kp for the line
            for k,v in self.var_dic.items():
                if k in self.K.keys():
                    if self.K[k][0] != 0:
                        k_matx[v] = self.K[k][0] * k_matx[v]
                    else:
                        k_matx[v] = 0.0
            self.var_arry.append(k_matx)
            self.coef_arry.append(0)

    def Iterate_Test(self, Qa, Qb):
        # convert the two dictionary of flows into ordered lists,
        # since the keys are the same they can be sorted together
        Qa_lst = []
        Qb_lst = []

        for k in sorted(Qa):
            Qa_lst.append(Qa[k])
            Qb_lst.append(Qb[k])
        diff = np.abs(np.subtract(np.abs(np.array(Qa_lst)),
                      np.abs(np.array(Qb_lst))))
        # find the average of the differences between all the flows
        mu = sum(diff) / len(diff)
        numer = sum((diff - mu)**2)
        denom = len(Qa_lst)-1
        sigma = numer / denom
        return sigma

    def Kp_Iterated(self, Flows):
        # calculate the new Kp values using n and the old Kp & Flows
        # then replace the corresponding Kp value in the energy equations
        for key, val in self.K.items():
            Kp_iter = val[0] * abs(Flows[key])**(val[1]-1)
            self.K[key] = [Kp_iter, val[1]]

    def Iterate_Flow(self, Flows):
        # percentage variation in range of flow estimates
        # to calculate Q1 and Q2
        DeltaQ_Percent = .3
        Qsum = 0
        density = 62.37  # lbs/ft^3
        gravity = 32.2
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
            if i > 0:
                Avg_Flow = (flow + Calc_Flow) / 2
                Qsum = Qsum + abs(flow - Calc_Flow)
            # upgrade the 'flow' value to the avg of the
            # latest iterated values, if it passes the iterations
            # then this will be the final line flow
            flow = Avg_Flow
            DeltaQ = Avg_Flow * DeltaQ_Percent
            Avg_Flow = abs(Avg_Flow)

            dia = self.D_e[ln][0]  # diameter in inches
            Dia = dia/12   # diameter in feet
            e = self.D_e[ln][1] / dia  # e/dia equivalent relative roughness
            AR = self.D_e[ln][2]
            Lgth = self.D_e[ln][4]
            ARL = self.D_e[ln][3]

            # Crane 410 Eq 3-2   velocity = ft^3/sec / Flow Area
            V1 = (Avg_Flow - DeltaQ) / AR
            if V1 < .001:
                V1 = .002
            V2 = (Avg_Flow + DeltaQ) / AR
            VE = Avg_Flow / AR

            # Crane 410 Eq 3-3 Re = 22700 * ft^3/sec * density / (PipeID" * abs_vis)
            RE1 = 22700 * (Avg_Flow - DeltaQ) * density / (abs_vis * dia)
            RE2 = 22700 * (Avg_Flow + DeltaQ) * density / (abs_vis * dia)

            if RE2 < 2100:
                F1 = 64 / RE1
                F2 = 64 / RE2
                F = (F1+F2) / 2
                EXPP = 1.0
                Kp = 64 * kin_vis * ARL / dia
                continue
            else:
                F = 1 / (1.14 - 2*log10(e))**2
                PAR =  VE *(.125 * F)**.5 * Dia * e / kin_vis
                if PAR <= 65:
                    RE = RE1
                    for MM in range(0, 2):
                        MCT = 0
                        while True:
                            # Colebrook Friction Factor for turbulent flow
                            ARG = e + 9.35 / (RE * F**.5)
                            FF = (1 / F**.5) - 1.14 + 2 * log10(ARG)
                            DF = 1 / (2 * F * F**.5) + ELOG / 2 * (F * F**.5 * ARG * RE)
                            DIF = FF / DF
                            F = F + DIF
                            MCT += 1
                            if (abs(DIF) < .00001 or MCT > 15):
                                break
                        if MM == 0:
                            RE = RE2
                            F1 = F
                        else:
                            F2 = F

                    Le = self.dct[ln] * Dia / F
                    ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)
                    BE = (log10(F1) - log10(F2)) / (log10(Avg_Flow + DeltaQ) - log10(Avg_Flow - DeltaQ))
                    AE =  F1 * (Avg_Flow - DeltaQ)**BE
                    EP = 1 - BE
                    EXPP = EP + 1
                    Kp = AE * ARL

                else:
                    EXPP = 2
                    Le = self.dct[ln] * Dia / F
                    ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)
                    Kp = F * ARL

            i += 1
            self.D_e[ln][3] = ARL
            self.K[ln] = [Kp, EXPP]
            self.D_e[ln][5] = Le
