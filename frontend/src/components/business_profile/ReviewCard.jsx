import AspectSentimentChip from '../AspectSentimentChip';
import { PositiveIcon, NeutralIcon, NegativeIcon } from '../icons/SentimentIcons';
import formatRelativeTime from "../../utils/formatRelativeTime";

export default function ReviewCard({ review }) {
  const getInitials = (firstname, lastname) => {
    return `${(firstname?.[0] || '').toUpperCase()}${(lastname?.[0] || '').toUpperCase()}`;
  };

  const getSentimentIcon = () => {
    switch (review.sentiment_label) {
      case 'positive':
        return <PositiveIcon className="w-5 h-5 text-emerald-600" />;
      case 'neutral':
        return <NeutralIcon className="w-5 h-5 text-gray-600" />;
      case 'negative':
        return <NegativeIcon className="w-5 h-5 text-rose-600" />;
      default:
        return null;
    }
  };

  const aspectSentiments = review.aspect_sentiments || [];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header with user info and sentiment */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-[#004687] flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
            {getInitials(review.user?.firstname, review.user?.lastname)}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-gray-900">
              {review.user?.lastname}, {review.user?.firstname}
            </p>
            <p className="text-sm text-gray-500">{formatRelativeTime(review.created_at)}</p>
          </div>
        </div>
       
      </div>

      {/* Review content */}
      <p className="text-gray-700 leading-relaxed mb-4">{review.content}</p>

      {/* Aspect sentiments */}
      {aspectSentiments.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
          {aspectSentiments.map((aspect, index) => (
            <AspectSentimentChip
              key={index}
              aspect={aspect.aspect}
              sentiment={aspect.sentiment_label}
            />
          ))}
        </div>
      )}
    </div>
  );
}
