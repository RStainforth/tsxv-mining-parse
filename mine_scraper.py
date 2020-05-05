#!/usr/bin/env python

#################################################
#################################################
# Author: Rob/HypnoFunk
# Date: February 8th, 2020
# Last Updated: May 4th, 2020
#################################################
#################################################

# Import the necessary modules
import os
from os import path
import sys
import string
import math # standard math library
from math import sqrt, pow, isnan
import seaborn as sns # Seaborn
import pandas as pd # Pandas for Data Frames
import numpy as np # Numpy
from numpy import linspace
import matplotlib # MatPlotLib
import matplotlib.pyplot as plt # MatPlotLib
import scipy
from scipy.interpolate import BSpline
from scipy.interpolate import interp1d
from scipy.stats.distributions import t as tdist
from scipy import stats
import operator

from bs4 import BeautifulSoup
import json
import requests
import datetime
import glob
import time

#################################################################
#################################################################

def get_managers_dict( href_link, out_file ):
	
	time.sleep(5)
	response = ''
	while response == '':
		try:
			response = requests.get("https://www.marketscreener.com"+href_link+"company/")
			break
		except:
			print( "Error in connection, will sleep" )
			time.sleep(5)
	data = response.text
	soup = BeautifulSoup( data, "html.parser" )
	
	top_tables = soup.find_all('table', {"class": "nfvtTab"})
	index_dict = {}
	for t in top_tables:
		table_rows = t.find_all('tr')
		res = []
		for tr in table_rows:
			if ( table_rows.index(tr) == 0 ):
				continue
			td = tr.find_all('td')
			row = [tr.text.strip() for tr in td if tr.text.strip()]
			if row:
				res.append(row)
		print(res)
		if ( res[0][0] == 'Managers' ):
			index_dict['Managers'] = top_tables.index(t)
		if ( res[0][0] == 'Shareholders' ):
			index_dict['Shareholders'] = top_tables.index(t)
		
	tables_arr = soup.find_all('table', {"class": "nfvtTab"})
	
	#print(tables_arr)
	
	df_arr = []
	total_inside = 0.0
	
	n_tables = len(tables_arr)
	
	for iT in range( 0, len( tables_arr ) ):
		top_table_rows = tables_arr[iT].find_all('tr')
		top_tr = top_table_rows[0]
		top_td = top_tr.find_all('td')
		top_row = [tr.text.strip() for tr in top_td if tr.text.strip()]
		print("top row length: "+str(len(top_row)))
		print("top row [2]: "+str(top_row))
		if ( ((len(top_row) == 4) and str(top_row[2])=="Since") ):
			col_arr = ['Name', 'Age', 'Since', 'Title']
			table_rows = tables_arr[iT].find_all('tr')
	
			res = []
			for tr in table_rows:
				if ( table_rows.index(tr) == 0 ):
					continue
				td = tr.find_all('td')
				row = [tr.text.strip() for tr in td if tr.text.strip()]
				if row:
					res.append(row)
			
			df = pd.DataFrame(res, columns=col_arr)
			df_arr.append(df)
		if ( ((len(top_row) == 3) and str(top_row[1])=="Equities") ):
			col_arr = ['Name', 'Equities', '%']
			table_rows = tables_arr[iT].find_all('tr')
	
			res = []
			for tr in table_rows:
				if ( table_rows.index(tr) == 0 ):
					continue
				td = tr.find_all('td')
				row = [tr.text.strip() for tr in td if tr.text.strip()]
				if row:
					res.append(row)
			
			df = pd.DataFrame(res, columns=col_arr)
			df_arr.append(df)
	
	#print("management and inside ownership")
	#out_file.write("management and inside ownership\n")
	
	#print("Total inside ownership: "+str(total_inside)+" %")
	#out_file.write("Total inside ownership: "+str(total_inside)+" %\n")
	
	#print("Management")
	#out_file.write("\nManagement\n")
	
	man_arr = []
	own_dict = {}
	print(str(len(df_arr)))
	if ( len(df_arr) == 0 ):
		return {}
	for index, row in df_arr[0].iterrows():
		cur_name = str(row['Name'])
		if ( cur_name in man_arr ):
			continue
		else:
			man_arr.append(cur_name)
	
	man_str = "Management: "
	for im in range( 0, len(man_arr) ):
		man_str += man_arr[im]
		if ( im < len(man_arr)-1 ):
			man_str += ", "
	man_str += "\n"
	if ( len(man_arr) > 0 ):
		print(man_str)
		out_file.write(man_str)
	else:
		print("No management information provided")
		out_file.write("No management informaiton provided\n")	
	
	if ( len(df_arr) <= 1 ):
		return {}
		
	for index, row in df_arr[1].iterrows():
		cur_name = str(row['Name'])
		cur_hold = 0.0
		try:
			cur_hold = float(row['%'].split('%')[0])
		except ValueError:
			cur_hold = 0.0
		if ( cur_name in own_dict ):
			own_dict[cur_name] += cur_hold
		else:
			own_dict[cur_name] = cur_hold
	
	total_inside = 0.0
	for d in own_dict:
		total_inside += own_dict[d]
	if ( len(own_dict) > 0 ):
		total_str = "%.2f" % total_inside
		print("Total insider ownership: "+total_str +" %")
		out_f.write("Total insider ownership: "+total_str +" %\n")
		
	return {}
	
