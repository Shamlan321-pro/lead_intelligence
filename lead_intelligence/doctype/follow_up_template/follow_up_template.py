# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FollowUpTemplate(Document):
    def validate(self):
        """Validate follow-up template data"""
        self.validate_follow_up_day()
        self.validate_content()
        
    def validate_follow_up_day(self):
        """Validate follow-up day is positive"""
        if self.follow_up_day < 1:
            frappe.throw("Follow-up day must be at least 1")
            
    def validate_content(self):
        """Validate subject and body content"""
        if not self.subject_line or len(self.subject_line.strip()) < 3:
            frappe.throw("Subject line must be at least 3 characters long")
            
        if not self.email_body or len(self.email_body.strip()) < 10:
            frappe.throw("Email body must be at least 10 characters long")
            
    def get_template_data(self):
        """Get formatted template data"""
        return {
            'day': self.follow_up_day,
            'type': self.template_type,
            'subject': self.subject_line,
            'body': self.email_body
        }