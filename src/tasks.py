import pyodbc
import xlsxwriter
import pandas as pd
from datetime import datetime 
from decimal import Decimal
from settings import db_server, db_pms, db_user, db_pswd, db_2021

xlsFormat = {
				'caption' : { 'bold' : True },
				'header'  : { 'font_size' : 10, 'align' : 'center', 'bg_color' : '#4caf50', 'border' : 2, 'font_color' : 'white' },
				'font'    : { 'font_name' : 'Times New Roman', 'font_size' : 12 },
				'str'	  : { 'align' : 'left' },
				'datetime': { 'num_format' : 'dd-mmm-yyy'},
				'decimal' : { 'num_format' : '[Black]#,##0.0000;[Red]-#,##0.0000'},
				'int'     : { 'num_format' : '[Black]General;[Red]-General;General' },
				'float'   : { 'num_format' : '[Black]#,##0.0000;[Red]-#,##0.0000' } }

class sqlConn(object):
	def __init__(self, server, database, user, pwd):
		self.sqlString = 'DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+user+';PWD='+ pwd

	def __enter__(self):
		self.conn = pyodbc.connect(self.sqlString)
		self.cursor = self.conn.cursor()
		return self.cursor

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.cursor.close()
		self.conn.close()

def get_fifo_cap_gains(customerName, fyYear, fileName):

	query = "set nocount on; exec [dbo].[procFIFOCapitalGain] @Investor_Name = ?"
	params = (customerName)
	fy = int(fyYear)
	start = '{0:d}-04-01'.format(fy)
	end = '{0:d}-03-31'.format(fy+1)
	
	print(start, end)

	df = None
	with sqlConn(db_server, db_pms, db_user, db_pswd) as cur:
		vers = cur.execute("SELECT @@version;")
		cur.execute(query, params)
		cols = [col[0] for col in cur.description]
		rows = cur.fetchall()
		df = pd.DataFrame.from_records(rows, columns=cols, coerce_float=True)

	df_fy = df[df["S_Trdt"].isin(pd.date_range(start, end))].copy()

	# strip whitespace from strings
	for col in df_fy.columns:
		if df_fy[col].dtype == object:
			df_fy[col] = df_fy[col].str.strip()

	# get index of column	
	#print(df.columns.get_loc('S_Trdt'))

	# print all column data types
	#print(df.dtypes)

	# select columns that are string
	#df_str = df.select_dtypes(include='object')

	# print one column after stripping whitespaces
	#print(df_str['Company_Name'].str.strip().to_string())

	# filter by financial year

	# convert these columns to float
	#df_fy['Short_Normal_Capital_Gain'] = df['Short_Normal_Capital_Gain'].astype(float)
	#df_fy['Long_Normal_Capital_Gain'] = df['Long_Normal_Capital_Gain'].astype(float)

	cust_name = df_fy['Investor_Name'].values[0]
	cust_pan = df_fy['Pan_No'].values[0]

	# remove these columns
	df_fy.drop(['Investor_Name', 'Pan_No'], axis=1, inplace=True)
	cols.remove('Investor_Name')
	cols.remove('Pan_No')
	
	caption = { 'Customer Name' : cust_name, 'FY' : fyYear }

	savecapgainas_xls(df_fy, caption, fileName)
	
	df_fy = df_fy.astype(str)
	rows = df_fy.values.tolist()

	return { 'cols' : cols, 'rows' : rows }

