import csv
from pathlib import Path


# Project directories
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

COMPILE_FILE = DATA_DIR / "compile_results.csv"
PERFORMANCE_FILE = DATA_DIR / "performance_results.csv"
OUTPUT_FILE = DATA_DIR / "analysis_results.csv"

BASELINE = "C0_baseline"

# Read a CSV file and return its rows as dictionaries
def read_csv(filename):
	if not filename.exists():
		raise FileNotFoundError(f"Could not find: {filename}")

	with open(filename, "r", newline="") as file:
		return list(csv.DictReader(file))


# Calculate percentage change relative to the baseline
def percent_change(value, baseline):
	if baseline == 0:
		return None

	return ((value - baseline) / baseline) * 100


# Format a number for readable terminal output
def format_number(value, decimals=4):
	if value is None:
		return "N/A"

	return f"{value:.{decimals}f}"


def analyze_results():
	compile_results = read_csv(COMPILE_FILE)
	performance_results = read_csv(PERFORMANCE_FILE)

	# Index results by configuration name for easy matching.
	compile_by_config = {
		row["configuration"]: row
		for row in compile_results
	}

	performance_by_config = {
		row["configuration"]: row
		for row in performance_results
	}

	# The baseline must exist in both files.
	if BASELINE not in compile_by_config:
		raise ValueError(f"{BASELINE} was not found in compile_results.csv")

	if BASELINE not in performance_by_config:
		raise ValueError(f"{BASELINE} was not found in performance_results.csv")

	baseline_compile = compile_by_config[BASELINE]
	baseline_performance = performance_by_config[BASELINE]

	baseline_compile_mean = float(baseline_compile["mean_seconds"])
	baseline_size = float(baseline_compile["executable_size_bytes"])
	baseline_latency = float(baseline_performance["mean_ms"])

	# Sort the configurations
	configurations = sorted(compile_by_config)

	results = []

	for config in configurations:
		compile_row = compile_by_config.get(config)
		performance_row = performance_by_config.get(config)

		result = {
			"configuration": config,
			"compile_mean_seconds": "",
			"compile_median_seconds": "",
			"compile_stdev_seconds": "",
			"compile_min_seconds": "",
			"compile_max_seconds": "",
			"compile_change_percent": "",
			"executable_size_bytes": "",
			"executable_size_change_percent": "",
			"performance_runs": "",
			"latency_mean_ms": "",
			"latency_median_ms": "",
			"latency_stdev_ms": "",
			"latency_min_ms": "",
			"latency_max_ms": "",
			"latency_change_percent": "",
		}

		# Analyze compilation results.
		if compile_row:
			compile_mean = float(compile_row["mean_seconds"])
			executable_size = float(compile_row["executable_size_bytes"])

			result.update({
				"compile_mean_seconds": compile_mean,
				"compile_median_seconds": float(compile_row["median_seconds"]),
				"compile_stdev_seconds": float(compile_row["stdev_seconds"]),
				"compile_min_seconds": float(compile_row["min_seconds"]),
				"compile_max_seconds": float(compile_row["max_seconds"]),
				"compile_change_percent": percent_change(compile_mean, baseline_compile_mean),
				"executable_size_bytes": int(executable_size),
				"executable_size_change_percent": percent_change(executable_size, baseline_size),
			})

		# Analyze network performance results.
		if performance_row:
			latency_mean = float(performance_row["mean_ms"])

			result.update({
				"performance_runs": int(performance_row["runs"]),
				"latency_mean_ms": latency_mean,
				"latency_median_ms": float(performance_row["median_ms"]),
				"latency_stdev_ms": float(performance_row["stdev_ms"]),
				"latency_min_ms": float(performance_row["min_ms"]),
				"latency_max_ms": float(performance_row["max_ms"]),
				"latency_change_percent": percent_change(latency_mean, baseline_latency),
			})

		results.append(result)

	# Save the combined analysis.
	DATA_DIR.mkdir(parents=True, exist_ok=True)

	with open(OUTPUT_FILE, "w", newline="") as file:
		writer = csv.DictWriter(file, fieldnames=results[0].keys())
		writer.writeheader()
		writer.writerows(results)

	# Print a compact summary.
	print("\nSummary")
	print("=" * 100)
	print(f"{'Configuration':<20}"
		  f"{'Compile Mean (s)':>18}"
		  f"{'Compile Change':>18}"
		  f"{'Latency Mean (ms)':>20}"
		  f"{'Latency Change':>18}")

	print("-" * 100)

	for row in results:
		compile_change = row["compile_change_percent"]
		latency_change = row["latency_change_percent"]

		compile_change_text = (f"{compile_change:+.2f}%" if compile_change != "" else "N/A")

		latency_change_text = (f"{latency_change:+.2f}%" if latency_change != "" else "N/A")

		print(
			f"{row['configuration']:<20}"
			f"{format_number(row['compile_mean_seconds']):>18}"
			f"{compile_change_text:>18}"
			f"{format_number(row['latency_mean_ms']):>20}"
			f"{latency_change_text:>18}"
		)

	print("\nAnalysis saved to:")
	print(OUTPUT_FILE)


if __name__ == "__main__":
	analyze_results()