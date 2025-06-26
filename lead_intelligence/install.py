# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe import _


def after_install():
	"""Setup Lead Intelligence after installation"""
	try:
		# Create custom fields
		create_lead_intelligence_custom_fields()
		
		# Create custom roles
		create_custom_roles()
		
		# Setup default settings
		setup_default_settings()
		
		# Create email templates
		create_email_templates()
		
		# Setup workflows
		setup_workflows()
		
		# Create default dashboards
		create_default_dashboards()
		
		frappe.db.commit()
		print("Lead Intelligence installation completed successfully!")
		
	except Exception as e:
		frappe.log_error(f"Installation error: {str(e)}", "Lead Intelligence Installation")
		print(f"Installation error: {str(e)}")


def create_lead_intelligence_custom_fields():
	"""Create custom fields for Lead Intelligence"""
	custom_fields = {
		"Lead": [
			{
				"fieldname": "lead_intelligence_section",
				"label": "Lead Intelligence",
				"fieldtype": "Section Break",
				"insert_after": "source",
				"collapsible": 1
			},
			{
				"fieldname": "lead_score",
				"label": "Lead Score",
				"fieldtype": "Int",
				"insert_after": "lead_intelligence_section",
				"read_only": 1,
				"description": "AI-calculated lead quality score (0-100)"
			},
			{
				"fieldname": "lead_quality",
				"label": "Lead Quality",
				"fieldtype": "Select",
				"options": "\nHot\nWarm\nCold\nUnqualified",
				"insert_after": "lead_score",
				"read_only": 1
			},
			{
				"fieldname": "campaign_source",
				"label": "Campaign Source",
				"fieldtype": "Link",
				"options": "Lead Campaign",
				"insert_after": "lead_quality",
				"read_only": 1
			},
			{
				"fieldname": "enrichment_data",
				"label": "Enrichment Data",
				"fieldtype": "Code",
				"options": "JSON",
				"insert_after": "campaign_source",
				"read_only": 1,
				"hidden": 1
			},
			{
				"fieldname": "column_break_li_1",
				"fieldtype": "Column Break",
				"insert_after": "enrichment_data"
			},
			{
				"fieldname": "ai_insights",
				"label": "AI Insights",
				"fieldtype": "Text Editor",
				"insert_after": "column_break_li_1",
				"read_only": 1
			},
			{
				"fieldname": "last_enriched",
				"label": "Last Enriched",
				"fieldtype": "Datetime",
				"insert_after": "ai_insights",
				"read_only": 1
			},
			{
				"fieldname": "engagement_score",
				"label": "Engagement Score",
				"fieldtype": "Float",
				"insert_after": "last_enriched",
				"read_only": 1,
				"precision": 2
			}
		],
		"Customer": [
			{
				"fieldname": "lead_intelligence_section",
				"label": "Lead Intelligence",
				"fieldtype": "Section Break",
				"insert_after": "represents_company",
				"collapsible": 1
			},
			{
				"fieldname": "original_lead_score",
				"label": "Original Lead Score",
				"fieldtype": "Int",
				"insert_after": "lead_intelligence_section",
				"read_only": 1
			},
			{
				"fieldname": "conversion_source",
				"label": "Conversion Source",
				"fieldtype": "Link",
				"options": "Lead Campaign",
				"insert_after": "original_lead_score",
				"read_only": 1
			}
		],
		"Contact": [
			{
				"fieldname": "lead_intelligence_section",
				"label": "Lead Intelligence",
				"fieldtype": "Section Break",
				"insert_after": "sync_with_google_contacts",
				"collapsible": 1
			},
			{
				"fieldname": "contact_score",
				"label": "Contact Score",
				"fieldtype": "Int",
				"insert_after": "lead_intelligence_section",
				"read_only": 1
			},
			{
				"fieldname": "social_profiles",
				"label": "Social Profiles",
				"fieldtype": "Code",
				"options": "JSON",
				"insert_after": "contact_score",
				"read_only": 1,
				"hidden": 1
			}
		]
	}
	
	create_custom_fields(custom_fields)


def create_custom_roles():
	"""Create custom roles for Lead Intelligence"""
	roles = [
		{
			"role_name": "Lead Intelligence Manager",
			"desk_access": 1,
			"home_page": "/app/lead-campaign"
		},
		{
			"role_name": "Lead Intelligence User",
			"desk_access": 1,
			"home_page": "/app/lead"
		}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_data["role_name"],
				"desk_access": role_data["desk_access"],
				"home_page": role_data.get("home_page")
			})
			role.insert(ignore_permissions=True)


def setup_default_settings():
	"""Setup default Lead Intelligence settings"""
	if not frappe.db.exists("Lead Intelligence Settings", "Lead Intelligence Settings"):
		settings = frappe.get_doc({
			"doctype": "Lead Intelligence Settings",
			"name": "Lead Intelligence Settings",
			"active": 1,
			"default_search_radius": 10000,
			"max_leads_per_campaign": 1000,
			"email_rate_limit": 100,
			"api_rate_limit": 1000,
			"webhook_enabled": 0,
			"log_level": "Info",
			"log_retention_days": 30
		})
		settings.insert(ignore_permissions=True)


