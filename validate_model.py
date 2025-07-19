#!/usr/bin/env python3
"""
Script to validate the ONNX model file integrity
"""
import os
import onnx
import onnxruntime as ort

def validate_onnx_model(model_path):
    """Validate ONNX model file"""
    print(f"Validating ONNX model: {model_path}")
    
    # Check if file exists
    if not os.path.exists(model_path):
        print(f"❌ Model file does not exist: {model_path}")
        return False
    
    # Check file size
    file_size = os.path.getsize(model_path)
    print(f"📁 File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    try:
        # Try to load with ONNX
        print("🔍 Loading model with ONNX...")
        model = onnx.load(model_path)
        onnx.checker.check_model(model)
        print("✅ ONNX model validation passed")
        
        # Try to create inference session
        print("🔍 Creating ONNX Runtime inference session...")
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        print("✅ ONNX Runtime session created successfully")
        
        # Print model info
        print(f"📊 Model inputs: {[input.name for input in session.get_inputs()]}")
        print(f"📊 Model outputs: {[output.name for output in session.get_outputs()]}")
        
        return True
        
    except onnx.onnx_cpp2py_export.checker.ValidationError as e:
        print(f"❌ ONNX validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

if __name__ == "__main__":
    model_path = "inswapper_128.onnx"
    is_valid = validate_onnx_model(model_path)
    
    if not is_valid:
        print("\n🔧 Suggested solutions:")
        print("1. Delete the corrupted model file and let the app re-download it")
        print("2. Download a fresh copy from the official source")
        print("3. Check if the file was corrupted during transfer")