import sqlite3


class Dbase(object):
    '''DATABASE CLASS HANDLER'''
    # this initializes the database and opens the specified table
    def __init__(self, frmtbl=None):
        # this sets the path to the database and needs
        # to be changed accordingly

        self.db = sqlite3.connect('mt.db')
        with self.db:
            self.cursr = self.db.cursor()
            self.cursr.execute('PRAGMA foreign_keys=ON')

#        self.cursr = cursr
#        self.db = db

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

    def Daddrows(self, InQuery, Rcrds):
        self.cursr.executemany(InQuery, Rcrds)
        self.db.commit()

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