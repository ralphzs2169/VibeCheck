import { useState } from 'react';
import ReviewCard from './ReviewCard';
import VibeSummaryCard from './VibeSummaryCard';

function ProfileContent({ reviews, latestVibe }) {
  const reviewCount = reviews.length || 0;
  const [sortOpen, setSortOpen] = useState(false);
  const [sortLabel, setSortLabel] = useState('Recent');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const sortOptions = ['Recent', 'Highest Rated', 'Lowest Rated', 'Most Helpful'];

  const filteredReviews = reviews.filter((r) =>
    searchQuery === '' ||
    r.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.user?.firstname?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.user?.lastname?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <main className="flex-1 flex flex-col overflow-hidden w-full h-full">

      {/* Fixed Summary */}
      {latestVibe?.summary_text && (
        <div className="flex-shrink-0 px-6 pt-6 pb-4 max-w-4xl w-full mx-auto">
          <VibeSummaryCard
            summary={latestVibe.summary_text}
            reviewCount={reviewCount}
          />
        </div>
      )}

    {/* Scrollable Reviews Container — no longer scrolls */}
    <div className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 pb-8 h-full flex flex-col">

            {/* White card — this is now the scrollable element */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col flex-1 overflow-hidden">

            {/* Header row — stays fixed at top of card */}
            <div className="flex-shrink-0 flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <h2 className="text-lg font-bold text-gray-900">
                Guest Reviews ({reviewCount})
                </h2>

                <div className="flex items-center gap-2">

                {searchOpen && (
                    <input
                    autoFocus
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search reviews..."
                    className="w-48 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#004687]/20 focus:border-[#004687] transition"
                    />
                )}

                <div className="relative">
                    <button
                    onClick={() => { setSortOpen(!sortOpen); setSearchOpen(false); }}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h18M7 8h10M11 12h4" />
                    </svg>
                    Sort by: {sortLabel}
                    </button>

                    {sortOpen && (
                    <div className="absolute right-0 mt-1 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
                        {sortOptions.map((opt) => (
                        <button
                            key={opt}
                            onClick={() => { setSortLabel(opt); setSortOpen(false); }}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition ${sortLabel === opt ? 'text-[#004687] font-medium' : 'text-gray-700'}`}
                        >
                            {opt}
                        </button>
                        ))}
                    </div>
                    )}
                </div>

                <button
                    onClick={() => { setSearchOpen(!searchOpen); setSortOpen(false); if (searchOpen) setSearchQuery(''); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded-lg transition ${searchOpen ? 'bg-[#004687] text-white border-[#004687]' : 'text-gray-600 border-gray-300 hover:bg-gray-50'}`}
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                    </svg>
                    Search
                </button>

                </div>
            </div>

            {/* Reviews list — scrolls inside the card */}
            <div className="flex-1 overflow-y-auto hide-scrollbar divide-y divide-gray-100">
                {filteredReviews.length === 0 ? (
                <div className="p-12 text-center">
                    {searchQuery ? (
                    <>
                        <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                        </svg>
                        <h3 className="text-base font-semibold text-gray-900 mb-1">No results found</h3>
                        <p className="text-sm text-gray-500">No reviews match "{searchQuery}"</p>
                    </>
                    ) : (
                    <>
                        <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                        </svg>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No reviews yet</h3>
                        <p className="text-gray-600">This resort doesn't have any reviews yet. Be the first to review!</p>
                    </>
                    )}
                </div>
                ) : (
                filteredReviews.map((review) => (
                    <div key={review.id} className="px-5 py-2">
                    <ReviewCard review={review} />
                    </div>
                ))
                )}
            </div>

        </div>

        
    </div>
    </div>
    </main>
  );
}

export default ProfileContent;