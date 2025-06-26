# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, get_datetime, time_diff_in_seconds, add_days
from datetime import datetime, timedelta

class CampaignExecution(Document):
    def before_insert(self):
        """Set default values before insertion"""
        self.started_by = frappe.session.user
        self.started_at = now()
        
    def validate(self):
        """Validate execution data"""
        if self.status == 'Running' and not self.started_at:
            self.started_at = now()
            
    def start_execution(self):
        """Start the campaign execution"""
        self.status = 'Running'
        self.started_at = now()
        self.log_message("Campaign execution started")
        self.save(ignore_permissions=True)
        
    def complete_execution(self, success=True):
        """Complete the campaign execution"""
        self.status = 'Completed' if success else 'Failed'
        self.completed_at = now()
        
        # Calculate execution duration
        if self.started_at:
            duration_seconds = time_diff_in_seconds(self.completed_at, self.started_at)
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            self.execution_duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
        self.log_message(f"Campaign execution {self.status.lower()}")
        self.save(ignore_permissions=True)
        
    def cancel_execution(self, reason="Cancelled by user"):
        """Cancel the campaign execution"""
        self.status = 'Cancelled'
        self.completed_at = now()
        self.log_message(f"Campaign execution cancelled: {reason}")
        self.save(ignore_permissions=True)
        
    def log_message(self, message):
        """Add message to execution log"""
        timestamp = now()
        log_entry = f"[{timestamp}] {message}\n"
        
        if self.execution_log:
            self.execution_log += log_entry
        else:
            self.execution_log = log_entry
            
    def update_progress(self, processed=0, emails_sent=0, emails_failed=0, leads_created=0):
        """Update execution progress"""
        self.processed_leads = (self.processed_leads or 0) + processed
        self.emails_sent = (self.emails_sent or 0) + emails_sent
        self.emails_failed = (self.emails_failed or 0) + emails_failed
        self.leads_created = (self.leads_created or 0) + leads_created
        
        # Calculate progress percentage
        if self.target_leads > 0:
            progress = (self.processed_leads / self.target_leads) * 100
            self.log_message(f"Progress: {progress:.1f}% ({self.processed_leads}/{self.target_leads})")
            
        self.save(ignore_permissions=True)
        
    def update_ai_usage(self, requests=0, tokens=0, cost=0.0):
        """Update AI usage statistics"""
        self.ai_requests_made = (self.ai_requests_made or 0) + requests
        self.ai_tokens_used = (self.ai_tokens_used or 0) + tokens
        self.ai_cost_incurred = (self.ai_cost_incurred or 0.0) + cost
        
        # Calculate personalization success rate
        if self.ai_requests_made > 0 and self.emails_sent > 0:
            self.personalization_success_rate = (self.emails_sent / self.ai_requests_made) * 100
            
        self.save(ignore_permissions=True)
        
    def update_performance_metrics(self, delivered=0, opened=0, clicked=0, responses=0):
        """Update performance metrics"""
        self.emails_delivered = (self.emails_delivered or 0) + delivered
        self.emails_opened = (self.emails_opened or 0) + opened
        self.emails_clicked = (self.emails_clicked or 0) + clicked
        self.responses_received = (self.responses_received or 0) + responses
        
        self.save(ignore_permissions=True)
        
    def get_execution_summary(self):
        """Get execution summary"""
        summary = {
            'execution_id': self.name,
            'campaign': self.lead_campaign,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration': self.execution_duration,
            'statistics': {
                'target_leads': self.target_leads or 0,
                'processed_leads': self.processed_leads or 0,
                'leads_created': self.leads_created or 0,
                'emails_sent': self.emails_sent or 0,
                'emails_failed': self.emails_failed or 0,
                'emails_delivered': self.emails_delivered or 0,
                'emails_opened': self.emails_opened or 0,
                'emails_clicked': self.emails_clicked or 0,
                'responses_received': self.responses_received or 0
            },
            'ai_usage': {
                'requests_made': self.ai_requests_made or 0,
                'tokens_used': self.ai_tokens_used or 0,
                'cost_incurred': self.ai_cost_incurred or 0.0,
                'success_rate': self.personalization_success_rate or 0
            }
        }
        
        # Calculate rates
        if self.emails_sent > 0:
            summary['rates'] = {
                'delivery_rate': (self.emails_delivered / self.emails_sent) * 100 if self.emails_delivered else 0,
                'open_rate': (self.emails_opened / self.emails_delivered) * 100 if self.emails_delivered and self.emails_opened else 0,
                'click_rate': (self.emails_clicked / self.emails_opened) * 100 if self.emails_opened and self.emails_clicked else 0,
                'response_rate': (self.responses_received / self.emails_delivered) * 100 if self.emails_delivered and self.responses_received else 0
            }
        else:
            summary['rates'] = {
                'delivery_rate': 0,
                'open_rate': 0,
                'click_rate': 0,
                'response_rate': 0
            }
            
        return summary

# Whitelisted methods for API access
@frappe.whitelist()
def get_campaign_executions(campaign=None, status=None, limit=50):
    """Get campaign executions with filters"""
    filters = {}
    
    if campaign:
        filters['lead_campaign'] = campaign
    if status:
        filters['status'] = status
        
    executions = frappe.get_list(
        'Campaign Execution',
        filters=filters,
        fields=[
            'name', 'lead_campaign', 'status', 'started_at', 'completed_at',
            'target_leads', 'processed_leads', 'emails_sent', 'emails_failed',
            'leads_created', 'execution_duration'
        ],
        order_by='started_at desc',
        limit=limit
    )
    
    return executions

