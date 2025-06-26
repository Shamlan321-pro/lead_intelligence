# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.model.document import Document
from frappe.utils import validate_email_address

class CompanyProfile(Document):
    def validate(self):
        """Validate company profile data"""
        self.validate_unique_default()
        self.validate_website_url()
        self.validate_contact_email()
        
    def validate_unique_default(self):
        """Ensure only one default profile exists"""
        if self.is_default:
            existing_default = frappe.db.get_value(
                'Company Profile',
                {'is_default': 1, 'name': ['!=', self.name]},
                'name'
            )
            if existing_default:
                frappe.throw(f"Default profile already exists: {existing_default}")
                
    def validate_website_url(self):
        """Validate website URL format"""
        if self.website_url:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(self.website_url):
                frappe.throw("Please enter a valid website URL")
                
    def validate_contact_email(self):
        """Validate contact email format"""
        if self.contact_email:
            try:
                validate_email_address(self.contact_email, throw=True)
            except frappe.InvalidEmailAddressError:
                frappe.throw("Please enter a valid contact email address")
                
    def on_update(self):
        """Handle updates to default profile"""
        if self.is_default:
            # Unset other default profiles
            frappe.db.sql("""
                UPDATE `tabCompany Profile` 
                SET is_default = 0 
                WHERE name != %s AND is_default = 1
            """, (self.name,))
            
    def get_target_industries_list(self):
        """Get list of target industries"""
        industries = []
        for industry in self.target_industries:
            industries.append({
                'industry_name': industry.industry_name,
                'priority': industry.priority,
                'description': industry.description,
                'key_decision_makers': industry.key_decision_makers
            })
        return industries
        
    def get_profile_summary(self):
        """Get summarized profile for AI personalization"""
        summary = {
            'company_name': self.company_name,
            'description': self.company_description,
            'services': self.services_offered,
            'value_props': self.value_propositions,
            'website': self.website_url,
            'contact_person': self.contact_person,
            'target_industries': self.get_target_industries_list()
        }
        return summary

# Whitelisted methods for API access
@frappe.whitelist()
def get_default_profile():
    """Get the default company profile"""
    default_profile = frappe.db.get_value(
        'Company Profile',
        {'is_default': 1, 'active': 1},
        ['name', 'company_name', 'company_description', 'services_offered',
         'value_propositions', 'website_url', 'contact_person', 'contact_email']
    )
    
    if default_profile:
        profile_doc = frappe.get_doc('Company Profile', default_profile[0])
        return profile_doc.get_profile_summary()
    
    return None

@frappe.whitelist()
def get_all_profiles():
    """Get all active company profiles"""
    profiles = frappe.get_list(
        'Company Profile',
        filters={'active': 1},
        fields=[
            'name', 'company_name', 'company_description',
            'is_default', 'creation'
        ],
        order_by='is_default desc, creation desc'
    )
    
    return profiles

@frappe.whitelist()
def get_profile_details(profile_name):
    """Get detailed profile information"""
    profile = frappe.get_doc('Company Profile', profile_name)
    return profile.get_profile_summary()

@frappe.whitelist()
def set_default_profile(profile_name):
    """Set a profile as default"""
    # Unset all default profiles
    frappe.db.sql("""
        UPDATE `tabCompany Profile` 
        SET is_default = 0 
        WHERE is_default = 1
    """)
    
    # Set new default
    frappe.db.set_value('Company Profile', profile_name, 'is_default', 1)
    frappe.db.commit()
    
    return {'success': True, 'message': 'Default profile updated successfully'}

@frappe.whitelist()
def create_profile_from_template(template_data):
    """Create a new profile from template data"""
    profile = frappe.get_doc({
        'doctype': 'Company Profile',
        'company_name': template_data.get('company_name'),
        'company_description': template_data.get('description'),
        'services_offered': template_data.get('services'),
        'value_propositions': template_data.get('value_props'),
        'website_url': template_data.get('website'),
        'contact_person': template_data.get('contact_person'),
        'contact_email': template_data.get('contact_email'),
        'contact_phone': template_data.get('contact_phone'),
        'company_address': template_data.get('address')
    })
    
    # Add target industries if provided
    if template_data.get('target_industries'):
        for industry in template_data['target_industries']:
            profile.append('target_industries', {
                'industry_name': industry.get('name'),
                'priority': industry.get('priority', 'Medium'),
                'description': industry.get('description'),
                'key_decision_makers': industry.get('decision_makers')
            })
    
    profile.insert()
    return profile.name

@frappe.whitelist()
def validate_profile_data(profile_data):
    """Validate profile data before saving"""
    errors = []
    
    # Required fields
    if not profile_data.get('company_name'):
        errors.append('Company name is required')
    if not profile_data.get('company_description'):
        errors.append('Company description is required')
        
    # Email validation
    if profile_data.get('contact_email'):
        try:
            validate_email_address(profile_data['contact_email'], throw=True)
        except frappe.InvalidEmailAddressError:
            errors.append('Invalid contact email address')
            
    # URL validation
    if profile_data.get('website_url'):
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(profile_data['website_url']):
            errors.append('Invalid website URL format')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }