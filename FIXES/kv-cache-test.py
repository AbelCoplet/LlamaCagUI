#!/usr/bin/env python3
"""
Test script for KV cache functionality with llama-cpp-python.
This script validates the approach of using low-level token generation 
after loading a saved KV cache state.
"""

import os
import sys
import pickle
from pathlib import Path
import time
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

try:
    from llama_cpp import Llama
except ImportError:
    logging.error("llama-cpp-python is not installed. Install with: pip install llama-cpp-python")
    sys.exit(1)

def test_kv_cache(model_path, context_text, test_query, cache_path, temperature=0.7, max_tokens=512):
    """Test KV cache functionality by:
    1. Processing context text and saving state
    2. Loading state and generating a response to test_query
    3. Comparing with baseline approach
    """
    start_time = time.time()
    logging.info(f"Using model: {model_path}")
    
    # Part 1: Process context and save KV cache
    logging.info(f"Creating KV cache for context ({len(context_text)} chars)...")
    llm = Llama(model_path=model_path, n_ctx=8192, n_threads=4)
    
    # Tokenize context
    context_tokens = llm.tokenize(context_text.encode('utf-8'))
    logging.info(f"Context tokenized to {len(context_tokens)} tokens")
    
    # Process context
    llm.eval(context_tokens)
    logging.info("Context processed and model state updated")
    
    # Save state
    try:
        logging.info(f"Saving KV cache state to {cache_path}")
        state_data = llm.save_state()
        with open(cache_path, 'wb') as f:
            pickle.dump(state_data, f)
        logging.info("KV cache saved successfully")
    except Exception as e:
        logging.error(f"Error saving KV cache: {e}")
        return
    
    logging.info(f"KV cache creation took {time.time() - start_time:.2f} seconds")
    
    # Part 2: Test the KV cache by loading it and generating a response
    logging.info("\n--- Testing KV Cache Approach ---")
    kv_start_time = time.time()
    
    # Load a fresh model
    llm2 = Llama(model_path=model_path, n_ctx=8192, n_threads=4)
    
    # Load state
    try:
        logging.info(f"Loading KV cache from {cache_path}")
        with open(cache_path, 'rb') as f:
            state_data = pickle.load(f)
        llm2.load_state(state_data)
        logging.info("KV cache loaded successfully")
    except Exception as e:
        logging.error(f"Error loading KV cache: {e}")
        return
    
    # Tokenize query
    query_tokens = llm2.tokenize(f"\n\nQuestion: {test_query}\n\nAnswer: ".encode('utf-8'))
    logging.info(f"Query tokenized to {len(query_tokens)} tokens")
    
    # Evaluate query tokens
    llm2.eval(query_tokens)
    logging.info("Query tokens evaluated")
    
    # Generate response using low-level approach
    logging.info("Generating response using low-level token sampling...")
    eos_token = llm2.token_eos()
    tokens_generated = []
    
    for _ in range(max_tokens):
        token_id = llm2.sample(temperature=temperature)
        if token_id == eos_token:
            break
        tokens_generated.append(token_id)
        llm2.eval([token_id])
    
    # Get the response
    kv_response = llm2.detokenize(tokens_generated).decode('utf-8', errors='replace')
    logging.info(f"Generated {len(tokens_generated)} tokens")
    logging.info(f"KV cache approach took {time.time() - kv_start_time:.2f} seconds")
    
    # Part 3: Compare with baseline approach (full context as prompt)
    logging.info("\n--- Testing Baseline Approach ---")
    baseline_start_time = time.time()
    
    # Load a fresh model
    llm3 = Llama(model_path=model_path, n_ctx=8192, n_threads=4)
    
    # Create a combined prompt
    prompt = f"{context_text}\n\nQuestion: {test_query}\n\nAnswer: "
    
    # Generate response using create_completion
    response = llm3.create_completion(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    baseline_response = response['choices'][0]['text']
    logging.info(f"Baseline approach took {time.time() - baseline_start_time:.2f} seconds")
    
    # Compare results
    logging.info("\n--- Results ---")
    logging.info(f"KV Cache Response:\n{kv_response}")
    logging.info(f"Baseline Response:\n{baseline_response}")
    logging.info(f"KV Cache Approach: {time.time() - kv_start_time:.2f} seconds")
    logging.info(f"Baseline Approach: {time.time() - baseline_start_time:.2f} seconds")
    
    return {
        "kv_response": kv_response,
        "baseline_response": baseline_response,
        "kv_time": time.time() - kv_start_time,
        "baseline_time": time.time() - baseline_start_time
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test KV Cache functionality")
    parser.add_argument("--model", type=str, required=True, help="Path to the model file")
    parser.add_argument("--context", type=str, help="Context text file path")
    parser.add_argument("--cache", type=str, default="test_cache.pickle", help="Path to save/load KV cache")
    parser.add_argument("--query", type=str, default="What is the main topic of this text?", help="Test query")
    
    args = parser.parse_args()
    
    # Load context from file if specified
    if args.context:
        with open(args.context, 'r', encoding='utf-8') as f:
            context_text = f.read()
    else:
        # Sample context
        context_text = """
        Context-Augmented Generation (CAG) is a technique for enhancing large language models by feeding documents
        into the model's context window and enabling chat interactions that leverage that context. This allows
        users to effectively "chat with their documents" by asking questions that the model can answer based on 
        the document's content. Unlike standard Retrieval-Augmented Generation (RAG) that retrieves snippets of text,
        CAG processes the entire document through the language model once to generate its internal state (the KV cache),
        saves this state to disk, and loads the saved state for subsequent interactions. This approach allows the model
        to "remember" the document context without re-processing the full text for each interaction.
        
        The key advantages of CAG include:
        1. Deep contextual understanding by having the model's state primed with the document content
        2. Fast follow-up questions as only the new query needs to be processed
        3. Efficient utilization of large context windows (e.g., 128K tokens)
        4. Significant performance improvements for subsequent interactions
        
        CAG is particularly useful for in-depth document analysis, knowledge base interactions, and personalized 
        learning experiences where users need to have extended conversations about specific content.
        """
    
    # Run the test
    results = test_kv_cache(
        model_path=args.model,
        context_text=context_text,
        test_query=args.query,
        cache_path=args.cache
    )
    
    # Summarize speedup if results were obtained
    if results and results["baseline_time"] > 0:
        speedup = results["baseline_time"] / results["kv_time"] if results["kv_time"] > 0 else 0
        print(f"\nKV Cache approach is {speedup:.2f}x faster than the baseline")
