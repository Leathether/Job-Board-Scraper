# LinkedIn Job Scraper

A web application that scrapes and displays LinkedIn job listings with a modern UI. Built with Next.js, FastAPI, and Selenium.

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Chrome browser installed

## Quick Start

```bash
# Install dependencies and set up the environment
npm run setup

# Start both frontend and backend servers
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Features

- Real-time LinkedIn job scraping
- Search by job title/keywords
- Filter by location
- Modern, responsive UI
- Job details including company, location, and description

## Development

The project consists of two main parts:
1. Frontend (Next.js) in the root directory
2. Backend (FastAPI + Selenium) in the `backend` directory

### Available Scripts

- `npm run dev` - Start both frontend and backend servers
- `npm run dev:frontend` - Start only the frontend server
- `npm run dev:backend` - Start only the backend server
- `npm run build` - Build the frontend for production
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint

## Troubleshooting

If you encounter any issues:

1. Make sure Chrome is installed on your system
2. Check that Python and Node.js are in your system PATH
3. If you get a "module not found" error, try running `npm run setup` again
4. If the backend fails to start, try running `cd backend && python server.py` directly to see any Python-specific errors

## Notes

- The scraper uses Selenium with Chrome in headless mode
- Rate limiting and anti-scraping measures may affect the results
- For development purposes only - respect LinkedIn's terms of service
