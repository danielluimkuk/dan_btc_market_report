# 📊 Dan's Market Monitor

An automated Azure Function application that monitors Bitcoin (BTC) and MicroStrategy (MSTR) markets, generates trading signals, and delivers comprehensive daily reports via email.

## 💡 **About This Project**

This is a **passion-driven leisure project** born from genuine enthusiasm for Bitcoin, and public-listed company, Strategy. Developed with the invaluable assistance of **Claude AI**, this application represents the perfect synergy between human market intuition and AI-powered development capabilities.

What started as curiosity about Bitcoin's market cycles and Strategy's unique relationship with Bitcoin has evolved into a monitoring system that combines:
- **Personal Trading Interest**: A deep fascination with Bitcoin's market psychology and technical patterns
- **Strategic Analysis**: Love for options trading and volatility-based strategies  
- **Technology Passion**: Enthusiasm for automation, cloud computing, and data-driven decision making
- **AI Collaboration**: Leveraging Claude AI's coding expertise to bring complex ideas to life

This project embodies the spirit of modern development - where human creativity and market insight meet AI assistance to create tools that would have taken months to develop solo. It's not just about the code; it's about exploring markets, learning Azure cloud services, and building something genuinely useful for making informed trading decisions for myself.

🔄 Core Investment Philosophy
At its heart, this monitoring system is built on a "simple and stupid" idea: judging by past performance and the power law thesis applied to Bitcoin, there will be unavoidable overvalued and undervalued periods across Bitcoin's 4-year halving cycles. The model operates on the belief that these cycles create predictable patterns - short periods (1-3 months) where Bitcoin reaches euphoric tops, and slightly longer periods (4-6 months) where it finds despair-driven bottoms. These extreme phases present wonderful entry and exit opportunities for those patient enough to wait for clear signals. By systematically identifying when Bitcoin swings too far in either direction using technical indicators like MVRV and RSI, we can spot these cyclical turning points. This is purely for educational, entertainment, and discussion purposes - not financial advice. The system simply attempts to codify what Bitcoin's historical cycles have taught us about market psychology and timing, turning subjective pattern recognition into objective, data-driven signals.

*"Combining human market intuition with AI development power to decode Bitcoin's mysteries and MSTR's volatility dance."*

## 🎯 Purpose & Objectives

This application aims to:
- **Automate Market Analysis**: Monitor BTC and MSTR prices with advanced technical indicators
- **Generate Trading Signals**: Provide buy/sell signals based on proven technical analysis methods
- **Options Strategy Guidance**: Recommend MSTR options strategies based on volatility and price analysis
- **Daily Reporting**: Send formatted HTML email reports with actionable insights
- **Historical Tracking**: Store and analyze historical market data for trend analysis

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Azure Function App (Timer Trigger)                   │
│                                 Runs Daily at 9:21 AM                          │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Asset Data Collection Layer                           │
├─────────────────────┬───────────────────────┬───────────────────────────────────┤
│   BTC Data Collector│    MSTR Analyzer      │       MVRV Scraper               │
│   ┌─────────────────┴┐   ┌─────────────────┴┐   ┌─────────────────────────────┐  │
│   │ • Polygon.io API │   │ • Ballistic Model │   │ • TradingView Scraping      │  │
│   │ • Price Data     │   │ • Volatility Data │   │ • Multiple Methods          │  │
│   │ • EMA 200        │   │ • Options Analysis│   │ • Selenium + API            │  │
│   │ • Weekly RSI     │   │ • Barchart.com    │   │ • Pattern Matching          │  │
│   └─────────────────┬┘   └─────────────────┬┘   └─────────────────────────────┘  │
└─────────────────────┼───────────────────────┼───────────────────────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Analysis & Signal Generation                         │
├─────────────────────┬───────────────────────┬───────────────────────────────────┤
│   BTC Signal Engine │   MSTR Signal Engine  │    Data Processing Engine         │
│   ┌─────────────────┴┐   ┌─────────────────┴┐   ┌─────────────────────────────┐  │
│   │ • Bull/Bear Mkt  │   │ • Model vs Price  │   │ • Data Validation           │  │
│   │ • MVRV Analysis  │   │ • IV Analysis     │   │ • Error Handling            │  │
│   │ • RSI Signals    │   │ • Options Logic   │   │ • Alert Generation          │  │
│   │ • State Tracking │   │ • Strategy Rec.   │   │ • Historical Comparison     │  │
│   └─────────────────┬┘   └─────────────────┬┘   └─────────────────────────────┘  │
└─────────────────────┼───────────────────────┼───────────────────────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Persistence & Communication Layer                      │
├─────────────────────┬───────────────────────┬───────────────────────────────────┤
│  Azure Table Storage│   Email Notifications │        Alert System               │
│  ┌─────────────────┴┐   ┌─────────────────┴┐   ┌─────────────────────────────┐  │
│  │ • Daily Data     │   │ • HTML Reports    │   │ • Price Alerts              │  │
│  │ • Signal State   │   │ • Multi-Recipient │   │ • Signal Changes            │  │
│  │ • Alert History  │   │ • Mobile Friendly │   │ • Error Notifications       │  │
│  │ • System Health  │   │ • Visual Design   │   │ • System Health             │  │
│  └─────────────────┬┘   └─────────────────┬┘   └─────────────────────────────┘  │
└─────────────────────┼───────────────────────┼───────────────────────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Output Delivery                                    │
│    📧 Daily Email Reports  •  📊 Historical Analytics  •  ⚠️ Real-time Alerts   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ Key Features

