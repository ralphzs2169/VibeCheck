import { useNavigate } from 'react-router-dom';
import { BASE_URL } from '../services/api';

export default function ResortCard({ resort, vibeData }) {
  const navigate = useNavigate();
  
  const getVibeColor = (score) => {
    if (score >= 0.6) return 'text-green-600 bg-green-50';
    if (score >= 0.4) return 'text-amber-600 bg-amber-50';
    return 'text-red-600 bg-red-50';
  };

  const getScoreBadgeColor = (score) => {
    if (score >= 0.6) return 'bg-green-500';
    if (score >= 0.4) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const handleViewInsights = () => {
    navigate(`/resort/${resort.id}`, { state: { resort } });
  };

  const vibeScore = vibeData?.overall_score || 0.5;
  const sentimentDistribution = vibeData?.sentiment_distribution || { positive: 0.33, neutral: 0.33, negative: 0.34 };

  const getVibeLabel = (score) => {
    if (score >= 0.7) return 'Exceptional';
    if (score >= 0.6) return 'Great';
    if (score >= 0.5) return 'Good';
    if (score >= 0.4) return 'Fair';
    return 'Needs Improvement';
  };


  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow overflow-hidden group">
      {/* Image Container */}
      <div className="relative h-48 bg-gradient-to-br from-blue-100 to-cyan-100 overflow-hidden">
        {resort.image_path ? (
          <img
            src={`${BASE_URL}${resort.image_path}`}
            alt={resort.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}

        {/* Vibe Score Badge */}
       <div className="absolute top-3 right-3">
  <div
    className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium backdrop-blur-md bg-white/80 shadow-sm border border-white/40`}
  >
    <span
      className={`w-2 h-2 rounded-full ${
        vibeScore >= 0.6
          ? 'bg-green-500'
          : vibeScore >= 0.4
          ? 'bg-amber-500'
          : 'bg-red-500'
      }`}
    ></span>

    <span className="text-gray-800 font-semibold">
      {vibeScore.toFixed(1)}
    </span>
  </div>
</div>
      </div>

      {/* Content Container */}
      <div className="p-6">
        {/* Resort Name & Location */}
        <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-[#004687] transition">
          {resort.name}
        </h3>
        <p className="text-gray-500 text-sm mb-4 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {resort.location || 'Unknown Location'}
        </p>

        {/* Vibe Label */}
        <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-4 ${getVibeColor(vibeScore)}`}>
          {getVibeLabel(vibeScore)}
        </div>

        {/* Sentiment Distribution Bars */}
        <div className="space-y-2 mb-5">
          <div className="flex items-center justify-between text-xs font-medium">
            <div className="flex gap-4">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Positive
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                Neutral
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                Negative
              </span>
            </div>
          </div>

          <div className="flex gap-1 h-2 rounded-full overflow-hidden bg-gray-100">
            <div
              className="bg-green-500 transition-all"
              style={{ width: `${(sentimentDistribution.positive || 0) * 100}%` }}
            ></div>
            <div
              className="bg-gray-400 transition-all"
              style={{ width: `${(sentimentDistribution.neutral || 0) * 100}%` }}
            ></div>
            <div
              className="bg-red-500 transition-all"
              style={{ width: `${(sentimentDistribution.negative || 0) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Button */}
        <button
          onClick={handleViewInsights}
          className="w-full px-4 py-3 bg-[#004687] text-white rounded-lg font-medium hover:bg-blue-800 transition shadow-sm"
        >
          View Insights
        </button>
      </div>
    </div>
  );
}
