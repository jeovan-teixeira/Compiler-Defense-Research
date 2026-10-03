import subprocess
import time
import csv
import statistics
from pathlib import Path

SOURCE = Path("../server/vulnerable_server.c")
BUILD_DIR = Path("../builds")
DATA_DIR = Path("../data")

COMPILE_REPETITIONS = 100


CONFIGURATIONS = {
	"No_Flags": [], # Naturally becomes Partial RELRO + NX

	"C0_baseline": [
		"-O0",
		"-fno-stack-protector",
		"-no-pie",
		"-Wl,-z,execstack",
		"-Wl,-z,norelro"
	],

	"C1_canary": [
		"-O0",
		"-fstack-protector-strong",
		"-no-pie",
		"-Wl,-z,execstack",
		"-Wl,-z,norelro"
	],

	"C2_nx": [
		"-O0",
		"-fno-stack-protector",
		"-no-pie",
		"-Wl,-z,noexecstack",
		"-Wl,-z,norelro"
	],

	"C3_pie_nx": [
		"-O0",
		"-fno-stack-protector",
		"-fPIE",
		"-pie",
		"-Wl,-z,noexecstack",
		"-Wl,-z,norelro"
	],

	"C4_hardened": [ # Canary + PIE + NX + RELRO
		"-O0",
		"-fstack-protector-strong",
		"-fPIE",
		"-pie",
		"-Wl,-z,noexecstack",
		"-Wl,-z,relro",
		"-Wl,-z,now"
	],

	"C5_full": [ # Same as C4 but also with _FORTIFY_SOUCE
		"-O2",
		"-fstack-protector-strong",
		"-fPIE",
		"-pie",
		"-Wl,-z,noexecstack",
		"-Wl,-z,relro",
		"-Wl,-z,now",
		"-D_FORTIFY_SOURCE=2"
	]
}

# Compiles program and times how long it takes as well as success or not
def compile_program(flags, output_path):

	# Build gcc compiler command
	command = [
		"gcc",
		str(SOURCE),
		"-o",
		str(output_path)
	] + flags

	start = time.perf_counter()

	result = subprocess.run(
		command,
		capture_output=True,
		text=True
	)

	end = time.perf_counter()

	compile_time = end - start

	return result.returncode, compile_time, result.stderr


def main():

	BUILD_DIR.mkdir(exist_ok=True)
	DATA_DIR.mkdir(exist_ok=True)

	results = []

	# Go through each config and run each experiment COMPILE_REPETITIONS times
	for config_name, flags in CONFIGURATIONS.items():

		print(f"\nTesting {config_name}")

		config_dir = BUILD_DIR / config_name
		config_dir.mkdir(parents=True, exist_ok=True)

		executable = config_dir / "vulnerable_server"

		compile_times = []

		for run in range(1, COMPILE_REPETITIONS + 1):

			# Remove previous executable
			if executable.exists():
				executable.unlink()

			return_code, compile_time, error = compile_program(flags, executable)

			if return_code != 0:
				print("Compilation failed:")
				print(error)
				continue

			compile_times.append(compile_time)

			print(
				f"Run {run}/{COMPILE_REPETITIONS}: "
				f"{compile_time:.6f} seconds"
			)

		# Make sure we actually collected measurements
		if not compile_times:
			print(f"No successful compilations for {config_name}")
			continue

		# Get executable size
		executable_size = executable.stat().st_size

		# Calculate statistics
		mean_time = statistics.mean(compile_times)

		median_time = statistics.median(compile_times)

		stdev_time = (statistics.stdev(compile_times) if len(compile_times) > 1 else 0)

		min_time = min(compile_times)

		max_time = max(compile_times)

		# Store row for this configuration
		results.append({
			"configuration": config_name,
            "runs": COMPILE_REPETITIONS,
			"mean_seconds": mean_time,
			"median_seconds": median_time,
			"stdev_seconds": stdev_time,
			"min_seconds": min_time,
			"max_seconds": max_time,
			"executable_size_bytes": executable_size
		})

		print("\nSummary:")
		print(f"  Mean:	   {mean_time:.6f} seconds")
		print(f"  Median:	 {median_time:.6f} seconds")
		print(f"  Std Dev:	{stdev_time:.6f} seconds")
		print(f"  Min:		{min_time:.6f} seconds")
		print(f"  Max:		{max_time:.6f} seconds")
		print(f"  File Size:  {executable_size} bytes")

	# Write summary CSV
	output_file = DATA_DIR / "compile_results.csv"

	with open(output_file, "w", newline="") as f:

		fieldnames = [
			"configuration",
            "runs",
			"mean_seconds",
			"median_seconds",
			"stdev_seconds",
			"min_seconds",
			"max_seconds",
			"executable_size_bytes"
		]

		writer = csv.DictWriter(f, fieldnames=fieldnames)

		writer.writeheader()
		writer.writerows(results)

	print(f"\nSummary saved to {output_file}")


if __name__ == "__main__":
	main()