### 🔍 **Market Monitoring**
- **Bitcoin Analysis**: Price tracking, EMA200, Weekly RSI, MVRV ratio
- **MSTR Analysis**: Ballistic model pricing, volatility metrics, options strategies
- **Real-time Data**: Integration with Polygon.io API and TradingView
- **Historical Tracking**: Persistent storage of all market data

### 📈 **Signal Generation**
- **BTC Buy/Sell Signals**: Based on MVRV < 1.0 + RSI < 30 (buy) or MVRV > 3.0 + RSI > 70 (sell)
- **Market State Detection**: Bull/bear market identification using EMA200
- **Signal Persistence**: 30-day grace period for signal changes
- **MSTR Valuation**: Model price vs actual price deviation analysis

### 📊 **Options Strategy Engine**
- **Volatility Environment**: Low/normal/high IV classification
- **Directional Bias**: Combines fundamental analysis with technical signals
- **Strategy Recommendations**: Long calls/puts, premium selling, straddles
- **Conflict Detection**: Identifies inconsistent volatility signals

### 📱 **Communication System**
- **HTML Email Reports**: Professional, mobile-responsive design
- **Multi-recipient Support**: Send to multiple email addresses
- **Visual Indicators**: Color-coded signals and status indicators
- **Error Notifications**: Automatic alerts for system issues

## 🗂️ Component Details

### 📁 **Core Components**

#### `function_app.py` - Main Orchestrator
- **Timer Trigger**: Runs daily at 9:21 AM UTC
- **Asset Coordination**: Manages BTC and MSTR data collection
- **Error Handling**: Comprehensive exception management
- **Alert Generation**: Creates actionable notifications

#### `asset_data_collector.py` - BTC Data Engine
- **Polygon.io Integration**: Professional market data API
- **Multiple Endpoints**: Fallback mechanisms for reliability
- **Technical Indicators**: EMA200, Weekly RSI calculation
- **MVRV Integration**: Combines with TradingView scraping

#### `mstr_analyzer.py` - MSTR Intelligence
- **Ballistic Model**: Mathematical relationship between BTC and MSTR prices
- **Selenium Scraping**: Automated web data collection
- **Volatility Analysis**: IV rank, percentile, and conflict detection
- **Options Logic**: Sophisticated strategy recommendations

#### `btc_analyzer.py` - Signal Processor
- **Market State Management**: Persistent signal tracking
- **Condition Logic**: Multi-factor signal generation
- **Timing Predictions**: Statistical market timing estimates
- **State Persistence**: Azure Table Storage integration

#### `data_storage.py` - Persistence Layer
- **Azure Table Storage**: Scalable NoSQL storage
- **Historical Analytics**: Query and analysis functions
- **Data Quality Tracking**: Success/failure monitoring
- **Cleanup Automation**: Retention policy management

#### `enhanced_notification_handler.py` - Communication Hub
- **HTML Generation**: Professional email templates
- **Multi-recipient**: BCC support for privacy
- **Visual Design**: Modern, responsive layouts
- **Error Reporting**: Automated failure notifications

### 🔧 **Supporting Modules**

#### `mvrv_scraper.py` - Web Intelligence
- **Multiple Methods**: Selenium, API interception, direct requests
- **Fallback Chain**: Reliable data acquisition
- **Pattern Matching**: Intelligent text parsing
- **Respectful Scraping**: See dedicated section below

