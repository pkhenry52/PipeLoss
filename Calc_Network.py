import wx
import numpy as np
import DBase
from math import cos, pi, log10, log, exp


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
        # final flows by line lbl
        self.Q_old = {}

        self.dct = self.Kt_vals()
        self.density, self.kin_vis = self.Vis_Ro()

    def Kt_vals(self):
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
        return dct

    def Vis_Ro(self):
        qry = 'SELECT * FROM Fluid'
        tbldata = DBase.Dbase(self).Dsqldata(qry)

        rho_f = None
        nu_f = None

        if tbldata == []:
            msg = "No fluid data has been specified."
            self.WarnData(msg)
            return rho_f, nu_f #, eta_mix
        else:
            dt = tbldata[0]

            if (dt[1] == 0 and dt[6] == 0):
                msg = "No fluid density has been specified."
                self.WarnData(msg)
                return rho_f, nu_f
            elif (dt[1] != 0 and dt[14] == -1) or (dt[6] != 0 
                  and dt[17] == -1):
                msg = "Fluid density units have not been specified"
                self.WarnData(msg)
                return rho_f, nu_f

            if (dt[1] != 0 and dt[2] == 0 and dt[3] == 0) or \
             (dt[6] != 0 and dt[7] == 0 and dt[8] == 0):
                msg = "Fluid vicosity has not been specified."
                self.WarnData(msg)
                return rho_f, nu_f
            elif (dt[2] != 0 and dt[15] == -1 or dt[3] != 0
                  and dt[16] == -1) or (dt[7] != 0 and
                  dt[18] == -1 or dt[8] != 0 and dt[19] == -1):
                msg = "Fluid vicosity units have not been specified."
                self.WarnData(msg)
                return rho_f, nu_f

            if (dt[1] != 0 and dt[4] == 0 and dt[5] == 0) or \
             (dt[6] != 0 and dt[9] == 0 and dt[10] == 0):
                msg = 'No fluid concentration has been specified.  If this is'
                msg2 = ' a homogenous fluid specify "% by vol" as 100'
                self.WarnData(msg + msg2)
                return rho_f, nu_f

            if dt[11] != 0:
                if dt[20] == -1:
                    msg = "Solids density units have not been specified."
                    self.WarnData(msg)
                    return rho_f, nu_f

                if dt[12] == 0 and dt[13] == 0:
                    msg1 = 'Either percent solids by weight'
                    msg2 = ' or by volume need to be specified'
                    self.WarnData(msg1 + msg2)
                    return rho_f, nu_f

        # this will calculate the liquid viscosity
        # and density without any slurry present

        # collect the densities convert to lb/ft^3
        rho_1 = float(dt[1])
        rho_2 = float(dt[6])
        rho = dt[11]

        if rho_1 == 0 and rho_2 == 0:
            msg = "Both fluid densities cannot be specified as zero."
            self.WarnData(msg)
            return rho_f, nu_f

        if dt[14] == 1:
            rho_1 *= 62.428
        elif dt[14] == 2:
            rho_1 *= .06243

        if dt[17] == 1:
            rho_2 *= 62.428
        elif dt[17] == 2:
            rho_2 *= .06243

        if dt[20] == 1:
            rho *= 62.428
        elif dt[20] == 2:
            rho *= .06243

        Cv_1 = dt[4]
        Cw_1 = dt[5]
        Cv_2 = dt[9]
        Cw_2 = dt[10]

        # if the volume of weight percent do not add up
        # to 100 then adjust based on given values
        if Cv_1 + Cv_2 != 100:
            Cv_1 += (Cv_1 * (100-Cv_1-Cv_2))
            Cv_2 += (Cv_2 * (100-Cv_2-Cv_1))
        elif Cw_1 + Cw_2 != 100:
            Cw_1 += (Cw_1 * (100-Cw_1-Cw_2))
            Cw_2 += (Cw_2 * (100-Cw_2-Cw_1))

        # collect the absolute (dynamic) vicosity convert to centipoise
        # ['lbm/ft-sec', 'g/cm-s\n(poise)', 'centipoise']
        eta_1 = float(dt[3])
        eta_2 = float(dt[8])

        # units speced as lbm/ft-sec
        if dt[16] == 0:
            eta_1 *= 1488.164
        # units speced as g/cm-s\n(poise)
        elif dt[16] == 1:
            eta_1 *= 100

        if dt[19] == 0:
            eta_2 *= 1488.164
        elif dt[19] == 1:
            eta_2 *= 100

        # convert the kinematic viscostiy to ft^2/s
        # ['ft^2/s', 'cm^2/s\n(stokes)', 'centistokes']
        nu_1 = float(dt[2])
        nu_2 = float(dt[7])

        # units speced as cm^2/s\n(stokes)
        if dt[15] == 1:
            nu_1 *= .001076
        # units speced as centistokes
        elif dt[15] == 2:
            nu_1 *= .00001076

        if dt[18] == 1:
            nu_2 *= .001076
        elif dt[18] == 2:
            nu_2 *= .00001076

        # depending on which viscosity is provided calculate the other
        if rho_2 == 0:
            rho_f = rho_1
            if nu_1 == 0:
                nu_1 = eta_1 / rho_1
            else:
                eta_1 = nu_1 * rho_1
            rho_f = rho_1
        elif rho_1 == 0:
            rho_f = rho_2
            if nu_2 == 0:
                nu_2 = eta_2 / rho_2
            else:
                eta_2 = nu_2 * rho_2
            rho_f = rho_2
        else:
            # calculate the liquid mixture density
            if Cw_1 != 0 and Cw_2 != 0:
                rho_f = 100/(Cw_1/rho_1 + Cw_2/rho_2)
                Cv_1 = Cw_1 * rho_f / rho_1
                Cv_2 = Cw_2 * rho_f / rho_2
            elif Cv_1 != 0 and Cv_2 != 0:
                rho_f = (Cv_1 * rho_1 + Cv_2 * rho_2)/100
                Cw_1 = Cv_1 * rho_1 / rho_f
                Cw_2 = Cv_2 * rho_2 / rho_f

        # if there are solids present then calculate
        # the slurry vicosity and density
        if nu_1 == 0:
            nu_f = nu_2
        elif nu_2 == 0:
            nu_f = nu_1
        else:
            VBN_1 = 14.534 * log(log(nu_1/.00001076 + 0.8)) + 10.975
            VBN_2 = 14.534 * log(log(nu_2/.00001076 + 0.8)) + 10.975

            VBN_f = (Cw_1/100 * VBN_1) + (Cw_2/100 * VBN_2)

            exp_1 = 2.71828**((VBN_f - 10.975) / 14.534)
            nu_f = (2.71828**(exp_1) - .8) * .00001076

        # if solids are present then recalc density and
        # viscosity bsaed on slurry equations
        if dt[11] != 0:
            if dt[12] != 0:
                rho_s = dt[11]
                if dt[20] == 1:
                    rho_s *= 62.428
                elif dt[20] == 2:
                    rho_s *= .06243

            Cw_m = dt[12]
            Cv_m = dt[13]
            if Cw_m != 0:
                rho_f = 100 / ((Cw_m / rho_s) + ((100 - Cw_m) / rho_f))
                Cv_m = Cw_m * rho_f / rho_s
            elif Cv_m !=0:
                rho_f = Cv_m / 100 * (rho_s - rho_f) + rho_f
                Cw_m = Cv_m * rho_s / rho_f

            if Cw_m <= 1:
                nu_f = nu_f * (1 + 2.5 * Cv_m)
            elif Cw_m > 1 and Cw_m <= 20:
                nu_f = nu_f * (1 + 2.5 * Cv_m / 100 + 14.1 * (Cv_m/100)**2)
            elif Cw_m > 20:
                coef_1 = (1 + 2.5 * Cv_m / 100 + 10.05 * (Cv_m/100)**2 )
                coef_2 = (.00273 * 2.71828**(16.6*Cv_m/100))
                nu_f = nu_f * (coef_1 + coef_2)

        return rho_f, nu_f

    def Evaluation(self):
        Nl = 0
        Nn = 0
        Ncl = 0
        Npl = 0
        Np = 0
        Q1 = []

        iters = 80
        iter_num = 0
        completed = False

        var_lst = set()

        for val in self.parent.nodes.values():
            # generate val=[('B', 0, 0), ('C', 0, 20.0), ('D', 1, 0)]
            # for each node in self.nodes
            for l in val:
                if l[2] == 0:
                    # make a list of all the pipes itersecting nodes
                    # excluding consumption flows
                    var_lst.add(l[0])

        # sort them then index them for matrix position
        # {'B': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'H': 5, 'I': 6}
        self.var_dic = dict((v,k) for k,v in enumerate(sorted(var_lst)))
        Nl = len(self.var_dic)

        # STEP 1 is to define the node matrices
        # these do not change during the calculations
        node_var, node_cof = self.node_matrix()
        Nn = len(node_cof)

        # STEP 2 use the Hazen-Williams equation
        # to determine an initial Kp values once the Q's are calculated
        # then a new Kp will be calculated using the friction factors
        self.Kp_Le()

        # use the preliminary Kp values to determine the
        # loop energy equations
        if self.parent.poly_pts != {}:
            loop_var, loop_cof = self.loop_matrix()
            Ncl = len(loop_cof)

        # then develop the matrices for the various pumps
        if self.parent.pumps != {}:
            trans_var, trans_cof, A_var, ho_cof = self.pump_matrix()
            Np = len(trans_cof)

        if self.parent.Pseudo != {}:
            pseudo_var, pseudo_cof = self.pseudo_matrix(A_var, ho_cof)
            Npl = len(pseudo_cof)

        Nu = Nl + Np

        Nn, Ncl, Npl, procd = self.Varify(Nl, Np, Nn, Ncl, Npl)

        if procd is False:
            self.Q_old = {}
            return self.Q_old, self.D_e, self.density, self.kin_vis #, self.abs_vis

        while Nu < Nn + Np + Ncl + Npl:
            if Nu < Nn + Np + Ncl + Npl:
                Ncl -= 1
            if Nu < Nn + Np + Ncl + Npl:
                Npl -= 1
            if Nu < Nn + Np + Ncl + Npl:
                Np -= 1
            if Nu < Nn + Np + Ncl + Npl:
                Nn -= 1
            
        self.var_arry = node_var[:Nn]
        self.coef_arry = node_cof[:Nn]

        if self.parent.poly_pts != {}:
            self.var_arry = self.var_arry + loop_var[:Ncl]
            self.coef_arry = self.coef_arry + loop_cof[:Ncl]
        if self.parent.pumps != {}:
            self.var_arry = self.var_arry + trans_var[:Np]
            self.coef_arry = self.coef_arry + trans_cof[:Np]
        if self.parent.Pseudo != {}:
            self.var_arry = self.var_arry + pseudo_var[:Npl]
            self.coef_arry = self.coef_arry + pseudo_cof[:Npl]            

        # Array values for the lines ['B', 'D', 'E', 'F', 'G', 'H', 'I']
        Ar = np.array(self.var_arry)
        Cof = np.array(self.coef_arry)

        # STEP 3 solve for the initial flow values
        try:
            Q1 = np.linalg.solve(Ar, Cof)
            # put the flow and line labels into a dictionary
            Flows = dict(zip(list(sorted(self.var_dic.keys())), Q1))
            '''flows in ft^3/sec
            Flows dictionary {'B': 3.679435757336772,
            'D': 0.7768922284029779, 'E': 1.185590835521604,
            'F': 1.4512717644668973, 'G': 1.962483063924582,
            'H': 3.0765650603595196, 'I': 1.3797629253802302}'''

            while True:
                if iter_num == 0:
                    Qsum = self.Iterate_Flow(Flows, iter_num)
                    Flows = self.Q1_Calc(Nn, Ncl, Npl, Np)
                    iter_num += 1
                elif Qsum > .001 and iter_num < iters:
                    Qsum = self.Iterate_Flow(Flows, iter_num)
                    iter_num += 1
                    Flows = self.Q1_Calc(Nn, Ncl, Npl, Np)
                elif iter_num >= iters:
                    completed = False
                    break
                else:
                    completed = True
                    break
        except:
            completed = False

        if completed is True:
            self.Save_Output()
        else:
            msg1 = 'Unable to iterate network to a solution\n'
            msg2 = 'total number of iterations completed = ' + str(iter_num)
            msg3 = '.\nBased on presented information system cannot be solved.'
            self.WarnData(msg1 + msg2 + msg3)
            self.Q_old = {}

        return self.Q_old, self.D_e, self.density, self.kin_vis #, self.abs_vis

    def Iterate_Flow(self, Flows, iter_num):
        # percentage variation in range of flow estimates
        # to calculate Q1 and Q2
        DeltaQ_Percent = .1
        gravity = 32.2
        Qsum = 100
        ELOG = 9.35 * log10(2.71828183)

        if iter_num > 0:
            Qsum = 0

        for ln, flow in Flows.items():
            # start by using the 'flow' calculated in
            # the solution of linear equations
            # for the first iteration use;
            Calc_Flow = flow
            Avg_Flow = Calc_Flow
            # after the first iteration change values to:
            # where the 'Calc_Flow' is the iterated value for the flow
            if iter_num > 0:
                Avg_Flow = (self.Q_old[ln] + Calc_Flow) / 2
                Qsum = Qsum + abs(self.Q_old[ln] - Calc_Flow)
            # upgrade the 'flow' value to the avg of the
            # latest iterated values, if it passes the iterations
            # then this will be the final line flow
            self.Q_old[ln] = Avg_Flow
            DeltaQ = Avg_Flow * DeltaQ_Percent
            Avg_Flow = abs(Avg_Flow)

            dia, e, AR, ARL, Lgth, _, lgth = self.D_e[ln]

            Dia = dia / 12
            er = e / dia
            V1 = (Avg_Flow - DeltaQ) / AR
            if V1 < .001:
                V1 = .002
            V2 = (Avg_Flow + DeltaQ) / AR
            VE = Avg_Flow / AR

            # Crane 410 Eq 3-3 Re = 22700 * ft/sec * density / (PipeID" * abs_vis)
            RE1 = V1 * Dia / self.kin_vis
            RE2 = V2 * Dia / self.kin_vis
            if RE2 < 2100:
                F1 = 64 / RE1
                F2 = 64 / RE2
                EXPP = 1.0

                Le = self.dct[ln] * Dia / F2
                ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)
                self.D_e[ln][3] = ARL
                self.D_e[ln][5] = Le
                '''Revised original documentation for Kp = f * Lgth/Diamater'''
