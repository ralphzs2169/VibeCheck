function WaveBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">

      {/* TOP WAVE (subtle inverted wave) */}
      {/* <svg
        className="absolute top-0 left-0 w-full text-[#002446] opacity-5"
        viewBox="0 0 1200 120"
        preserveAspectRatio="none"
        style={{ height: "220px" }}
      >
        <path
          d="M0,80 C200,140 400,20 600,70 C800,120 1000,40 1200,80 L1200,0 L0,0 Z"
          fill="currentColor"
        />
      </svg> */}

      {/* BOTTOM WAVE (your original but slightly refined) */}
      <svg
        className="absolute bottom-0 left-0 w-full text-[#002446] opacity-10"
        viewBox="0 0 1200 120"
        preserveAspectRatio="none"
        style={{ height: "300px" }}
      >
        <path
          d="M0,60 C250,20 450,100 650,60 C850,20 1000,90 1200,50 L1200,120 L0,120 Z"
          fill="currentColor"
        />
      </svg>

    </div>
  );
}

export default WaveBackground;