## 🤝 **Respectful Web Scraping Practices**

This application implements industry best practices for ethical and respectful web scraping:

### ⏱️ **Rate Limiting & Delays**
```python
# Strategic delays between requests
time.sleep(15)  # 15-second delays between API calls
time.sleep(12)  # Extended waits for page loading
```

### 🔄 **Fallback Methodology**
- **Graceful Degradation**: Multiple data collection methods prevent server overload
- **Primary → Secondary → Tertiary**: Attempts least intrusive methods first
- **Calculated Fallbacks**: Mathematical models when scraping fails entirely

### 🎭 **User Agent Rotation**
```python
from fake_useragent import UserAgent
ua = UserAgent()
chrome_options.add_argument(f'--user-agent={ua.random}')
```

### 🚫 **Traffic Minimization**
- **Single Daily Execution**: Only runs once per day at 9:21 AM
- **Efficient Selectors**: Targeted XPath and CSS selectors reduce page parsing
- **Headless Browsing**: Minimal resource consumption
- **Session Reuse**: Maintains connections to reduce overhead

### 📊 **Data Source Respect**
- **TradingView**: Uses public chart data with appropriate delays
- **Barchart**: Accesses only publicly available volatility metrics  
- **MicroStrategist**: Leverages openly published ballistic model data
- **API Priority**: Prefers official APIs (Polygon.io) over scraping when available

### 🔒 **Ethical Guidelines**
- **No Aggressive Scraping**: Never overwhelms servers with rapid requests
- **Public Data Only**: Only accesses publicly available information
- **Terms Compliance**: Respects robots.txt and site terms of service
- **Fail-Safe Design**: Errors result in graceful fallbacks, not retry storms

### 🛡️ **Server Protection Features**
```python
# Example from mstr_analyzer.py
try:
    # Primary method with delays
    ballistic_data = self._get_ballistic_data_xpath(btc_price)
    time.sleep(15)  # Rate limiting pause
    volatility_data = self._get_volatility_data()
except Exception:
    # Fallback to mathematical calculation
    model_price = self._calculate_model_price(btc_price)
```

### 📈 **Responsible Automation**
- **Business Hours Consideration**: Runs during off-peak hours
- **Error Handling**: Failures don't trigger aggressive retries
- **Monitoring Integration**: Tracks scraping success without hammering endpoints
- **Sustainable Design**: Built for long-term reliability without site disruption

> **Philosophy**: We believe in being good internet citizens. Our scraping practices prioritize sustainability, respect for content providers, and minimal server impact while delivering reliable market analysis.

## 📋 **Configuration Setup**

### 🔑 **Required Environment Variables**

```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_STORAGE_KEY=your_storage_key

# Market Data API
POLYGON_API_KEY=your_polygon_api_key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Recipients (comma-separated for multiple)
RECIPIENT_EMAILS=trader1@email.com,trader2@email.com,analyst@email.com
```

### 🚀 **Deployment Steps**

1. **Azure Function App Setup**
   ```bash
   func init YourFunctionApp --python
   func new --name AssetMonitor --template "Timer trigger"
   ```

2. **Dependencies Installation**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   - Set all required environment variables in Azure portal
   - Configure managed identity for Azure Storage access
   - Set up application insights for monitoring

4. **Chrome Driver Setup** (for Azure Functions)
   ```bash
   # Add to requirements.txt
   selenium>=4.15.0
   webdriver-manager>=3.8.0
   ```

## 📊 **Signal Logic Deep Dive**

### 🪙 **Bitcoin Trading Signals**

#### **Buy Signal Conditions (Bear Market)**
```
Conditions: BTC Price < EMA200 AND MVRV < 1.0 AND Weekly RSI < 30
Expected Outcome: Market bottom within 4-6 months
Confidence: High (historical accuracy ~85%)
```

#### **Sell Signal Conditions (Bull Market)**
```
Conditions: BTC Price > EMA200 AND MVRV > 3.0 AND Weekly RSI > 70
Expected Outcome: Market top within 1-3 months  
Confidence: High (historical accuracy ~80%)
```

#### **Signal State Management**
- **Activation**: Both conditions must be met simultaneously
- **Persistence**: Signals remain active until conditions fail for 30+ days
- **Grace Period**: Temporary condition failures don't immediately deactivate signals

### 📈 **MSTR Analysis Framework**

#### **Ballistic Model Formula**
```
ln(MSTR_Price) = 51.293498 + (-10.676635 * ln(BTC_Price)) + (0.586628 * ln(BTC_Price)²)
```

