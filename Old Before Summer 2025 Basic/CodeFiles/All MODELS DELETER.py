import os
import shutil

def delete_all_huggingface_cache():
    """
    Deletes all cached files and directories in the Hugging Face hub cache.
    The Hugging Face hub typically caches items under ~/.cache/huggingface/hub.
    This function will delete every file and subdirectory in that folder.
    """
    # Determine the cache directory for Hugging Face hub files
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    
    if not os.path.exists(cache_dir):
        print(f"Cache directory not found: {cache_dir}")
        return
    
    removed_any = False
    # List every item in the cache directory
    for item in os.listdir(cache_dir):
        item_path = os.path.join(cache_dir, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Deleted directory: {item_path}")
            else:
                os.remove(item_path)
                print(f"Deleted file: {item_path}")
            removed_any = True
        except Exception as e:
            print(f"Error deleting {item_path}: {e}")
    
    if not removed_any:
        print(f"No cached files or directories found in {cache_dir}")

if __name__ == "__main__":
    delete_all_huggingface_cache()
