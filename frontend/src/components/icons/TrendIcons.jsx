// Improving / Upward trend icon
// Improving / Upward trend icon
export function ImprovingIcon({ className = "w-5 h-5" }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      stroke="currentColor"
    >
      {/* trend line */}
      <path
        d="M10 32L22 20L28 26L38 14"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* arrow head */}
      <path
        d="M38 14V20M38 14H32"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Declining / Downward trend icon
export function DecliningIcon({ className = "w-5 h-5" }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      stroke="currentColor"
    >
      {/* trend line */}
      <path
        d="M10 16L22 28L28 22L38 34"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* arrow head */}
      <path
        d="M38 34V28M38 34H32"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Stable / Flat trend icon
export function StableIcon({ className = "w-5 h-5" }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      stroke="currentColor"
    >
      {/* flat line */}
      <line
        x1="10"
        y1="24"
        x2="38"
        y2="24"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}