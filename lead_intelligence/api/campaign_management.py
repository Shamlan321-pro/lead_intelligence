# Campaign Management API

import frappe
from frappe import _
from frappe.utils import nowdate, now, cint, flt, get_datetime, add_days
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


@frappe.whitelist()
def create_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new lead generation campaign
    
    Args:
        campaign_data: Dictionary containing campaign configuration
    
    Returns:
        Dictionary containing creation results
    """
    try:
        # Validate campaign data
        validation_result = validate_campaign_data(campaign_data)
        if not validation_result['valid']:
            return {
                'success': False,
                'errors': validation_result['errors']
            }
        
        # Create campaign document
        campaign = frappe.new_doc('Lead Campaign')
        campaign.update({
            'campaign_name': campaign_data['name'],
            'description': campaign_data.get('description', ''),
            'status': 'Draft',
            'owner': frappe.session.user,
            'start_date': campaign_data.get('start_date', nowdate()),
            'end_date': campaign_data.get('end_date'),
            'target_business_type': campaign_data.get('business_type'),
            'target_location': campaign_data.get('location'),
            'target_lead_count': cint(campaign_data.get('target_lead_count', 100)),
            'filter_criteria_json': json.dumps(campaign_data.get('filters', {})),
            'ai_personalization_enabled': campaign_data.get('ai_personalization', True),
            'company_profile': campaign_data.get('company_profile'),
            'outreach_template': campaign_data.get('outreach_template'),
            'email_subject': campaign_data.get('email_subject', ''),
            'email_body': campaign_data.get('email_body', '')
        })
        
        campaign.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'campaign_id': campaign.name,
            'message': _(f"Campaign '{campaign.campaign_name}' created successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign creation failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to create campaign")
        }


@frappe.whitelist()
def update_campaign(campaign_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing campaign
    
    Args:
        campaign_id: ID of the campaign to update
        updates: Dictionary containing fields to update
    
    Returns:
        Dictionary containing update results
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Check permissions
        if not frappe.has_permission('Lead Campaign', 'write', campaign):
            frappe.throw(_("Insufficient permissions to update this campaign"))
        
        # Validate status transitions
        if 'status' in updates:
            if not is_valid_status_transition(campaign.status, updates['status']):
                frappe.throw(_(f"Invalid status transition from {campaign.status} to {updates['status']}"))
        
        # Update allowed fields
        allowed_fields = [
            'campaign_name', 'description', 'status', 'start_date', 'end_date',
            'target_business_type', 'target_location', 'target_lead_count',
            'filter_criteria_json', 'ai_personalization_enabled', 'company_profile',
            'outreach_template', 'email_subject', 'email_body'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(campaign, field, value)
        
        campaign.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': _("Campaign updated successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign update failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to update campaign")
        }


@frappe.whitelist()
def start_campaign(campaign_id: str) -> Dict[str, Any]:
    """
    Start a campaign and begin lead generation
    
    Args:
        campaign_id: ID of the campaign to start
    
    Returns:
        Dictionary containing start results
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Validate campaign can be started
        if campaign.status not in ['Draft', 'Paused']:
            frappe.throw(_(f"Cannot start campaign with status: {campaign.status}"))
        
        # Validate required fields
        required_fields = ['target_location', 'target_lead_count', 'company_profile']
        missing_fields = [field for field in required_fields if not getattr(campaign, field)]
        
        if missing_fields:
            frappe.throw(_(f"Missing required fields: {', '.join(missing_fields)}"))
        
        # Update campaign status
        campaign.status = 'Active'
        campaign.actual_start_date = now()
        campaign.save(ignore_permissions=True)
        
        # Create campaign execution record
        execution = frappe.new_doc('Campaign Execution')
        execution.update({
            'lead_campaign': campaign_id,
            'execution_type': 'Lead Generation',
            'status': 'Running',
            'started_by': frappe.session.user,
            'started_at': now(),
            'target_leads': campaign.target_lead_count
        })
        execution.insert(ignore_permissions=True)
        
        # Enqueue background job for lead generation
        frappe.enqueue(
            'lead_intelligence.api.lead_generation.search_businesses',
            queue='long',
            timeout=3600,
            filters=json.loads(campaign.filter_criteria_json or '{}'),
            campaign_id=campaign_id,
            execution_id=execution.name
        )
        
        return {
            'success': True,
            'execution_id': execution.name,
            'message': _("Campaign started successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign start failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to start campaign")
        }


