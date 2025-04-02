import sys
from datetime import datetime
import os
import subprocess
from flask import Flask, send_from_directory, Response, render_template, redirect, url_for

app = Flask(__name__)

PLOTS_DIR = 'plots'

if not os.path.exists(PLOTS_DIR):
	os.makedirs(PLOTS_DIR)

def plot_temperature(filename, month=None, day=None, dumb=False):
	if not os.path.exists(filename):
		print(f"No log file found: {filename}")
		return

	data = []
	last_date = None

	with open(filename, 'r') as file:
		for line in file:
			parts = line.strip().split(", ")
			if len(parts) != 2:
				continue

			timestamp_str, temp_str = parts

			try:
				timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
				temp = float(temp_str)
			except ValueError:
				continue

			# If month and day are provided, filter by them
			if month and day:
				if timestamp.month == month and timestamp.day == day:
					data.append((timestamp, temp))
			else:
				data.append((timestamp, temp))
			
			if last_date is None or timestamp > last_date:
				last_date = timestamp

	if not data:
		print(f"No data found for the specified date or in file {filename}.")
		return

	plot_data = ""
	for (ts, temp) in data:
		total_seconds = (ts - ts.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
		hours = total_seconds / 3600.0
		plot_data += f"{round(hours, 2)} {float(temp)}\n"

	# Define output filename (just room.png)
	base_name = os.path.splitext(filename)[0]
	plot_file = f"{base_name}.png" if not dumb else f"{base_name}.plot"
	script_file = f"{base_name}.gnuplot"

	# Generate the gnuplot script
	gnuplot_script = f"""
	set terminal {"dumb" if dumb else "pngcairo size 1600,600 enhanced"}
	set title "Temperature for {base_name} on {last_date.date()}"
	set xlabel "Time (HH:MM)"
	set ylabel "Temperature (°C)"
	set xtics rotate by -45
	#set xdata time
	#set timefmt "%H:%M:%S"
	#set format x "%H:%M"
	set xrange [0 : 24]
	#set yrange [0:40]
	set output '{PLOTS_DIR}/{plot_file}'
	plot '-' using 1:2 with linespoints title "Temperature"
	{plot_data}
	e
	"""

	with open(script_file, 'w') as f:
		f.write(gnuplot_script)

	try:
		result = subprocess.run(['gnuplot', script_file], capture_output=True, text=True)
		if result.returncode != 0:
			print(f"Gnuplot Error: {result.stderr}")
		else:
			print(f"Plot saved to {plot_file}")


		os.remove(script_file)
	except FileNotFoundError:
		print("Gnuplot not found. Please install Gnuplot to generate plots.")

def plot_temperature_api(filename, month=None, day=None, dumb=False, inverse=False, w=1600, h=600):
	if not os.path.exists(filename):
		print(f"No log file found: {filename}")
		return

	data = []
	last_date = None

	with open(filename, 'r') as file:
		for line in file:
			parts = line.strip().split(", ")
			if len(parts) != 2:
				continue

			timestamp_str, temp_str = parts

			try:
				timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
				temp = float(temp_str)
			except ValueError:
				continue

			# If month and day are provided, filter by them
			if month and day:
				if timestamp.month == month and timestamp.day == day:
					data.append((timestamp, temp))
			else:
				data.append((timestamp, temp))
			
			if last_date is None or timestamp > last_date:
				last_date = timestamp

	if not data:
		print(f"No data found for the specified date or in file {filename}.")
		return

	plot_data = ""
	for (ts, temp) in data:
		total_seconds = (ts - ts.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
		hours = total_seconds / 3600.0
		plot_data += f"{round(hours, 2)} {float(temp)}\n"

	# Define output filename (just room.png)
	base_name = os.path.splitext(filename)[0]
	plot_file = f"{base_name}.png" if not dumb else f"{base_name}.plot"
	if inverse:
		plot_file = f"{base_name}_inverse.png"
	script_file = f"{base_name}.gnuplot"

	# Generate the gnuplot script
	gnuplot_script = f"""
	set terminal {"dumb" if dumb else f"pngcairo size {w},{h} enhanced"}
	set title "Temperature for {base_name} on {last_date.date()}"
	set xlabel "Time (HH:MM)"
	set ylabel "Temperature (°C)"
	set xtics rotate by -45
	{"set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb 'black' behind" if inverse else ""}
	{"set border lc rgb 'white'" if inverse else ""}
	{"set tics textcolor rgb 'white'" if inverse else ""}
	{"set title textcolor rgb 'white'" if inverse else ""}
	{"set xlabel textcolor rgb 'white'" if inverse else ""}
	{"set ylabel textcolor rgb 'white'" if inverse else ""}
	{"set key textcolor rgb 'white'" if inverse else ""}
	set xrange [0 : 24]
	set output '{PLOTS_DIR}/{plot_file}'
	plot '-' using 1:2 with linespoints title "Temperature" {"lc rgb 'white'" if inverse else ""}
	{plot_data}
	e
	"""

	with open(script_file, 'w') as f:
		f.write(gnuplot_script)

	try:
		result = subprocess.run(['gnuplot', script_file], capture_output=True, text=True)
		if result.returncode != 0:
			print(f"Gnuplot Error: {result.stderr}")
		else:
			print(f"Plot saved to {plot_file}")

		os.remove(script_file)
	except FileNotFoundError:
		print("Gnuplot not found. Please install Gnuplot to generate plots.")

@app.route('/')
def index():
	"""
	Root page that lists all rooms (based on .tlog files present)
	with links to classic (PNG) and simple (ASCII) plots.
	"""

	# Look for all .tlog files in the current directory
	tlog_files = [f for f in os.listdir('.') if f.endswith('.tlog')]
	# Extract room names from the file names (remove extension)
	rooms = [os.path.splitext(f)[0] for f in tlog_files]
	return render_template('index.html', rooms=rooms)

@app.route('/plottemp/<room>', methods=['GET'])
def plottemp(room):
	CURR_DAY = datetime.now().day
	CURR_MONTH = datetime.now().month
	CURR_YEAR = datetime.now().year

	return redirect(url_for('plottemp_date', room=room, month=CURR_MONTH, day=CURR_DAY))

@app.route('/plottemp/<room>/<int:month>/<int:day>', methods=['GET'])
def plottemp_date(room, month, day):
	filename = f"{room}.tlog"
	plot_temperature(filename, month=month, day=day)
	plot_file = f"{room}.png"
	return render_template('display_plot.html', plot_file=plot_file)

@app.route('/plotsimple/<room>', methods=['GET'])
def plotsimple(room):
	CURR_DAY = datetime.now().day
	CURR_MONTH = datetime.now().month
	CURR_YEAR = datetime.now().year

	return redirect(url_for('plotsimple_date', room=room, month=CURR_MONTH, day=CURR_DAY))
	
@app.route('/plotsimple/<room>/<int:month>/<int:day>', methods=['GET'])
def plotsimple_date(room, month, day):
	filename = f"{room}.tlog"
	plot_file = f"{room}.plot"
	
	plot_temperature(filename, dumb=True, month=month, day=day)

	try:
		with open(f"{PLOTS_DIR}/{plot_file}", 'r') as f:
			plot_content = f.read()
		return Response(plot_content, content_type='text/plain')
	except FileNotFoundError:
		return "Error: Plot file not found", 404

@app.route('/plots/<filename>')
def serve_plot(filename):
	return send_from_directory(PLOTS_DIR, filename)

@app.route('/temp/<room>/<temp>', methods=['GET'])
def log_temperature(room, temp):
	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	log_entry = f"{timestamp}, {temp}\n"
	log_file = f"{room}.tlog"

	with open(log_file, "a") as file:
		file.write(log_entry)

	return f"Logged {temp}°C for {room} at {timestamp}\n"

from flask import request

@app.route('/plot/<room>', defaults={'month': None, 'day': None}, methods=['GET'])
@app.route('/plot/<room>/<int:month>/<int:day>', methods=['GET'])
def plot_on_date_inverse(room, month, day):
	if month is None or day is None:
		now = datetime.now()
		month = now.month
		day = now.day

	width = request.args.get('w', default=1600, type=int)
	height = request.args.get('h', default=600, type=int)
	inverse = request.args.get('inverse', default=0, type=int)

	print(f"Plotting {room} on {month}/{day} with inverse={inverse}")
	print(f"Width: {width}, Height: {height}")

	filename = f"{room}.tlog"
	plot_temperature_api(filename, month=month, day=day, inverse=inverse, w=width, h=height)
	plot_file = f"{room}_inverse.png"
	return send_from_directory(PLOTS_DIR, plot_file)

@app.route('/all')
def all_plots():
	"""
	Route to display all available plots as images in one place.
	"""
	tlog_files = [f for f in os.listdir('.') if f.endswith('.tlog')]

	CURR_DAY = datetime.now().day
	CURR_MONTH = datetime.now().month
	CURR_YEAR = datetime.now().year

	for tf in tlog_files:
		plot_temperature(tf, month=CURR_MONTH, day=CURR_DAY)

	plot_files = [f for f in os.listdir(PLOTS_DIR) if f.endswith('.png')]
	return render_template('all_plots.html', plot_files=plot_files)


if __name__ == "__main__":
	app.run(debug=True)