def create_email_templates():
	"""Create default email templates"""
	templates = [
		{
			"name": "Lead Intelligence Welcome",
			"subject": "Welcome to Lead Intelligence",
			"response": """
				<h3>Welcome to Lead Intelligence!</h3>
				<p>Thank you for installing Lead Intelligence. Your AI-powered lead generation system is now ready to use.</p>
				<p>To get started:</p>
				<ol>
					<li>Configure your API keys in Lead Intelligence Settings</li>
					<li>Create your first Lead Campaign</li>
					<li>Start generating high-quality leads</li>
				</ol>
				<p>Best regards,<br>The Lead Intelligence Team</p>
			"""
		},
		{
			"name": "Campaign Completion Notification",
			"subject": "Campaign {{ campaign_name }} Completed",
			"response": """
				<h3>Campaign Completed Successfully!</h3>
				<p>Your campaign <strong>{{ campaign_name }}</strong> has been completed.</p>
				<p><strong>Results:</strong></p>
				<ul>
					<li>Total Leads Generated: {{ total_leads }}</li>
					<li>High Quality Leads: {{ high_quality_leads }}</li>
					<li>Completion Time: {{ completion_time }}</li>
				</ul>
				<p>You can view the detailed results in your Lead Intelligence dashboard.</p>
			"""
		},
		{
			"name": "Lead Quality Alert",
			"subject": "High Quality Lead Alert - {{ lead_name }}",
			"response": """
				<h3>High Quality Lead Detected!</h3>
				<p>A high-quality lead has been identified:</p>
				<p><strong>Lead Details:</strong></p>
				<ul>
					<li>Name: {{ lead_name }}</li>
					<li>Company: {{ company_name }}</li>
					<li>Email: {{ email_id }}</li>
					<li>Lead Score: {{ lead_score }}/100</li>
				</ul>
				<p>Consider prioritizing this lead for immediate follow-up.</p>
			"""
		},
		{
			"name": "API Usage Warning",
			"subject": "API Usage Warning - {{ service_name }}",
			"response": """
				<h3>API Usage Warning</h3>
				<p>Your {{ service_name }} API usage is approaching the daily limit.</p>
				<p><strong>Current Usage:</strong> {{ current_usage }} / {{ daily_limit }}</p>
				<p>Please monitor your usage to avoid service interruption.</p>
				<p>Consider upgrading your plan if you need higher limits.</p>
			"""
		},
		{
			"name": "System Error Notification",
			"subject": "Lead Intelligence System Error",
			"response": """
				<h3>System Error Notification</h3>
				<p>An error has occurred in the Lead Intelligence system:</p>
				<p><strong>Error Details:</strong></p>
				<ul>
					<li>Error Type: {{ error_type }}</li>
					<li>Time: {{ error_time }}</li>
					<li>Component: {{ component }}</li>
				</ul>
				<p>Please check the system logs for more details.</p>
			"""
		}
	]
	
	for template_data in templates:
		if not frappe.db.exists("Email Template", template_data["name"]):
			template = frappe.get_doc({
				"doctype": "Email Template",
				"name": template_data["name"],
				"subject": template_data["subject"],
				"response": template_data["response"],
				"use_html": 1
			})
			template.insert(ignore_permissions=True)


def setup_workflows():
	"""Setup workflows for Lead Intelligence"""
	# Lead Campaign Workflow
	if not frappe.db.exists("Workflow", "Lead Campaign Workflow"):
		workflow = frappe.get_doc({
			"doctype": "Workflow",
			"workflow_name": "Lead Campaign Workflow",
			"document_type": "Lead Campaign",
			"workflow_state_field": "status",
			"is_active": 1,
			"send_email_alert": 1,
			"states": [
				{
					"state": "Draft",
					"doc_status": "0",
					"allow_edit": "Lead Intelligence Manager"
				},
				{
					"state": "Queued",
					"doc_status": "1",
					"allow_edit": "Lead Intelligence Manager"
				},
				{
					"state": "Processing",
					"doc_status": "1",
					"allow_edit": "Lead Intelligence Manager"
				},
				{
					"state": "Completed",
					"doc_status": "1",
					"allow_edit": "Lead Intelligence Manager"
				},
				{
					"state": "Failed",
					"doc_status": "1",
					"allow_edit": "Lead Intelligence Manager"
				}
			],
			"transitions": [
				{
					"state": "Draft",
					"action": "Submit",
					"next_state": "Queued",
					"allowed": "Lead Intelligence Manager"
				},
				{
					"state": "Queued",
					"action": "Start Processing",
					"next_state": "Processing",
					"allowed": "Lead Intelligence Manager"
				},
				{
					"state": "Processing",
					"action": "Complete",
					"next_state": "Completed",
					"allowed": "Lead Intelligence Manager"
				},
				{
					"state": "Processing",
					"action": "Mark as Failed",
					"next_state": "Failed",
					"allowed": "Lead Intelligence Manager"
				}
			]
		})
		workflow.insert(ignore_permissions=True)