#                Kp = 2 * gravity * self.kin_vis * ARL / Dia
                Kp = F2 * (Lgth + lgth) / Dia
                if ln in self.parent.vlvs:
                    Kp = Kp * lgth / Lgth
                self.K[ln] = [Kp, EXPP]
                continue
            else:
                F = 1 / (1.14 - 2*log10(er))**2
                PAR =  (VE * (.125 * F)**.5 * Dia * er) / self.kin_vis
                if PAR <= 120:
                    RE = RE1
                    for MM in range(0, 2):
                        MCT = 0
                        while True:
                            # Colebrook Friction Factor for turbulent flow
                            ARG = er + 9.35 / (RE * F**.5)
                            FF = (1 / F**.5) - 1.14 + 2 * log10(ARG)
                            DF = 1 / (2 * F**1.5) + (ELOG / 2 * F**1.5) / (ARG * RE)
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
                    Kp = AE * ARL * Avg_Flow**EP
                    if ln in self.parent.vlvs:
                        Kp = Kp * lgth / Lgth
                else:
                    EXPP = 2
                    Le = self.dct[ln] * Dia / F
                    ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)
                    Kp = F * ARL *Avg_Flow**2
                    if ln in self.parent.vlvs:
                        Kp = Kp * lgth / Lgth

                self.K[ln] = [Kp, EXPP]

            self.D_e[ln][3] = ARL
            self.D_e[ln][5] = Le

        return Qsum

    def Q1_Calc(self, Nn, Ncl, Npl, Np):

        loop_var, loop_cof = self.loop_matrix()
        trans_var, trans_cof, A_var, ho_cof = self.pump_matrix()
        pseudo_var, pseudo_cof = self.pseudo_matrix(A_var, ho_cof)
        
        self.var_arry = (self.var_arry[:Nn] + loop_var[:Ncl] +
                         trans_var[:Np] + pseudo_var[:Npl])

        self.coef_arry = (self.coef_arry[:Nn] + loop_cof[:Ncl] +
                          trans_cof[:Np] + pseudo_cof[:Npl])

        Ar = np.array(self.var_arry)
        Cof = np.array(self.coef_arry)

        Q1 = np.linalg.solve(Ar, Cof)
        # STEP 7 calculate the new flow values
        # put the flow and line labels into a dictionary
        return dict(zip(list(sorted(self.var_dic.keys())), Q1))

    def Kp_Le(self):
        gravity = 32.2  # ft/s^2

        # get the dimensional information for each line and
        # order data based on line label into a dictionary
        qry = 'SELECT * FROM General'
        tbldata = DBase.Dbase(self).Dsqldata(qry)

        for itm in tbldata:
            lbl = itm[0]

            # if there is a control valve in the line then use
            # the upstream or down stream length as the new pipe length
            lgth = 0
            if lbl in self.parent.vlvs:
                lgth = float(self.parent.vlvs[lbl][2])

            # convert the input diameter to inches
            unt = itm[6]

            if unt == 0:
                dia = float(itm[1])
            elif unt == 1:
                dia = float(itm[1]) / 25.4

            # convert the input length to feet
            unt = itm[7]
            if unt == 0:
                Lgth = float(itm[2])
            elif unt == 1:
                Lgth = float(itm[2]) * 3.281
                lgth = lgth * 3.281 

            # specify the corresponding absolute e in inches
            unt = itm[8]
            if unt == 0:
                e = float(itm[3])
            elif unt == 1:
                e = float(itm[3]) / 25.4

            Chw = 100  # this can be changed but has limited effect on
            # final out come typical is between 100 and 140
            Dia = dia / 12    # ft
            AR = pi * Dia**2 / 4  # ft^2
            n_exp = 0
            f = (1.14 - 2 * log10(e/dia))**-2
            Le = self.dct[lbl] * Dia / f    # ft
            Kp = 4.73 * (Lgth + Le) / (Dia**4.87 * Chw**1.852)
            ARL = (Lgth + Le) / (gravity * 2 * Dia * AR**2)

            # modify Kp for line with control valve
            if lbl in self.parent.vlvs:
                Kp = Kp * lgth / Lgth

            self.D_e[lbl] = [dia, e, AR, ARL, Lgth, Le, lgth]
            self.K[lbl] = [Kp, n_exp]

    def pump_matrix(self):
        trans_var = []
        trans_cof = []
        N_pmp = len(self.parent.pumps)
        A_var = {}
        ho_cof = {}
        '''pump flows must be converted to ft^3 / s to get TDH in ft'''
        # use the pump data enetered for 3 opeating point to calculate
        # the constants for the pump equation
        n = 0
        for k, v in sorted(self.parent.pumps.items()):
            # convert the flow to ft^3/s and TDH to ft
            # ['US GPM & ft', 'ft^3/s & ft', 'm^3/hr & m']
            if v[0] == 0:
                f = .002228
                t = 1
            elif v[0] == 1:
                f = 1
                t = 1
            elif v[0] == 2:
                f = .00981
                t = 3.28
            pump_Flow = np.array([v[2]*f,v[3]*f,v[4]*f])
            pump_TDH = np.array([v[5]*t,v[6]*t,v[7]*t])

            A, B, Ho = np.polyfit(pump_Flow, pump_TDH, 2)

            # ho is the head generated by the pump
            ho = Ho - B / (4 * A)
            # this is the coef value in the transformation equation
            cof_arry = (B / (2 * A))
            # this defines the variable arry for the transformation
            # equation where -1 is the flow indicator for the actual
            # discharge pipe and +1 is the indicator or the pump flow
            var_matx = [0] * (len(self.var_dic) + N_pmp)
            ln_lbl = self.parent.nodes[k][0][0]
            var_matx[self.var_dic[ln_lbl]] = -1
            var_matx[n - N_pmp] = 1
            A_var[k] = A, n - N_pmp
            ho_cof[k] = ho, n - N_pmp
            trans_var.append(var_matx)
            trans_cof.append(cof_arry)
            n += 1
        return trans_var, trans_cof, A_var, ho_cof

    def node_matrix(self):
        node_var = []
        node_cof = []
        N_pmp = len(self.parent.pumps)
        # generate the matrix for each node
        for val in sorted(self.parent.nodes.values()):
            if len(val) > 1:
                '''following line causes issue when there are no pumps at line 423'''
                nd_matx = [0]*(len(self.var_dic) + N_pmp) # - 1)
                coeff = 0
                for k, v1, v2, v3 in val:
                    if v2 == 0:
                        nd_matx[self.var_dic[k]] = cos(pi*v1)*-1
                    else:
                        # convert the flow to ft^3/s from
                        # ['US GPM', 'm^3/hr']
                        if v3 == 0:
                            v2 = v2 * .002228
                        elif v3 == 2:
                            v2 = v2 * .0098
                        # specify the value for the coef array coresponding
                        # to the matrix in the variable array
                        # [20.0, 0, 0, 0]
                        coeff = v2 *cos(pi*v1)
                # collect the array of node coeficients
                # ie the value of any comsumption at the node
                node_cof.append(coeff)
                # add the node matrix to the main variable array
                # [[0, -1.0, 1.0, 0, 0, 0, 0],
                # [0, 0, -1.0, -1.0, 1.0, 0, -1.0],
                # [0, 0, 0, 0, -1.0, -1.0, 0],
                # [-1.0, 1.0, 0, 1.0, 0, 1.0, 0]]
                node_var.append(nd_matx)
        return node_var, node_cof

    def loop_matrix(self):
        loop_var = []
        loop_cof = []
        # reverse the key and values in the points dictionary
        # with the cordinates as the key
        # and the node label as the value
        inv_pts = {tuple(v):k for k,v in self.parent.pts.items()}
        # change the poly_pts dictionary cordinates
        # to the coresponding node label
        for num in sorted(self.parent.poly_pts):
            k_matx = [0]*(len(self.var_dic)+len(self.parent.pumps))
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
                        k_matx[self.var_dic[ln]] = cos(pi*val[1]) * -1
                        break
            # run through the matrix of all the lines mapped
            # in the plot as specified as part of a node in order to specify
            # the index location for the Kp variable in the loop equations
            # and combine the sign of the direction arrow with the
            # calculated Kp for the line
            for k,v in self.var_dic.items():
                if k in self.K.keys():
                    if self.K[k][0] != 0:
                        k_matx[v] = self.K[k][0] * k_matx[v]
                    else:
                        k_matx[v] = 0.0
            loop_var.append(k_matx)
            loop_cof.append(0)
        return loop_var, loop_cof

    def pseudo_matrix(self, A_var, ho_cof):
        pseudo_var = []
        pseudo_cof = []

        # reverse the key and values in the points dictionary
        # with the cordinates as the key
        # and the node label as the value
        inv_pts = {tuple(v):k for k,v in self.parent.pts.items()}
        # change the poly_pts dictionary cordinates
        # to the coresponding node label
        for num in sorted(self.parent.Pseudo):
            Elev = 0
            skip_0 = False
            skip_1 = False
            rev_sgn = 1

            k_matx = [0]*(len(self.var_dic)+len(self.parent.pumps))
            alpha_poly_pts = []

            # lines starting with a control valve shift the
            # start point and line one position therefore
            # the coefficient signs must be reversed
            if self.parent.Pseudo[num][1][0] in self.parent.vlvs:
                rev_sgn = -1
            # self.Pseudo= {3:[[
                            #  [11.0, 9.0],[11.0, 4.0], [5.0, -9.0], (3.25, -3.75)],
                            #  ['D', 'E', 'F']]}
            # get the corresponding alpha point for
            # each coordinate in the Pseudo loop
            for v in self.parent.Pseudo[num][0]:
                if tuple(v) in inv_pts:
                    alpha_poly_pts.append(inv_pts[tuple(v)])

            for n, ln in enumerate(self.parent.Pseudo[num][1]):
                nd1 = alpha_poly_pts[n]

                if ln in self.parent.vlvs:
                    # convert values of elevation to feet of water
                    # based on elev in ft = psig  * 2.31 * density water / density of fluid
                    # elev' = pressure * 2.31 * 62.4 / density of liquid
                    if self.parent.vlvs[ln][1] == 0:
                        cnvrt = 144.14 / self.density
                    elif self.parent.vlvs[ln][1] == 1:
                        cnvrt = 20.901 / self.density
                    elif self.parent.vlvs[ln][1] == 2:
                        cnvrt = 1
                    elif self.parent.vlvs[ln][1] == 3:
                        cnvrt = 3.28
                    # get the set pressure for any control valve
                    if n == 0:
                        Elev = float(self.parent.vlvs[ln][3]) * cnvrt
                        skip_0 = True
                    else:
                        Elev = -1 * float(self.parent.vlvs[ln][3]) * cnvrt
                        skip_1 = True

                for val in self.parent.nodes[nd1]:
                    if ln in val:
                        if val[1] == 0:
                            k_matx[self.var_dic[ln]] = -1 * rev_sgn
                        elif val[1] == 1:
                            k_matx[self.var_dic[ln]] = 1 * rev_sgn
                        break

            m = 0
            for pt in alpha_poly_pts[::len(alpha_poly_pts)-1]:
                # when m = 0 or the last point is at a tank or pump
                # if it is the first point then the elevation is +
                if (m == 0 and skip_0 is False) or \
                   (m == 1 and skip_1 is False):
                    if m == 0:
                        sgn = 1
                    else:
                        sgn = -1
                    # convert the elevations at the node to feet
                    if pt in self.parent.elevs:
                        if self.parent.elevs[pt][1] == 1:
                            cnvrt = 3.28
                        else:
                            cnvrt = 1
                        Elev = Elev + float(self.parent.elevs[pt][0]) * cnvrt * sgn
                    # convert the pump elevation to feet
                    if pt in self.parent.pumps:
                        if self.parent.pumps[pt][0] == 2:
                            cnvrt = 3.28
                        else:
                            cnvrt = 1
                        Elev = Elev + float(self.parent.pumps[pt][1]) * cnvrt * sgn
                        k_matx[A_var[pt][1]] = A_var[pt][0] * sgn * -1
                        Elev = Elev + ho_cof[pt][0] * sgn
                    elif pt in self.parent.tanks:
                        if int(self.parent.tanks[pt][1]) == 1:
                            cnvrt = 3.28
                        else:
                            cnvrt = 1
                        Elev = Elev + float(self.parent.tanks[pt][0]) * cnvrt * sgn
                m += 1

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
            pseudo_var.append(k_matx)
            pseudo_cof.append(Elev)

        return pseudo_var, pseudo_cof

    def Varify(self, Nl, Np, Nn, Ncl, Npl):
        procd = True

        for ln in self.var_dic:
            if ln not in self.D_e:
                msg1 = 'Pipe data has not been set up for pipe ' + ln
                msg2 = '\nSelect the line letter to complete the information.'
                self.WarnData(msg1 + msg2)
                procd = False
                return[Nn, Ncl, Npl, procd]

        # total number of unknowns is the
        # number of pipelines plus the number of pumps
        Nu = Nl + Np
        # this is the number of equations required to solve for the system

        # pure junction nodes with more than one connection line
        junct_nodes = [node for node, lines
                 in self.parent.nodes.items() if len(lines) > 1]
        # discharge node: the consumption, pump & tank supply line
        consump_runs = {node:lines[0][0] for node, lines
                        in self.parent.nodes.items() if len(lines) == 1}
        # Consumption Lines plus Tank & Pump Supply Lines
        consump_lines = [ln[0] for ln in consump_runs.values()]
        # all the lines not connect to a pump tank or consumption line
        flow_lines = list(set(list(self.parent.runs.keys()))-set(consump_lines))

        # maximum number of potential closed loops
        Max_Ncl = len(flow_lines) - len(junct_nodes) + 1

        # maximum number of pseudo loops
        Max_Npl = (len(self.parent.tanks.keys()) +
                   len(self.parent.pumps.keys()) +
                   len(self.parent.vlvs.keys()) - 1)
        if Max_Npl < 0:
            Max_Npl = 0

        if Ncl > Max_Ncl:
            Ncl = Max_Ncl
        if Npl > Max_Npl:
            Npl = Max_Npl

        # check that there is the correct number of defined equation to proceed
        # if there are no pumps, tanks or CVs one node needs to be removed
        # and Nu = Nn + Nl
        if self.parent.pumps == {} and \
           self.parent.tanks == {} and \
           self.parent.vlvs == {}:
            if Nn == len(junct_nodes):
                Nn -= 1

            if Nu > Nn + Ncl:
                msg1 = ('A total of ' + str(Nu) +
                        ' unknowns have been declared.\n')
                msg2 = 'This means there should be ' + str(Nu - Nn)
                msg3 = ' nodes defined.\n'
                msg4 = 'If a node is not shaded in'
                msg5 = 'the grid\nit means it has not been defined.'
                self.WarnData(msg1 + msg2 + msg3 + msg4 + msg5)
                procd = False
