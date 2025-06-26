# Lead Intelligence Module
# Copyright (c) 2024, Lead Intelligence Team
# License: MIT

__version__ = '1.0.0'
__title__ = 'Lead Intelligence'
__author__ = 'Lead Intelligence Team'
__license__ = 'MIT'
__description__ = 'Advanced lead generation and intelligence platform for ERPNext'

# Module metadata
app_name = 'lead_intelligence'
app_title = 'Lead Intelligence'
app_publisher = 'Lead Intelligence Team'
app_description = 'Advanced lead generation and intelligence platform for ERPNext'
app_icon = 'fa fa-search'
app_color = '#3498db'
app_email = 'support@leadintelligence.com'
app_license = 'MIT'
app_version = '1.0.0'

# Required apps
required_apps = ['frappe', 'erpnext']

# Module imports
from . import api
from . import utils
from . import tasks
from . import install

# Export main functions
__all__ = [
    'api',
    'utils', 
    'tasks',
    'install'
]

# Module initialization
def get_module_info():
    """Get module information."""
    return {
        'name': app_name,
        'title': app_title,
        'version': app_version,
        'description': app_description,
        'author': app_publisher,
        'license': app_license,
        'icon': app_icon,
        'color': app_color
    }

def get_api_endpoints():
    """Get available API endpoints."""
    return {
        'dashboard_stats': 'lead_intelligence.api.get_dashboard_stats',
        'start_campaign': 'lead_intelligence.api.start_campaign',
        'stop_campaign': 'lead_intelligence.api.stop_campaign',
        'get_campaign_status': 'lead_intelligence.api.get_campaign_status',
        'enrich_lead': 'lead_intelligence.api.enrich_lead',
        'calculate_lead_score': 'lead_intelligence.api.calculate_lead_score_api',
        'export_leads': 'lead_intelligence.api.export_leads',
        'get_settings': 'lead_intelligence.api.get_settings',
        'save_settings': 'lead_intelligence.api.save_settings',
        'test_api_connection': 'lead_intelligence.api.test_api_connection',
        'get_usage_analytics': 'lead_intelligence.api.get_usage_analytics',
        'search_leads': 'lead_intelligence.api.search_leads',
        'get_lead_insights': 'lead_intelligence.api.get_lead_insights'
    }

def get_scheduled_tasks():
    """Get scheduled tasks configuration."""
    return {
        'daily': [
            'lead_intelligence.tasks.cleanup_old_usage_stats',
            'lead_intelligence.tasks.generate_daily_usage_summary',
            'lead_intelligence.tasks.check_api_usage_limits',
            'lead_intelligence.tasks.update_lead_scores'
        ],
        'hourly': [
            'lead_intelligence.tasks.process_pending_campaigns',
            'lead_intelligence.tasks.update_campaign_statuses',
            'lead_intelligence.tasks.retry_failed_webhooks'
        ],
        'weekly': [
            'lead_intelligence.tasks.generate_weekly_analytics',
            'lead_intelligence.tasks.cleanup_old_campaign_executions',
            'lead_intelligence.tasks.update_lead_quality_scores'
        ],
        'monthly': [
            'lead_intelligence.tasks.generate_monthly_reports',
            'lead_intelligence.tasks.archive_old_leads',
            'lead_intelligence.tasks.update_system_performance_metrics'
        ],
        'cron': {
            '0 0 * * *': 'lead_intelligence.tasks.cleanup_old_data',
            '*/15 * * * *': 'lead_intelligence.tasks.process_campaign_queue',
            '0 */6 * * *': 'lead_intelligence.tasks.sync_crm_data'
        }
    }

def get_doctypes():
    """Get module DocTypes."""
    return [
        'Lead Intelligence Campaign',
        'Lead Intelligence Settings', 
        'Lead Intelligence Usage Stats'
    ]

def get_custom_fields():
    """Get custom fields added by this module."""
    return {
        'Lead': [
            'lead_score',
            'lead_quality', 
            'campaign_source',
            'enrichment_data',
            'ai_insights'
        ],
        'Customer': [
            'engagement_score',
            'original_lead_score',
            'conversion_source'
        ],
        'Contact': [
            'contact_score',
            'social_profiles'
        ]
    }

