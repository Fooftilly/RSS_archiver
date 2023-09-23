import os
import time
import pickle
import hashlib

# Define the FileCache class
class FileCache:
    def __init__(self, cache_dir, expiry_time):
        """
        Initialize the cache.

        :param cache_dir: Directory to store cache files.
        :param expiry_time: Expiry time for cache items in seconds.
        """
        self.cache_dir = cache_dir
        self.expiry_time = expiry_time
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_file_path(self, key):
        """
        Generate a file path for a given cache key.

        :param key: Cache key.
        :return: File path corresponding to the cache key.
        """
        # Hash the key to generate a valid filename
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, hashed_key)

    def store(self, key, data):
        """
        Store data in the cache associated with the given key.

        :param key: Cache key.
        :param data: Data to be cached.
        """
        file_path = self._get_cache_file_path(key)
        try:
            # Store the data along with the current timestamp
            with open(file_path, 'wb') as cache_file:
                try:
                    pickle.dump((time.time(), data), cache_file)
                except pickle.PickleError as e:
                    print(f"Error pickling data for cache key {key}: {e}")
        except IOError as e:
            print(f"Error writing cache file {file_path}: {e}")

    def retrieve(self, key):
        """
        Retrieve data from the cache associated with the given key.

        :param key: Cache key.
        :return: Cached data if exists and not expired, otherwise None.
        """
        file_path = self._get_cache_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as cache_file:
                    try:
                        timestamp, data = pickle.load(cache_file)
                        # Check if the cache item has expired
                        if time.time() - timestamp < self.expiry_time:
                            return data
                        else:
                            # Delete the expired cache file
                            os.remove(file_path)
                    except pickle.UnpicklingError as e:
                        print(f"Error unpickling data for cache key {key}: {e}")
            except IOError as e:
                print(f"Error reading cache file {file_path}: {e}")
        return None
