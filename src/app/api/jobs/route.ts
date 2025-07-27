import { NextResponse } from 'next/server';

// Create a persistent rate limiter Map outside the function
const rateLimiter = new Map();

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { query, location } = body;
    
    try {
      const ip = request.headers.get('x-forwarded-for') || 'unknown';
      const ipKey = `ip:${ip}`;
      const window = 100000; // 100 seconds
      const limit = 1; // 1 requests per 100 seconds
      
      if (rateLimiter.has(ipKey)) {
        const lastRequestTime = rateLimiter.get(ipKey);
        if (Date.now() - lastRequestTime < window) {
          return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 });
        }
      }
      
      // Update the rate limiter with current request time
      rateLimiter.set(ipKey, Date.now());
      
    } catch (error) {
      console.error('Error in rate limiting:', error);
      return NextResponse.json(
        { error: error instanceof Error ? error.message : 'Failed to process rate limiting' },
        { status: 500 }
      );
    }

    if (!query) {
      return NextResponse.json(
        { error: 'Search query is required' },
        { status: 400 }
      );
    }

    // Forward the request to our Python scraper server
    const response = await fetch('http://127.0.0.1:8000/jobs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        location,
        num_jobs: 10
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch jobs from scraper');
    }

    const data = await response.json();
    
    if (!data.jobs || !Array.isArray(data.jobs)) {
      throw new Error('Invalid response format from scraper');
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching jobs:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch jobs' },
      { status: 500 }
    );
  }
} 