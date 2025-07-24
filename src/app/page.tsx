'use client';

import { useState, useEffect } from 'react';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  postedDate: string;
  url: string;
}

interface SearchResponse {
  jobs: Job[];
  total_results: number;
  search_time: number;
  query: string;
  location?: string;
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [searchStats, setSearchStats] = useState<{
    total: number;
    time: number;
  } | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      setSearchStats(null);
      
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          location: locationQuery || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }

      const data: SearchResponse = await response.json();
      setJobs(data.jobs);
      setSearchStats({
        total: data.total_results,
        time: data.search_time,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setError('Please enter a job title or keyword');
      return;
    }
    fetchJobs();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">LinkedIn Job Board</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <input
                type="text"
                placeholder="Job title or keyword"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                required
              />
            </div>
            <div>
              <input
                type="text"
                placeholder="Location (optional)"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={locationQuery}
                onChange={(e) => setLocationQuery(e.target.value)}
              />
            </div>
            <div>
              <button 
                type="submit"
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search Jobs'}
              </button>
            </div>
          </div>
        </form>
        {/* Progress Bar */}
        {loading && (
          <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-blue-600 h-2 rounded-full animate-progress"
                style={{
                  width: '0%',
                  animation: 'progress 90s ease-out forwards'
                }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2 text-center">Searching for jobs...</p>
            <style jsx>{`
              @keyframes progress {
                from { width: 0%; }
                to { width: 100%; }
              }
            `}</style>
          </div>
        )}

        {/* Search Stats */}
        {searchStats && !loading && !error && (
          <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
            <p className="text-sm text-gray-600">
              Found {searchStats.total} jobs in {searchStats.time.toFixed(2)} seconds
            </p>
          </div>
        )}

        {/* Job Listings */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-500">Searching LinkedIn for jobs...</p>
              <p className="text-gray-400 text-sm mt-2">This may take a few moments</p>
            </div>
          ) : error ? (
            <div className="text-center text-red-500 py-8">
              <p className="font-semibold">{error}</p>
              <p className="text-sm mt-2">Please try again or modify your search criteria</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="font-semibold">No jobs found</p>
              <p className="text-sm mt-2">Try adjusting your search criteria or location</p>
            </div>
          ) : (
            jobs.map((job) => (
              <div key={job.id} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{job.title}</h2>
                    <p className="text-gray-600 mt-1">{job.company}</p>
                    <p className="text-gray-500 mt-1">{job.location}</p>
                    <p className="text-gray-700 mt-2 line-clamp-2">
                      {job.description}
                    </p>
                  </div>
                  <span className="text-sm text-gray-500">
                    Posted {new Date(job.postedDate).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-4">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View on LinkedIn →
                  </a>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
