import VibeScoreGauge from './VibeScoreGauge';
import SentimentBreakdown from './SentimentBreakdown';
import { BASE_URL } from '../../services/api';

function ProfileSidebar({ business, latestVibe, getVibeLabel }) {
  const vibeScore = latestVibe?.vibe_score || 0;

  return (
    <aside className="w-full lg:w-[500px] h-full bg-white shadow-lg flex flex-col flex-shrink-0 overflow-hidden">
      
      {/* Hero Image */}
      <div className="relative h-52 flex-shrink-0">
        {business.image_path ? (
          <img
            src={`${BASE_URL}${business.image_path}`}
            alt={business.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-blue-100 to-cyan-100 flex items-center justify-center text-gray-400">
            <svg
              className="w-12 h-12"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}

        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

        <div className="absolute bottom-0 left-0 right-0 p-4">
          <h1 className="text-xl font-bold text-white leading-tight drop-shadow">
            {business.name}
          </h1>

          <p className="text-white/80 text-sm flex items-center gap-1.5 mt-1 drop-shadow">
            <svg
              className="w-3.5 h-3.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {business.location}
          </p>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
           <h3 className="text-sm font-semibold text-gray-900 mb-4">
              About this place
            </h3>
          {/* Description */}
          {business.short_description && (

            <p className="text-gray-700 text-xs pb-5 leading-relaxed border-b border-gray-200">
              {business.short_description}
            </p>
          )}


          {/* Vibe Score */}
          <div className="bg-white rounded-xl p-4 border border-gray-300 shadow-sm">
            <p className="text-xs font-semibold text-gray-600 text-center mb-4 tracking-wide">
              VIBE SCORE
            </p>

            <VibeScoreGauge
              score={vibeScore}
              label={getVibeLabel(vibeScore)}
              positive={latestVibe?.positive_count || 0}
              neutral={latestVibe?.mixed_count || 0}
              negative={latestVibe?.negative_count || 0}
            />
          </div>

          {/* Sentiment */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">
              How Guests Feel
            </h3>

            <SentimentBreakdown
              positive={latestVibe?.positive_count || 0}
              neutral={latestVibe?.mixed_count || 0}
              negative={latestVibe?.negative_count || 0}
            />
          </div>
        </div>
      </div>
    </aside>
  );
}

export default ProfileSidebar;