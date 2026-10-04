import socket
import time
import csv
import statistics
import argparse


SERVER_IP = "169.254.125.100"
SERVER_PORT = 4444

REQUEST = b"HELLO\n"

NUM_RUNS = 1000

OUTPUT_FILE = "../data/performance_results.csv"

# Function to meausure one run through
def measure_request():
	start = time.perf_counter_ns()

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((SERVER_IP, SERVER_PORT))
		sock.sendall(REQUEST)
		response = sock.recv(1024)

	end = time.perf_counter_ns()

	return (end - start) / 1_000_000

# Run multiple runs to get an accurate reading on the server performance
def run_test():

	measurements = []

	print(f"Testing {NUM_RUNS} requests...")

	for i in range(NUM_RUNS):

		try:
			latency = measure_request()
			measurements.append(latency)

			print(f"\rProgress: {i + 1}/{NUM_RUNS}", end="")

		except Exception as e:
			print(f"\nRequest failed: {e}")

	print()

	if not measurements:
		print("No successful measurements.")
		return None

	return {
		"runs": len(measurements),
		"mean_ms": statistics.mean(measurements),
		"median_ms": statistics.median(measurements),
		"stdev_ms": (statistics.stdev(measurements) if len(measurements) > 1 else 0),
		"min_ms": min(measurements),
		"max_ms": max(measurements)
	}


def save_result(configuration, result):

	with open(OUTPUT_FILE, "a", newline="") as f:

		fieldnames = [
			"configuration",
			"runs",
			"mean_ms",
			"median_ms",
			"stdev_ms",
			"min_ms",
			"max_ms"
		]

		writer = csv.DictWriter(f, fieldnames=fieldnames)

		# Create header if file is empty
		if f.tell() == 0:
			writer.writeheader()

		row = {
			"configuration": configuration,
			**result
		}

		writer.writerow(row)


def main():
	# This program will need a --config parameter to specify which config to test
	parser = argparse.ArgumentParser()

	parser.add_argument(
		"--config",
		required=True,
		help="Name of the server configuration being tested"
	)

	args = parser.parse_args()

	print(f"Configuration: {args.config}")
	print(f"Server: {SERVER_IP}:{SERVER_PORT}")

	result = run_test()

	if result:

		save_result(args.config, result)

		print("\nResults:")
		print(f"Mean:   {result['mean_ms']:.4f} ms")
		print(f"Median: {result['median_ms']:.4f} ms")
		print(f"Std:    {result['stdev_ms']:.4f} ms")
		print(f"Min:    {result['min_ms']:.4f} ms")
		print(f"Max:    {result['max_ms']:.4f} ms")


if __name__ == "__main__":
	main()