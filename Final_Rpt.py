import os
from math import log10
import numpy as np
import PDF_Rpt
    
class Report_Data(object):

    def __init__(self, parent, filename, Qs, D_e, density, kin_vis, abs_vis):
        self.parent = parent
        
        ttl = os.path.basename(filename)
        self.ttl = 'Calculated Data for ' + ttl
        self.filename = filename[:-2] + 'pdf'

        self.Flows = Qs
        self.D_e = D_e

        self.density = density
        self.kin_vis = kin_vis
        self.abs_vis = abs_vis
        self.head_loss = {}

    def tbl_data(self):

        rptdata = []

        # information regarding fluid properties
        rptdata.append(self.density)
        rptdata.append(self.abs_vis)
        rptdata.append(self.kin_vis)

        # Information for the lines table
        self.tbldata1 = [('Line\nLabel', 'Pipe Dia\ninches', 'Pipe Length\nfeet',
                      'Flow\nft^3/s', '\nUSGPM', '\nm^3/s', 'Head Loss\nft',
                      'meters', 'Pressure Drop\npsid',
                      'Velocity\nft/s', '\nm/s')]

        Colwdths1 = [6, 8, 10, 8, 8, 8, 8, 8, 12, 8, 6]

        rptdata1 = self.tbl_lines()

        # information for the nodes table
        self.tbldata2 = [('Node\nLabel', 'Head\nfeet', '\nmeters',
                      'Pressure\npsig', '\nkPa')]

        Colwdths2 = [6, 8, 8, 8, 8]

        rptdata2 = self.tbl_nodes()

        # information for the pump table
        self.tbldata3 = [('Pump\nNode', 'Head\nfeet', '\nmeters',
                      'Flow\nUSGPM', '\nm^3/hr')]

        Colwdths3 = [6, 8, 8, 8, 8]

        rptdata3 = self.tbl_pumps()

        # information for the control valves
        Colnames4 = [('Line\nLabel', 'Set\nfeet', 'Pressure\npsig',
                      'Upstream\nfeet', 'Pressure\npsig','Downstream\nfeet',
                      'Pressure\npsig')]

        Colwdths4 = [8, 8, 8, 8, 8, 8, 8]

        self.tbl_Cvlvs()

        PDF_Rpt.Report(rptdata1, Colwdths1,
                       rptdata2, Colwdths2,
                       rptdata3, Colwdths3,
                       self.filename, self.ttl).create_pdf()

    def tbl_lines(self):
        # output for the flows, hL etc for each line

        ELOG = 9.35 * log10(2.71828183)

        for lbl, flow in self.Flows.items():
            gpm = flow * 448.83
            dia = self.D_e[lbl][0]
            Dia = dia / 12
            lgth = (self.D_e[lbl][4] + self.D_e[lbl][5])
            # convert absolute roughness to relative roughness
            er = self.D_e[lbl][1] / dia
            vel = .408 * abs(gpm) / dia**2
            Re = 123.9 * dia * vel * self.density / self.abs_vis
            if Re <= 2100:
                f = 64 / Re
                hL = (.0962 * self.abs_vis * lgth * vel /
                        (dia**2 * self.density))
                delta_P = (.000668 * self.abs_vis * lgth * vel / dia**2)
            else:
                f = 1 / (1.14 - 2*log10(er))**2
                PAR = vel *(.125 * f)**.5 * Dia * er / self.kin_vis
                if PAR <= 65:
                    MCT = 0
                    while True:
                        # Colebrook Friction Factor for turbulent flow
                        ARG = er + 9.35 / (Re * f**.5)
                        FF = (1 / f**.5) - 1.14 + 2 * log10(ARG)
                        DF = 1 / (2 * f * f**.5) + ELOG / 2 * (f * f**.5 * ARG * Re)
                        DIF = FF / DF
                        f = f + DIF
                        MCT += 1
                        if (abs(DIF) < .00001 or MCT > 15):
                            break
                hL = .1863 * f * lgth * vel**2 / dia
                delta_P = .001294 * f * lgth * self.density * vel**2 / dia

            self.head_loss[lbl] = hL

            rptdata = []
            rptdata.append(lbl)
            rptdata.append(round(dia,2))
            rptdata.append(round(lgth,2))
            rptdata.append(round(flow,3))
            rptdata.append(round(gpm,2))
            rptdata.append(round(flow * .028316,3))
            rptdata.append(round(hL,3))
            rptdata.append(round(hL * .3048,3))
            rptdata.append(round(delta_P,2))
            rptdata.append(round(vel,2))
            rptdata.append(round(vel * .3048, 2))

            self.tbldata1.append(rptdata)

        return self.tbldata1

    def tbl_nodes(self):

        # output of pressure at each node
        elev = self.parent.elevs
        self.node_press = {}
        # get all the nodes which are not consumption points
        junct_nodes = [node for node, lines
                 in self.parent.nodes.items() if len(lines) > 1]
        # all the consumption, pump & tank supply lines
        consump_runs = {node:lines[0][0] for node, lines
                        in self.parent.nodes.items() if len(lines) == 1}
        consump_lines = [ln[0] for ln in consump_runs.values()]

        pump_nodes = list(self.parent.pumps.keys())
        tank_nodes = list(self.parent.tanks.keys())
        flow_nodes = junct_nodes + pump_nodes + tank_nodes
        flow_nodes.sort()
        all_nodes = [node for node, _ in self.parent.nodes.items()]
        # all the lines not connect to a pump tank or consumption line
        flow_lines = list(set(list(self.parent.runs.keys()))-set(consump_lines))
        # list of none junction comsumption nodes
        consump_nodes = list(set(all_nodes) - set(flow_nodes))
        consump_nodes.sort()

        # if there is a pump of tank at the node
        if pump_nodes != [] or tank_nodes != []:
            to_do_nodes = []
            done_nodes = []
            if pump_nodes != []:
                for pmp in range(len(pump_nodes)):
                    # get the pump discharge head plus the fluid elevation
                    start_nd = pump_nodes[pmp]

                    # convert elevation to feet
                    if elev[start_nd][1] == 0:
                        el = float(elev[start_nd][0])
                    elif elev[start_nd][1] == 0:
                        el = float(elev[start_nd][0]) * 3.3

                    ln = consump_runs[start_nd]
                    hd = float(self.pump_tdh(start_nd, ln)[0])
                    self.node_press[start_nd] = hd + el
                    done_nodes.append(start_nd)
                    # get the end points for the pump discharge line
                    pt1, pt2 = self.parent.runs[consump_runs[start_nd]][0]

                    if pt1 == start_nd:
                        self.node_press[pt2] = self.node_press[start_nd] -\
                                          self.head_loss[consump_runs[start_nd]]
                        start_nd = pt2
                        done_nodes.append(pt2)
                    else:
                        self.node_press[pt1] = self.node_press[start_nd] - \
                                          self.head_loss[consump_runs[start_nd]]
                        start_nd = pt1
                        done_nodes.append(pt1)

                    to_do_nodes.append(start_nd)

            if tank_nodes != []:
                for tk in range(len(tank_nodes)):
                    start_nd = tank_nodes[tk]

                    # convert elevation to feet
                    if elev[start_nd][1] == 0:
                        el = float(elev[start_nd][0])
                    elif elev[start_nd][1] == 0:
                        el = float(elev[start_nd][0]) * 3.3

                    # get the tank fluid elevation
                    v = self.parent.tanks[start_nd]
                    if v[1] == 2:
                        hd = v[0] * 3.28
                    else:
                        hd = v[0]

                    self.node_press[start_nd] = hd + el
                    done_nodes.append(start_nd)

                    # get the end points for the pump discharge line
                    pt1, pt2 = self.parent.runs[consump_runs[start_nd]][0]
                    if pt1 == start_nd:
                        self.node_press[pt2] = self.node_press[start_nd] - \
                                          self.head_loss[consump_runs[start_nd]]
                        start_nd = pt2
                        done_nodes.append(pt2)
                    else:
                        self.node_press[pt1] = self.node_press[start_nd] - \
                                          self.head_loss[consump_runs[start_nd]]
                        start_nd = pt1
                        done_nodes.append(pt1)

                    to_do_nodes.append(start_nd)

            n = 0

            while len(to_do_nodes) > 0:
                if n == 50:
                    break
                start_nd = to_do_nodes[0]
                # get all the flow lines at the node and
                # direction of flow at node (1 is out)
                nd_lines = [(ln[0], ln[1]) for ln in
                             self.parent.nodes[start_nd] if ln[2]==0]
                # remove the start node from the to do nodes
                # since it has been completed
                to_do_nodes.remove(start_nd)

                for line in nd_lines:
                    if line[0] in flow_lines:
                        # get the end points of the line
                        ends = list(self.parent.runs[line[0]][0])
                        # remove the start_nd from the line end points and
                        # add the remaining pt to the to do list of nodes
                        ends.remove(start_nd)
                        if ends[0] not in to_do_nodes:
                            to_do_nodes.extend(ends)
      
                        # check that the specified flow direction is
                        # correct if it is not then reverse
                        # additon of the line loss
                        if self.Flows[line[0]] >= 0:
                            sgn = 1
                        else:
                            sgn = -1

                        # determine if all the nodes have been completed
                        if list(set(flow_nodes)-set(done_nodes)) == []:
                            to_do_nodes = []
                            break        

                        # add or subtract the line loss from the nodes pressure
                        # to pressure at the other end node
                        if line[1] == 1:
                            self.node_press[ends[0]] = (self.node_press[start_nd] - \
                                                   self.head_loss[line[0]] * sgn)
                            done_nodes.append(ends[0])
                        elif line[1] == 0:
                            self.node_press[ends[0]] = (self.node_press[start_nd] + \
                                                  self.head_loss[line[0]] * sgn)
                            done_nodes.append(ends[0])
                        flow_lines.remove(line[0])

                    if flow_lines == []:
                        to_do_nodes = []
                        break
                n += 1

        for nd, val in self.node_press.items():
            rptdata = []
            rptdata.append(nd)
            rptdata.append(round(val,3))
            rptdata.append(round(val * .3048,2))
            rptdata.append(round(val * self.density / (62.4*2.307),2))
            rptdata.append(round(val * self.density/ (62.4*2.307) * 6.895,2))
            
            self.tbldata2.append(rptdata)

        return self.tbldata2

    def tbl_pumps(self):

        # dictionary by node of all lines that have unshared junctions
        consump_runs = {node:lines[0][0] for node, lines
                        in self.parent.nodes.items() if len(lines) == 1}        

        pump_nodes = list(self.parent.pumps.keys())

        if pump_nodes != []:
            for pmp in range(len(pump_nodes)):
                rptdata = []
                # get the pump discharge head plus the fluid elevation
                start_nd = pump_nodes[pmp]
                ln = consump_runs[start_nd]
                hd = float(self.pump_tdh(start_nd, ln)[1])
                rptdata.append(start_nd)
                rptdata.append(round(hd,3))
                rptdata.append(round(hd * .3048,3))
                rptdata.append(round(self.Flows[ln] * 448.8,3))
                rptdata.append(round(self.Flows[ln] * 101.94,3))

                self.tbldata3.append(rptdata)

        return self.tbldata3

    def tbl_Cvlvs(self):
        for ln, cv in self.parent.vlvs.items():

            if cv[0] == 0:
                typ = 'PRV'
            else:
                typ = 'BPV'

            # set pressure saved as psig
            if cv[2] == 0:
                press = cv[3] * self.density / (62.4*2.307)
            # set pressure saved as kPa
            elif cv[2] == 1:
                press = cv[3] * self.density/ (62.4*2.307) * 6.895
            # set pressure saved as feet of water
            else:
                press = cv[3]


    def pump_tdh(self, nd, ln):
        v = self.parent.pumps[nd]
        # convert the flow to ft^3/s and TDH to ft
        # [ v[0] = 0    ,    v[0] = 1   ,  v[0] = 2]
        # ['US GPM & ft', 'ft^3/s & ft', 'm^3/hr & m']
        if v[0] == 0:
            f = .00223
            t = 1
        elif v[0] == 1:
            f = 1
            t = 1
        elif v[0] == 2:
            f = .0098
            t = 3.28

        pump_Flow = np.array([v[2]*f,v[3]*f,v[4]*f])
        pump_TDH = np.array([v[5]*t,v[6]*t,v[7]*t])

        A, B, Ho = np.polyfit(pump_Flow, pump_TDH, 2)

        flow = self.Flows[ln]

        Ho = (A * flow**2 + B * flow + Ho)
        TDH = Ho  + v[1]*t

        return TDH, Ho
