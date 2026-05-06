export default function HeroSection({ children }) {
  return (
    <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4">
            Find the Vibe
            <span className="block text-[#004687]">Before You Book</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Discover resorts based on real guest sentiment. AI-powered insights from thousands of reviews to help you find your perfect stay.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8 mb-12">
          {children}
        </div>

        <div className="text-center">
          <p className="text-gray-500 text-sm">
            Analyzing sentiment from real guest reviews using AI
          </p>
        </div>
      </div>
    </section>
  );
}
