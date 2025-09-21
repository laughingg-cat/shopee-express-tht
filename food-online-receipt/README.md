# Food Receipt AI

A minimal web application that uses OCR and AI to extract and analyze food receipt data.

## Quick Start

### Using Docker (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repo-url>
   cd food-online-receipt
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Main app: http://localhost:7860
   - Database admin: http://localhost:8080

### Using Python (Development)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   sudo apt-get install tesseract-ocr  # On Ubuntu/Debian
   ```

2. **Set environment variable:**
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

3. **Run the application:**
   ```bash
   python src/app.py
   ```

## Features

- **Upload Receipts**: Upload receipt images for OCR processing
- **AI Chat**: Ask questions about your food expenses
- **View Data**: Browse all processed receipts
- **SQL Queries**: Run custom database queries

## Requirements

- Python 3.11+
- OpenAI API key
- Tesseract OCR
- Docker (for containerized deployment)

## Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## API Endpoints

- `POST /upload_and_process` - Upload and process receipt images
- `POST /chat` - Chat with AI about expenses
- `GET /get_receipts` - Get all receipts
- `POST /execute_custom_query` - Run SQL queries
- `POST /delete_receipt` - Delete receipts

## Database

Uses SQLite database (`receipts.db`) with the following schema:
- `receipts` table stores receipt data with JSON extraction results
- Automatic database initialization on first run
- Data persists between container restarts