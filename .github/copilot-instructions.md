# PDF 圖片轉文字處理系統

A Docker-based PDF OCR system using Qwen2.5-VL model with vLLM inference engine for extracting and analyzing images from PDF documents with AI-powered description and OCR capabilities.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install system dependencies:
  - `sudo apt-get update && sudo apt-get install -y docker.io`
  - `sudo usermod -aG docker $USER` (logout/login required)
  - Install NVIDIA Container Toolkit if GPU available
- Clone and setup repository:
  - `./scripts/setup.sh` -- takes 5 seconds. Creates directories and .env file.
  - ALTERNATIVE if setup.sh fails: `mkdir -p input output temp models && cp .env.example .env`

### Python Development (Recommended for Code Changes)
- Install Python dependencies:
  - `pip3 install -r requirements.txt` -- takes 3 minutes. NEVER CANCEL.
- Test core functionality without Docker:
  - `python3 -c "import src.pdf_processor; import src.vlm_client; print('Modules OK')"` -- takes 2 seconds
  - `echo "n" | python3 main.py` -- takes 5 seconds. Tests PDF analysis without VLM.

### Docker Build and Run (Full System)
- Build PDF processor container:
  - `docker build . -t pdf-processor` -- takes 5-10 minutes. NEVER CANCEL. Set timeout to 15+ minutes.
  - NOTE: May fail with SSL certificate errors in some environments. Use Python development workflow instead.
- Start vLLM service (requires NVIDIA GPU):
  - `docker compose up -d vllm-qwen` -- takes 10-45 minutes for first run due to model download (20GB+). NEVER CANCEL. Set timeout to 60+ minutes.
  - Model download time depends on internet speed. Qwen2.5-VL-32B-Instruct-AWQ is ~20GB.
  - `docker compose logs -f vllm-qwen` -- Monitor startup progress. Wait for "Application startup complete".
- Process PDFs:
  - Place PDF files in `input/` directory
  - `docker compose run --rm pdf-processor` -- processing time varies by PDF size and image count. Set timeout to 30+ minutes for large PDFs.

### Manual Testing and Validation Scenarios
After making changes, ALWAYS test these scenarios:

1. **Basic PDF Analysis (No VLM Required)**:
   - `echo "n" | python3 main.py` 
   - Verify: Images extracted to `extracted_images/` directory
   - Expected: Shows count of images found in PDF

2. **Full Docker Workflow (If GPU Available)**:
   - `./scripts/process.sh`
   - Verify: Enhanced PDF created in `output/` directory with image descriptions
   - Expected: Blue text annotations added below images in output PDF

3. **Component Integration Test**:
   - `python3 -c "from src.vlm_client import QwenVLMClient; client = QwenVLMClient('http://localhost:8000'); print('VLM client created')"`
   - Only works if vLLM service is running

## Repository Structure and Navigation

### Key Files and Directories
```
/home/runner/work/pdf_ocr/pdf_ocr/
├── main.py                 # Main application entry point
├── src/
│   ├── pdf_processor.py    # Core PDF manipulation with PyMuPDF
│   └── vlm_client.py       # Qwen VLM API client for image analysis
├── scripts/
│   ├── setup.sh           # Environment setup script
│   └── process.sh         # End-to-end processing script
├── docker-compose.yml     # Orchestrates vLLM server and processor
├── Dockerfile            # PDF processor container definition
├── requirements.txt      # Python dependencies
├── input/               # Place PDF files here for processing
├── output/              # Enhanced PDFs with annotations
├── temp/                # Temporary processing files
└── extracted_images/    # Saved images from PDFs
```

### Important Code Locations
- PDF processing logic: `src/pdf_processor.py` - Contains image extraction and PDF enhancement functions
- VLM integration: `src/vlm_client.py` - Handles communication with Qwen model API
- Main workflow: `main.py` - Orchestrates PDF analysis and user interaction
- Docker configuration: `docker-compose.yml` - Model and service configuration
- Environment variables: `.env` - API URLs and model settings

