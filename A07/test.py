import psutil
import numpy as np

# Record the initial CPU usage percentage
initial_cpu_percent = psutil.cpu_percent(interval=1)

# Capture the initial memory usage in KB
initial_memory_usage = psutil.virtual_memory().used / 1024

# Initialize a variable
counter = 3

# Perform a computation to simulate CPU and memory usage
for _ in range(1_000_000):
    counter += 1

# Capture the final memory usage in KB
final_memory_usage = psutil.virtual_memory().used / 1024

# Calculate the absolute difference in memory usage
memory_usage_diff = np.abs(final_memory_usage - initial_memory_usage)

# Print the results
print(f"Initial CPU Percent: {initial_cpu_percent}%")
print(f"Initial Memory Usage: {initial_memory_usage} KB")
print(f"Memory Usage Difference: {memory_usage_diff} KB")
print(f"Random Integer: {np.random.randint(10)}")