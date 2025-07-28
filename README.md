# Adobe Hackathon Document Processor

## Overview

This is an AI-powered document analysis system that processes multiple PDF documents to extract relevant sections based on user requirements. The solution uses semantic similarity matching to identify and rank the most pertinent content for specific personas and tasks.

## Key Features

- **AI-Powered Analysis**: Uses SentenceTransformers for semantic understanding
- **Optimized Docker**: Multi-stage build for reduced image size (2.2GB)
- **Multi-Level Analysis**: Extracts both sections and detailed subsections
- **Professional Output**: Clean JSON with ✅ status indicators
- **Offline Operation**: No internet required after build
- **Humanized Code**: Natural variable names and professional messaging

## Quick Start

1. **Build**: `docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .`
2. **Run**: `docker run --platform linux/amd64 -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" mysolutionname:somerandomidentifier`
3. **Check Output**: Results in `output/1b_001_output.json` with ✅ status messages

> For detailed instructions, see `EXECUTION_INSTRUCTIONS.md`
> For methodology details, see `approach_explanation.md`

## File Structure

```
adobe-hackathon-offline/
├── process_pdf.py                  # Main processing script (humanized)
├── Dockerfile                      # Optimized multi-stage build
├── requirements.txt                # Python dependencies
├── approach_explanation.md         # Methodology documentation
├── EXECUTION_INSTRUCTIONS.md       # Detailed run instructions
├── input/                          # Input files and PDFs
│   ├── challenge1b_input.json      # Configuration file
│   └── PDFs/                       # PDF documents to process
├── output/                         # Processing results (JSON)
└── models/                         # Pre-downloaded AI models
    └── all-MiniLM-L6-v2/           # SentenceTransformer model
```

## Output Format

The system generates `output/1b_001_output.json` with:

- **Professional Status**: ✅ checkmark indicators for each processing step
- **Metadata**: Processing timestamp, input documents, persona, job requirements
- **Extracted Sections**: Top 5 ranked relevant sections with importance scores
- **Subsection Analysis**: Detailed ingredient lists and instructions with clean formatting

## Technical Specifications

- **AI Model**: all-MiniLM-L6-v2 (87MB, pre-downloaded for offline use)
- **Base Image**: Python 3.9-slim with multi-stage optimization
- **Final Size**: ~2.2GB (optimized from 2.6GB baseline)
- **Operation**: CPU-only, completely offline after build
- **Processing**: ~30-60 seconds for 9 PDF documents with ✅ status updates

## Performance Notes

- **Memory Usage**: ~2GB RAM during execution
- **CPU Optimized**: Utilizes available CPU cores for embedding generation
- **Docker Optimization**: Multi-stage build reduces image size by ~15%
- **Storage**: Volume-mounted input/output for data persistence
- **User Experience**: Professional ✅ status messages throughout processing

## Troubleshooting

### Build Issues

- Ensure Docker has sufficient disk space (3GB+)
- Verify Docker Desktop is running
- Check platform compatibility (linux/amd64)

### Runtime Issues

- Verify `challenge1b_input.json` format and PDF file availability
- Check Docker volume mounting permissions
- Ensure output directory is writable

### Performance Issues

- Monitor memory usage (~2GB required)
- For large document sets, consider processing in batches
- CPU-only operation may be slower on low-end systems

## License

Created for Adobe Hackathon 2025
