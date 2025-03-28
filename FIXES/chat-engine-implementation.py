def _inference_thread_with_true_kv_cache(self, message: str, model_path: str, context_window: int,
                         kv_cache_path: Optional[str], max_tokens: int, temperature: float):
    """Thread function for model inference using true KV cache loading"""
    llm = None
    try:
        self.response_started.emit()
        logging.info(f"True KV cache inference thread started. Model: {model_path}, Cache: {kv_cache_path}")

        # --- Configuration ---
        threads = int(self.config.get('LLAMACPP_THREADS', os.cpu_count() or 4))
        batch_size = int(self.config.get('LLAMACPP_BATCH_SIZE', 512))
        gpu_layers = int(self.config.get('LLAMACPP_GPU_LAYERS', 0))

        # --- Load Model ---
        logging.info(f"Loading model: {model_path}")
        abs_model_path = str(Path(model_path).resolve())
        if not Path(abs_model_path).exists():
            raise FileNotFoundError(f"Model file not found: {abs_model_path}")

        llm = Llama(
            model_path=abs_model_path,
            n_ctx=context_window,
            n_threads=threads,
            n_batch=batch_size,
            n_gpu_layers=gpu_layers,
            verbose=False
        )
        logging.info("Model loaded.")

        # --- Load KV Cache ---
        if kv_cache_path and Path(kv_cache_path).exists():
            logging.info(f"Loading KV cache state from: {kv_cache_path}")
            try:
                with open(kv_cache_path, 'rb') as f_pickle:
                    state_data = pickle.load(f_pickle)
                llm.load_state(state_data)
                logging.info("KV cache state loaded successfully.")

                # --- Tokenize user input ---
                message_tokens = llm.tokenize(message.encode('utf-8'))
                logging.info(f"Tokenized user message ({len(message_tokens)} tokens)")

                # --- Add special tokens to help model understand we're asking a question about the loaded context ---
                # This may help guide the model to use the cached context
                prefix_text = "\n\nQuestion: "
                suffix_text = "\n\nAnswer: "
                
                prefix_tokens = llm.tokenize(prefix_text.encode('utf-8'))
                suffix_tokens = llm.tokenize(suffix_text.encode('utf-8'))
                
                # --- Evaluate all tokens to add to KV cache ---
                logging.info("Evaluating prefix tokens")
                llm.eval(prefix_tokens)
                
                logging.info("Evaluating message tokens")
                llm.eval(message_tokens)
                
                logging.info("Evaluating suffix tokens")
                llm.eval(suffix_tokens)
                
                # --- Generate response using low-level token sampling ---
                logging.info("Generating response using low-level token sampling")
                eos_token = llm.token_eos()
                tokens_generated = []
                
                # Low-level token generation loop
                for _ in range(max_tokens):
                    # Sample the next token based on current KV cache context
                    token_id = llm.sample(temperature=temperature)
                    
                    # Stop if we hit the end token
                    if token_id == eos_token:
                        break
                    
                    # Add token to our result list
                    tokens_generated.append(token_id)
                    
                    # Evaluate the token to update KV cache (feed it back in)
                    llm.eval([token_id])
                    
                    # Send progress updates for longer generations
                    if len(tokens_generated) % 8 == 0:
                        partial_text = llm.detokenize(tokens_generated).decode('utf-8', errors='replace')
                        self.response_chunk.emit(partial_text)
                
                # Detokenize all generated tokens
                response_text = llm.detokenize(tokens_generated).decode('utf-8', errors='replace')
                logging.info(f"Generated response with {len(tokens_generated)} tokens")
                
                # Add to chat history
                if response_text.strip():
                    self.history.append({"role": "assistant", "content": response_text})
                    self.response_complete.emit(response_text, True)
                else:
                    logging.warning("Model generated an empty response.")
                    self.error_occurred.emit("Model generated an empty response.")
                    self.response_complete.emit("", False)
                
                # Successful true KV cache usage
                return
                
            except Exception as e:
                logging.error(f"Error using true KV cache, falling back to manual context: {e}")
                # Fall through to standard approach if KV cache loading/usage fails
        
        # --- Fallback to Manual Context Approach ---
        logging.info("Using manual context approach (fallback)")
        
        # Prepare chat history with system prompt and context
        chat_messages = []
        system_prompt_content = "You are a helpful assistant."  # Default

        # Try to read context from the original document
        if kv_cache_path:
            logging.info("Attempting to prepend document context to system prompt (fallback method).")
            doc_context_text = ""
            try:
                cache_info = self.cache_manager.get_cache_info(kv_cache_path)
                if cache_info and 'original_document' in cache_info:
                    original_doc_path_str = cache_info['original_document']
                    if original_doc_path_str != "Unknown":
                        original_doc_path = Path(original_doc_path_str)
                        if original_doc_path.exists():
                            logging.info(f"Reading from original document: {original_doc_path}")
                            with open(original_doc_path, 'r', encoding='utf-8', errors='replace') as f_doc:
                                doc_context_text = f_doc.read(8000)
                            logging.info(f"Read {len(doc_context_text)} chars from original document.")
                    
                if doc_context_text:
                    system_prompt_content = (
                        f"Use the following text to answer the user's question:\n"
                        f"--- TEXT START ---\n"
                        f"{doc_context_text}...\n"
                        f"--- TEXT END ---\n\n"
                        f"Answer based *only* on the text provided above."
                    )
            except Exception as e_ctx:
                logging.error(f"Error getting document context: {e_ctx}")

        # Add system prompt
        chat_messages.append({"role": "system", "content": system_prompt_content})

        # Add recent history
        history_limit = 4
        start_index = max(0, len(self.history) - history_limit)
        recent_history = self.history[start_index:]
        chat_messages.extend(recent_history)

        # Add user message
        chat_messages.append({"role": "user", "content": message})

        # Generate response using create_chat_completion
        logging.info("Generating response with manual context using create_chat_completion")
        stream = llm.create_chat_completion(
            messages=chat_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )

        complete_response = ""
        for chunk in stream:
            try:
                delta = chunk["choices"][0].get("delta", {})
                text = delta.get("content")
                if text:
                    self.response_chunk.emit(text)
                    complete_response += text
            except (KeyError, IndexError, TypeError) as e:
                logging.warning(f"Error extracting text from chunk: {e}")

        # Finalize
        if complete_response.strip():
            self.history.append({"role": "assistant", "content": complete_response})
            self.response_complete.emit(complete_response, True)
        else:
            logging.warning("Model generated an empty response.")
            self.error_occurred.emit("Model generated an empty response.")
            self.response_complete.emit("", False)

    except Exception as e:
        error_message = f"Error during inference: {str(e)}"
        logging.exception(error_message)
        self.error_occurred.emit(error_message)
        self.response_complete.emit("", False)
    finally:
        logging.debug("Inference thread finished.")

