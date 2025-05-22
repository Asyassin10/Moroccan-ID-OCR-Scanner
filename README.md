# Moroccan ID OCR Scanner

A Flask-based REST API service that uses Optical Character Recognition (OCR) to extract information from Moroccan National ID cards. The service processes uploaded ID card images and returns structured data including personal information, ID numbers, dates, and other relevant details.

## Features

- **OCR Processing**: Uses EasyOCR with French language support to read text from ID card images
- **Image Preprocessing**: Applies advanced image enhancement techniques for better OCR accuracy
- **Smart Data Extraction**: Intelligently parses and categorizes extracted text into structured information
- **Moroccan ID Specific**: Tailored specifically for Moroccan National ID card format and data
- **RESTful API**: Simple HTTP endpoints for easy integration
- **Health Check**: Built-in health monitoring endpoint

## Extracted Information

The service can extract the following information from Moroccan ID cards:

- **Card Type**: Identifies if it's a Moroccan National ID
- **Personal Information**: Full name, first name, last name
- **Identification**: ID number (various formats supported)
- **Dates**: Date of birth, issue date, expiry date
- **Location**: Place of birth (supports major Moroccan cities)
- **Demographics**: Gender, nationality
- **Raw Data**: Original OCR text results

## Docker Image Details

- **Base Image**: Python 3.9-slim
- **System Dependencies**: OpenCV, OpenGL, and other required libraries
- **Python Dependencies**: Flask, EasyOCR, OpenCV-Python, NumPy, Pillow, PyTorch, Gunicorn
- **Port**: 5000
- **Production Ready**: Uses Gunicorn WSGI server with optimized settings

### Requirements (for reference)
```
Flask==2.3.3
easyocr==1.7.0
opencv-python==4.8.1.78
numpy==1.24.3
pillow<10.0.0
torch==2.0.1
torchvision==0.15.2
gunicorn==21.2.0
```

## Installation & Deployment

This application is designed to run in Docker containers for easy deployment and consistency across environments.

### Prerequisites

- Docker installed on your system
- Internet connection for downloading dependencies

### Quick Start with Docker

#### Option 1: Pull from Docker Hub
```bash
# Pull the pre-built image from Docker Hub
docker pull yassine-as/moroccan-id-ocr:latest

# Run the container
docker run -d -p 5000:5000 --name moroccan-ocr yassine-as/moroccan-id-ocr:latest
```

#### Option 2: Build from Source
```bash
# Clone the repository
git clone <your-repository-url>
cd moroccan-id-ocr-scanner

# Build the Docker image
docker build -t yassine-as/moroccan-id-ocr:latest .

# Run the container
docker run -d -p 5000:5000 --name moroccan-ocr yassine-as/moroccan-id-ocr:latest
```

### Docker Commands

```bash
# Build the image
docker build -t yassine-as/moroccan-id-ocr:latest .

# Run the container
docker run -d -p 5000:5000 --name moroccan-ocr yassine-as/moroccan-id-ocr:latest

# Check container status
docker ps

# View container logs
docker logs moroccan-ocr

# Stop the container
docker stop moroccan-ocr

# Remove the container
docker rm moroccan-ocr

# Push to Docker Hub (for maintainers)
docker push yassine-as/moroccan-id-ocr:latest
```

## API Endpoints

### POST /ocr

Processes an uploaded ID card image and extracts information.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Form data with 'image' field containing the ID card image file

**Response:**
```json
{
    "success": true,
    "data": {
        "card_type": "Moroccan National ID",
        "full_name": "JOHN DOE",
        "first_name": "JOHN",
        "last_name": "DOE",
        "id_number": "AB123456",
        "date_of_birth": "01/01/1990",
        "place_of_birth": "Casablanca",
        "nationality": "Moroccan",
        "gender": "Male",
        "expiry_date": "01/01/2030",
        "issue_date": "01/01/2020",
        "address": null,
        "raw_text": ["ROYAUME", "DU", "MAROC", "JOHN", "DOE", ...]
    }
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Error message description"
}
```

### GET /health

Health check endpoint to verify service status.

**Response:**
```json
{
    "status": "healthy",
    "service": "Moroccan ID OCR Scanner"
}
```

## Usage Examples

### Using curl

```bash
# Upload an ID card image
curl -X POST \
  http://localhost:5000/ocr \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@/path/to/id-card.jpg'

# Health check
curl http://localhost:5000/health
```

### Using Python requests

```python
import requests

# OCR processing
url = 'http://localhost:5000/ocr'
files = {'image': open('id-card.jpg', 'rb')}
response = requests.post(url, files=files)
result = response.json()

print(result)
```

### Using JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://localhost:5000/ocr', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Production Deployment

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  moroccan-ocr:
    image: yassine-as/moroccan-id-ocr:latest
    ports:
      - "5000:5000"
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

### Environment Variables

- `FLASK_APP=app.py` (default)
- `FLASK_ENV=production` (default)

## Technical Details

### Image Preprocessing

The service applies several image enhancement techniques to improve OCR accuracy:

1. **Grayscale Conversion**: Converts color images to grayscale for better text recognition
2. **Noise Reduction**: Uses Non-local Means Denoising to remove image noise
3. **Contrast Enhancement**: Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
4. **Format Optimization**: Converts processed images to optimal format for OCR

### Data Extraction Logic

The system uses intelligent pattern matching and text analysis:

- **ID Number Recognition**: Supports multiple Moroccan ID formats (alphanumeric patterns)
- **Date Parsing**: Handles various date formats (DD/MM/YYYY, DD-MM-YYYY, etc.)
- **City Recognition**: Extensive database of Moroccan cities and regions
- **Name Extraction**: Filters out common keywords to identify personal names
- **Gender Detection**: Recognizes gender indicators in French and Arabic contexts

### Supported ID Formats

- Standard Moroccan National ID cards
- Various ID number patterns: `A123456`, `AB1234567`, `U1234567`, etc.
- French language text recognition
- Date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY/MM/DD

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: When no image file is provided
- **500 Internal Server Error**: When OCR processing fails
- **Detailed Error Messages**: Specific error descriptions in JSON format

## Performance Considerations

- **Gunicorn Configuration**: Optimized for production with 1 worker and 120-second timeout
- **Memory Efficient**: Uses slim Python base image to minimize resource usage
- **OCR Caching**: EasyOCR model is loaded once at startup
- **Image Processing**: Efficient OpenCV operations for fast processing

## Security Notes

- **File Upload Validation**: Only processes uploaded image files
- **No Data Persistence**: Processed images and results are not stored
- **Memory Management**: Images are processed in memory and cleaned up automatically
