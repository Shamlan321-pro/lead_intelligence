# Lead Intelligence for ERPNext

Advanced lead generation and intelligence platform for ERPNext that leverages AI and external APIs to automate lead discovery, enrichment, and scoring.

## Features

### 🎯 Lead Generation
- **Google Places Integration**: Automatically discover businesses based on location and keywords
- **Campaign Management**: Create and manage targeted lead generation campaigns
- **Real-time Progress Tracking**: Monitor campaign progress with live updates
- **Bulk Lead Import**: Import leads from CSV files or external sources

### 🧠 AI-Powered Intelligence
- **Lead Scoring**: Automatically score leads based on data completeness and quality
- **Lead Quality Classification**: Categorize leads as Hot, Warm, Cold, or Unqualified
- **AI Insights**: Get AI-powered recommendations for lead engagement
- **Predictive Analytics**: Forecast lead conversion probability

### 📊 Data Enrichment
- **Company Information**: Enrich leads with company data from external sources
- **Social Profile Discovery**: Find LinkedIn, Twitter, and other social profiles
- **Contact Information**: Discover additional email addresses and phone numbers
- **Industry Classification**: Automatically categorize leads by industry

### 📈 Analytics & Reporting
- **Dashboard Analytics**: Comprehensive dashboard with key metrics
- **Usage Statistics**: Track API usage and costs
- **Performance Metrics**: Monitor system performance and success rates
- **Export Capabilities**: Export leads and analytics to CSV/Excel

### 🔗 CRM Integration
- **Seamless ERPNext Integration**: Works natively with ERPNext Lead and Customer modules
- **Custom Fields**: Adds intelligence fields to existing DocTypes
- **Workflow Integration**: Integrates with ERPNext workflows
- **External CRM Sync**: Sync with Salesforce, HubSpot, and Pipedrive

## Installation

### Prerequisites
- ERPNext v13+ or Frappe v13+
- Python 3.7+
- Redis (for background jobs)
- Valid API keys for external services

### Quick Install

1. **Clone the repository**:
   ```bash
   cd /path/to/frappe-bench/apps
   git clone https://github.com/your-org/lead_intelligence.git
   ```

2. **Install the app**:
   ```bash
   bench --site your-site install-app lead_intelligence
   ```

3. **Run post-installation setup**:
   ```bash
   bench --site your-site execute lead_intelligence.install.post_install
   ```

4. **Restart services**:
   ```bash
   bench restart
   ```

### Manual Installation

1. **Download and extract** the Lead Intelligence module to your ERPNext apps directory
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run database migrations**:
   ```bash
   bench --site your-site migrate
   ```
4. **Clear cache**:
   ```bash
   bench --site your-site clear-cache
   ```

## Configuration

### API Keys Setup

1. **Navigate to Lead Intelligence Settings**:
   - Go to `Setup > Lead Intelligence > Lead Intelligence Settings`

2. **Configure API Keys**:
   - **Google Places API**: For location-based lead discovery
   - **OpenAI API**: For AI-powered insights and scoring
   - **SendGrid API**: For email notifications
   - **External CRM APIs**: For data synchronization

3. **Set Rate Limits**:
   - Configure API rate limits to control usage and costs
   - Set daily/monthly spending limits

### Basic Settings

```python
# Example configuration
settings = {
    'enabled': True,
    'search_radius': 50,  # km
    'max_leads_per_campaign': 1000,
    'auto_enrich_leads': True,
    'auto_score_leads': True,
    'email_notifications': True
}
```

## Usage

### Creating a Lead Generation Campaign

1. **Navigate to Lead Intelligence Campaign**:
   - Go to `CRM > Lead Intelligence > Lead Intelligence Campaign`

2. **Create New Campaign**:
   ```python
   campaign = {
       'campaign_name': 'Tech Startups in San Francisco',
       'search_keywords': 'software development, tech startup',
       'target_location': 'San Francisco, CA',
       'search_radius': 25,
       'max_leads': 500,
       'status': 'Draft'
   }
   ```

3. **Start Campaign**:
   - Click "Start Campaign" to begin lead generation
   - Monitor progress in real-time

### Lead Scoring and Enrichment

**Automatic Scoring**:
```python
# Lead score is calculated based on:
# - Data completeness (40%)
# - Company profile (30%)
# - Contact information quality (20%)
# - Engagement potential (10%)

lead_score = calculate_lead_score(lead)
lead_quality = determine_lead_quality(lead_score)
```

**Manual Enrichment**:
1. Open any Lead record
2. Click "Enrich Data" in the Lead Intelligence section
3. Review enriched information

### API Usage

**Get Dashboard Statistics**:
```javascript
frappe.call({
    method: 'lead_intelligence.api.get_dashboard_stats',
    callback: function(r) {
        console.log(r.message);
    }
});
```

**Start Campaign**:
```javascript
frappe.call({
    method: 'lead_intelligence.api.start_campaign',
    args: {
        campaign_id: 'CAMP-2024-001'
    },
    callback: function(r) {
        if (r.message.success) {
            frappe.show_alert('Campaign started successfully');
        }
    }
});
```

**Enrich Lead**:
```javascript
frappe.call({
    method: 'lead_intelligence.api.enrich_lead',
    args: {
        lead_id: 'LEAD-2024-001'
    },
    callback: function(r) {
        if (r.message.success) {
            // Handle enriched data
            console.log(r.message.data);
        }
    }
});
```

