# Copyright (c) 2025, AIDA AI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TargetIndustry(Document):
    def validate(self):
        """Validate target industry data"""
        self.validate_industry_name()
        
    def validate_industry_name(self):
        """Validate and format industry name"""
        if self.industry_name:
            # Clean and format industry name
            self.industry_name = self.industry_name.strip().title()
            
            # Check for minimum length
            if len(self.industry_name) < 2:
                frappe.throw("Industry name must be at least 2 characters long")
                
    def get_formatted_info(self):
        """Get formatted industry information"""
        return {
            'name': self.industry_name,
            'priority': self.priority,
            'description': self.description or '',
            'key_decision_makers': self.key_decision_makers or ''
        }
        
    def get_priority_weight(self):
        """Get numeric weight for priority"""
        priority_weights = {
            'High': 3,
            'Medium': 2,
            'Low': 1
        }
        return priority_weights.get(self.priority, 2)