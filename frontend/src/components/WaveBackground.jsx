function WaveBackground() {
  return (
    <svg
      className="fixed bottom-0 left-0 w-full text-[#002446] opacity-8 pointer-events-none"
      viewBox="0 0 1200 120"
      preserveAspectRatio="none"
      style={{ height: '300px' }}
    >
      <path
        d="M0,50 Q300,0 600,50 T1200,50 L1200,120 L0,120 Z"
        fill="currentColor"
      />
    </svg>
  );
}

export default WaveBackground;