## Configuration and Model Options

### Supported Models (in docker-compose.yml)
- `Qwen/Qwen2.5-VL-72B-Instruct-AWQ` (72B, 4-bit quantized, ~32GB VRAM)
- `Qwen/Qwen2.5-VL-32B-Instruct-AWQ` (32B, 4-bit quantized, ~16GB VRAM) - DEFAULT
- `Qwen/Qwen2.5-VL-7B-Instruct` (7B, ~8GB VRAM)

### Key Configuration Parameters
- `VLLM_API_URL`: Default `http://localhost:8000` for local development
- `--max-model-len`: Sequence length limit (default 8192)
- `--gpu-memory-utilization`: GPU memory usage (0.7 = 70%)
- `CUDA_VISIBLE_DEVICES`: GPU selection (default: 2)

## Common Commands and Expected Timing

### Build Commands
- `pip3 install -r requirements.txt` -- 3 minutes. NEVER CANCEL.
- `docker build . -t pdf-processor` -- 5-10 minutes. NEVER CANCEL. Set timeout to 15+ minutes.
- `docker compose up -d vllm-qwen` -- 10-45 minutes first run. NEVER CANCEL. Set timeout to 60+ minutes.

### Test Commands  
- `python3 main.py` -- Interactive mode, processes all PDFs in input/
- `echo "n" | python3 main.py` -- Analysis only, no VLM processing. Takes 5 seconds.
- `./scripts/setup.sh` -- 5 seconds. Environment setup.
- `./scripts/process.sh` -- Full pipeline. Time varies with PDF size.

### Debugging Commands
- `docker compose logs vllm-qwen` -- Check vLLM service status
- `docker compose logs pdf-processor` -- Check processing logs
- `docker compose ps` -- Show running services

## Troubleshooting

### Common Issues
1. **Docker Build SSL Errors**: 
   - Use Python development workflow: `pip3 install -r requirements.txt`
   - SSL certificate issues are common in some environments

2. **GPU Memory Insufficient**:
   - Edit docker-compose.yml: Change to smaller model (7B or 32B)
   - Reduce `--gpu-memory-utilization` value

3. **Model Download Slow/Fails**:
   - Pre-download to `./models` directory if available
   - Edit docker-compose.yml to use local model path

4. **vLLM Service Won't Start**:
   - Check `docker compose logs vllm-qwen`
   - Verify NVIDIA Container Toolkit installation
   - Ensure sufficient GPU memory

### No GPU Environment Limitations
- Cannot run full VLM inference without NVIDIA GPU
- Use Python development mode for code changes: `echo "n" | python3 main.py`
- Test image extraction and PDF processing logic
- Docker build may fail due to environment SSL issues

## Validation Requirements

### Before Committing Changes
1. **Code Changes**: 
   - Run `python3 -c "import src.pdf_processor; import src.vlm_client"`
   - Test with `echo "n" | python3 main.py`

2. **Docker Changes**:
   - `docker build . -t pdf-processor` (if environment supports)
   - Verify no new build errors introduced

3. **Configuration Changes**:
   - Check docker-compose.yml syntax: `docker compose config`
   - Verify .env.example has required variables

### End-to-End Testing (GPU Required)
1. Start services: `docker compose up -d vllm-qwen`
2. Wait for ready: Monitor logs until "Application startup complete"
3. Process test PDF: `docker compose run --rm pdf-processor`
4. Verify output: Check `output/` for enhanced PDF with blue annotations

## Performance Expectations

### Timing Benchmarks (Measured)
- Environment setup: 5 seconds
- Python dependency install: 3 minutes
- Docker build: 5-10 minutes  
- Model download (first time): 10-45 minutes
- PDF analysis (230 images): 5 seconds
- VLM processing: Varies by image count and model size

### Timeout Recommendations
- Set 15+ minute timeout for Docker builds
- Set 60+ minute timeout for initial vLLM startup
- Set 30+ minute timeout for large PDF processing
- **NEVER CANCEL** long-running operations