#################################################################
#################################################################

if __name__ == '__main__':

	# Spreadsheet available through: https://www.tsx.com/listings/current-market-statistics
	# The path the input excel spreadsheet
	cur_path = "mine_list_april_2020.xlsx"
	cur_df = pd.read_excel(cur_path, sheet_name='TSXV Issuers March 2020')
	print(cur_df)
	
	start_index = int(sys.argv[1])
	end_index = int(sys.argv[2])
	
	
	out_f = open("company_list_index_"+str(start_index)+"_"+str(end_index)+".txt", 
	 'w')
	
	n_comp = 0
	mining_index = -1
	
	# Loop through the rows of the excel spreadsheet for the sheet
	# names 'TSXV MM Issuers March 2020' as above.
	for index, row in cur_df.iterrows():
		
		if ( str(row['Sector']) != "Mining" ):
			continue
		
		mining_index += 1
		if ( mining_index < start_index or mining_index >= end_index ):
			continue
		
		print("processing line: "+str(mining_index))
		# We only want companies with a project in Canada
		# or the US, excluding companies in the BC region
		# of Canada (i.e. golden triangle)
		if ( ((str(row['CANADA']) != ""
			 and str(row['CANADA']) != "nan"
			 and str(row['CANADA']).find("BC") < 0)
			 or
			 (str(row['USA']) != ""
			 and
			  str(row['USA']) != "nan"))
			 and
			 float(row['QMV (C$)\n31-March-2020']) < 5e6 ):
			 	#if ( n_comp > 5 ):
			 	#	break
			 	cur_name = row['Name']
			 	cur_mcap_str = "%.2f" % (float(row['QMV (C$)\n31-March-2020'])/1.0e6)
			 	
			 	print("Name: "+cur_name+", MCAP ($000,000 CAD): "+cur_mcap_str)
			 	out_f.write("Name: "+cur_name+"\n")
			 	out_f.write("MCAP ($000,000 CAD): "+cur_mcap_str+"\n")
			 	
			 	if ( row['CANADA'] != "" and str(row['CANADA']) != "nan" ):
			 		print("Canada projects: "+str(row['CANADA']))
			 		out_f.write("Canada projects: "+str(row['CANADA'])+"\n")
			 		
			 	if ( row['USA'] != "" and str(row['USA']) != "nan" ):
			 		print("USA projects: "+str(row['USA']))
			 		out_f.write("USA projects: "+str(row['USA'])+"\n")
			 	
			 	response = ""
			 	name_arr = str(row['Name']).split(' ')
			 	q_str = ""
			 	for i in range(0,len(name_arr)):
			 		q_str += name_arr[i]
			 		if ( i != len(name_arr)-1 ):
			 			q_str += "+"
			 	#print('q_str = '+q_str)
			 	while response == '':
			 		try:
			 			response = requests.get("https://www.marketscreener.com/search/?aComposeInputSearch=s_"+q_str)
			 			print( "Visiting: " + "https://www.marketscreener.com/search/?aComposeInputSearch=s_"+q_str )
			 			break
			 		except:
			 			print( "Error in connection, will sleep" )
			 			response = "NAN"
			 			break
			 	if ( response == "NAN" ):
			 		print("Error querying database")
			 		continue
			 		
			 	data = response.text
			 	for l in response.iter_lines():
			 		
			 		if ( str(l).find('codezb') > 0
			 			 and str(l).find('title="CA"') > 0
			 			 and (str(l).lower()).find('venture') > 0 ):
			 			 	soup = BeautifulSoup( str(l), "html.parser" )
			 			 	cur_a = str(soup.find_all('a')[0])
			 			 	cur_a = cur_a.split('href="')[1]
			 			 	cur_a = cur_a.split('"><b>')[0]
			 			 	print(cur_a)
			 			 	managers_dict = get_managers_dict(cur_a, out_f)
			 	time.sleep(5)
			 	print("-------------------------------------------")
			 	out_f.write("-------------------------------------------\n")
			 	n_comp += 1
			 	#soup = BeautifulSoup( response.text, "lxml" )
			 	#my_tables = soup.find_all('tr')
			 	#for t in my_tables:
			 	#	if ( str(t).find('codezb') > 0
			 	#		 and str(t).find('title="CA"') > 0 ):
			 	#		cur_a = soup.find_all('a')
			 	#		print(cur_a)
			 	#print(my_tables)
	out_f.close()		 	
	