@frappe.whitelist()
def get_execution_details(execution_id):
    """Get detailed execution information"""
    execution = frappe.get_doc('Campaign Execution', execution_id)
    return execution.get_execution_summary()

@frappe.whitelist()
def cancel_execution(execution_id, reason=None):
    """Cancel a running execution"""
    execution = frappe.get_doc('Campaign Execution', execution_id)
    
    if execution.status not in ['Running', 'Queued']:
        frappe.throw(f"Cannot cancel execution with status: {execution.status}")
        
    execution.cancel_execution(reason or "Cancelled by user")
    return {'success': True, 'message': 'Execution cancelled successfully'}

@frappe.whitelist()
def get_execution_analytics(days=30, campaign=None):
    """Get execution analytics for specified period"""
    from_date = add_days(get_datetime(), -int(days))
    
    filters = {
        'started_at': ['>=', from_date]
    }
    
    if campaign:
        filters['lead_campaign'] = campaign
        
    executions = frappe.get_list(
        'Campaign Execution',
        filters=filters,
        fields=[
            'name', 'lead_campaign', 'status', 'started_at', 'completed_at',
            'target_leads', 'processed_leads', 'emails_sent', 'emails_failed',
            'leads_created', 'ai_requests_made', 'ai_tokens_used', 'ai_cost_incurred',
            'emails_delivered', 'emails_opened', 'emails_clicked', 'responses_received'
        ]
    )
    
    # Calculate summary statistics
    total_executions = len(executions)
    completed_executions = len([e for e in executions if e.status == 'Completed'])
    failed_executions = len([e for e in executions if e.status == 'Failed'])
    
    total_leads_processed = sum(e.processed_leads or 0 for e in executions)
    total_emails_sent = sum(e.emails_sent or 0 for e in executions)
    total_leads_created = sum(e.leads_created or 0 for e in executions)
    total_ai_cost = sum(e.ai_cost_incurred or 0 for e in executions)
    
    # Calculate rates
    success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0
    
    total_delivered = sum(e.emails_delivered or 0 for e in executions)
    total_opened = sum(e.emails_opened or 0 for e in executions)
    total_clicked = sum(e.emails_clicked or 0 for e in executions)
    total_responses = sum(e.responses_received or 0 for e in executions)
    
    delivery_rate = (total_delivered / total_emails_sent * 100) if total_emails_sent > 0 else 0
    open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
    click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
    response_rate = (total_responses / total_delivered * 100) if total_delivered > 0 else 0
    
    # Group by status for chart data
    status_data = {}
    for execution in executions:
        status = execution.status
        if status not in status_data:
            status_data[status] = 0
        status_data[status] += 1
        
    # Group by date for trend analysis
    daily_data = {}
    for execution in executions:
        date = execution.started_at.date() if execution.started_at else None
        if date:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'executions': 0,
                    'leads_processed': 0,
                    'emails_sent': 0
                }
            daily_data[date_str]['executions'] += 1
            daily_data[date_str]['leads_processed'] += execution.processed_leads or 0
            daily_data[date_str]['emails_sent'] += execution.emails_sent or 0
            
    return {
        'summary': {
            'total_executions': total_executions,
            'completed_executions': completed_executions,
            'failed_executions': failed_executions,
            'success_rate': success_rate,
            'total_leads_processed': total_leads_processed,
            'total_emails_sent': total_emails_sent,
            'total_leads_created': total_leads_created,
            'total_ai_cost': total_ai_cost,
            'delivery_rate': delivery_rate,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'response_rate': response_rate
        },
        'executions': executions,
        'status_distribution': status_data,
        'daily_trends': daily_data
    }

@frappe.whitelist()
def get_running_executions():
    """Get currently running executions"""
    running_executions = frappe.get_list(
        'Campaign Execution',
        filters={'status': ['in', ['Running', 'Queued']]},
        fields=[
            'name', 'lead_campaign', 'status', 'started_at',
            'target_leads', 'processed_leads', 'emails_sent'
        ],
        order_by='started_at desc'
    )
    
    # Add progress percentage
    for execution in running_executions:
        if execution.target_leads and execution.target_leads > 0:
            execution.progress = (execution.processed_leads or 0) / execution.target_leads * 100
        else:
            execution.progress = 0
            
    return running_executions

@frappe.whitelist()
def retry_failed_execution(execution_id):
    """Retry a failed execution"""
    original_execution = frappe.get_doc('Campaign Execution', execution_id)
    
    if original_execution.status != 'Failed':
        frappe.throw("Can only retry failed executions")
        
    # Create new execution
    new_execution = frappe.copy_doc(original_execution)
    new_execution.status = 'Queued'
    new_execution.started_at = None
    new_execution.completed_at = None
    new_execution.execution_duration = None
    new_execution.execution_log = None
    new_execution.error_details = None
    
    # Reset statistics
    new_execution.processed_leads = 0
    new_execution.emails_sent = 0
    new_execution.emails_failed = 0
    new_execution.leads_created = 0
    new_execution.ai_requests_made = 0
    new_execution.ai_tokens_used = 0
    new_execution.ai_cost_incurred = 0
    new_execution.emails_delivered = 0
    new_execution.emails_opened = 0
    new_execution.emails_clicked = 0
    new_execution.responses_received = 0
    
    new_execution.insert()
    return new_execution.name