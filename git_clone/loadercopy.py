from subprocess import Popen, PIPE
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

SCRIPT_PATH = '/home/talkad/Downloads/thesis/data_gathering_script/git_clone/git_clone.sh'

def load(start_date=None, end_date=None, is_dry=False):
	'''
	Load repositories created in range of dates from github that include omp directives

	Parameters:
		start_date - lower bound of dates
		end_date   - upper bound of dates
		is_dry     - whether to load the files or not
	'''
	
	month = 30
	max_results = 10**3
	start_date = date(2012, 1, 1) if start_date is None else start_date
	end_date = date.today() if end_date is None else end_date
	total_repos = 0
	repos_per_month = {}

	while start_date <= end_date:
		start = start_date.strftime("%Y-%m-%d")
		delta = relativedelta(days=month)
		end = (start_date + delta).strftime("%Y-%m-%d")

		# exectue the "dry" version
		p = Popen([SCRIPT_PATH, "y", start, end], stdin=PIPE, stdout=PIPE, stderr=PIPE)
		output, err = p.communicate()

		num_results = 0 if len(output) == 0 else len(output.split(b"\ndry-run:"))
		print(output.split(b"\ndry-run:"))
		break

		if num_results < max_results:
			#clone
			if not is_dry:
				p = Popen([SCRIPT_PATH, "", start, end], stdin=PIPE, stdout=PIPE, stderr=PIPE)
				output, err = p.communicate()
				
			print(f'cloned {num_results} repos from {start} to {end}')
			repos_per_month[f'{start_date.month}-{start_date.year}'] = num_results # update this line

			month = 30
			total_repos += num_results
			start_date += delta
		else:
			month = month // 2

	print(f'total number of repos cloned: {total_repos}')	
	return repos_per_month	

load(is_dry=True)

# {'1-2008': 1, '2-2008': 1, '3-2008': 1, '4-2008': 1, '5-2008': 1, '6-2008': 1, '7-2008': 1, '8-2008': 1, '9-2008': 1, '10-2008': 1, '11-2008': 1, '12-2008': 1, '1-2009': 1, '2-2009': 1, '3-2009': 1, '4-2009': 1, '5-2009': 1, '6-2009': 1, '7-2009': 1, '8-2009': 1, '9-2009': 1, '10-2009': 1, '11-2009': 1, '12-2009': 1, '1-2010': 1, '2-2010': 1, '3-2010': 1, '4-2010': 1, '5-2010': 1, '6-2010': 1, '7-2010': 1, '8-2010': 1, '9-2010': 3, '10-2010': 3, '11-2010': 2, '12-2010': 1, '1-2011': 3, '2-2011': 1, '3-2011': 1, '4-2011': 1, '5-2011': 3, '6-2011': 6, '7-2011': 1, '8-2011': 2, '9-2011': 1, '10-2011': 3, '11-2011': 1, '12-2011': 8, '1-2012': 1, '2-2012': 9, '3-2012': 5, '4-2012': 9, '5-2012': 4, '6-2012': 4, '7-2012': 6, '8-2012': 6, '9-2012': 10, '10-2012': 11, '11-2012': 14, '12-2012': 6, '1-2013': 5, '2-2013': 13, '3-2013': 18, '4-2013': 17, '5-2013': 8, '6-2013': 9, '7-2013': 14, '8-2013': 12, '9-2013': 9, '10-2013': 23, '11-2013': 22, '12-2013': 26, '1-2014': 25, '2-2014': 16, '3-2014': 29, '4-2014': 29, '5-2014': 24, '6-2014': 22, '7-2014': 26, '8-2014': 16, '9-2014': 27, '10-2014': 27, '11-2014': 31, '12-2014': 27, '1-2015': 38, '2-2015': 29, '3-2015': 50, '4-2015': 38, '5-2015': 37, '6-2015': 32, '7-2015': 26, '8-2015': 34, '9-2015': 41, '10-2015': 59, '11-2015': 54, '12-2015': 45, '1-2016': 36, '2-2016': 51, '3-2016': 66, '4-2016': 56, '5-2016': 59, '6-2016': 41, '7-2016': 32, '8-2016': 28, '9-2016': 50, '10-2016': 76, '11-2016': 83, '12-2016': 53, '1-2017': 65, '2-2017': 70, '3-2017': 122, '4-2017': 89, '5-2017': 89, '6-2017': 61, '7-2017': 72, '8-2017': 60, '9-2017': 71, '10-2017': 117, '11-2017': 96, '12-2017': 98, '1-2018': 60, '2-2018': 96, '3-2018': 116, '4-2018': 110, '5-2018': 114, '6-2018': 77, '7-2018': 71, '8-2018': 69, '9-2018': 82, '10-2018': 118, '11-2018': 93, '12-2018': 91, '1-2019': 105, '2-2019': 113, '3-2019': 147, '4-2019': 135, '5-2019': 119, '6-2019': 97, '7-2019': 75, '8-2019': 73, '9-2019': 90, '10-2019': 140, '11-2019': 124, '12-2019': 121, '1-2020': 91, '2-2020': 92, '3-2020': 102, '4-2020': 152, '5-2020': 141, '6-2020': 110, '7-2020': 90, '8-2020': 78, '9-2020': 107, '10-2020': 141, '11-2020': 135, '12-2020': 125, '1-2021': 110, '2-2021': 99, '3-2021': 113, '4-2021': 116, '5-2021': 121, '6-2021': 87, '7-2021': 70, '8-2021': 97, '9-2021': 93, '10-2021': 91, '11-2021': 148, '12-2021': 120, '1-2022': 94, '2-2022': 71, '3-2022': 117, '4-2022': 134, '5-2022': 159, '6-2022': 101, '7-2022': 99, '8-2022': 48}
# total: 8644