@frappe.whitelist()
def pause_campaign(campaign_id: str) -> Dict[str, Any]:
    """
    Pause an active campaign
    
    Args:
        campaign_id: ID of the campaign to pause
    
    Returns:
        Dictionary containing pause results
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        if campaign.status != 'Active':
            frappe.throw(_(f"Cannot pause campaign with status: {campaign.status}"))
        
        # Update campaign status
        campaign.status = 'Paused'
        campaign.save(ignore_permissions=True)
        
        # Pause any running executions
        running_executions = frappe.get_all('Campaign Execution', {
            'lead_campaign': campaign_id,
            'status': 'Running'
        })
        
        for execution in running_executions:
            execution_doc = frappe.get_doc('Campaign Execution', execution.name)
            execution_doc.status = 'Paused'
            execution_doc.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': _("Campaign paused successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign pause failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to pause campaign")
        }


@frappe.whitelist()
def complete_campaign(campaign_id: str) -> Dict[str, Any]:
    """
    Mark a campaign as completed
    
    Args:
        campaign_id: ID of the campaign to complete
    
    Returns:
        Dictionary containing completion results
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        if campaign.status not in ['Active', 'Paused']:
            frappe.throw(_(f"Cannot complete campaign with status: {campaign.status}"))
        
        # Update campaign status
        campaign.status = 'Completed'
        campaign.actual_end_date = now()
        campaign.save(ignore_permissions=True)
        
        # Complete any running executions
        running_executions = frappe.get_all('Campaign Execution', {
            'lead_campaign': campaign_id,
            'status': ['in', ['Running', 'Paused']]
        })
        
        for execution in running_executions:
            execution_doc = frappe.get_doc('Campaign Execution', execution.name)
            execution_doc.status = 'Completed'
            execution_doc.completed_at = now()
            execution_doc.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': _("Campaign completed successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign completion failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to complete campaign")
        }


