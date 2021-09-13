import wx
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate,\
     Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
import os


class LineDrw(Flowable):

    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def __repr__(self):
        return "Line(w=%s)" % self.width

    def draw(self):
        self.canv.line(0, self.height, self.width, self.height)


class Report:

    def __init__(self,
                 rptdata1, Colwdths1, col_spans1,
                 rptdata5, Colwdths5,
                 rptdata2, Colwdths2, col_spans2,
                 rptdata3, Colwdths3, col_spans3,
                 rptdata4, Colwdths4, col_spans4,
                 filename, ttl):
        # (table name, table data, table column names, table column
        # widths, name of PDF file)
        self.rptdata1 = rptdata1
        self.Colwdths1 = Colwdths1
        self.col_spans1 = col_spans1

        self.rptdata5 = rptdata5
        self.Colwdths5 = Colwdths5

        self.rptdata2 = rptdata2
        self.Colwdths2 = Colwdths2
        self.col_spans2 = col_spans2

        self.rptdata3 = rptdata3
        self.Colwdths3 = Colwdths3
        self.col_spans3 = col_spans3

        self.rptdata4 = rptdata4
        self.Colwdths4 = Colwdths4
        self.col_spans4 = col_spans4

        self.filename = filename
        self.ttl = ttl
        self.width, self.height = letter

    def create_pdf(self):
        body = []
        textAdjust = 6.5

#        doc_name = os.path.basename(self.filename)

        doc = SimpleDocTemplate(
            self.filename, pagesize=letter,
            rightMargin=.5*inch, leftMargin=.5*inch, topMargin=.75*inch,
            bottomMargin=.5*inch)

        styles = getSampleStyleSheet()
        spacer2 = Spacer(0, 0.5*inch)

        tblstyle = TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])

        # provide the table name for the page header
        ptext = '<font size=14>%s</font>' % self.ttl
        body.append(Paragraph(ptext, styles["Heading2"]))

        for n in range(5):
            if n == 0:
                rptdata = self.rptdata1
                colwdth = self.Colwdths1
                spn = self.col_spans1
            elif n == 1:
                rptdata = self.rptdata2
                colwdth = self.Colwdths2
                spn = self.col_spans2
            elif n == 2:
                rptdata = self.rptdata3
                colwdth = self.Colwdths3
                spn = self.col_spans3
            elif n == 3:
                rptdata = self.rptdata4
                colwdth = self.Colwdths4
                spn = self.col_spans4
            elif n == 4:
                rptdata = self.rptdata5
                colwdth = self.Colwdths5

            # table style for all but the fittings table
            if len(rptdata) > 2 and n < 4:
                colwd = [i * textAdjust for i in colwdth]
                tbl1 = Table(rptdata, colWidths=colwd, style=spn)
                tbl1.setStyle(tblstyle)
                body.append(KeepTogether(tbl1))
                body.append(spacer2)
            # print only the fittings table which contain data
            elif n == 4 and len(rptdata) >= 1:
                for lst in rptdata:
                    colwd = [i * textAdjust for i in colwdth]
                    tbl1 = Table(lst, colWidths=colwd)
                    tbl1.setStyle(tblstyle)
                    body.append(KeepTogether(tbl1))
                    body.append(spacer2)

        doc.build(body)
      