## Architecture

### Module Structure
```
lead_intelligence/
├── __init__.py                 # Module initialization
├── api.py                      # API endpoints
├── utils.py                    # Utility functions
├── tasks.py                    # Background tasks
├── install.py                  # Installation scripts
├── hooks.py                    # ERPNext hooks
├── public/
│   ├── css/
│   │   └── lead_intelligence.css
│   └── js/
│       ├── lead_intelligence.js
│       ├── lead.js
│       ├── customer.js
│       └── contact.js
└── lead_intelligence/
    └── doctype/
        ├── lead_intelligence_campaign/
        ├── lead_intelligence_settings/
        └── lead_intelligence_usage_stats/
```

### Data Flow
1. **Campaign Creation**: User creates campaign with search criteria
2. **Lead Discovery**: Google Places API searches for matching businesses
3. **Data Enrichment**: External APIs enrich lead data
4. **AI Scoring**: OpenAI analyzes and scores leads
5. **CRM Integration**: Leads are created/updated in ERPNext
6. **Analytics**: Usage and performance metrics are tracked

### Background Jobs
- **Campaign Processing**: Handles lead generation campaigns
- **Data Enrichment**: Enriches leads with external data
- **Score Calculation**: Updates lead scores periodically
- **CRM Synchronization**: Syncs data with external CRMs
- **Cleanup Tasks**: Maintains data hygiene

## API Reference

### Dashboard APIs
- `GET /api/method/lead_intelligence.api.get_dashboard_stats`
- `GET /api/method/lead_intelligence.api.get_usage_analytics`

### Campaign APIs
- `POST /api/method/lead_intelligence.api.start_campaign`
- `POST /api/method/lead_intelligence.api.stop_campaign`
- `GET /api/method/lead_intelligence.api.get_campaign_status`

### Lead APIs
- `POST /api/method/lead_intelligence.api.enrich_lead`
- `POST /api/method/lead_intelligence.api.calculate_lead_score_api`
- `GET /api/method/lead_intelligence.api.get_lead_insights`
- `POST /api/method/lead_intelligence.api.export_leads`

### Settings APIs
- `GET /api/method/lead_intelligence.api.get_settings`
- `POST /api/method/lead_intelligence.api.save_settings`
- `POST /api/method/lead_intelligence.api.test_api_connection`

## Customization

### Custom Lead Scoring

Create custom scoring algorithms:

```python
# In your custom app
from lead_intelligence.utils import calculate_lead_score

def custom_lead_scoring(lead):
    base_score = calculate_lead_score(lead)
    
    # Add custom scoring logic
    if lead.industry == 'Technology':
        base_score += 10
    
    if lead.company_size == 'Large':
        base_score += 15
    
    return min(base_score, 100)

# Override in hooks.py
override_whitelisted_methods = {
    'lead_intelligence.utils.calculate_lead_score': 'your_app.custom.custom_lead_scoring'
}
```

### Custom Data Sources

Add custom data enrichment sources:

```python
# In your custom app
def custom_enrich_lead(lead_data):
    # Your custom enrichment logic
    enriched_data = {}
    
    # Call your custom APIs
    company_info = get_company_info_from_custom_api(lead_data['company'])
    enriched_data['company_info'] = company_info
    
    return enriched_data

# Register in hooks.py
enrichment_sources = {
    'custom_source': 'your_app.custom.custom_enrich_lead'
}
```

## Troubleshooting

### Common Issues

**1. API Rate Limits Exceeded**
```bash
# Check current usage
bench --site your-site execute "lead_intelligence.api.get_usage_analytics()"

# Adjust rate limits in settings
```

**2. Background Jobs Not Running**
```bash
# Check job queue
bench --site your-site doctor

# Restart workers
bench restart
```

**3. Missing Custom Fields**
```bash
# Reinstall custom fields
bench --site your-site execute "lead_intelligence.install.create_custom_fields()"
```

### Debug Mode

Enable debug logging:

```python
# In site_config.json
{
    "lead_intelligence_debug": true,
    "log_level": "DEBUG"
}
```

### Performance Optimization

1. **Database Indexing**:
   ```sql
   CREATE INDEX idx_lead_score ON `tabLead` (lead_score);
   CREATE INDEX idx_lead_quality ON `tabLead` (lead_quality);
   ```

2. **Cache Configuration**:
   ```python
   # Increase cache timeout for enrichment data
   ENRICHMENT_CACHE_TIMEOUT = 3600  # 1 hour
   ```

3. **Background Job Optimization**:
   ```python
   # Adjust worker configuration
   WORKER_CONFIG = {
       'timeout': 300,
       'max_retries': 3,
       'retry_delay': 60
   }
   ```

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create development branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. **Run tests**:
   ```bash
   python -m pytest tests/
   ```

### Code Standards

- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Write comprehensive tests
- Document all functions and classes
- Use type hints where applicable

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_lead_scoring.py

# Run with coverage
python -m pytest --cov=lead_intelligence tests/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://docs.leadintelligence.com](https://docs.leadintelligence.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/lead_intelligence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/lead_intelligence/discussions)
- **Email**: support@leadintelligence.com

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Google Places integration
- AI-powered lead scoring
- Data enrichment capabilities
- Dashboard analytics
- Campaign management
- ERPNext integration

---

**Made with ❤️ for the ERPNext community**