#!/usr/bin/env python3
import os
import subprocess
import sys

def test_script(script_path, *args):
    """Test if a script can be executed with the given arguments."""
    print(f"Testing script: {script_path}")
    print(f"Arguments: {args}")
    
    # Check if script exists
    if not os.path.exists(script_path):
        print(f"ERROR: Script not found at {script_path}")
        return False
    
    # Check if script is executable
    if not os.access(script_path, os.X_OK):
        print(f"WARNING: Script is not executable. Trying to fix...")
        try:
            os.chmod(script_path, 0o755)
            print("Set executable permission on script.")
        except Exception as e:
            print(f"ERROR: Could not set executable permission: {e}")
            return False
    
    # Try to execute the script
    try:
        print(f"Executing: {script_path} {' '.join(args)}")
        result = subprocess.run([script_path] + list(args), 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True,
                               check=False)
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: Exception during execution: {e}")
        return False

if __name__ == "__main__":
    script_path = "/Users/steinbockbarite/Documents/GitHub/LlamaCagUI/scripts/bash/create_kv_cache.sh"
    model_path = "/Users/steinbockbarite/Documents/llama.cpp/models/google_gemma-3-4b-it-Q4_K_M.gguf"
    doc_path = "/tmp/test_document.txt"
    
    # Create test document if it doesn't exist
    if not os.path.exists(doc_path):
        with open(doc_path, 'w') as f:
            f.write("This is a test document for KV cache testing.")
    
    success = test_script(script_path, model_path, doc_path, "test_cache")
    
    if success:
        print("\nScript executed successfully!")
    else:
        print("\nScript execution failed. See errors above.")