def savecapgainas_xls(df, caption, fileName):

	start_row = len(caption)
	start_col = 1

	# Create a Pandas Excel writer using XlsxWriter as the engine.
	writer = pd.ExcelWriter(fileName, engine='xlsxwriter', date_format='dd-mmm-yyyy', datetime_format='dd-mmm-yyyy')

	df.to_excel(writer, sheet_name='capital_gains', startrow=start_row, startcol=start_col, index=False, float_format="%.4f");
	
	df_stcg = df[df["Gain_Type"] == 'ShortTerm'].copy()
	df_stcg.drop(['Gain_Type', 'Gain_Calc_Type'], axis=1, inplace=True)
	df_stcg.to_excel(writer, sheet_name='short_term', startrow=2, startcol=1, index=False, float_format="%.4f");

	df_ltcg = df[df["Gain_Type"] == 'LongTerm'].copy()
	df_ltcg.drop(['Gain_Type'], axis=1, inplace=True)
	df_ltcg.to_excel(writer, sheet_name='long_term', startrow=2, startcol=1, index=False, float_format="%.4f");

	wb = writer.book
	ws1 = writer.sheets['capital_gains']
	ws2 = writer.sheets['short_term']
	ws3 = writer.sheets['long_term']

	# Apply formats to the workbook
	wb.formats[0].set_font_name('Times New Roman')
	wb.formats[0].set_font_size(10)
	
	fmtCaption = wb.add_format(xlsFormat['caption'])
	for i, (k,v) in enumerate(caption.items()):
		ws1.write(i, 1, k, fmtCaption)
		ws1.write(i, 2, v, fmtCaption)
	
	fmtHeader = wb.add_format(xlsFormat['header'])
	ws1.conditional_format(start_row, start_col, start_row, len(df.columns), {'type': 'no_blanks', 'format': fmtHeader})
	ws2.conditional_format(start_row, start_col, start_row, len(df_stcg.columns), {'type': 'no_blanks', 'format': fmtHeader})
	ws3.conditional_format(start_row, start_col, start_row, len(df_ltcg.columns), {'type': 'no_blanks', 'format': fmtHeader})

	fmtCells = wb.add_format({'border' : 1})
	ws1.conditional_format(start_row+1, start_col, start_row+len(df), start_col+len(df.columns)-1, {'type': 'no_blanks', 'format': fmtCells})
	ws1.conditional_format(start_row+1, start_col, start_row+len(df), start_col+len(df.columns)-1, {'type': 'blanks', 'format': fmtCells})
	ws2.conditional_format(start_row+1, start_col, start_row+len(df_stcg), start_col+len(df_stcg.columns)-1, {'type': 'no_blanks', 'format': fmtCells})
	ws2.conditional_format(start_row+1, start_col, start_row+len(df_stcg), start_col+len(df_stcg.columns)-1, {'type': 'blanks', 'format': fmtCells})
	ws3.conditional_format(start_row+1, start_col, start_row+len(df_ltcg), start_col+len(df_ltcg.columns)-1, {'type': 'no_blanks', 'format': fmtCells})
	ws3.conditional_format(start_row+1, start_col, start_row+len(df_ltcg), start_col+len(df_ltcg.columns)-1, {'type': 'blanks', 'format': fmtCells})

	fmtFormula = wb.add_format({'border' : 1, 'font_color' : 'blue', 'bold' : True})
	fmtFormula.set_align('left')

	start_idx = df.columns.get_loc('Short_Normal_Capital_Gain')
	for idx in range(start_idx, start_idx+4, 1):
		f = xlsxwriter.utility.xl_rowcol_to_cell(start_row+1, start_col+idx)
		s = xlsxwriter.utility.xl_rowcol_to_cell(start_row+len(df), start_col+idx)
		ws1.write_formula(start_row+len(df)+1, start_col+idx, '=SUM({}:{})'.format(f, s), fmtFormula)
	
	fmtCol = wb.add_format({'align' : 'left'})
	for i, col in enumerate(df.columns):
		col_width = max(df[col].astype(str).str.len().max(), len(col))
		ws1.set_column(start_col+i, start_col+i, col_width+5, fmtCol)
		
	for i, col in enumerate(df_stcg.columns):
		col_width = max(df_stcg[col].astype(str).str.len().max(), len(col))
		ws2.set_column(start_col+i, start_col+i, col_width+5, fmtCol)

	for i, col in enumerate(df_ltcg.columns):
		col_width = max(df_ltcg[col].astype(str).str.len().max(), len(col))
		ws3.set_column(start_col+i, start_col+i, col_width+5, fmtCol)

	# save to file
	print("Saving to {}".format(fileName))
	writer.save()

def get_bill_ledger_comp(date, fileName):

	query = "exec [dbo].[procBillLedgerComp] @DateParam = ?"
	params = (date)
	
	df = None
	with sqlConn(db_server, db_pms, db_user, db_pswd) as cur:
		vers = cur.execute("SELECT @@version;")
		cur.execute(query, params)
		cols = [col[0] for col in cur.description]
		rows = cur.fetchall()
		df = pd.DataFrame.from_records(rows, columns=cols, coerce_float=True)

	# select columns that are string
	#df_str = df.select_dtypes(include='object')
	
	for col in df.columns:
		if df[col].dtype == object:
			df[col] = df[col].str.strip()

	saveledgeras_xls(df, fileName)

	df = df.astype(str)
	rows = df.values.tolist()

	return { 'cols' : cols, 'rows' : rows }

def saveledgeras_xls(df, fileName):

	# Create a Pandas Excel writer using XlsxWriter as the engine.
	writer = pd.ExcelWriter(fileName, engine='xlsxwriter', date_format='yyyy-mm-dd', datetime_format='yyyy-mm-dd')

	df.to_excel(writer, sheet_name='bill_ledger', index=False, float_format="%.4f");
	
	wb = writer.book
	ws = writer.sheets['bill_ledger']
	
	# Apply formats to the workbook
	wb.formats[0].set_font_name('Times New Roman')
	wb.formats[0].set_font_size(10)
	
	fmtHeader = wb.add_format(xlsFormat['header'])
	ws.conditional_format(0, 0, 0, len(df.columns), {'type': 'no_blanks', 'format': fmtHeader})
	
	fmtCol = wb.add_format({'border' : 1})
	fmtCol.set_align('left')
	for i, col in enumerate(df.columns):
		col_width = max(df[col].astype(str).str.len().max(), len(col))
		col_width += 5
		ws.set_column(i, i, col_width, fmtCol)

	writer.save()

def get_customer_names():

	names = list()
	with sqlConn(db_server, db_2021, db_user, db_pswd) as cur:
		cur.execute("SELECT DESCR FROM dbo.DLMAST;")
		rows = cur.fetchall()
		names = [str(row[0]).strip().title() for row in rows]

	return(names)

def main():
	customer = "SATISH RANGA"
	fy = "2015"
	#get_fifo_cap_gains(customer, fy, "downloads/test.xlsx")
	get_customer_names()

if __name__ == '__main__':
	main()