@frappe.whitelist()
def get_campaign_list(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get list of campaigns with optional filters
    
    Args:
        filters: Optional filters to apply
    
    Returns:
        Dictionary containing campaign list
    """
    try:
        # Build filters
        campaign_filters = {}
        if filters:
            if filters.get('status'):
                campaign_filters['status'] = filters['status']
            if filters.get('owner'):
                campaign_filters['owner'] = filters['owner']
            if filters.get('date_range'):
                date_range = filters['date_range']
                if date_range.get('start'):
                    campaign_filters['creation'] = ['>=', date_range['start']]
                if date_range.get('end'):
                    if 'creation' in campaign_filters:
                        campaign_filters['creation'] = ['between', [date_range['start'], date_range['end']]]
                    else:
                        campaign_filters['creation'] = ['<=', date_range['end']]
        
        # Get campaigns
        campaigns = frappe.get_all('Lead Campaign',
            filters=campaign_filters,
            fields=[
                'name', 'campaign_name', 'description', 'status', 'owner',
                'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
                'target_lead_count', 'leads_created', 'emails_sent',
                'emails_delivered', 'emails_opened', 'emails_clicked',
                'responses_received', 'response_rate', 'creation', 'modified'
            ],
            order_by='creation desc'
        )
        
        # Enhance with additional data
        for campaign in campaigns:
            # Calculate progress
            if campaign.target_lead_count and campaign.leads_created:
                campaign['progress'] = min(100, (campaign.leads_created / campaign.target_lead_count) * 100)
            else:
                campaign['progress'] = 0
            
            # Get latest execution status
            latest_execution = frappe.db.get_value('Campaign Execution',
                {'lead_campaign': campaign.name},
                ['status', 'started_at', 'completed_at'],
                order_by='creation desc'
            )
            
            if latest_execution:
                campaign['latest_execution_status'] = latest_execution[0]
                campaign['latest_execution_started'] = latest_execution[1]
                campaign['latest_execution_completed'] = latest_execution[2]
        
        return {
            'success': True,
            'campaigns': campaigns,
            'total_count': len(campaigns)
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign list fetch failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to fetch campaign list")
        }


@frappe.whitelist()
def get_campaign_details(campaign_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific campaign
    
    Args:
        campaign_id: ID of the campaign
    
    Returns:
        Dictionary containing campaign details
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Get campaign executions
        executions = frappe.get_all('Campaign Execution',
            filters={'lead_campaign': campaign_id},
            fields=[
                'name', 'execution_type', 'status', 'started_by', 'started_at',
                'completed_at', 'target_leads', 'processed_leads', 'emails_sent',
                'emails_failed', 'leads_created', 'ai_requests_made', 'ai_tokens_used',
                'ai_cost_incurred', 'execution_log'
            ],
            order_by='creation desc'
        )
        
        # Get related leads
        leads = frappe.get_all('Lead',
            filters={'campaign_name': campaign_id},
            fields=[
                'name', 'lead_name', 'company_name', 'email_id', 'phone',
                'status', 'source', 'creation'
            ],
            order_by='creation desc',
            limit=50
        )
        
        # Calculate analytics
        analytics = calculate_campaign_analytics(campaign_id)
        
        campaign_data = campaign.as_dict()
        campaign_data.update({
            'executions': executions,
            'recent_leads': leads,
            'analytics': analytics
        })
        
        return {
            'success': True,
            'campaign': campaign_data
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign details fetch failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to fetch campaign details")
        }


@frappe.whitelist()
def duplicate_campaign(campaign_id: str, new_name: str) -> Dict[str, Any]:
    """
    Create a duplicate of an existing campaign
    
    Args:
        campaign_id: ID of the campaign to duplicate
        new_name: Name for the new campaign
    
    Returns:
        Dictionary containing duplication results
    """
    try:
        original_campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Create new campaign
        new_campaign = frappe.new_doc('Lead Campaign')
        
        # Copy fields (excluding unique fields)
        exclude_fields = ['name', 'creation', 'modified', 'modified_by', 'owner',
                         'actual_start_date', 'actual_end_date', 'leads_created',
                         'emails_sent', 'emails_delivered', 'emails_opened',
                         'emails_clicked', 'responses_received', 'response_rate']
        
        for field in original_campaign.meta.fields:
            if field.fieldname not in exclude_fields:
                setattr(new_campaign, field.fieldname, getattr(original_campaign, field.fieldname))
        
        # Set new values
        new_campaign.campaign_name = new_name
        new_campaign.status = 'Draft'
        new_campaign.owner = frappe.session.user
        new_campaign.start_date = nowdate()
        new_campaign.end_date = None
        
        new_campaign.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'new_campaign_id': new_campaign.name,
            'message': _(f"Campaign duplicated as '{new_name}'")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign duplication failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to duplicate campaign")
        }


@frappe.whitelist()
def delete_campaign(campaign_id: str) -> Dict[str, Any]:
    """
    Delete a campaign and its related data
    
    Args:
        campaign_id: ID of the campaign to delete
    
    Returns:
        Dictionary containing deletion results
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Check if campaign can be deleted
        if campaign.status == 'Active':
            frappe.throw(_("Cannot delete an active campaign. Please pause or complete it first."))
        
        # Check for related leads
        lead_count = frappe.db.count('Lead', {'campaign_name': campaign_id})
        if lead_count > 0:
            frappe.throw(_(f"Cannot delete campaign with {lead_count} associated leads. Please remove leads first."))
        
        # Delete related executions
        executions = frappe.get_all('Campaign Execution', {'lead_campaign': campaign_id})
        for execution in executions:
            frappe.delete_doc('Campaign Execution', execution.name, ignore_permissions=True)
        
        # Delete campaign
        frappe.delete_doc('Lead Campaign', campaign_id, ignore_permissions=True)
        
        return {
            'success': True,
            'message': _("Campaign deleted successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign deletion failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to delete campaign")
        }


def validate_campaign_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate campaign data before creation/update
    
    Args:
        data: Campaign data to validate
    
    Returns:
        Dictionary containing validation results
    """
    errors = []
    
    # Required fields
    if not data.get('name'):
        errors.append("Campaign name is required")
    
    # Check for duplicate name
    if data.get('name'):
        existing = frappe.db.exists('Lead Campaign', {'campaign_name': data['name']})
        if existing:
            errors.append(f"Campaign with name '{data['name']}' already exists")
    
    # Validate dates
    if data.get('start_date') and data.get('end_date'):
        start_date = get_datetime(data['start_date'])
        end_date = get_datetime(data['end_date'])
        if start_date >= end_date:
            errors.append("End date must be after start date")
    
    # Validate target lead count
    if data.get('target_lead_count'):
        target_count = cint(data['target_lead_count'])
        if target_count <= 0:
            errors.append("Target lead count must be greater than 0")
        elif target_count > 10000:
            errors.append("Target lead count cannot exceed 10,000")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    """
    Check if a status transition is valid
    
    Args:
        current_status: Current campaign status
        new_status: Desired new status
    
    Returns:
        Boolean indicating if transition is valid
    """
    valid_transitions = {
        'Draft': ['Active', 'Cancelled'],
        'Active': ['Paused', 'Completed', 'Cancelled'],
        'Paused': ['Active', 'Completed', 'Cancelled'],
        'Completed': [],
        'Cancelled': []
    }
    
    return new_status in valid_transitions.get(current_status, [])


def calculate_campaign_analytics(campaign_id: str) -> Dict[str, Any]:
    """
    Calculate analytics for a campaign
    
    Args:
        campaign_id: ID of the campaign
    
    Returns:
        Dictionary containing analytics data
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Basic metrics
        analytics = {
            'leads_generated': campaign.leads_created or 0,
            'emails_sent': campaign.emails_sent or 0,
            'emails_delivered': campaign.emails_delivered or 0,
            'emails_opened': campaign.emails_opened or 0,
            'emails_clicked': campaign.emails_clicked or 0,
            'responses_received': campaign.responses_received or 0,
            'response_rate': campaign.response_rate or 0
        }
        
        # Calculate rates
        if analytics['emails_sent'] > 0:
            analytics['delivery_rate'] = (analytics['emails_delivered'] / analytics['emails_sent']) * 100
            analytics['open_rate'] = (analytics['emails_opened'] / analytics['emails_sent']) * 100
            analytics['click_rate'] = (analytics['emails_clicked'] / analytics['emails_sent']) * 100
        else:
            analytics['delivery_rate'] = 0
            analytics['open_rate'] = 0
            analytics['click_rate'] = 0
        
        # Lead status distribution
        lead_statuses = frappe.db.sql("""
            SELECT status, COUNT(*) as count
            FROM `tabLead`
            WHERE campaign_name = %s
            GROUP BY status
        """, (campaign_id,), as_dict=True)
        
        analytics['lead_status_distribution'] = {status['status']: status['count'] for status in lead_statuses}
        
        # Daily progress (last 30 days)
        daily_progress = frappe.db.sql("""
            SELECT DATE(creation) as date, COUNT(*) as leads_created
            FROM `tabLead`
            WHERE campaign_name = %s AND creation >= %s
            GROUP BY DATE(creation)
            ORDER BY date
        """, (campaign_id, add_days(nowdate(), -30)), as_dict=True)
        
        analytics['daily_progress'] = daily_progress
        
        # Cost analysis (if available)
        total_cost = frappe.db.sql("""
            SELECT SUM(ai_cost_incurred) as total_cost
            FROM `tabCampaign Execution`
            WHERE lead_campaign = %s
        """, (campaign_id,))[0][0] or 0
        
        analytics['total_cost'] = flt(total_cost, 2)
        
        if analytics['leads_generated'] > 0:
            analytics['cost_per_lead'] = flt(total_cost / analytics['leads_generated'], 2)
        else:
            analytics['cost_per_lead'] = 0
        
        return analytics
        
    except Exception as e:
        frappe.log_error(f"Campaign analytics calculation failed: {str(e)}", "Campaign Analytics Error")
        return {}


@frappe.whitelist()
def get_campaign_templates() -> Dict[str, Any]:
    """
    Get available campaign templates
    
    Returns:
        Dictionary containing campaign templates
    """
    try:
        templates = [
            {
                'id': 'tech_startup',
                'name': 'Tech Startup Outreach',
                'description': 'Template for reaching out to technology startups',
                'target_business_type': 'Technology',
                'default_filters': {
                    'industry': 'Technology',
                    'min_rating': 4.0,
                    'business_types': ['establishment', 'point_of_interest']
                },
                'email_subject': 'Partnership Opportunity for {{company_name}}',
                'email_body': 'Hi {{contact_name}},\n\nI came across {{company_name}} and was impressed by your work in {{industry}}...'
            },
            {
                'id': 'ecommerce',
                'name': 'E-commerce Business',
                'description': 'Template for e-commerce businesses',
                'target_business_type': 'E-commerce',
                'default_filters': {
                    'industry': 'Retail',
                    'keywords': 'online store shop',
                    'min_rating': 3.5
                },
                'email_subject': 'Boost Your Online Sales with {{our_service}}',
                'email_body': 'Hello {{contact_name}},\n\nI noticed {{company_name}} has a great online presence...'
            },
            {
                'id': 'healthcare',
                'name': 'Healthcare Providers',
                'description': 'Template for healthcare and medical businesses',
                'target_business_type': 'Healthcare',
                'default_filters': {
                    'industry': 'Healthcare',
                    'business_types': ['health', 'hospital', 'doctor'],
                    'min_rating': 4.0
                },
                'email_subject': 'Streamline Your Practice with {{our_solution}}',
                'email_body': 'Dear {{contact_name}},\n\nAs a healthcare provider, {{company_name}} faces unique challenges...'
            }
        ]
        
        return {
            'success': True,
            'templates': templates
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign templates fetch failed: {str(e)}", "Campaign Management Error")
        return {
            'success': False,
            'error': _("Failed to fetch campaign templates")
        }