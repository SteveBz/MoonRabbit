import numpy as np
import time

class ModeCalculator:
    def __init__(self, numbers, tolerance=1e-5):
        self.numbers = numbers
        self.tolerance = tolerance
    
    def calculate_mode_mean(self):
        # Step 1: Sort the data
        sorted_numbers = sorted(self.numbers)
        
        # Step 2: Initialize variables for counting frequencies
        current_count = 1
        max_count = 1
        mode_ranges = [sorted_numbers[:1]]
        
        # Step 3: Iterate through the sorted list to count frequencies
        for i in range(1, len(sorted_numbers)):
            if abs(sorted_numbers[i] - sorted_numbers[i-1]) <= self.tolerance:
                current_count += 1
            else:
                if current_count > max_count:
                    max_count = current_count
                    mode_ranges = [sorted_numbers[i-current_count:i]]
                elif current_count == max_count:
                    mode_ranges.append(sorted_numbers[i-current_count:i])
                current_count = 1
        
        # Final check for the last group
        if current_count > max_count:
            mode_ranges = [sorted_numbers[-current_count:]]
        elif current_count == max_count:
            mode_ranges.append(sorted_numbers[-current_count:])
        
        # Step 4: Calculate the mean of the mode ranges
        range_means = [np.mean(range) for range in mode_ranges]
        mode_mean = np.mean(range_means)
        
        # Step 5: Calculate the overall mean of the values
        overall_mean = np.mean(self.numbers)
        
        # Step 6: Round the means to the nearest multiple of tolerance
        rounded_mode_mean = round(mode_mean / self.tolerance) * self.tolerance
        rounded_overall_mean = round(overall_mean / self.tolerance) * self.tolerance
        
        return rounded_mode_mean, rounded_overall_mean

if __name__ == "__main__":
    numbers = [1.001, 1.002, 1.002, 2.5, 2.50001, 2.50002, 3.0, 3.0001]
    tolerance = 1e-3  # Define a suitable tolerance
    
    start_time = time.time()  # Start timing
    mode_calculator = ModeCalculator(numbers, tolerance)
    mode_mean, overall_mean = mode_calculator.calculate_mode_mean()
    end_time = time.time()  # End timing
    
    # Print results
    print(f"The mode of the numbers is: {mode_mean} +/- {tolerance}")
    print(f"The overall mean of the numbers is: {overall_mean}")
    
    # Calculate and print execution time in milliseconds
    execution_time_ms = (end_time - start_time) * 1000
    print(f"Execution time: {execution_time_ms:.3f} milliseconds")
