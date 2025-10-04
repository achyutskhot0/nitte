# Legal Lens - AI-Powered Legal Document Analysis

Legal Lens is an intelligent legal document analysis system that provides comprehensive insights for both legal professionals and citizens. The system uses AI to classify, extract, and summarize legal documents with real-time processing capabilities.

## Features

### 🎯 Core Functionality
- **Document Classification**: Automatically identifies legal documents
- **Legal Analysis**: Professional-grade analysis for lawyers
- **Citizen Summary**: Simplified explanations for non-legal users
- **Key Facts Extraction**: Identifies important information and entities
- **Next Steps**: Extracts deadlines and actionable items

### 🚀 Interactive Features
- **Real-time Processing**: Live progress updates via WebSocket
- **File Management**: Upload, view, delete, and reprocess documents
- **Export Functionality**: Download analysis results as JSON
- **Recent Files**: Quick access to previously processed documents
- **Responsive UI**: Modern, mobile-friendly interface

### 📊 Backend Capabilities
- **RESTful API**: Comprehensive API for all operations
- **Database Storage**: SQLite database for file and result management
- **Progress Tracking**: Real-time status updates
- **Error Handling**: Robust error management and reporting
- **Health Monitoring**: System health and statistics endpoints

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd legal-lens
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download spaCy model (required for NLP processing):
```bash
python -m spacy download en_core_web_sm
```

4. Start the application:
```bash
python start.py
```

The application will be available at:
- **Frontend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

### Web Interface
1. Open your browser and navigate to http://localhost:8000
2. Upload legal documents (PDF, DOCX, or TXT files)
3. View real-time processing progress
4. Explore analysis results in different tabs:
   - **Legal Analysis**: Professional legal insights
   - **Citizen Summary**: Simplified explanations
   - **Next Steps**: Deadlines and action items
   - **Key Facts**: Extracted information and entities

### API Usage
The system provides a comprehensive REST API:

#### Upload Documents
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@document.pdf"
```

#### Process Document
```bash
curl -X POST "http://localhost:8000/summaries/{file_id}"
```

#### List Files
```bash
curl -X GET "http://localhost:8000/files"
```

#### Get File Results
```bash
curl -X GET "http://localhost:8000/files/{file_id}/results"
```

#### Delete File
```bash
curl -X DELETE "http://localhost:8000/files/{file_id}"
```

## Architecture

### Frontend
- **HTML5/CSS3**: Modern, responsive interface
- **JavaScript**: Interactive functionality and WebSocket communication
- **Bulma CSS**: Professional styling framework
- **Font Awesome**: Icon library

### Backend
- **FastAPI**: High-performance web framework
- **SQLite**: Lightweight database for file management
- **WebSocket**: Real-time communication
- **Background Tasks**: Asynchronous processing

### AI Components
- **Document Classifier**: Legal document identification
- **Text Extraction**: PDF and DOCX processing
- **Fact Extraction**: Key information identification
- **Summarization**: AI-powered content summarization
- **Entity Recognition**: Named entity extraction

## File Structure

```
legal-lens/
├── frontend/                 # Frontend files
│   ├── index.html           # Main HTML file
│   └── app.js              # JavaScript functionality
├── classifier/              # Document classification
│   ├── clf_infer.py        # Inference script
│   └── clf_train.py        # Training script
├── extraction/              # Fact extraction
│   ├── extract.py          # Extraction logic
│   └── fields.yaml         # Field definitions
├── summarisers/             # AI summarization
│   ├── lawyer_sum.py       # Legal analysis
│   ├── citizen_sum.py      # Citizen summary
│   └── together_client.py  # AI client
├── nextsteps/               # Next steps extraction
│   ├── next_steps.py       # Processing logic
│   └── calendar.py         # Calendar integration
├── prompts/                 # AI prompts
│   ├── lawyer.txt          # Legal analysis prompt
│   └── citizen.txt         # Citizen summary prompt
├── templates/               # Template files
│   └── next_steps.md.j2    # Next steps template
├── glue.py                 # Main FastAPI application
├── start.py                # Startup script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Configuration

### Environment Variables
- `UPLOAD_DIR`: Directory for uploaded files (default: "file_queue")
- `RESULTS_DIR`: Directory for results (default: "results")
- `DB_FILE`: Database file path (default: "legal_lens.db")

### AI Model Configuration
The system uses various AI models for different tasks:
- **Classification**: SetFit model for legal document identification
- **Summarization**: Together AI for content generation
- **Entity Recognition**: spaCy for named entity extraction

## Development

### Running in Development Mode
```bash
python start.py
```

The server will automatically reload on code changes.

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation.

### Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test statistics
curl http://localhost:8000/stats
```

## Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Port already in use**:
   - Change the port in `start.py`
   - Or kill the process using the port

3. **File upload errors**:
   - Check file permissions
   - Ensure sufficient disk space
   - Verify file format is supported

4. **AI processing failures**:
   - Check internet connection (for Together AI)
   - Verify model files are present
   - Check system resources

### Logs
The application logs are displayed in the console. For production deployment, consider using a proper logging configuration.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the troubleshooting section

## Roadmap

- [ ] Multi-language support
- [ ] Advanced search and filtering
- [ ] User authentication and authorization
- [ ] Batch processing capabilities
- [ ] Integration with legal databases
- [ ] Mobile application
- [ ] Advanced analytics and reporting