def get_permissions():
    """Get module permissions."""
    return {
        'Lead Intelligence Manager': {
            'Lead Intelligence Campaign': ['read', 'write', 'create', 'delete'],
            'Lead Intelligence Settings': ['read', 'write'],
            'Lead Intelligence Usage Stats': ['read', 'write'],
            'Lead': ['read', 'write'],
            'Customer': ['read', 'write'],
            'Contact': ['read', 'write']
        },
        'Lead Intelligence User': {
            'Lead Intelligence Campaign': ['read', 'write', 'create'],
            'Lead Intelligence Settings': ['read'],
            'Lead Intelligence Usage Stats': ['read'],
            'Lead': ['read', 'write'],
            'Customer': ['read'],
            'Contact': ['read']
        }
    }

def validate_installation():
    """Validate module installation."""
    import frappe
    
    errors = []
    
    # Check if required DocTypes exist
    for doctype in get_doctypes():
        if not frappe.db.exists('DocType', doctype):
            errors.append(f'DocType {doctype} not found')
    
    # Check if custom fields exist
    for doctype, fields in get_custom_fields().items():
        for field in fields:
            if not frappe.db.exists('Custom Field', {'dt': doctype, 'fieldname': field}):
                errors.append(f'Custom field {field} not found in {doctype}')
    
    # Check if settings exist
    if not frappe.db.exists('Lead Intelligence Settings'):
        errors.append('Lead Intelligence Settings not found')
    
    return errors

def get_module_status():
    """Get module status information."""
    import frappe
    
    try:
        # Check installation
        errors = validate_installation()
        
        # Get usage statistics
        stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_campaigns,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_campaigns,
                SUM(leads_generated) as total_leads_generated
            FROM `tabLead Intelligence Campaign`
        """, as_dict=True)[0] if frappe.db.exists('DocType', 'Lead Intelligence Campaign') else {}
        
        # Get settings status
        settings_configured = bool(frappe.db.exists('Lead Intelligence Settings'))
        
        return {
            'installed': len(errors) == 0,
            'errors': errors,
            'settings_configured': settings_configured,
            'statistics': stats,
            'version': app_version
        }
        
    except Exception as e:
        return {
            'installed': False,
            'errors': [str(e)],
            'settings_configured': False,
            'statistics': {},
            'version': app_version
        }

# Module health check
def health_check():
    """Perform module health check."""
    import frappe
    from .utils import get_system_health
    
    try:
        # Get module status
        module_status = get_module_status()
        
        # Get system health
        system_health = get_system_health()
        
        # Check API connections
        api_status = {}
        try:
            from .api import test_api_connection
            api_status['google_places'] = test_api_connection('google_places')
            api_status['openai'] = test_api_connection('openai')
            api_status['sendgrid'] = test_api_connection('sendgrid')
        except:
            api_status = {'error': 'API test failed'}
        
        return {
            'module': module_status,
            'system': system_health,
            'apis': api_status,
            'timestamp': frappe.utils.now()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': frappe.utils.now()
        }

# Utility functions for external access
def get_version():
    """Get module version."""
    return __version__

def get_title():
    """Get module title."""
    return __title__

def get_description():
    """Get module description."""
    return __description__

# Module configuration
MODULE_CONFIG = {
    'name': app_name,
    'title': app_title,
    'version': app_version,
    'description': app_description,
    'author': app_publisher,
    'license': app_license,
    'required_apps': required_apps,
    'doctypes': get_doctypes(),
    'custom_fields': get_custom_fields(),
    'permissions': get_permissions(),
    'api_endpoints': get_api_endpoints(),
    'scheduled_tasks': get_scheduled_tasks()
}

# Export module configuration
__all__.extend([
    'MODULE_CONFIG',
    'get_module_info',
    'get_module_status', 
    'health_check',
    'validate_installation'
])