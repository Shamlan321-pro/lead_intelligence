# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, getdate, add_days
from datetime import datetime

class LeadCampaign(Document):
    def validate(self):
        """Validate campaign data before saving"""
        self.validate_target_count()
        self.validate_dates()
        self.validate_filter_criteria()
        
    def validate_target_count(self):
        """Ensure target lead count is reasonable"""
        if self.target_lead_count and self.target_lead_count > 1000:
            frappe.throw("Target lead count cannot exceed 1000 per campaign")
        if self.target_lead_count and self.target_lead_count < 1:
            frappe.throw("Target lead count must be at least 1")
            
    def validate_dates(self):
        """Validate start and end dates"""
        if self.start_date and self.end_date:
            if getdate(self.start_date) > getdate(self.end_date):
                frappe.throw("Start date cannot be after end date")
                
    def validate_filter_criteria(self):
        """Validate JSON format of filter criteria"""
        if self.filter_criteria:
            try:
                json.loads(self.filter_criteria)
            except json.JSONDecodeError:
                frappe.throw("Filter criteria must be valid JSON")
                
    def before_save(self):
        """Set default values before saving"""
        if not self.owner:
            self.owner = frappe.session.user
        if not self.created_date:
            self.created_date = getdate()
            
    def on_update(self):
        """Handle status changes"""
        if self.has_value_changed('status'):
            self.handle_status_change()
            
    def handle_status_change(self):
        """Handle campaign status changes"""
        if self.status == 'Active':
            self.start_campaign()
        elif self.status == 'Paused':
            self.pause_campaign()
        elif self.status == 'Completed':
            self.complete_campaign()
            
    def start_campaign(self):
        """Start the campaign execution"""
        if not self.start_date:
            self.start_date = getdate()
        self.log_execution(f"Campaign started by {frappe.session.user}")
        
    def pause_campaign(self):
        """Pause the campaign"""
        self.log_execution(f"Campaign paused by {frappe.session.user}")
        
    def complete_campaign(self):
        """Complete the campaign"""
        if not self.end_date:
            self.end_date = getdate()
        self.log_execution(f"Campaign completed by {frappe.session.user}")
        
    def log_execution(self, message):
        """Add entry to execution log"""
        timestamp = now()
        log_entry = f"[{timestamp}] {message}\n"
        
        if self.execution_log:
            self.execution_log += log_entry
        else:
            self.execution_log = log_entry
            
    def update_statistics(self, stats_dict):
        """Update campaign statistics"""
        for field, value in stats_dict.items():
            if hasattr(self, field):
                setattr(self, field, value)
                
        # Calculate response rate
        if self.emails_sent > 0:
            responses = (self.emails_opened or 0) + (self.emails_clicked or 0)
            self.response_rate = (responses / self.emails_sent) * 100
            
        self.save(ignore_permissions=True)
        
    def get_filter_criteria_dict(self):
        """Get filter criteria as dictionary"""
        if self.filter_criteria:
            try:
                return json.loads(self.filter_criteria)
            except json.JSONDecodeError:
                return {}
        return {}
        
    def update_api_usage(self, api_stats):
        """Update API usage statistics"""
        current_stats = {}
        if self.api_usage_stats:
            try:
                current_stats = json.loads(self.api_usage_stats)
            except json.JSONDecodeError:
                current_stats = {}
                
        # Merge new stats with existing
        for key, value in api_stats.items():
            if key in current_stats:
                current_stats[key] += value
            else:
                current_stats[key] = value
                
        self.api_usage_stats = json.dumps(current_stats)
        self.save(ignore_permissions=True)

# Whitelisted methods for API access
@frappe.whitelist()
def get_campaign_statistics(campaign_name):
    """Get campaign statistics"""
    campaign = frappe.get_doc('Lead Campaign', campaign_name)
    return {
        'created_leads': campaign.created_leads or 0,
        'emails_sent': campaign.emails_sent or 0,
        'emails_delivered': campaign.emails_delivered or 0,
        'emails_opened': campaign.emails_opened or 0,
        'emails_clicked': campaign.emails_clicked or 0,
        'response_rate': campaign.response_rate or 0.0
    }

@frappe.whitelist()
def start_lead_generation(campaign_name):
    """Start lead generation for a campaign"""
    campaign = frappe.get_doc('Lead Campaign', campaign_name)
    
    if campaign.status != 'Active':
        frappe.throw("Campaign must be active to start lead generation")
        
    # Create campaign execution record
    execution = frappe.get_doc({
        'doctype': 'Campaign Execution',
        'lead_campaign': campaign_name,
        'execution_type': 'Lead Generation',
        'status': 'Running',
        'started_by': frappe.session.user,
        'started_at': now()
    })
    execution.insert()
    
    # Queue background job for lead generation
    frappe.enqueue(
        'lead_intelligence.api.lead_generation.process_campaign',
        campaign_name=campaign_name,
        execution_name=execution.name,
        queue='long',
        timeout=3600
    )
    
    return {
        'success': True,
        'execution_id': execution.name,
        'message': 'Lead generation started successfully'
    }

@frappe.whitelist()
def get_user_campaigns():
    """Get campaigns for current user"""
    campaigns = frappe.get_list(
        'Lead Campaign',
        filters={'owner': frappe.session.user},
        fields=[
            'name', 'campaign_name', 'status', 'target_lead_count',
            'created_leads', 'emails_sent', 'response_rate', 'creation'
        ],
        order_by='creation desc'
    )
    
    return campaigns

@frappe.whitelist()
def duplicate_campaign(campaign_name, new_name):
    """Duplicate an existing campaign"""
    original = frappe.get_doc('Lead Campaign', campaign_name)
    
    # Create new campaign with copied data
    new_campaign = frappe.get_doc({
        'doctype': 'Lead Campaign',
        'campaign_name': new_name,
        'business_type': original.business_type,
        'location': original.location,
        'target_lead_count': original.target_lead_count,
        'filter_criteria': original.filter_criteria,
        'ai_personalization': original.ai_personalization,
        'company_profile': original.company_profile,
        'outreach_template': original.outreach_template,
        'email_subject': original.email_subject,
        'email_body': original.email_body,
        'status': 'Draft'
    })
    
    new_campaign.insert()
    return new_campaign.name

@frappe.whitelist()
def get_campaign_execution_history(campaign_name):
    """Get execution history for a campaign"""
    executions = frappe.get_list(
        'Campaign Execution',
        filters={'lead_campaign': campaign_name},
        fields=[
            'name', 'execution_type', 'status', 'started_by',
            'started_at', 'completed_at', 'target_leads', 'processed_leads',
            'emails_sent', 'emails_failed'
        ],
        order_by='started_at desc'
    )
    
    return executions