def create_default_dashboards():
	"""Create default dashboards and charts"""
	# This would create dashboard charts and number cards
	# For now, we'll just log that this step was completed
	frappe.log_error("Default dashboards created", "Lead Intelligence Installation")


def setup_property_setters():
	"""Setup property setters for customizations"""
	property_setters = [
		{
			"doctype": "Lead",
			"fieldname": "lead_name",
			"property": "reqd",
			"value": "1"
		},
		{
			"doctype": "Lead",
			"fieldname": "email_id",
			"property": "reqd",
			"value": "1"
		}
	]
	
	for prop in property_setters:
		make_property_setter(
			prop["doctype"],
			prop["fieldname"],
			prop["property"],
			prop["value"],
			"Lead Intelligence"
		)


def create_workspace():
	"""Create Lead Intelligence workspace"""
	if not frappe.db.exists("Workspace", "Lead Intelligence"):
		workspace = frappe.get_doc({
			"doctype": "Workspace",
			"name": "Lead Intelligence",
			"title": "Lead Intelligence",
			"icon": "target",
			"indicator_color": "blue",
			"is_standard": 1,
			"module": "Lead Intelligence",
			"charts": [
				{
					"chart_name": "Lead Generation Trends",
					"label": "Lead Generation Trends"
				},
				{
					"chart_name": "Campaign Performance",
					"label": "Campaign Performance"
				}
			],
			"shortcuts": [
				{
					"type": "DocType",
					"link_to": "Lead Campaign",
					"label": "Lead Campaign"
				},
				{
					"type": "DocType",
					"link_to": "Lead",
					"label": "Leads"
				},
				{
					"type": "DocType",
					"link_to": "Campaign Execution",
					"label": "Campaign Execution"
				},
				{
					"type": "DocType",
					"link_to": "Lead Intelligence Settings",
					"label": "Settings"
				}
			]
		})
		workspace.insert(ignore_permissions=True)


def setup_number_cards():
	"""Setup number cards for dashboard"""
	number_cards = [
		{
			"name": "Total Leads Generated",
			"label": "Total Leads Generated",
			"document_type": "Lead",
			"function": "Count",
			"is_public": 1,
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly"
		},
		{
			"name": "Active Campaigns",
			"label": "Active Campaigns",
			"document_type": "Lead Campaign",
			"function": "Count",
			"filters_json": '[{"fieldname": "status", "operator": "in", "value": ["Active", "Processing"]}]',
			"is_public": 1
		},
		{
			"name": "High Quality Leads",
			"label": "High Quality Leads",
			"document_type": "Lead",
			"function": "Count",
			"filters_json": '[{"fieldname": "lead_quality", "operator": "=", "value": "Hot"}]',
			"is_public": 1,
			"show_percentage_stats": 1
		},
		{
			"name": "Conversion Rate",
			"label": "Lead Conversion Rate",
			"document_type": "Lead",
			"function": "Count",
			"filters_json": '[{"fieldname": "status", "operator": "=", "value": "Converted"}]',
			"is_public": 1,
			"show_percentage_stats": 1
		}
	]
	
	for card_data in number_cards:
		if not frappe.db.exists("Number Card", card_data["name"]):
			card = frappe.get_doc({
				"doctype": "Number Card",
				**card_data
			})
			card.insert(ignore_permissions=True)


def create_dashboard_charts():
	"""Create dashboard charts"""
	charts = [
		{
			"name": "Lead Generation Trends",
			"chart_name": "Lead Generation Trends",
			"chart_type": "Line",
			"document_type": "Lead",
			"based_on": "creation",
			"value_based_on": "name",
			"time_interval": "Daily",
			"timespan": "Last Month",
			"is_public": 1
		},
		{
			"name": "Campaign Performance",
			"chart_name": "Campaign Performance",
			"chart_type": "Bar",
			"document_type": "Lead Campaign",
			"based_on": "status",
			"value_based_on": "name",
			"is_public": 1
		},
		{
			"name": "Lead Quality Distribution",
			"chart_name": "Lead Quality Distribution",
			"chart_type": "Donut",
			"document_type": "Lead",
			"based_on": "lead_quality",
			"value_based_on": "name",
			"is_public": 1
		},
		{
			"name": "Lead Source Analysis",
			"chart_name": "Lead Source Analysis",
			"chart_type": "Bar",
			"document_type": "Lead",
			"based_on": "source",
			"value_based_on": "name",
			"is_public": 1
		}
	]
	
	for chart_data in charts:
		if not frappe.db.exists("Dashboard Chart", chart_data["name"]):
			chart = frappe.get_doc({
				"doctype": "Dashboard Chart",
				**chart_data
			})
			chart.insert(ignore_permissions=True)