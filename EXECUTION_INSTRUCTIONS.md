# Execution Instructions

## Prerequisites

- Docker Desktop installed and running
- Windows PowerShell or Linux/Mac terminal
- Input files placed in the `input/` directory
- Ensure `challenge1b_input.json` is present with document list

## Build Instructions

Build the Docker image using the following command:

```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

**Note**: The build process will:

- Install Python dependencies including PyTorch (CPU-only)
- Download the SentenceTransformers model for offline use
- Set up the application environment
- Create necessary directories

**Expected build time**: 5-7 minutes depending on network speed
**Final image size**: ~2.2GB (optimized multi-stage build)

## Run Instructions

### Standard Command (Recommended):

```bash
docker run --platform linux/amd64 -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" mysolutionname:somerandomidentifier
```

### For Windows PowerShell:

```bash
docker run --platform linux/amd64 -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" mysolutionname:somerandomidentifier
```

### For Linux/Mac/Git Bash:

```bash
docker run --platform linux/amd64 -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" mysolutionname:somerandomidentifier
```

## Command Explanation

- `--platform linux/amd64`: Ensures consistent platform execution
- `-v "$(pwd)/input:/app/input"`: Mount local input directory to container
- `-v "$(pwd)/output:/app/output"`: Mount local output directory to container
- Professional ✅ status indicators shown during processing

## Input Requirements

The system expects:

1. `input/challenge1b_input.json` - Configuration file with:

   - `persona`: User role (e.g., "Food Contractor")
   - `job_to_be_done`: Specific task description
   - `documents`: List of PDF filenames to process

2. PDF files in `input/PDFs/` directory as specified in the JSON

## Output

The system generates:

- `output/1b_001_output.json` - Main results file containing:
  - Professional ✅ status messages throughout processing
  - Metadata about processed documents
  - Top 5 ranked relevant sections
  - Detailed subsection analysis with ingredients and instructions

## Execution Flow

1. **✅ Initialization**: System startup with professional status indicators
2. **✅ Model Loading**: SentenceTransformer model loads (CPU mode)
3. **✅ Document Processing**: All PDFs are parsed and analyzed
4. **✅ Content Analysis**: Semantic embeddings created for query and content
5. **✅ Ranking**: Sections ranked by relevance to user requirements
6. **✅ Output Generation**: Structured JSON results written to output directory

## Troubleshooting

- **Build fails**: Ensure Docker has sufficient disk space (3GB+)
- **Permission errors**: Check that Docker has access to the workspace directory
- **No output**: Verify input JSON format and PDF file availability
- **Memory issues**: The solution is optimized for CPU-only operation

## Performance Notes

- **Processing time**: ~30-60 seconds for 9 PDF documents
- **Memory usage**: ~2GB RAM during execution
- **CPU usage**: Utilizes available CPU cores for embedding generation
- **Image optimization**: Multi-stage Docker build reduces size by ~15%
- **User experience**: Professional ✅ status indicators throughout processing
- **Offline operation**: No internet required after initial build
