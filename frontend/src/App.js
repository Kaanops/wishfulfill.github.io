import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [wishes, setWishes] = useState([]);
  const [selectedWish, setSelectedWish] = useState(null);
  const [currentView, setCurrentView] = useState('home'); // home, browse, create, detail
  const [loading, setLoading] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    amount_needed: '',
    currency: 'EUR',
    creator_name: '',
    creator_email: '',
    creator_paypal: ''
  });

  const currencies = ['EUR', 'USD', 'GBP', 'CAD', 'AUD'];

  // Fetch wishes
  const fetchWishes = async () => {
    try {
      const response = await fetch(`${API_URL}/api/wishes`);
      const data = await response.json();
      setWishes(data);
    } catch (error) {
      console.error('Error fetching wishes:', error);
    }
  };

  // Fetch single wish
  const fetchWish = async (wishId) => {
    try {
      const response = await fetch(`${API_URL}/api/wishes/${wishId}`);
      const data = await response.json();
      setSelectedWish(data);
    } catch (error) {
      console.error('Error fetching wish:', error);
    }
  };

  // Create wish
  const createWish = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/api/wishes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          amount_needed: parseFloat(formData.amount_needed)
        }),
      });
      
      if (response.ok) {
        setFormData({
          title: '',
          description: '',
          amount_needed: '',
          currency: 'EUR',
          creator_name: '',
          creator_email: '',
          creator_paypal: ''
        });
        setCurrentView('browse');
        fetchWishes();
      }
    } catch (error) {
      console.error('Error creating wish:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchWishes();
  }, []);

  const formatAmount = (amount, currency) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Home View
  const HomeView = () => (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div 
        className="relative h-screen flex items-center justify-center text-white"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("https://images.unsplash.com/photo-1570050785780-3c79854c7813")',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="text-center max-w-4xl px-4">
          <h1 className="text-6xl font-bold mb-6">Make Wishes Come True</h1>
          <p className="text-xl mb-8">
            A platform where dreams meet generosity. Share your wishes and connect with anonymous donors ready to help.
          </p>
          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('create')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors"
            >
              Post Your Wish
            </button>
            <button 
              onClick={() => setCurrentView('browse')}
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors"
            >
              Browse Wishes
            </button>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">✨</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Share Your Wish</h3>
              <p className="text-gray-600">Post what you need or dream of. Be honest and specific about your wish.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👥</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Connect with Donors</h3>
              <p className="text-gray-600">Generous people browse wishes and choose which ones speak to their hearts.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎁</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Dreams Come True</h3>
              <p className="text-gray-600">Anonymous donors help fulfill wishes, spreading joy and kindness.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Wishes Preview */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">Recent Wishes</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {wishes.slice(0, 3).map((wish) => (
              <div key={wish.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{wish.title}</h3>
                <p className="text-gray-600 mb-4 line-clamp-3">{wish.description}</p>
                <div className="flex justify-between items-center mb-4">
                  <span className="text-2xl font-bold text-blue-600">
                    {formatAmount(wish.amount_needed, wish.currency)}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatDate(wish.created_at)}
                  </span>
                </div>
                <button 
                  onClick={() => {
                    setSelectedWish(wish);
                    setCurrentView('detail');
                  }}
                  className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg transition-colors"
                >
                  Help This Wish
                </button>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <button 
              onClick={() => setCurrentView('browse')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
            >
              View All Wishes
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Browse View
  const BrowseView = () => (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold">Browse All Wishes</h1>
          <button 
            onClick={() => setCurrentView('create')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Post Your Wish
          </button>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {wishes.map((wish) => (
            <div key={wish.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <h3 className="text-xl font-semibold mb-3 text-gray-800">{wish.title}</h3>
              <p className="text-gray-600 mb-4 line-clamp-4">{wish.description}</p>
              
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-2xl font-bold text-blue-600">
                    {formatAmount(wish.amount_needed, wish.currency)}
                  </span>
                  <span className="text-sm text-gray-500">
                    by {wish.creator_name}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  Posted {formatDate(wish.created_at)}
                </div>
              </div>

              <button 
                onClick={() => {
                  setSelectedWish(wish);
                  setCurrentView('detail');
                }}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Help This Wish
              </button>
            </div>
          ))}
        </div>
        
        {wishes.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No wishes posted yet. Be the first!</p>
          </div>
        )}
      </div>
    </div>
  );

  // Create View
  const CreateView = () => (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-4xl font-bold mb-8 text-center">Share Your Wish</h1>
        
        <div className="bg-white rounded-lg shadow-lg p-8">
          <form onSubmit={createWish} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Wish Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="What's your wish?"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows="5"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Tell your story... Why is this important to you?"
                required
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount Needed *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount_needed}
                  onChange={(e) => setFormData({...formData, amount_needed: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Currency *
                </label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({...formData, currency: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {currencies.map(currency => (
                    <option key={currency} value={currency}>{currency}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Name *
              </label>
              <input
                type="text"
                value={formData.creator_name}
                onChange={(e) => setFormData({...formData, creator_name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Email *
              </label>
              <input
                type="email"
                value={formData.creator_email}
                onChange={(e) => setFormData({...formData, creator_email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                PayPal Email (optional)
              </label>
              <input
                type="email"
                value={formData.creator_paypal}
                onChange={(e) => setFormData({...formData, creator_paypal: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="paypal@email.com (for receiving donations)"
              />
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Coming Soon:</strong> There will be a 2€ posting fee to prevent spam and maintain quality. 
                For now, posting is free during our beta phase!
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-4 rounded-lg font-semibold text-lg transition-colors"
            >
              {loading ? 'Posting Your Wish...' : 'Post Your Wish'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );

  // Detail View
  const DetailView = () => {
    if (!selectedWish) return null;

    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <button 
            onClick={() => setCurrentView('browse')}
            className="mb-6 text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Browse
          </button>
          
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-8">
              <h1 className="text-4xl font-bold mb-4 text-gray-800">{selectedWish.title}</h1>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <span className="text-3xl font-bold text-blue-600">
                    {formatAmount(selectedWish.amount_needed, selectedWish.currency)}
                  </span>
                  <span className="text-gray-500 ml-2">needed</span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Posted by</div>
                  <div className="font-semibold">{selectedWish.creator_name}</div>
                  <div className="text-sm text-gray-500">{formatDate(selectedWish.created_at)}</div>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">The Story</h2>
              <p className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">
                {selectedWish.description}
              </p>
            </div>

            <div className="bg-green-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-4 text-green-800">Help Make This Wish Come True</h3>
              <p className="text-green-700 mb-4">
                Ready to help? Payment integration coming soon! For now, you can contact the wish maker directly.
              </p>
              
              {selectedWish.creator_paypal && (
                <div className="mb-4">
                  <strong>PayPal:</strong> {selectedWish.creator_paypal}
                </div>
              )}
              
              <div className="mb-4">
                <strong>Email:</strong> {selectedWish.creator_email}
              </div>
              
              <button className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
                Coming Soon: Donate Now
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Navigation
  const Navigation = () => (
    <nav className="bg-white shadow-md fixed top-0 w-full z-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <button 
            onClick={() => setCurrentView('home')}
            className="text-2xl font-bold text-blue-600"
          >
            WishFulfill
          </button>
          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('home')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                currentView === 'home' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Home
            </button>
            <button 
              onClick={() => setCurrentView('browse')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                currentView === 'browse' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Browse Wishes
            </button>
            <button 
              onClick={() => setCurrentView('create')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Post Wish
            </button>
          </div>
        </div>
      </div>
    </nav>
  );

  return (
    <div className="App">
      {currentView !== 'home' && <Navigation />}
      <div className={currentView !== 'home' ? 'pt-20' : ''}>
        {currentView === 'home' && <HomeView />}
        {currentView === 'browse' && <BrowseView />}
        {currentView === 'create' && <CreateView />}
        {currentView === 'detail' && <DetailView />}
      </div>
    </div>
  );
}

export default App;