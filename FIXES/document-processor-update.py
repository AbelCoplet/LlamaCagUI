def _save_kv_cache_state(self, llm, kv_cache_path: Path) -> bool:
    """
    Improved function to save KV cache state using recommended approach.
    Returns True if successful, False otherwise.
    """
    logging.info(f"Saving KV cache state to {kv_cache_path}...")
    
    # Method 1: Try getting state without arguments first, then pickle
    try:
        logging.info("Using save_state() without arguments and pickling...")
        state_data = llm.save_state()  # Get state data object
        
        # Verify we got something valid
        if state_data is None:
            logging.error("save_state() returned None")
            return False
            
        # Save with pickle
        with open(kv_cache_path, 'wb') as f_pickle:
            pickle.dump(state_data, f_pickle)
        logging.info("KV cache state saved successfully via pickle")
        return True
    except (AttributeError, pickle.PicklingError) as e:
        logging.error(f"Error in primary KV cache save method: {e}")
    
    # Method 2: Try direct path argument as fallback
    try:
        logging.info("Trying save_state with direct path argument...")
        llm.save_state(str(kv_cache_path))
        
        # Check if file was created
        if kv_cache_path.exists() and kv_cache_path.stat().st_size > 0:
            logging.info("KV cache saved successfully with path argument")
            return True
        else:
            logging.error("save_state(path) did not create a valid file")
    except Exception as e:
        logging.error(f"Error in fallback KV cache save method: {e}")
    
    # If we get here, both methods failed
    logging.error("All KV cache save methods failed")
    return False

# Updated portion of _process_document_thread that handles state saving
# This would replace the existing save_state block in the function
def _updated_save_state_block(self, llm, document_id, kv_cache_path, token_count, context_window):
    """
    This is not a standalone function but shows the code that would 
    replace the existing save_state implementation in _process_document_thread
    """
    # --- Save KV Cache State ---
    save_successful = self._save_kv_cache_state(llm, kv_cache_path)
    
    if not save_successful:
        # Create placeholder to prevent subsequent errors
        with open(kv_cache_path, 'w') as f:
            f.write("KV CACHE SAVE FAILED PLACEHOLDER")
        error_msg = f"Failed to save KV cache state to {kv_cache_path} using known methods."
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    # --- Continue if save was successful ---
    logging.info("KV cache state saved successfully.")
