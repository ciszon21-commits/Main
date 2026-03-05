import os
import hashlib
from collections import defaultdict
from datetime import datetime

def hash_file(filepath):
    """
    Computes and returns the SHA-256 hash of a file.
    Reads the file in chunks to handle large files.
    """
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096 * 1024), b""): # 4MB chunks
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        # Ignore files that cannot be read (e.g., due to permissions)
        return None

def format_size(size_bytes):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def find_duplicates(directory_path):
    """
    Scans the directory for duplicate files.
    1. Groups files by size.
    2. For files with the same size (>1), computes hash.
    3. Groups files by hash.
    
    Returns a list of duplicate file groups.
    Each group is a list of file info dictionaries.
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        raise ValueError("Provided path is not a valid directory.")

    # Step 1: Group files by size
    size_groups = defaultdict(list)
    seen_inodes = set()
    
    for root, _, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            # Skip symlinks, broken links, and Windows shortcuts
            if filename.lower().endswith(('.lnk', '.url')):
                continue
            if not os.path.isfile(filepath) or os.path.islink(filepath):
                continue
            
            try:
                stat_info = os.stat(filepath)
                # Ignore hard links (same physical file)
                inode_id = (stat_info.st_dev, stat_info.st_ino)
                if inode_id in seen_inodes:
                    continue
                seen_inodes.add(inode_id)

                size = stat_info.st_size
                # Ignore zero-byte files
                if size > 0:
                    size_groups[size].append(filepath)
            except OSError:
                # Skip files we can't access
                continue
    
    # Filter out sizes that only have 1 file
    potential_duplicates = {size: paths for size, paths in size_groups.items() if len(paths) > 1}
    
    duplicate_groups = []
    
    # Step 2: Compute hash for potential duplicates
    for size, paths in potential_duplicates.items():
        hash_groups = defaultdict(list)
        
        for filepath in paths:
            file_hash = hash_file(filepath)
            if file_hash:
                hash_groups[file_hash].append(filepath)
                
        # Step 3: Filter groups that have more than 1 file with the exact same hash
        for file_hash, identical_files in hash_groups.items():
            if len(identical_files) > 1:
                group_info = []
                for f_path in identical_files:
                    try:
                        stat = os.stat(f_path)
                        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        group_info.append({
                            'path': f_path,
                            'dir': os.path.dirname(f_path),
                            'name': os.path.basename(f_path),
                            'size': format_size(size),
                            'raw_size': size,
                            'modified': mod_time,
                        })
                    except OSError:
                        pass
                
                if len(group_info) > 1:
                    duplicate_groups.append(group_info)
    
    # Sort groups by file size descending (largest files first) for better UX
    duplicate_groups.sort(key=lambda g: g[0]['raw_size'] if g else 0, reverse=True)
    
    return duplicate_groups
