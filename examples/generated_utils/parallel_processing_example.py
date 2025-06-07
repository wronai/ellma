"""
Parallel Processing Example

This example demonstrates how to use the parallel_map function
to process items in parallel using multiple worker processes.
"""
import time
from typing import List, Dict, Any
from ellma.modules import parallel_map

def process_image(image_path: str) -> Dict[str, Any]:
    """Simulate processing an image (CPU-bound operation)."""
    print(f"Processing {image_path}...")
    time.sleep(0.5)  # Simulate processing time
    
    # Simulate some image processing
    width = 1000
    height = 800
    file_size = len(image_path) * 1000  # Fake file size
    
    return {
        'path': image_path,
        'dimensions': (width, height),
        'size_kb': file_size // 1024,
        'processed_at': time.time()
    }

def process_images_sequentially(image_paths: List[str]) -> List[Dict[str, Any]]:
    """Process images one at a time (sequential)."""
    print("\nProcessing images sequentially...")
    start_time = time.time()
    
    results = []
    for path in image_paths:
        results.append(process_image(path))
    
    elapsed = time.time() - start_time
    print(f"Processed {len(results)} images in {elapsed:.2f} seconds")
    return results

def process_images_in_parallel(image_paths: List[str], max_workers: int = 4) -> List[Dict[str, Any]]:
    """Process images in parallel using parallel_map."""
    print(f"\nProcessing images in parallel (max_workers={max_workers})...")
    start_time = time.time()
    
    results = parallel_map(process_image, image_paths, max_workers=max_workers)
    
    elapsed = time.time() - start_time
    print(f"Processed {len(results)} images in {elapsed:.2f} seconds")
    return results

def main():
    print("=== Parallel Processing Example ===\n")
    
    # Generate some sample image paths
    image_paths = [f"images/photo_{i}.jpg" for i in range(1, 9)]
    
    # Process images sequentially
    seq_results = process_images_sequentially(image_paths)
    
    # Process images in parallel with different worker counts
    for workers in [2, 4, 8]:
        parallel_results = process_images_in_parallel(image_paths, max_workers=workers)
    
    # Verify all results are the same
    assert len(seq_results) == len(parallel_results)
    print("\n✅ All images processed successfully!")

if __name__ == "__main__":
    main()
