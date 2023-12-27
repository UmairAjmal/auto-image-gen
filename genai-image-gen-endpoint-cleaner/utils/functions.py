from datetime import datetime


def is_diff_10_min(last_updated):
    # Define reference time
    reference_time = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S.%f")
    
    # Get current time
    current_time = datetime.now()
    
    # Calculate the time difference in seconds
    time_diff = (current_time - reference_time).total_seconds()

    # Check if the difference is 10 minutes (600 seconds)
    return True if time_diff >= 600 else False