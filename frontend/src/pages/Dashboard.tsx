import React from 'react';
import '../styles/dashboard.css';

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard">
      {/* Top row with two cards side by side */}
      <div className="dashboard-row top-row">
      <div className="card">
          <h5>Portfolio</h5>
          <p>BTC Balance: (Placeholder)</p>
          <p>USD Value: (Placeholder)</p>
          <p>Unrealized Gains/Losses: (Placeholder)</p>
          <p>Portfolio Chart (Placeholder)</p>
        </div>
        
        <div className="card">
          <h5>Bitcoin Price</h5>
          <p>Placeholder for live BTC price & chart</p>
        </div>
      </div>

      {/* Bottom row with three cards side by side */}
      <div className="dashboard-row bottom-row">
        <div className="card">
          <h5>Bank</h5>
          <p>Placeholder: USD balance</p>
        </div>
        <div className="card">
          <h5>Exchange</h5>
          <p>USD & BTC balances</p>
        </div>
        <div className="card">
          <h5>Wallet</h5>
          <p>BTC balance</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;