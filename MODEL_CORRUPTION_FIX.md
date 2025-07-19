# Face Swap Model Corruption Fix

## Problem Description

The face swap application was failing to start with the following error:

```
[ONNXRuntimeError] : 7 : INVALID_PROTOBUF : Load model from inswapper_128.onnx failed:Protobuf parsing failed.
```

This error indicates that the `inswapper_128.onnx` model file is corrupted and cannot be loaded by ONNX Runtime.

## Root Cause

The ONNX model file (`inswapper_128.onnx`) became corrupted, likely due to:
- Incomplete download during initial setup
- File system corruption
- Interrupted transfer or deployment process
- Network issues during model download

## Solution Overview

We've implemented a comprehensive fix that includes:

1. **Manual Fix Script** (`fix_model.py`) - For immediate resolution
2. **Enhanced Application** (`main_fixed.py`) - With automatic recovery
3. **Validation Tools** (`validate_model.py`) - For diagnostics
4. **Test Suite** (`test_fix.py`) - For verification

## Quick Fix (Immediate Solution)

### Option 1: Manual Fix Script

Run the fix script to remove the corrupted model and clear cache:

```bash
python fix_model.py
```

This script will:
- Create a backup of the corrupted model
- Remove the corrupted file
- Clear InsightFace cache directories
- Allow the application to re-download a fresh model

### Option 2: Manual Steps

If you prefer manual steps:

```bash
# 1. Remove the corrupted model
rm inswapper_128.onnx

# 2. Clear InsightFace cache (Linux/Mac)
rm -rf ~/.insightface
rm -rf ~/.cache/insightface

# 3. Clear InsightFace cache (Windows)
rmdir /s "%USERPROFILE%\.insightface"

# 4. Restart your application
python main.py
```

## Long-term Solution (Recommended)

### Use the Enhanced Application

Replace your current main application with the enhanced version that includes automatic recovery:

```bash
# Use the fixed version with auto-recovery
python main_fixed.py
```

### Key Features of the Enhanced Application

1. **Automatic Model Validation**
   - Validates ONNX model integrity on startup
   - Detects corrupted models before they cause crashes

2. **Auto-Recovery System**
   - Automatically fixes corrupted models
   - Retries model loading with progressive recovery steps
   - Clears cache and re-downloads when necessary

3. **Enhanced Health Checks**
   - `/health` endpoint now includes model validation status
   - Memory usage monitoring
   - InsightFace version information

4. **Manual Recovery Endpoint**
   - `POST /fix-model` - Manually trigger model fix
   - Useful for remote debugging and maintenance

### API Endpoints

The enhanced application includes all original endpoints plus:

- `GET /health` - Enhanced health check with model validation
- `POST /fix-model` - Manual model corruption fix

## Docker Deployment

Update your Dockerfile to use the fixed version:

```dockerfile
# Replace the CMD line with:
CMD ["python", "main_fixed.py"]
```

Or update your docker-compose.yml:

```yaml
services:
  face-swap:
    # ... other configuration
    command: python main_fixed.py
```

## Validation and Testing

### Test the Fix

Run the test suite to verify everything is working:

```bash
python test_fix.py
```

### Validate Model Integrity

Use the validation script to check model health:

```bash
python validate_model.py
```

### Health Check

Once the application is running, check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "face_analysis_ready": true,
  "swapper_model_ready": true,
  "model_file_valid": true,
  "memory_usage_mb": 1234.56,
  "insightface_version": "0.7.3"
}
```

## Prevention

To prevent future model corruption:

1. **Use the Enhanced Application** - It includes automatic recovery
2. **Monitor Health Checks** - Regular monitoring of `/health` endpoint
3. **Backup Models** - Keep backup copies of working models
4. **Stable Storage** - Ensure reliable file system and storage
5. **Network Stability** - Ensure stable network during deployments

## Troubleshooting

### If the fix doesn't work:

1. **Check Python Environment**
   ```bash
   python -c "import insightface; print(insightface.__version__)"
   python -c "import onnxruntime; print('ONNX Runtime available')"
   ```

2. **Check File Permissions**
   ```bash
   ls -la inswapper_128.onnx
   ```

3. **Check Disk Space**
   ```bash
   df -h
   ```

4. **Manual Download**
   If automatic download fails, manually download the model:
   ```python
   import insightface
   model = insightface.model_zoo.get_model('inswapper_128.onnx', download=True, download_zip=True)
   ```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_PROTOBUF` | Corrupted ONNX file | Run `fix_model.py` |
| `FileNotFoundError` | Missing model file | Let app re-download |
| `PermissionError` | File permission issues | Check file permissions |
| `OutOfMemoryError` | Insufficient RAM | Use smaller images or add more RAM |

## Files Created

- `fix_model.py` - Manual fix script
- `main_fixed.py` - Enhanced application with auto-recovery
- `validate_model.py` - Model validation utility
- `test_fix.py` - Test suite
- `MODEL_CORRUPTION_FIX.md` - This documentation

## Migration Guide

### From Original to Enhanced Version

1. **Backup Current Setup**
   ```bash
   cp main.py main.py.backup
   ```

2. **Test the Enhanced Version**
   ```bash
   python main_fixed.py
   ```

3. **Update Production**
   ```bash
   # Update your deployment scripts to use main_fixed.py
   # Update Docker files
   # Update process managers (systemd, supervisor, etc.)
   ```

4. **Monitor**
   - Check `/health` endpoint regularly
   - Monitor application logs for auto-recovery events
   - Set up alerts for model corruption events

## Support

If you continue to experience issues:

1. Check the application logs for detailed error messages
2. Run the validation script: `python validate_model.py`
3. Try the manual fix: `python fix_model.py`
4. Use the enhanced application: `python main_fixed.py`
5. Check the health endpoint: `GET /health`

The enhanced application provides much better error handling and automatic recovery, making it the recommended solution for production deployments.