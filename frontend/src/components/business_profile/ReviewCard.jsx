import AspectSentimentChip from "../AspectSentimentChip";
import { PositiveIcon, NeutralIcon, NegativeIcon } from "../icons/SentimentIcons";
import formatRelativeTime from "../../utils/formatRelativeTime";

export default function ReviewCard({ review, compact = false }) {
  const getInitials = (firstname, lastname) => {
    return `${(firstname?.[0] || "").toUpperCase()}${(lastname?.[0] || "").toUpperCase()}`;
  };


  return (
    <div
      className={[
        "bg-white border border-gray-200 rounded-lg transition-shadow hover:shadow-sm",
        compact ? "p-4" : "p-6",
      ].join(" ")}
    >
      {/* HEADER */}
      <div className={`flex items-start justify-between ${compact ? "mb-2" : "mb-4"}`}>
        <div className={`flex items-start ${compact ? "gap-2" : "gap-4"}`}>
          
          {/* Avatar */}
          <div
            className={[
              "rounded-full bg-[#004687] flex items-center justify-center text-white font-semibold flex-shrink-0",
              compact ? "w-7 h-7 text-[10px]" : "w-12 h-12 text-sm",
            ].join(" ")}
          >
            {getInitials(review.user?.firstname, review.user?.lastname)}
          </div>

          {/* User */}
          <div className="leading-tight">
            <p className={`font-semibold text-gray-900 ${compact ? "text-sm" : "text-base"}`}>
              {review.user?.lastname}, {review.user?.firstname}
            </p>

            <p className={`text-gray-500 ${compact ? "text-[11px]" : "text-sm"}`}>
             <p className="text-sm text-gray-500">{formatRelativeTime(review.created_at)}</p>
            </p>
          </div>
        </div>
      </div>

      {/* CONTENT */}
      <p
        className={[
          "text-gray-700",
          compact ? "text-sm leading-snug mb-2" : "text-base leading-relaxed mb-4",
        ].join(" ")}
      >
        {review.content}
      </p>

  
    </div>
  );
}