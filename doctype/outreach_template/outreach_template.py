# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
import re
import json
from frappe.model.document import Document
from frappe.utils import now, get_datetime, add_days
from datetime import datetime

class OutreachTemplate(Document):
    def validate(self):
        """Validate template content and personalization variables"""
        self.validate_template_content()
        self.validate_personalization_variables()
        
    def validate_template_content(self):
        """Validate subject line and email body"""
        if not self.subject_line or len(self.subject_line.strip()) < 5:
            frappe.throw("Subject line must be at least 5 characters long")
            
        if not self.email_body or len(self.email_body.strip()) < 20:
            frappe.throw("Email body must be at least 20 characters long")
            
    def validate_personalization_variables(self):
        """Validate personalization variables in template"""
        # Extract variables from subject and body
        subject_vars = self.extract_template_variables(self.subject_line)
        body_vars = self.extract_template_variables(self.email_body)
        
        # Common allowed variables
        allowed_vars = {
            'lead_name', 'company_name', 'industry', 'location',
            'job_title', 'first_name', 'last_name', 'company_size',
            'website', 'phone', 'email', 'our_company', 'our_service',
            'value_proposition', 'contact_person'
        }
        
        # Check for invalid variables
        all_vars = subject_vars.union(body_vars)
        invalid_vars = all_vars - allowed_vars
        
        if invalid_vars:
            frappe.throw(f"Invalid personalization variables: {', '.join(invalid_vars)}")
            
    def extract_template_variables(self, text):
        """Extract template variables from text"""
        if not text:
            return set()
            
        # Find variables in format {variable_name}
        pattern = r'\{([^}]+)\}'
        variables = re.findall(pattern, text)
        return set(variables)
        
    def render_template(self, lead_data, company_profile=None):
        """Render template with lead data"""
        context = self.prepare_template_context(lead_data, company_profile)
        
        rendered_subject = self.render_text(self.subject_line, context)
        rendered_body = self.render_text(self.email_body, context)
        
        return {
            'subject': rendered_subject,
            'body': rendered_body,
            'template_name': self.template_name,
            'template_type': self.template_type
        }
        
    def prepare_template_context(self, lead_data, company_profile=None):
        """Prepare context for template rendering"""
        context = {
            'lead_name': lead_data.get('lead_name', ''),
            'company_name': lead_data.get('company_name', ''),
            'industry': lead_data.get('industry', ''),
            'location': lead_data.get('territory', ''),
            'job_title': lead_data.get('designation', ''),
            'first_name': lead_data.get('first_name', ''),
            'last_name': lead_data.get('last_name', ''),
            'company_size': lead_data.get('no_of_employees', ''),
            'website': lead_data.get('website', ''),
            'phone': lead_data.get('phone', ''),
            'email': lead_data.get('email_id', '')
        }
        
        # Add company profile data if available
        if company_profile:
            context.update({
                'our_company': company_profile.get('company_name', ''),
                'our_service': company_profile.get('services_offered', ''),
                'value_proposition': company_profile.get('value_propositions', ''),
                'contact_person': company_profile.get('contact_person', '')
            })
            
        return context
        
    def render_text(self, text, context):
        """Render text with context variables"""
        if not text:
            return ''
            
        rendered = text
        for key, value in context.items():
            placeholder = f'{{{key}}}'
            rendered = rendered.replace(placeholder, str(value or ''))
            
        return rendered
        
    def update_usage_stats(self, sent_count=0, response_count=0):
        """Update template usage statistics"""
        self.usage_count = (self.usage_count or 0) + 1
        self.total_sent = (self.total_sent or 0) + sent_count
        self.total_responses = (self.total_responses or 0) + response_count
        
        # Calculate success rate
        if self.total_sent > 0:
            self.success_rate = (self.total_responses / self.total_sent) * 100
        else:
            self.success_rate = 0
            
        self.last_used = now()
        self.save(ignore_permissions=True)
        
    def get_follow_up_sequence(self):
        """Get follow-up templates in sequence"""
        follow_ups = []
        for template in self.follow_up_templates:
            follow_ups.append({
                'day': template.follow_up_day,
                'type': template.template_type,
                'subject': template.subject_line,
                'body': template.email_body
            })
        return sorted(follow_ups, key=lambda x: x['day'])