def send_message(self, message: str, max_tokens: int = 1024, temperature: float = 0.7):
    """Send a message to the model and get a response with true KV caching support"""
    # --- Get Model Info ---
    model_id = self.config.get('CURRENT_MODEL_ID')
    if not model_id:
        self.error_occurred.emit("No model selected in configuration.")
        return False
    model_info = self.model_manager.get_model_info(model_id)
    if not model_info:
        self.error_occurred.emit(f"Model '{model_id}' not found.")
        return False
    model_path = model_info.get('path')
    if not model_path or not Path(model_path).exists():
        self.error_occurred.emit(f"Model file not found for '{model_id}': {model_path}")
        return False
    context_window = model_info.get('context_window', 4096)

    # --- Determine KV Cache Path ---
    actual_kv_cache_path = None
    if self.use_kv_cache and self.current_kv_cache_path:
        if Path(self.current_kv_cache_path).exists():
            actual_kv_cache_path = self.current_kv_cache_path
            logging.info(f"Cache selected: {actual_kv_cache_path}")
        else:
            logging.warning(f"Selected KV cache file not found: {self.current_kv_cache_path}")
            self.error_occurred.emit(f"Selected KV cache file not found: {Path(self.current_kv_cache_path).name}")
    elif self.use_kv_cache:
        master_cache_path_str = self.config.get('MASTER_KV_CACHE_PATH')
        if master_cache_path_str and Path(master_cache_path_str).exists():
            actual_kv_cache_path = str(master_cache_path_str)
            logging.info(f"Using master KV cache: {actual_kv_cache_path}")
        else:
            logging.warning("KV cache enabled, but no cache selected and master cache is invalid or missing.")
            self.error_occurred.emit("KV cache enabled, but no cache selected/master invalid.")

    # Add user message to history
    self.history.append({"role": "user", "content": message})

    # --- Start Inference Thread ---
    inference_thread = threading.Thread(
        target=self._inference_thread_with_true_kv_cache,
        args=(message, model_path, context_window, actual_kv_cache_path, max_tokens, temperature),
        daemon=True,
    )
    inference_thread.start()

    return True
