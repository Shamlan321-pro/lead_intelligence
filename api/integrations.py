# Integrations API

import frappe
from frappe import _
from frappe.utils import nowdate, now, cint, flt
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64


@frappe.whitelist()
def sync_with_crm(crm_type: str, sync_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync lead data with external CRM systems
    
    Args:
        crm_type: Type of CRM (salesforce, hubspot, pipedrive, etc.)
        sync_data: Data to sync
    
    Returns:
        Dictionary containing sync results
    """
    try:
        if crm_type.lower() == 'salesforce':
            result = sync_with_salesforce(sync_data)
        elif crm_type.lower() == 'hubspot':
            result = sync_with_hubspot(sync_data)
        elif crm_type.lower() == 'pipedrive':
            result = sync_with_pipedrive(sync_data)
        else:
            return {
                'success': False,
                'error': _(f"Unsupported CRM type: {crm_type}")
            }
        
        # Log sync activity
        log_integration_activity('CRM Sync', crm_type, sync_data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"CRM sync failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to sync with CRM")
        }


@frappe.whitelist()
def send_email_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email campaign through external email service
    
    Args:
        campaign_data: Campaign data including recipients and content
    
    Returns:
        Dictionary containing send results
    """
    try:
        # Get email service settings
        email_settings = get_email_service_settings()
        
        if not email_settings:
            return {
                'success': False,
                'error': _("Email service not configured")
            }
        
        # Send emails based on configured service
        service_type = email_settings.get('service_type', 'smtp')
        
        if service_type == 'sendgrid':
            result = send_via_sendgrid(campaign_data, email_settings)
        elif service_type == 'mailgun':
            result = send_via_mailgun(campaign_data, email_settings)
        elif service_type == 'ses':
            result = send_via_ses(campaign_data, email_settings)
        else:
            result = send_via_smtp(campaign_data, email_settings)
        
        # Log email activity
        log_integration_activity('Email Campaign', service_type, campaign_data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Email campaign failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to send email campaign")
        }


@frappe.whitelist()
def webhook_handler(webhook_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming webhooks from external services
    
    Args:
        webhook_type: Type of webhook (email_event, crm_update, etc.)
        data: Webhook payload data
    
    Returns:
        Dictionary containing processing results
    """
    try:
        if webhook_type == 'email_event':
            result = process_email_webhook(data)
        elif webhook_type == 'crm_update':
            result = process_crm_webhook(data)
        elif webhook_type == 'lead_update':
            result = process_lead_webhook(data)
        else:
            return {
                'success': False,
                'error': _(f"Unsupported webhook type: {webhook_type}")
            }
        
        # Log webhook activity
        log_integration_activity('Webhook', webhook_type, data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Webhook processing failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to process webhook")
        }


@frappe.whitelist()
def sync_calendar_events(calendar_service: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync events with calendar services
    
    Args:
        calendar_service: Calendar service (google, outlook, etc.)
        event_data: Event data to sync
    
    Returns:
        Dictionary containing sync results
    """
    try:
        if calendar_service.lower() == 'google':
            result = sync_with_google_calendar(event_data)
        elif calendar_service.lower() == 'outlook':
            result = sync_with_outlook_calendar(event_data)
        else:
            return {
                'success': False,
                'error': _(f"Unsupported calendar service: {calendar_service}")
            }
        
        # Log calendar activity
        log_integration_activity('Calendar Sync', calendar_service, event_data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Calendar sync failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to sync calendar events")
        }


@frappe.whitelist()
def social_media_integration(platform: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrate with social media platforms
    
    Args:
        platform: Social media platform (linkedin, twitter, etc.)
        action: Action to perform (post, search, connect, etc.)
        data: Action data
    
    Returns:
        Dictionary containing action results
    """
    try:
        if platform.lower() == 'linkedin':
            result = linkedin_integration(action, data)
        elif platform.lower() == 'twitter':
            result = twitter_integration(action, data)
        elif platform.lower() == 'facebook':
            result = facebook_integration(action, data)
        else:
            return {
                'success': False,
                'error': _(f"Unsupported social media platform: {platform}")
            }
        
        # Log social media activity
        log_integration_activity('Social Media', f"{platform}_{action}", data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Social media integration failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to integrate with social media")
        }


@frappe.whitelist()
def data_enrichment_service(service: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead data using external services
    
    Args:
        service: Enrichment service (clearbit, zoominfo, etc.)
        lead_data: Lead data to enrich
    
    Returns:
        Dictionary containing enriched data
    """
    try:
        if service.lower() == 'clearbit':
            result = enrich_with_clearbit(lead_data)
        elif service.lower() == 'zoominfo':
            result = enrich_with_zoominfo(lead_data)
        elif service.lower() == 'hunter':
            result = enrich_with_hunter(lead_data)
        else:
            return {
                'success': False,
                'error': _(f"Unsupported enrichment service: {service}")
            }
        
        # Log enrichment activity
        log_integration_activity('Data Enrichment', service, lead_data, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Data enrichment failed: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to enrich lead data")
        }


# CRM Integration Functions

def sync_with_salesforce(sync_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync data with Salesforce
    """
    try:
        # Get Salesforce settings
        sf_settings = get_salesforce_settings()
        
        if not sf_settings:
            return {
                'success': False,
                'error': _("Salesforce not configured")
            }
        
        # Authenticate with Salesforce
        access_token = authenticate_salesforce(sf_settings)
        
        if not access_token:
            return {
                'success': False,
                'error': _("Salesforce authentication failed")
            }
        
        # Sync leads
        synced_records = []
        failed_records = []
        
        for lead in sync_data.get('leads', []):
            try:
                sf_lead = convert_to_salesforce_format(lead)
                
                # Create or update lead in Salesforce
                response = requests.post(
                    f"{sf_settings['instance_url']}/services/data/v52.0/sobjects/Lead",
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    },
                    json=sf_lead
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    synced_records.append({
                        'local_id': lead.get('name'),
                        'salesforce_id': result.get('id'),
                        'status': 'success'
                    })
                else:
                    failed_records.append({
                        'local_id': lead.get('name'),
                        'error': response.text
                    })
                    
            except Exception as e:
                failed_records.append({
                    'local_id': lead.get('name'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'synced_records': synced_records,
            'failed_records': failed_records,
            'total_processed': len(sync_data.get('leads', []))
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def sync_with_hubspot(sync_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync data with HubSpot
    """
    try:
        # Get HubSpot settings
        hs_settings = get_hubspot_settings()
        
        if not hs_settings or not hs_settings.get('api_key'):
            return {
                'success': False,
                'error': _("HubSpot not configured")
            }
        
        synced_records = []
        failed_records = []
        
        for lead in sync_data.get('leads', []):
            try:
                hs_contact = convert_to_hubspot_format(lead)
                
                # Create contact in HubSpot
                response = requests.post(
                    'https://api.hubapi.com/crm/v3/objects/contacts',
                    headers={
                        'Authorization': f'Bearer {hs_settings["api_key"]}',
                        'Content-Type': 'application/json'
                    },
                    json={'properties': hs_contact}
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    synced_records.append({
                        'local_id': lead.get('name'),
                        'hubspot_id': result.get('id'),
                        'status': 'success'
                    })
                else:
                    failed_records.append({
                        'local_id': lead.get('name'),
                        'error': response.text
                    })
                    
            except Exception as e:
                failed_records.append({
                    'local_id': lead.get('name'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'synced_records': synced_records,
            'failed_records': failed_records,
            'total_processed': len(sync_data.get('leads', []))
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def sync_with_pipedrive(sync_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync data with Pipedrive
    """
    try:
        # Get Pipedrive settings
        pd_settings = get_pipedrive_settings()
        
        if not pd_settings or not pd_settings.get('api_token'):
            return {
                'success': False,
                'error': _("Pipedrive not configured")
            }
        
        synced_records = []
        failed_records = []
        
        for lead in sync_data.get('leads', []):
            try:
                pd_person = convert_to_pipedrive_format(lead)
                
                # Create person in Pipedrive
                response = requests.post(
                    f'https://{pd_settings["company_domain"]}.pipedrive.com/api/v1/persons',
                    params={'api_token': pd_settings['api_token']},
                    json=pd_person
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    synced_records.append({
                        'local_id': lead.get('name'),
                        'pipedrive_id': result.get('data', {}).get('id'),
                        'status': 'success'
                    })
                else:
                    failed_records.append({
                        'local_id': lead.get('name'),
                        'error': response.text
                    })
                    
            except Exception as e:
                failed_records.append({
                    'local_id': lead.get('name'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'synced_records': synced_records,
            'failed_records': failed_records,
            'total_processed': len(sync_data.get('leads', []))
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Email Service Functions

def send_via_sendgrid(campaign_data: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send emails via SendGrid
    """
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, To
        
        sg = sendgrid.SendGridAPIClient(api_key=settings['api_key'])
        
        sent_emails = []
        failed_emails = []
        
        for recipient in campaign_data.get('recipients', []):
            try:
                message = Mail(
                    from_email=campaign_data['from_email'],
                    to_emails=recipient['email'],
                    subject=recipient.get('subject', campaign_data['subject']),
                    html_content=recipient.get('content', campaign_data['content'])
                )
                
                response = sg.send(message)
                
                if response.status_code in [200, 202]:
                    sent_emails.append({
                        'email': recipient['email'],
                        'message_id': response.headers.get('X-Message-Id'),
                        'status': 'sent'
                    })
                else:
                    failed_emails.append({
                        'email': recipient['email'],
                        'error': f"Status code: {response.status_code}"
                    })
                    
            except Exception as e:
                failed_emails.append({
                    'email': recipient['email'],
                    'error': str(e)
                })
        
        return {
            'success': True,
            'sent_emails': sent_emails,
            'failed_emails': failed_emails,
            'total_sent': len(sent_emails),
            'total_failed': len(failed_emails)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_via_mailgun(campaign_data: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send emails via Mailgun
    """
    try:
        sent_emails = []
        failed_emails = []
        
        for recipient in campaign_data.get('recipients', []):
            try:
                response = requests.post(
                    f"https://api.mailgun.net/v3/{settings['domain']}/messages",
                    auth=('api', settings['api_key']),
                    data={
                        'from': campaign_data['from_email'],
                        'to': recipient['email'],
                        'subject': recipient.get('subject', campaign_data['subject']),
                        'html': recipient.get('content', campaign_data['content'])
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    sent_emails.append({
                        'email': recipient['email'],
                        'message_id': result.get('id'),
                        'status': 'sent'
                    })
                else:
                    failed_emails.append({
                        'email': recipient['email'],
                        'error': response.text
                    })
                    
            except Exception as e:
                failed_emails.append({
                    'email': recipient['email'],
                    'error': str(e)
                })
        
        return {
            'success': True,
            'sent_emails': sent_emails,
            'failed_emails': failed_emails,
            'total_sent': len(sent_emails),
            'total_failed': len(failed_emails)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_via_ses(campaign_data: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send emails via Amazon SES
    """
    try:
        import boto3
        
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings['access_key'],
            aws_secret_access_key=settings['secret_key'],
            region_name=settings['region']
        )
        
        sent_emails = []
        failed_emails = []
        
        for recipient in campaign_data.get('recipients', []):
            try:
                response = ses_client.send_email(
                    Source=campaign_data['from_email'],
                    Destination={'ToAddresses': [recipient['email']]},
                    Message={
                        'Subject': {'Data': recipient.get('subject', campaign_data['subject'])},
                        'Body': {
                            'Html': {'Data': recipient.get('content', campaign_data['content'])}
                        }
                    }
                )
                
                sent_emails.append({
                    'email': recipient['email'],
                    'message_id': response['MessageId'],
                    'status': 'sent'
                })
                
            except Exception as e:
                failed_emails.append({
                    'email': recipient['email'],
                    'error': str(e)
                })
        
        return {
            'success': True,
            'sent_emails': sent_emails,
            'failed_emails': failed_emails,
            'total_sent': len(sent_emails),
            'total_failed': len(failed_emails)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_via_smtp(campaign_data: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send emails via SMTP
    """
    try:
        sent_emails = []
        failed_emails = []
        
        # Create SMTP connection
        server = smtplib.SMTP(settings['smtp_server'], settings['smtp_port'])
        
        if settings.get('use_tls'):
            server.starttls()
        
        if settings.get('username') and settings.get('password'):
            server.login(settings['username'], settings['password'])
        
        for recipient in campaign_data.get('recipients', []):
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = campaign_data['from_email']
                msg['To'] = recipient['email']
                msg['Subject'] = recipient.get('subject', campaign_data['subject'])
                
                html_part = MIMEText(recipient.get('content', campaign_data['content']), 'html')
                msg.attach(html_part)
                
                server.send_message(msg)
                
                sent_emails.append({
                    'email': recipient['email'],
                    'status': 'sent'
                })
                
            except Exception as e:
                failed_emails.append({
                    'email': recipient['email'],
                    'error': str(e)
                })
        
        server.quit()
        
        return {
            'success': True,
            'sent_emails': sent_emails,
            'failed_emails': failed_emails,
            'total_sent': len(sent_emails),
            'total_failed': len(failed_emails)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Webhook Processing Functions

def process_email_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process email event webhooks
    """
    try:
        event_type = data.get('event')
        email = data.get('email')
        message_id = data.get('message_id')
        timestamp = data.get('timestamp')
        
        # Find related campaign execution
        execution = find_execution_by_message_id(message_id)
        
        if execution:
            # Update execution metrics based on event type
            if event_type == 'delivered':
                execution.emails_delivered = (execution.emails_delivered or 0) + 1
            elif event_type == 'opened':
                execution.emails_opened = (execution.emails_opened or 0) + 1
            elif event_type == 'clicked':
                execution.emails_clicked = (execution.emails_clicked or 0) + 1
            elif event_type == 'bounced':
                execution.emails_failed = (execution.emails_failed or 0) + 1
            elif event_type == 'unsubscribed':
                # Handle unsubscribe
                handle_unsubscribe(email)
            
            execution.save()
        
        # Log the event
        create_email_event_log({
            'event_type': event_type,
            'email': email,
            'message_id': message_id,
            'timestamp': timestamp,
            'execution': execution.name if execution else None
        })
        
        return {
            'success': True,
            'processed': True
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def process_crm_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process CRM update webhooks
    """
    try:
        # Process CRM updates and sync back to local system
        crm_type = data.get('crm_type')
        record_id = data.get('record_id')
        changes = data.get('changes', {})
        
        # Find local record
        local_record = find_local_record_by_crm_id(crm_type, record_id)
        
        if local_record:
            # Update local record with CRM changes
            for field, value in changes.items():
                if hasattr(local_record, field):
                    setattr(local_record, field, value)
            
            local_record.save()
        
        return {
            'success': True,
            'updated_record': local_record.name if local_record else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def process_lead_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process lead update webhooks
    """
    try:
        # Process lead updates from external sources
        lead_id = data.get('lead_id')
        updates = data.get('updates', {})
        source = data.get('source')
        
        # Find and update lead
        lead = frappe.get_doc('Lead', lead_id)
        
        for field, value in updates.items():
            if hasattr(lead, field):
                setattr(lead, field, value)
        
        lead.save()
        
        return {
            'success': True,
            'updated_lead': lead.name
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Calendar Integration Functions

def sync_with_google_calendar(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync events with Google Calendar
    """
    try:
        # This would use Google Calendar API
        # For now, return placeholder
        return {
            'success': True,
            'event_id': 'google_event_123',
            'calendar_link': 'https://calendar.google.com/event?eid=...',
            'message': 'Event synced with Google Calendar'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def sync_with_outlook_calendar(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync events with Outlook Calendar
    """
    try:
        # This would use Microsoft Graph API
        # For now, return placeholder
        return {
            'success': True,
            'event_id': 'outlook_event_123',
            'calendar_link': 'https://outlook.live.com/calendar/...',
            'message': 'Event synced with Outlook Calendar'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Social Media Integration Functions

def linkedin_integration(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    LinkedIn integration
    """
    try:
        if action == 'search_prospects':
            return search_linkedin_prospects(data)
        elif action == 'send_connection':
            return send_linkedin_connection(data)
        elif action == 'post_content':
            return post_linkedin_content(data)
        else:
            return {
                'success': False,
                'error': f"Unsupported LinkedIn action: {action}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def twitter_integration(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Twitter integration
    """
    try:
        if action == 'search_prospects':
            return search_twitter_prospects(data)
        elif action == 'send_dm':
            return send_twitter_dm(data)
        elif action == 'post_tweet':
            return post_tweet(data)
        else:
            return {
                'success': False,
                'error': f"Unsupported Twitter action: {action}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def facebook_integration(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Facebook integration
    """
    try:
        if action == 'search_prospects':
            return search_facebook_prospects(data)
        elif action == 'send_message':
            return send_facebook_message(data)
        elif action == 'post_content':
            return post_facebook_content(data)
        else:
            return {
                'success': False,
                'error': f"Unsupported Facebook action: {action}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Data Enrichment Functions

def enrich_with_clearbit(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead data with Clearbit
    """
    try:
        # This would use Clearbit API
        # For now, return placeholder enriched data
        return {
            'success': True,
            'enriched_data': {
                'company_size': '50-100 employees',
                'industry': 'Technology',
                'annual_revenue': '$5M-$10M',
                'technologies': ['Salesforce', 'HubSpot', 'Slack'],
                'social_profiles': {
                    'linkedin': 'https://linkedin.com/company/example',
                    'twitter': 'https://twitter.com/example'
                }
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def enrich_with_zoominfo(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead data with ZoomInfo
    """
    try:
        # This would use ZoomInfo API
        # For now, return placeholder enriched data
        return {
            'success': True,
            'enriched_data': {
                'contact_info': {
                    'direct_phone': '+1-555-0123',
                    'mobile_phone': '+1-555-0124',
                    'work_email': 'contact@example.com'
                },
                'company_info': {
                    'headquarters': 'San Francisco, CA',
                    'founded_year': 2015,
                    'employee_count': 75
                }
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def enrich_with_hunter(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead data with Hunter.io
    """
    try:
        # This would use Hunter.io API for email finding
        # For now, return placeholder enriched data
        return {
            'success': True,
            'enriched_data': {
                'emails': [
                    {
                        'email': 'john.doe@example.com',
                        'confidence': 95,
                        'type': 'personal'
                    },
                    {
                        'email': 'contact@example.com',
                        'confidence': 85,
                        'type': 'generic'
                    }
                ],
                'domain_info': {
                    'organization': 'Example Corp',
                    'country': 'United States',
                    'disposable': False
                }
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Helper Functions

def get_email_service_settings() -> Optional[Dict[str, Any]]:
    """
    Get email service settings
    """
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        return {
            'service_type': settings.email_service_type,
            'api_key': settings.email_api_key,
            'domain': settings.email_domain,
            'smtp_server': settings.smtp_server,
            'smtp_port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls
        }
    except Exception:
        return None


def get_salesforce_settings() -> Optional[Dict[str, Any]]:
    """
    Get Salesforce integration settings
    """
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        return {
            'client_id': settings.salesforce_client_id,
            'client_secret': settings.salesforce_client_secret,
            'username': settings.salesforce_username,
            'password': settings.salesforce_password,
            'security_token': settings.salesforce_security_token,
            'instance_url': settings.salesforce_instance_url
        }
    except Exception:
        return None


def get_hubspot_settings() -> Optional[Dict[str, Any]]:
    """
    Get HubSpot integration settings
    """
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        return {
            'api_key': settings.hubspot_api_key,
            'portal_id': settings.hubspot_portal_id
        }
    except Exception:
        return None


def get_pipedrive_settings() -> Optional[Dict[str, Any]]:
    """
    Get Pipedrive integration settings
    """
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        return {
            'api_token': settings.pipedrive_api_token,
            'company_domain': settings.pipedrive_company_domain
        }
    except Exception:
        return None


def authenticate_salesforce(settings: Dict[str, Any]) -> Optional[str]:
    """
    Authenticate with Salesforce and get access token
    """
    try:
        auth_url = 'https://login.salesforce.com/services/oauth2/token'
        
        auth_data = {
            'grant_type': 'password',
            'client_id': settings['client_id'],
            'client_secret': settings['client_secret'],
            'username': settings['username'],
            'password': settings['password'] + settings['security_token']
        }
        
        response = requests.post(auth_url, data=auth_data)
        
        if response.status_code == 200:
            return response.json().get('access_token')
        
        return None
        
    except Exception:
        return None


def convert_to_salesforce_format(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert lead data to Salesforce format
    """
    return {
        'FirstName': lead.get('first_name', ''),
        'LastName': lead.get('last_name', lead.get('lead_name', '')),
        'Company': lead.get('company_name', ''),
        'Email': lead.get('email_id', ''),
        'Phone': lead.get('phone', ''),
        'Industry': lead.get('industry', ''),
        'Website': lead.get('website', ''),
        'Street': lead.get('address_line1', ''),
        'City': lead.get('city', ''),
        'State': lead.get('state', ''),
        'PostalCode': lead.get('pincode', ''),
        'Country': lead.get('country', ''),
        'LeadSource': lead.get('source', 'Lead Intelligence')
    }


def convert_to_hubspot_format(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert lead data to HubSpot format
    """
    return {
        'firstname': lead.get('first_name', ''),
        'lastname': lead.get('last_name', lead.get('lead_name', '')),
        'company': lead.get('company_name', ''),
        'email': lead.get('email_id', ''),
        'phone': lead.get('phone', ''),
        'industry': lead.get('industry', ''),
        'website': lead.get('website', ''),
        'address': lead.get('address_line1', ''),
        'city': lead.get('city', ''),
        'state': lead.get('state', ''),
        'zip': lead.get('pincode', ''),
        'country': lead.get('country', ''),
        'hs_lead_status': 'NEW',
        'lifecyclestage': 'lead'
    }


def convert_to_pipedrive_format(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert lead data to Pipedrive format
    """
    return {
        'name': lead.get('lead_name', ''),
        'email': [{'value': lead.get('email_id', ''), 'primary': True}] if lead.get('email_id') else [],
        'phone': [{'value': lead.get('phone', ''), 'primary': True}] if lead.get('phone') else [],
        'org_name': lead.get('company_name', ''),
        'visible_to': '3'  # Visible to entire company
    }


def find_execution_by_message_id(message_id: str) -> Optional[Any]:
    """
    Find campaign execution by email message ID
    """
    try:
        # This would typically search through email logs or execution records
        # For now, return None
        return None
    except Exception:
        return None


def handle_unsubscribe(email: str):
    """
    Handle email unsubscribe
    """
    try:
        # Add email to unsubscribe list
        # Update lead status
        leads = frappe.get_all('Lead', filters={'email_id': email})
        for lead in leads:
            lead_doc = frappe.get_doc('Lead', lead.name)
            lead_doc.status = 'Do Not Contact'
            lead_doc.save()
    except Exception as e:
        frappe.log_error(f"Failed to handle unsubscribe: {str(e)}", "Integration Error")


def create_email_event_log(event_data: Dict[str, Any]):
    """
    Create email event log
    """
    try:
        # This would create a log entry for email events
        pass
    except Exception as e:
        frappe.log_error(f"Failed to create email event log: {str(e)}", "Integration Error")


def find_local_record_by_crm_id(crm_type: str, crm_id: str) -> Optional[Any]:
    """
    Find local record by CRM ID
    """
    try:
        # This would search for records with CRM IDs
        # For now, return None
        return None
    except Exception:
        return None


def log_integration_activity(activity_type: str, service: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
    """
    Log integration activity
    """
    try:
        # This would create an integration activity log
        pass
    except Exception as e:
        frappe.log_error(f"Failed to log integration activity: {str(e)}", "Integration Error")


# Social Media Helper Functions

def search_linkedin_prospects(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for prospects on LinkedIn
    """
    # Placeholder implementation
    return {
        'success': True,
        'prospects': [],
        'message': 'LinkedIn prospect search completed'
    }


def send_linkedin_connection(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send LinkedIn connection request
    """
    # Placeholder implementation
    return {
        'success': True,
        'message': 'LinkedIn connection request sent'
    }


def post_linkedin_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post content to LinkedIn
    """
    # Placeholder implementation
    return {
        'success': True,
        'post_id': 'linkedin_post_123',
        'message': 'Content posted to LinkedIn'
    }


def search_twitter_prospects(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for prospects on Twitter
    """
    # Placeholder implementation
    return {
        'success': True,
        'prospects': [],
        'message': 'Twitter prospect search completed'
    }


def send_twitter_dm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send Twitter direct message
    """
    # Placeholder implementation
    return {
        'success': True,
        'message': 'Twitter DM sent'
    }


def post_tweet(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post tweet
    """
    # Placeholder implementation
    return {
        'success': True,
        'tweet_id': 'twitter_tweet_123',
        'message': 'Tweet posted'
    }


def search_facebook_prospects(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for prospects on Facebook
    """
    # Placeholder implementation
    return {
        'success': True,
        'prospects': [],
        'message': 'Facebook prospect search completed'
    }


def send_facebook_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send Facebook message
    """
    # Placeholder implementation
    return {
        'success': True,
        'message': 'Facebook message sent'
    }


def post_facebook_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post content to Facebook
    """
    # Placeholder implementation
    return {
        'success': True,
        'post_id': 'facebook_post_123',
        'message': 'Content posted to Facebook'
    }


@frappe.whitelist()
def get_integration_status() -> Dict[str, Any]:
    """
    Get status of all integrations
    
    Returns:
        Dictionary containing integration status
    """
    try:
        settings = frappe.get_single('Lead Intelligence Settings')
        
        status = {
            'email_service': {
                'configured': bool(settings.email_api_key),
                'service_type': settings.email_service_type,
                'status': 'active' if settings.email_api_key else 'not_configured'
            },
            'crm_integrations': {
                'salesforce': {
                    'configured': bool(settings.salesforce_client_id),
                    'status': 'active' if settings.salesforce_client_id else 'not_configured'
                },
                'hubspot': {
                    'configured': bool(settings.hubspot_api_key),
                    'status': 'active' if settings.hubspot_api_key else 'not_configured'
                },
                'pipedrive': {
                    'configured': bool(settings.pipedrive_api_token),
                    'status': 'active' if settings.pipedrive_api_token else 'not_configured'
                }
            },
            'ai_services': {
                'openai': {
                    'configured': bool(settings.openai_api_key),
                    'status': 'active' if settings.openai_api_key else 'not_configured'
                }
            },
            'data_services': {
                'google_places': {
                    'configured': bool(settings.google_places_api_key),
                    'status': 'active' if settings.google_places_api_key else 'not_configured'
                }
            }
        }
        
        return {
            'success': True,
            'integrations': status
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get integration status: {str(e)}", "Integration Error")
        return {
            'success': False,
            'error': _("Failed to retrieve integration status")
        }