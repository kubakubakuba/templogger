import sys
from datetime import datetime, timedelta
import os
import subprocess

def plot_temperature(filename):
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
			
			# fix erroneous negative temperatures
			if float(temp_str) < -69:
				continue

			try:
				timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
				temp = float(temp_str)
				
			except ValueError:
				continue
			
			data.append((timestamp, temp))
			if last_date is None or timestamp > last_date:
				last_date = timestamp

	if not data:
		print(f"No data found in file {filename}.")
		return

	data_points = [ (ts, temp) for ts, temp in data if ts.date() == last_date.date() ]

	if not data_points:
		print(f"No temperature data available for the last recorded day in file {filename}.")
		return


	plot_data = ""

	for (ts, temp) in data_points:
		total_seconds = (ts - ts.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
		hours = total_seconds / 3600.0

		plot_data += f"{round(hours, 2)} {float(temp)}\n"

	base_name = os.path.splitext(filename)[0]
	plot_file = f"{base_name}.png"
	script_file = f"{base_name}.gnuplot"

	gnuplot_script = f"""
	set terminal pngcairo size 800,600 enhanced
	set title "Temperature for {base_name} on {last_date.date()}"
	set xlabel "Time (HH:MM)"
	set ylabel "Temperature (°C)"
	set xtics rotate by -45
	set xdata time
	set timefmt "%H:%M:%S"
	set format x "%H:%M"
	set xrange ["00:00:00":"23:59:59"]
	set yrange [0:40]
	set output '{plot_file}'
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
		#os.remove(script_file)  # Clean up the script file
	except FileNotFoundError:
		print("Gnuplot not found. Please install Gnuplot to generate plots.")
		
if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python plot_temperature.py <filename>")
	else:
		filename = sys.argv[1]
		plot_temperature(filename)
