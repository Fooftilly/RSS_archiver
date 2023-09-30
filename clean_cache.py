import os

# Define the path to the file_cache directory
cache_dir = 'file_cache'

# List all items in the cache directory
items = os.listdir(cache_dir)

# Initialize a list to store file paths and their modification times
files_with_mtime = []

# Iterate over all items in the cache directory
for item in items:
    item_path = os.path.join(cache_dir, item)

    # Check if the item is a file (not a directory)
    if os.path.isfile(item_path):
        # Get the modification time of the file
        mtime = os.path.getmtime(item_path)

        # Append the file path and modification time to the list
        files_with_mtime.append((item_path, mtime))

# Sort the list of files by modification time (oldest first)
files_with_mtime.sort(key=lambda x: x[1])

# Check if the number of files exceeds 10,000
if len(files_with_mtime) > 10000:
    # Calculate the number of files to delete
    num_to_delete = len(files_with_mtime) - 10000

    # Delete the oldest files
    for i in range(num_to_delete):
        os.remove(files_with_mtime[i][0])
        print(f"Deleted {files_with_mtime[i][0]}")

print("File cache cleanup completed.")