# Whitelisted methods for API access
@frappe.whitelist()
def get_active_templates(template_type=None, industry=None):
    """Get active outreach templates"""
    filters = {'active': 1}
    
    if template_type:
        filters['template_type'] = template_type
    if industry:
        filters['target_industry'] = industry
        
    templates = frappe.get_list(
        'Outreach Template',
        filters=filters,
        fields=[
            'name', 'template_name', 'template_type', 'target_industry',
            'target_audience', 'subject_line', 'usage_count', 'success_rate',
            'last_used'
        ],
        order_by='success_rate desc, usage_count desc'
    )
    
    return templates

@frappe.whitelist()
def preview_template(template_name, sample_data=None):
    """Preview template with sample data"""
    template = frappe.get_doc('Outreach Template', template_name)
    
    # Use sample data if not provided
    if not sample_data:
        sample_data = {
            'lead_name': 'John Doe',
            'company_name': 'Sample Corp',
            'industry': 'Technology',
            'territory': 'Mumbai',
            'designation': 'CEO',
            'first_name': 'John',
            'last_name': 'Doe',
            'email_id': 'john@samplecorp.com'
        }
    else:
        sample_data = json.loads(sample_data) if isinstance(sample_data, str) else sample_data
        
    # Get default company profile
    company_profile = frappe.db.get_value(
        'Company Profile',
        {'is_default': 1, 'active': 1},
        ['company_name', 'services_offered', 'value_propositions', 'contact_person'],
        as_dict=True
    )
    
    rendered = template.render_template(sample_data, company_profile)
    return rendered

@frappe.whitelist()
def duplicate_template(template_name, new_name):
    """Duplicate an existing template"""
    original = frappe.get_doc('Outreach Template', template_name)
    
    # Create new template
    new_template = frappe.copy_doc(original)
    new_template.template_name = new_name
    new_template.usage_count = 0
    new_template.success_rate = 0
    new_template.total_sent = 0
    new_template.total_responses = 0
    new_template.last_used = None
    
    new_template.insert()
    return new_template.name

@frappe.whitelist()
def get_template_performance(template_name=None, days=30):
    """Get template performance analytics"""
    filters = {}
    if template_name:
        filters['name'] = template_name
        
    # Get templates with usage in specified period
    from_date = add_days(get_datetime(), -int(days))
    
    templates = frappe.get_list(
        'Outreach Template',
        filters=filters,
        fields=[
            'name', 'template_name', 'template_type', 'usage_count',
            'success_rate', 'total_sent', 'total_responses', 'last_used'
        ]
    )
    
    # Calculate performance metrics
    total_templates = len(templates)
    total_usage = sum(t.get('usage_count', 0) for t in templates)
    avg_success_rate = sum(t.get('success_rate', 0) for t in templates) / total_templates if total_templates > 0 else 0
    
    # Get top performing templates
    top_templates = sorted(templates, key=lambda x: x.get('success_rate', 0), reverse=True)[:5]
    
    return {
        'summary': {
            'total_templates': total_templates,
            'total_usage': total_usage,
            'avg_success_rate': avg_success_rate
        },
        'templates': templates,
        'top_performers': top_templates
    }

@frappe.whitelist()
def get_template_variables():
    """Get list of available template variables"""
    return {
        'lead_variables': [
            'lead_name', 'company_name', 'industry', 'location',
            'job_title', 'first_name', 'last_name', 'company_size',
            'website', 'phone', 'email'
        ],
        'company_variables': [
            'our_company', 'our_service', 'value_proposition', 'contact_person'
        ],
        'examples': {
            'subject': 'Quick question about {company_name}\'s {industry} operations',
            'greeting': 'Hi {first_name},',
            'company_mention': 'I noticed {company_name} is based in {location}',
            'value_prop': 'At {our_company}, we help companies like {company_name} with {our_service}'
        }
    }

@frappe.whitelist()
def validate_template_syntax(subject, body):
    """Validate template syntax and variables"""
    errors = []
    warnings = []
    
    # Check for unmatched braces
    for text, field_name in [(subject, 'subject'), (body, 'body')]:
        if text:
            open_braces = text.count('{')
            close_braces = text.count('}')
            if open_braces != close_braces:
                errors.append(f"Unmatched braces in {field_name}")
                
    # Extract and validate variables
    template_doc = frappe.new_doc('Outreach Template')
    template_doc.subject_line = subject
    template_doc.email_body = body
    
    try:
        template_doc.validate_personalization_variables()
    except frappe.ValidationError as e:
        errors.append(str(e))
        
    # Check for common issues
    if subject and len(subject) > 100:
        warnings.append("Subject line is quite long (>100 characters)")
        
    if body and body.count('{') > 10:
        warnings.append("Many personalization variables detected - ensure they're all necessary")
        
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }