import os
import shutil

def delete_huggingface_model_cache(model_id):
    """
    Deletes cached files and directories related to the given model_id.
    
    The Hugging Face hub typically caches models under ~/.cache/huggingface/hub.
    Cached files for a model with ID like "Norm/nougat-latex-base" are usually
    stored with "/" replaced by "--" (i.e. "Norm--nougat-latex-base") in their names.
    """
    # Determine the default cache directory for Hugging Face hub files
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    
    if not os.path.exists(cache_dir):
        print(f"Cache directory not found: {cache_dir}")
        return
    
    # Convert the model ID to the cache naming pattern
    model_pattern = model_id.replace("/", "--")
    
    removed_any = False
    # Walk through the cache directory recursively
    for root, dirs, files in os.walk(cache_dir, topdown=False):
        # Check directories for the model pattern
        for d in dirs:
            if model_pattern in d:
                dir_path = os.path.join(root, d)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Deleted directory: {dir_path}")
                    removed_any = True
                except Exception as e:
                    print(f"Error deleting directory {dir_path}: {e}")
        # Check files for the model pattern
        for f in files:
            if model_pattern in f:
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                    removed_any = True
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
    
    if not removed_any:
        print(f"No cached files or directories found for model '{model_id}' in {cache_dir}")

if __name__ == "__main__":
    model_id = "Norm/nougat-latex-base"
    delete_huggingface_model_cache(model_id)
