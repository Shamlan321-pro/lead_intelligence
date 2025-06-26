# Lead Intelligence API Module

import frappe
import json
from frappe import _
from frappe.utils import (
    now, today, add_days, get_datetime, format_datetime,
    cint, flt, cstr, get_url
)
from frappe.model.document import Document
from frappe.desk.form.load import get_attachments
from frappe.core.doctype.file.file import create_new_folder
import requests
import csv
import io
import os
from typing import Dict, List, Any, Optional

# Import utility functions
from .utils import (
    get_api_settings, track_api_usage, calculate_lead_score,
    determine_lead_quality, enrich_lead_data, send_notification_email,
    validate_email, validate_phone, log_activity
)

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for Lead Intelligence."""
    try:
        # Campaign statistics
        campaign_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed
            FROM `tabLead Intelligence Campaign`
        """, as_dict=True)[0]
        
        # Lead statistics
        lead_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN lead_quality = 'Hot' THEN 1 ELSE 0 END) as hot,
                SUM(CASE WHEN lead_quality = 'Warm' THEN 1 ELSE 0 END) as warm,
                SUM(CASE WHEN lead_quality = 'Cold' THEN 1 ELSE 0 END) as cold,
                SUM(CASE WHEN lead_quality = 'Unqualified' THEN 1 ELSE 0 END) as unqualified,
                AVG(lead_score) as avg_score
            FROM `tabLead`
            WHERE lead_score IS NOT NULL
        """, as_dict=True)[0]
        
        # API usage statistics (today)
        api_stats = frappe.db.sql("""
            SELECT 
                SUM(google_places_calls + openai_calls + email_calls + crm_calls + 
                    data_enrichment_calls + webhook_calls) as total_calls,
                SUM(google_places_cost + openai_cost + email_cost + crm_cost + 
                    data_enrichment_cost + webhook_cost) as total_cost
            FROM `tabLead Intelligence Usage Stats`
            WHERE date = %s
        """, (today(),), as_dict=True)
        
        api_usage = api_stats[0] if api_stats else {'total_calls': 0, 'total_cost': 0}
        
        # Performance metrics (last 7 days)
        performance_stats = frappe.db.sql("""
            SELECT 
                AVG(average_response_time) as avg_response_time,
                AVG(success_rate) as success_rate,
                SUM(error_count) as total_errors
            FROM `tabLead Intelligence Usage Stats`
            WHERE date >= %s
        """, (add_days(today(), -7),), as_dict=True)[0]
        
        return {
            'campaigns': campaign_stats,
            'leads': lead_stats,
            'api_usage': api_usage,
            'performance': performance_stats
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dashboard stats: {str(e)}")
        return {
            'campaigns': {'total': 0, 'active': 0, 'completed': 0, 'failed': 0},
            'leads': {'total': 0, 'hot': 0, 'warm': 0, 'cold': 0, 'unqualified': 0, 'avg_score': 0},
            'api_usage': {'total_calls': 0, 'total_cost': 0},
            'performance': {'avg_response_time': 0, 'success_rate': 0, 'total_errors': 0}
        }

@frappe.whitelist()
def start_campaign(campaign_id):
    """Start a lead intelligence campaign."""
    try:
        campaign = frappe.get_doc('Lead Intelligence Campaign', campaign_id)
        
        if campaign.status != 'Draft':
            return {'success': False, 'error': 'Campaign is not in draft status'}
        
        # Validate campaign settings
        if not campaign.search_keywords:
            return {'success': False, 'error': 'Search keywords are required'}
        
        if not campaign.target_location:
            return {'success': False, 'error': 'Target location is required'}
        
        # Update campaign status
        campaign.status = 'Processing'
        campaign.started_at = now()
        campaign.save()
        
        # Queue background job for campaign execution
        frappe.enqueue(
            'lead_intelligence.tasks.execute_campaign',
            campaign_id=campaign_id,
            queue='long',
            timeout=3600
        )
        
        log_activity('Campaign Started', f'Campaign {campaign_id} started by {frappe.session.user}')
        
        return {'success': True, 'message': 'Campaign started successfully'}
        
    except Exception as e:
        frappe.log_error(f"Error starting campaign {campaign_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def stop_campaign(campaign_id):
    """Stop a running campaign."""
    try:
        campaign = frappe.get_doc('Lead Intelligence Campaign', campaign_id)
        
        if campaign.status not in ['Processing', 'Queued']:
            return {'success': False, 'error': 'Campaign is not running'}
        
        campaign.status = 'Stopped'
        campaign.completed_at = now()
        campaign.save()
        
        log_activity('Campaign Stopped', f'Campaign {campaign_id} stopped by {frappe.session.user}')
        
        return {'success': True, 'message': 'Campaign stopped successfully'}
        
    except Exception as e:
        frappe.log_error(f"Error stopping campaign {campaign_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_campaign_status(campaign_id):
    """Get current status and progress of a campaign."""
    try:
        campaign = frappe.get_doc('Lead Intelligence Campaign', campaign_id)
        
        # Calculate progress based on leads generated vs target
        progress = 0
        if campaign.max_leads and campaign.leads_generated:
            progress = min(100, (campaign.leads_generated / campaign.max_leads) * 100)
        
        return {
            'status': campaign.status,
            'progress': progress,
            'leads_generated': campaign.leads_generated or 0,
            'max_leads': campaign.max_leads or 0,
            'started_at': campaign.started_at,
            'completed_at': campaign.completed_at
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting campaign status {campaign_id}: {str(e)}")
        return {'status': 'Unknown', 'progress': 0}

@frappe.whitelist()
def enrich_lead(lead_id):
    """Enrich a lead with additional data from external sources."""
    try:
        lead = frappe.get_doc('Lead', lead_id)
        
        # Perform data enrichment
        enrichment_data = enrich_lead_data({
            'email': lead.email_id,
            'company': lead.company_name,
            'phone': lead.phone,
            'website': getattr(lead, 'website', None)
        })
        
        if enrichment_data:
            # Update lead with enriched data
            if enrichment_data.get('company_info'):
                lead.enrichment_data = json.dumps(enrichment_data['company_info'])
            
            if enrichment_data.get('social_profiles'):
                lead.social_profiles = json.dumps(enrichment_data['social_profiles'])
            
            # Update lead score based on new data
            lead.lead_score = calculate_lead_score(lead)
            lead.lead_quality = determine_lead_quality(lead.lead_score)
            
            lead.save()
            
            log_activity('Lead Enriched', f'Lead {lead_id} enriched successfully')
            
            return {'success': True, 'message': 'Lead enriched successfully', 'data': enrichment_data}
        else:
            return {'success': False, 'error': 'No enrichment data found'}
            
    except Exception as e:
        frappe.log_error(f"Error enriching lead {lead_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def calculate_lead_score_api(lead_id):
    """Calculate and update lead score."""
    try:
        lead = frappe.get_doc('Lead', lead_id)
        
        # Calculate new score
        score = calculate_lead_score(lead)
        quality = determine_lead_quality(score)
        
        # Update lead
        lead.lead_score = score
        lead.lead_quality = quality
        lead.save()
        
        log_activity('Lead Scored', f'Lead {lead_id} scored: {score} ({quality})')
        
        return {
            'success': True,
            'score': score,
            'quality': quality,
            'message': f'Lead score calculated: {score} ({quality})'
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating lead score {lead_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def export_leads(filters=None):
    """Export leads to CSV file."""
    try:
        if isinstance(filters, str):
            filters = json.loads(filters)
        
        # Build query conditions
        conditions = []
        values = []
        
        if filters:
            if filters.get('lead_quality'):
                conditions.append('lead_quality = %s')
                values.append(filters['lead_quality'])
            
            if filters.get('campaign_source'):
                conditions.append('campaign_source = %s')
                values.append(filters['campaign_source'])
            
            if filters.get('date_from'):
                conditions.append('creation >= %s')
                values.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append('creation <= %s')
                values.append(filters['date_to'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # Get leads data
        leads = frappe.db.sql(f"""
            SELECT 
                name, lead_name, company_name, email_id, phone,
                lead_score, lead_quality, campaign_source, status,
                creation, modified
            FROM `tabLead`
            WHERE {where_clause}
            ORDER BY creation DESC
        """, values, as_dict=True)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'ID', 'Name', 'Company', 'Email', 'Phone',
            'Score', 'Quality', 'Source', 'Status',
            'Created', 'Modified'
        ])
        
        writer.writeheader()
        for lead in leads:
            writer.writerow({
                'ID': lead.name,
                'Name': lead.lead_name or '',
                'Company': lead.company_name or '',
                'Email': lead.email_id or '',
                'Phone': lead.phone or '',
                'Score': lead.lead_score or '',
                'Quality': lead.lead_quality or '',
                'Source': lead.campaign_source or '',
                'Status': lead.status or '',
                'Created': format_datetime(lead.creation),
                'Modified': format_datetime(lead.modified)
            })
        
        # Save file
        file_name = f"leads_export_{frappe.utils.now().replace(' ', '_').replace(':', '-')}.csv"
        file_path = f"/files/{file_name}"
        
        with open(frappe.get_site_path('public', 'files', file_name), 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        file_url = get_url(file_path)
        
        return {
            'success': True,
            'file_url': file_url,
            'file_name': file_name,
            'records_count': len(leads)
        }
        
    except Exception as e:
        frappe.log_error(f"Error exporting leads: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_settings():
    """Get Lead Intelligence settings."""
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        
        # Return safe settings (without sensitive data)
        return {
            'enabled': settings.enabled,
            'search_radius': settings.search_radius,
            'max_leads_per_campaign': settings.max_leads_per_campaign,
            'auto_enrich_leads': settings.auto_enrich_leads,
            'auto_score_leads': settings.auto_score_leads,
            'email_notifications': settings.email_notifications,
            'refresh_interval': getattr(settings, 'refresh_interval', 30),
            'max_retries': getattr(settings, 'max_retries', 3)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting settings: {str(e)}")
        return {}

@frappe.whitelist()
def save_settings(settings):
    """Save Lead Intelligence settings."""
    try:
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        doc = frappe.get_single('Lead Intelligence Settings')
        
        # Update settings
        for key, value in settings.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        
        doc.save()
        
        log_activity('Settings Updated', f'Settings updated by {frappe.session.user}')
        
        return {'success': True, 'message': 'Settings saved successfully'}
        
    except Exception as e:
        frappe.log_error(f"Error saving settings: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def test_api_connection(api_type):
    """Test API connection for various services."""
    try:
        settings = get_api_settings()
        
        if api_type == 'google_places':
            if not settings.get('google_places_api_key'):
                return {'success': False, 'error': 'Google Places API key not configured'}
            
            # Test Google Places API
            url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
            params = {
                'query': 'test',
                'key': settings['google_places_api_key']
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' or data.get('status') == 'ZERO_RESULTS':
                    return {'success': True, 'message': 'Google Places API connection successful'}
                else:
                    return {'success': False, 'error': f"API Error: {data.get('status')}"}
            else:
                return {'success': False, 'error': f"HTTP Error: {response.status_code}"}
        
        elif api_type == 'openai':
            if not settings.get('openai_api_key'):
                return {'success': False, 'error': 'OpenAI API key not configured'}
            
            # Test OpenAI API
            headers = {
                'Authorization': f"Bearer {settings['openai_api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'OpenAI API connection successful'}
            else:
                return {'success': False, 'error': f"HTTP Error: {response.status_code}"}
        
        elif api_type == 'sendgrid':
            if not settings.get('sendgrid_api_key'):
                return {'success': False, 'error': 'SendGrid API key not configured'}
            
            # Test SendGrid API
            headers = {
                'Authorization': f"Bearer {settings['sendgrid_api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.sendgrid.com/v3/user/profile',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'SendGrid API connection successful'}
            else:
                return {'success': False, 'error': f"HTTP Error: {response.status_code}"}
        
        else:
            return {'success': False, 'error': f"Unknown API type: {api_type}"}
            
    except requests.RequestException as e:
        return {'success': False, 'error': f"Network error: {str(e)}"}
    except Exception as e:
        frappe.log_error(f"Error testing {api_type} API: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_usage_analytics(period='week'):
    """Get usage analytics for specified period."""
    try:
        if period == 'week':
            start_date = add_days(today(), -7)
        elif period == 'month':
            start_date = add_days(today(), -30)
        elif period == 'year':
            start_date = add_days(today(), -365)
        else:
            start_date = add_days(today(), -7)
        
        # Get usage statistics
        usage_data = frappe.db.sql("""
            SELECT 
                date,
                SUM(google_places_calls + openai_calls + email_calls + crm_calls + 
                    data_enrichment_calls + webhook_calls) as total_calls,
                SUM(google_places_cost + openai_cost + email_cost + crm_cost + 
                    data_enrichment_cost + webhook_cost) as total_cost,
                SUM(leads_generated) as leads_generated,
                SUM(emails_sent) as emails_sent,
                AVG(success_rate) as avg_success_rate
            FROM `tabLead Intelligence Usage Stats`
            WHERE date >= %s
            GROUP BY date
            ORDER BY date
        """, (start_date,), as_dict=True)
        
        return {
            'success': True,
            'data': usage_data,
            'period': period,
            'start_date': start_date,
            'end_date': today()
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting usage analytics: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def search_leads(query, filters=None):
    """Search leads with advanced filtering."""
    try:
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        
        # Build search conditions
        conditions = []
        values = []
        
        if query:
            conditions.append(
                "(lead_name LIKE %s OR company_name LIKE %s OR email_id LIKE %s)"
            )
            search_term = f"%{query}%"
            values.extend([search_term, search_term, search_term])
        
        if filters:
            if filters.get('quality'):
                conditions.append('lead_quality = %s')
                values.append(filters['quality'])
            
            if filters.get('score_min'):
                conditions.append('lead_score >= %s')
                values.append(filters['score_min'])
            
            if filters.get('score_max'):
                conditions.append('lead_score <= %s')
                values.append(filters['score_max'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # Execute search
        leads = frappe.db.sql(f"""
            SELECT 
                name, lead_name, company_name, email_id, phone,
                lead_score, lead_quality, status, creation
            FROM `tabLead`
            WHERE {where_clause}
            ORDER BY lead_score DESC, creation DESC
            LIMIT 50
        """, values, as_dict=True)
        
        return {
            'success': True,
            'leads': leads,
            'count': len(leads)
        }
        
    except Exception as e:
        frappe.log_error(f"Error searching leads: {str(e)}")
        return {'success': False, 'error': str(e)}

@frappe.whitelist()
def get_lead_insights(lead_id):
    """Get AI-powered insights for a specific lead."""
    try:
        lead = frappe.get_doc('Lead', lead_id)
        
        # Get enrichment data
        enrichment_data = {}
        if lead.enrichment_data:
            try:
                enrichment_data = json.loads(lead.enrichment_data)
            except:
                pass
        
        # Calculate insights
        insights = {
            'score_breakdown': {
                'data_completeness': calculate_data_completeness_score(lead),
                'engagement_level': calculate_engagement_score(lead),
                'company_profile': calculate_company_score(lead, enrichment_data)
            },
            'recommendations': generate_lead_recommendations(lead, enrichment_data),
            'next_actions': suggest_next_actions(lead),
            'similar_leads': find_similar_leads(lead)
        }
        
        return {
            'success': True,
            'insights': insights
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting lead insights {lead_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

# Helper functions for lead insights
def calculate_data_completeness_score(lead):
    """Calculate data completeness score for a lead."""
    fields = ['lead_name', 'company_name', 'email_id', 'phone', 'website']
    completed = sum(1 for field in fields if getattr(lead, field, None))
    return (completed / len(fields)) * 100

def calculate_engagement_score(lead):
    """Calculate engagement score based on interactions."""
    # This would be based on email opens, clicks, website visits, etc.
    # For now, return a placeholder
    return 50

def calculate_company_score(lead, enrichment_data):
    """Calculate company profile score."""
    score = 0
    if enrichment_data.get('employee_count'):
        if enrichment_data['employee_count'] > 100:
            score += 30
        elif enrichment_data['employee_count'] > 10:
            score += 20
        else:
            score += 10
    
    if enrichment_data.get('annual_revenue'):
        score += 20
    
    if enrichment_data.get('industry'):
        score += 15
    
    return min(score, 100)

def generate_lead_recommendations(lead, enrichment_data):
    """Generate AI-powered recommendations for the lead."""
    recommendations = []
    
    if not lead.phone:
        recommendations.append("Consider finding a phone number for better contact options")
    
    if lead.lead_score and lead.lead_score < 50:
        recommendations.append("Lead score is low - focus on data enrichment")
    
    if not enrichment_data:
        recommendations.append("Run data enrichment to get more company information")
    
    return recommendations

def suggest_next_actions(lead):
    """Suggest next actions for the lead."""
    actions = []
    
    if lead.status == 'Lead':
        actions.append("Send initial outreach email")
        actions.append("Connect on LinkedIn")
    
    if lead.lead_quality == 'Hot':
        actions.append("Schedule a demo call")
        actions.append("Send pricing information")
    
    return actions

def find_similar_leads(lead):
    """Find similar leads based on company size, industry, etc."""
    try:
        similar = frappe.db.sql("""
            SELECT name, lead_name, company_name, lead_score
            FROM `tabLead`
            WHERE name != %s
            AND lead_quality = %s
            ORDER BY lead_score DESC
            LIMIT 5
        """, (lead.name, lead.lead_quality), as_dict=True)
        
        return similar
    except:
        return []