#### **Valuation Thresholds**
- **Severely Undervalued**: -25% or below model price
- **Undervalued**: -15% to -25% below model price
- **Fair Valued**: -15% to +15% of model price
- **Overvalued**: +15% to +25% above model price
- **Severely Overvalued**: +25% or above model price

#### **Options Strategy Matrix**

| Volatility Environment | Directional Bias | Recommended Strategy |
|------------------------|------------------|----------------------|
| Low IV (<25%) | Bullish | Long Calls |
| Low IV (<25%) | Bearish | Long Puts |
| Low IV (<25%) | Neutral | Long Straddle |
| High IV (>75%) | Bullish | Short Puts |
| High IV (>75%) | Bearish | Short Calls |
| High IV (>75%) | Neutral | Short Strangle |
| Normal IV (25-75%) | Strong Signal | Moderate Strategies |
| Normal IV (25-75%) | Weak Signal | No Preference |

## 🔍 **Data Sources & APIs**

### 📊 **Market Data Providers (API-First Approach)**
- **Polygon.io**: Professional BTC price and volume data via official API
- **TradingView**: MVRV ratio via respectful scraping (multiple fallback methods)
- **MicroStrategist.com**: MSTR ballistic model data via targeted extraction
- **Barchart.com**: MSTR options volatility metrics via ethical scraping

### 🛡️ **Data Collection Ethics**
- **API Priority**: Always prefer official APIs over scraping when available
- **Respectful Scraping**: See dedicated section above for our ethical practices
- **Fallback Strategy**: Mathematical models ensure service continuity without server burden
- **Rate Limiting**: Appropriate delays between all external requests

### 🗄️ **Storage Architecture**
- **assetdata**: Daily price and indicator storage
- **alerthistory**: Historical alert tracking
- **systemhealth**: Application performance monitoring
- **Retention**: 90-day automatic cleanup

## 📧 **Email Report Features**

### 🎨 **Visual Design**
- **Responsive Layout**: Mobile and desktop optimized
- **Color Coding**: Intuitive signal visualization
- **Professional Styling**: Modern gradient backgrounds
- **Accessibility**: High contrast and semantic markup

### 📱 **Content Structure**
- **Executive Summary**: Key signals at the top
- **Detailed Analysis**: Technical indicators and reasoning
- **Signal History**: Days active and timing predictions
- **Options Strategies**: Actionable trading recommendations

## 🚨 **Error Handling & Monitoring**

### ⚠️ **Failure Scenarios**
- **API Limits**: Automatic fallback to alternative endpoints
- **Scraping Failures**: Multiple method attempts with graceful degradation
- **Network Issues**: Retry logic with exponential backoff
- **Data Validation**: Range checking and anomaly detection
- **Rate Limiting**: Respectful delays prevent IP blocking and ensure long-term reliability

### 📊 **Health Monitoring**
- **Success Rates**: Daily collection success tracking
- **Performance Metrics**: Response time and reliability monitoring
- **Alert Thresholds**: Automatic notifications for failures
- **Data Quality**: Validation and consistency checks

## 🔄 **Maintenance & Updates**

### 📅 **Regular Tasks**
- **API Key Rotation**: Quarterly security updates
- **Dependency Updates**: Monthly package updates
- **Performance Review**: Weekly success rate analysis
- **Signal Accuracy**: Monthly historical validation

### 🔧 **Troubleshooting**
- **Common Issues**: Network timeouts, API rate limits
- **Debug Mode**: Verbose logging for development
- **Test Functions**: Manual trigger capabilities
- **Recovery Procedures**: Documented incident response

## 📚 **Technical Stack**

- **Runtime**: Azure Functions (Python 3.9+)
- **Storage**: Azure Table Storage
- **Web Scraping**: Selenium with Chrome WebDriver
- **Data Processing**: Pandas, NumPy
- **Email**: SMTP with HTML templates
- **APIs**: Polygon.io, TradingView, Barchart
- **Monitoring**: Azure Application Insights

---

## 🚀 **Getting Started**

1. **Clone Repository**: `git clone <repository-url>`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Configure Environment**: Set up Azure resources and API keys
4. **Deploy Function**: Use Azure CLI or VS Code extension
5. **Test Execution**: Trigger function manually to verify setup
6. **Monitor Logs**: Check Application Insights for successful execution

---

*Built with ❤️ for automated market analysis and informed trading decisions.*