#                Nn -= 1
#                return[Nn, procd]
        # if there is only one supply source then use all the nodes
        # and any closed loops
        elif (len(self.parent.pumps) +
              len(self.parent.tanks) +
              len(self.parent.vlvs)) == 1:
            if Nu > Nn + Ncl:
                msg1 = ('A total of ' + str(Nu) +
                        ' unknowns have been declared.\n')
                msg2 = 'This means there should be ' + str(Nu - Nn)
                msg3 = ' nodes defined.\n'
                msg4 = 'If a node is not shaded in'
                msg5 = 'the grid\nit means it has not been defined.'
                self.WarnData(msg1 + msg2 + msg3 + msg4 + msg5)
                procd = False
#                return[Nn, procd]
        # not enough data request additional information based on
        # multiple pumps, tanks and valves or the possible addition of pseudo loops
        else:
            if Nu > (Nn + Ncl + Npl + Np):
                msg3 = ''
                msg4 = ''
                if Ncl < Max_Ncl:
                    msg3 = ('\nThere is potential for '
                            + str(Max_Ncl) + ' closed loops, ')
                    msg4 = str(Ncl) + ' have been defined.'
                if Npl < Max_Npl:
                    msg3 = (msg3 + msg4 + '\nThere is a potential for '
                            + str(Max_Npl) + ' pseudo loops, ')
                    msg4 = str(Npl) + ' have been defined'
       
                msg1 = ('A total of ' + str(Nu) +
                        ' unknowns have been declared but only ')
                msg2 = (str(Nn + Ncl + Npl + Np) +
                    ' equations have been specified.\n')
                msg5 = 'Confirm that all the nodes\nhave been shaded in the grid.'
                self.WarnData(msg1 + msg2 + msg3 + msg4)
                procd = False
#                return[Nn, procd]

        return[Nn, Ncl, Npl, procd]

    def Save_Output(self):
        # clear data from table
        Dsql = 'DELETE FROM output'
        DBase.Dbase(self).TblEdit(Dsql)
        # build sql to add rows to table
        Insql = 'INSERT INTO output (ID, Flow) VALUES(?,?);'
        # convert the tuple inside the dictionary to a string
        Indata = [(i[0], str(i[1])) for i in list(self.Q_old.items())]
        DBase.Dbase(self).Daddrows(Insql, Indata)

    def WarnData(self, msg):
        dialog = wx.MessageDialog(self.parent, msg, 'Data Error',
                                  wx.OK|wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()
