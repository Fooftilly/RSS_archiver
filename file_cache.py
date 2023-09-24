import os
import time
import pickle
import hashlib

class FileCache:
    def __init__(self, cache_dir, expiry_time):
        self.cache_dir = cache_dir
        self.expiry_time = expiry_time
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_file_path(self, key):
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, hashed_key)

    def store(self, key, data):
        file_path = self._get_cache_file_path(key)
        try:
            with open(file_path, 'wb') as cache_file:
                try:
                    pickle.dump((time.time(), data), cache_file)
                except pickle.PickleError as e:
                    print(f"Error pickling data for cache key {key}: {e}")
        except IOError as e:
            print(f"Error writing cache file {file_path}: {e}")

    def retrieve(self, key):
        file_path = self._get_cache_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as cache_file:
                    try:
                        timestamp, data = pickle.load(cache_file)
                        if time.time() - timestamp < self.expiry_time:
                            return data
                        else:
                            os.remove(file_path)
                    except pickle.UnpicklingError as e:
                        print(f"Error unpickling data for cache key {key}: {e}")
            except IOError as e:
                print(f"Error reading cache file {file_path}: {e}")

    def cleanup(self):
        """
        Clean up expired items in the cache.
        """
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as cache_file:
                        timestamp, _ = pickle.load(cache_file)
                        if time.time() - timestamp >= self.expiry_time:
                            os.remove(file_path)
                except Exception as e:
                    print(f"Error cleaning up cache file {file_path}: {e}")
