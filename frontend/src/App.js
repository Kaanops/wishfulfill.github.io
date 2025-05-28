import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [wishes, setWishes] = useState([]);
  const [successStories, setSuccessStories] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [categories, setCategories] = useState([]);
  const [selectedWish, setSelectedWish] = useState(null);
  const [currentView, setCurrentView] = useState('home');
  const [loading, setLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  
  // Filters
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedUrgency, setSelectedUrgency] = useState('');

  // Form state - fix focus issue
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    amount_needed: '',
    currency: 'EUR',
    creator_name: '',
    creator_email: '',
    creator_paypal: '',
    category: 'Education',
    urgency: 'medium',
    photo_url: ''
  });

  // Fix form input focus loss
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const currencies = ['EUR', 'USD', 'GBP', 'CAD', 'AUD'];
  const urgencyLevels = [
    { value: 'low', label: 'Low Priority', color: 'bg-green-100 text-green-800' },
    { value: 'medium', label: 'Medium Priority', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'high', label: 'Urgent', color: 'bg-red-100 text-red-800' }
  ];

  // Payment processing
  const [pendingWish, setPendingWish] = useState(null);

  // Check if returning from PayPal payment
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentId = urlParams.get('paymentId');
    const payerId = urlParams.get('PayerID');
    
    if (paymentId && payerId) {
      handlePaymentReturn(paymentId, payerId);
    }
  }, []);

  // Handle PayPal payment return
  const handlePaymentReturn = async (paymentId, payerId) => {
    setPaymentLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/payments/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          payment_id: paymentId,
          payer_id: payerId
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert('Payment successful! Your wish has been posted.');
        setCurrentView('browse');
        fetchWishes();
        fetchStatistics();
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        alert('Payment verification failed. Please contact support.');
      }
    } catch (error) {
      console.error('Payment verification error:', error);
      alert('Payment verification error. Please contact support.');
    }
    setPaymentLoading(false);
  };

  // Create PayPal payment
  const createPayment = async (amount, currency, purpose, wishId = null) => {
    setPaymentLoading(true);
    try {
      const currentUrl = window.location.origin + window.location.pathname;
      const returnUrl = `${currentUrl}?paymentSuccess=true`;
      const cancelUrl = `${currentUrl}?paymentCancelled=true`;

      const response = await fetch(`${API_URL}/api/payments/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: amount,
          currency: currency,
          purpose: purpose,
          wish_id: wishId,
          return_url: returnUrl,
          cancel_url: cancelUrl
        }),
      });

      if (response.ok) {
        const result = await response.json();
        // Redirect to PayPal for payment
        window.location.href = result.approval_url;
      } else {
        const error = await response.json();
        alert(`Payment creation failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Payment creation error:', error);
      alert('Payment creation failed. Please try again.');
    }
    setPaymentLoading(false);
  };

  // Fetch data functions
  const fetchWishes = async () => {
    try {
      const categoryParam = selectedCategory !== 'All' ? `&category=${selectedCategory}` : '';
      const urgencyParam = selectedUrgency ? `&urgency=${selectedUrgency}` : '';
      const response = await fetch(`${API_URL}/api/wishes?limit=50${categoryParam}${urgencyParam}&paid_only=true`);
      const data = await response.json();
      setWishes(data);
    } catch (error) {
      console.error('Error fetching wishes:', error);
    }
  };

  const fetchSuccessStories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/success-stories`);
      const data = await response.json();
      setSuccessStories(data);
    } catch (error) {
      console.error('Error fetching success stories:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/categories`);
      const data = await response.json();
      setCategories(['All', ...data.categories]);
    } catch (error) {
      console.error('Error fetching categories:', error);
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

  // Create wish (now with payment integration)
  const createWish = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // First create the wish
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
        const newWish = await response.json();
        setPendingWish(newWish);
        
        // Now redirect to payment
        alert(`Great! Now you need to pay the ${statistics.posting_fee || 2}€ posting fee to publish your wish.`);
        createPayment(statistics.posting_fee || 2.0, 'EUR', 'posting_fee', newWish.id);
      }
    } catch (error) {
      console.error('Error creating wish:', error);
      alert('Error creating wish. Please try again.');
    }
    setLoading(false);
  };

  // Donate to wish
  const donateToWish = (amount) => {
    if (!selectedWish) return;
    
    const donationAmount = prompt(`How much would you like to donate? (in ${selectedWish.currency})`);
    if (donationAmount && parseFloat(donationAmount) > 0) {
      createPayment(parseFloat(donationAmount), selectedWish.currency, 'donation', selectedWish.id);
    }
  };

  useEffect(() => {
    fetchWishes();
    fetchSuccessStories();
    fetchStatistics();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchWishes();
  }, [selectedCategory, selectedUrgency]);

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

  const getUrgencyStyle = (urgency) => {
    return urgencyLevels.find(level => level.value === urgency)?.color || 'bg-gray-100 text-gray-800';
  };

  const getUrgencyLabel = (urgency) => {
    return urgencyLevels.find(level => level.value === urgency)?.label || urgency;
  };

  // Home View
  const HomeView = () => (
    <div className="min-h-screen">
      {/* Payment Loading Overlay */}
      {paymentLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-lg">Processing payment...</p>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <div 
        className="relative h-screen flex items-center justify-center text-white"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1570050785780-3c79854c7813")',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="text-center max-w-4xl px-4">
          <h1 className="text-6xl font-bold mb-6">Where Dreams Meet Generosity</h1>
          <p className="text-xl mb-8">
            Join thousands who have already made wishes come true. Real stories, real impact, real change.
          </p>
          
          {/* Statistics Bar */}
          <div className="bg-white bg-opacity-20 backdrop-blur-md rounded-lg p-6 mb-8">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold">{statistics.total_wishes || 0}</div>
                <div className="text-sm">Total Wishes</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{statistics.fulfilled_wishes || 0}</div>
                <div className="text-sm">Fulfilled</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{formatAmount(statistics.total_raised || 0, 'EUR').replace('€', '€')}</div>
                <div className="text-sm">Total Raised</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{statistics.success_rate || 0}%</div>
                <div className="text-sm">Success Rate</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{statistics.active_users || 0}</div>
                <div className="text-sm">Active Users</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{statistics.countries || 0}</div>
                <div className="text-sm">Countries</div>
              </div>
            </div>
          </div>

          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('create')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors shadow-lg"
            >
              Post Your Wish (€{statistics.posting_fee || 2})
            </button>
            <button 
              onClick={() => setCurrentView('browse')}
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors shadow-lg"
            >
              Browse Wishes
            </button>
          </div>
        </div>
      </div>

      {/* Success Stories Section */}
      <div className="py-20 bg-gradient-to-br from-green-50 to-blue-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">Success Stories</h2>
          <p className="text-xl text-gray-600 text-center mb-16">Real wishes that came true thanks to generous donors</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {successStories.slice(0, 6).map((story) => (
              <div key={story.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all transform hover:-translate-y-1">
                <img 
                  src={story.photo_url} 
                  alt={story.title}
                  className="w-full h-48 object-cover"
                />
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
                      ✓ Fulfilled
                    </span>
                    <span className="text-sm text-gray-500">{story.category}</span>
                  </div>
                  <h3 className="text-lg font-semibold mb-3 line-clamp-2">{story.title}</h3>
                  <p className="text-gray-600 mb-4 text-sm line-clamp-3">{story.description}</p>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xl font-bold text-green-600">
                        {formatAmount(story.amount_fulfilled, story.currency)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {story.donor_count} donors
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(story.fulfillment_date)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-12">
            <div className="bg-white bg-opacity-80 backdrop-blur-md rounded-lg p-6 inline-block">
              <h3 className="text-2xl font-bold mb-2">Join Our Success Community</h3>
              <p className="text-gray-600 mb-4">Over {statistics.active_users || 1200} people are already making dreams come true!</p>
              <button 
                onClick={() => setCurrentView('browse')}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold mr-4"
              >
                Help Someone Today
              </button>
              <button 
                onClick={() => setCurrentView('create')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
              >
                Share Your Dream
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">✨</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">1. Share Your Story</h3>
              <p className="text-gray-600">Post your wish with details and photos. Pay a small €{statistics.posting_fee || 2} fee to prevent spam and ensure quality.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">💝</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">2. Connect with Donors</h3>
              <p className="text-gray-600">Generous people browse by category and choose wishes that resonate with their hearts.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">🎉</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">3. Dreams Come True</h3>
              <p className="text-gray-600">Watch your progress grow as donors help fulfill your wish through secure PayPal payments.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Wishes Preview */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">Recent Wishes</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {wishes.slice(0, 3).map((wish) => (
              <div key={wish.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-all transform hover:-translate-y-1">
                {wish.photo_url && (
                  <img src={wish.photo_url} alt={wish.title} className="w-full h-32 object-cover rounded-lg mb-4" />
                )}
                <div className="flex items-center justify-between mb-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getUrgencyStyle(wish.urgency)}`}>
                    {getUrgencyLabel(wish.urgency)}
                  </span>
                  <span className="text-sm text-gray-500">{wish.category}</span>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{wish.title}</h3>
                <p className="text-gray-600 mb-4 line-clamp-3">{wish.description}</p>
                
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Progress</span>
                    <span>{Math.round(wish.fulfillment_percentage)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${wish.fulfillment_percentage}%` }}
                    ></div>
                  </div>
                </div>

                <div className="flex justify-between items-center mb-4">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {formatAmount(wish.amount_needed, wish.currency)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {wish.donor_count} donors • {formatDate(wish.created_at)}
                    </div>
                  </div>
                </div>
                
                <button 
                  onClick={() => {
                    setSelectedWish(wish);
                    setCurrentView('detail');
                  }}
                  className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg transition-colors font-semibold"
                >
                  Help This Wish
                </button>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <button 
              onClick={() => setCurrentView('browse')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold"
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
            Post Your Wish (€{statistics.posting_fee || 2})
          </button>
        </div>
        
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Urgency</label>
              <select
                value={selectedUrgency}
                onChange={(e) => setSelectedUrgency(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Priorities</option>
                {urgencyLevels.map(level => (
                  <option key={level.value} value={level.value}>{level.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {wishes.map((wish) => (
            <div key={wish.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-all transform hover:-translate-y-1">
              {wish.photo_url && (
                <img src={wish.photo_url} alt={wish.title} className="w-full h-40 object-cover rounded-lg mb-4" />
              )}
              
              <div className="flex items-center justify-between mb-3">
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getUrgencyStyle(wish.urgency)}`}>
                  {getUrgencyLabel(wish.urgency)}
                </span>
                <span className="text-sm text-gray-500">{wish.category}</span>
              </div>
              
              <h3 className="text-xl font-semibold mb-3 text-gray-800">{wish.title}</h3>
              <p className="text-gray-600 mb-4 line-clamp-4">{wish.description}</p>
              
              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Progress</span>
                  <span>{Math.round(wish.fulfillment_percentage)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${wish.fulfillment_percentage}%` }}
                  ></div>
                </div>
              </div>
              
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
                  {wish.donor_count} donors • Posted {formatDate(wish.created_at)}
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
            <p className="text-gray-500 text-lg">No wishes found for your current filters.</p>
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
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="What's your wish?"
                required
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {categories.filter(cat => cat !== 'All').map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority Level *
                </label>
                <select
                  value={formData.urgency}
                  onChange={(e) => setFormData({...formData, urgency: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {urgencyLevels.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Story *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows="5"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Tell your story... Why is this important to you? How will it change your life?"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Photo URL (optional)
              </label>
              <input
                type="url"
                value={formData.photo_url}
                onChange={(e) => handleInputChange('photo_url', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://example.com/photo.jpg"
              />
              <p className="text-sm text-gray-500 mt-1">Adding a photo increases your chances of getting support by 3x!</p>
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
                  onChange={(e) => handleInputChange('amount_needed', e.target.value)}
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
                PayPal Email (recommended)
              </label>
              <input
                type="email"
                value={formData.creator_paypal}
                onChange={(e) => setFormData({...formData, creator_paypal: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="paypal@email.com (for receiving donations)"
              />
              <p className="text-sm text-gray-500 mt-1">Donors can send money directly to your PayPal</p>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Posting Fee:</strong> €{statistics.posting_fee || 2} to prevent spam and maintain quality. 
                After posting, you'll be redirected to PayPal for secure payment.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || paymentLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-4 rounded-lg font-semibold text-lg transition-colors"
            >
              {loading ? 'Creating Your Wish...' : `Post Your Wish (€${statistics.posting_fee || 2})`}
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
          
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {selectedWish.photo_url && (
              <img 
                src={selectedWish.photo_url} 
                alt={selectedWish.title}
                className="w-full h-64 object-cover"
              />
            )}
            
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getUrgencyStyle(selectedWish.urgency)}`}>
                  {getUrgencyLabel(selectedWish.urgency)}
                </span>
                <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-semibold">
                  {selectedWish.category}
                </span>
              </div>

              <h1 className="text-4xl font-bold mb-6 text-gray-800">{selectedWish.title}</h1>
              
              {/* Progress Section */}
              <div className="bg-green-50 rounded-lg p-6 mb-8">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <span className="text-3xl font-bold text-green-600">
                      {formatAmount(selectedWish.amount_needed, selectedWish.currency)}
                    </span>
                    <span className="text-gray-500 ml-2">goal</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(selectedWish.fulfillment_percentage)}%
                    </div>
                    <div className="text-sm text-gray-500">funded</div>
                  </div>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                  <div 
                    className="bg-green-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${selectedWish.fulfillment_percentage}%` }}
                  ></div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="font-semibold text-lg">
                      {formatAmount(selectedWish.donations_received, selectedWish.currency)}
                    </div>
                    <div className="text-sm text-gray-500">raised</div>
                  </div>
                  <div>
                    <div className="font-semibold text-lg">{selectedWish.donor_count}</div>
                    <div className="text-sm text-gray-500">donors</div>
                  </div>
                  <div>
                    <div className="font-semibold text-lg">{formatDate(selectedWish.created_at)}</div>
                    <div className="text-sm text-gray-500">posted</div>
                  </div>
                </div>
              </div>

              <div className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">The Story</h2>
                <p className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">
                  {selectedWish.description}
                </p>
              </div>

              <div className="mb-8">
                <div className="text-sm text-gray-500 mb-2">Posted by</div>
                <div className="font-semibold text-lg">{selectedWish.creator_name}</div>
              </div>

              <div className="bg-green-50 p-6 rounded-lg">
                <h3 className="text-xl font-semibold mb-4 text-green-800">Help Make This Wish Come True</h3>
                <p className="text-green-700 mb-4">
                  Ready to help? Make a secure donation through PayPal.
                </p>
                
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <button 
                    onClick={() => donateToWish()}
                    className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                  >
                    💳 Donate via PayPal
                  </button>
                  
                  {selectedWish.creator_paypal && (
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-sm text-gray-600">Direct PayPal:</div>
                      <div className="font-semibold">{selectedWish.creator_paypal}</div>
                    </div>
                  )}
                </div>
                
                <div className="text-sm text-gray-600">
                  <strong>Email:</strong> {selectedWish.creator_email}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Navigation
  const Navigation = () => (
    <nav className="bg-white shadow-md fixed top-0 w-full z-50 backdrop-blur-md bg-opacity-95">
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
              Post Wish (€{statistics.posting_fee || 2})
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