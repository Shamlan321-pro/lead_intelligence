# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "lead_intelligence"
app_title = "Lead Intelligence"
app_publisher = "Your Organization"
app_description = "Advanced lead generation and intelligence platform for ERPNext"
app_icon = "octicon octicon-search"
app_color = "blue"
app_email = "support@yourorganization.com"
app_license = "MIT"
app_version = app_version

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/lead_intelligence/css/lead_intelligence.css"
app_include_js = "/assets/lead_intelligence/js/lead_intelligence.js"

# include js, css files in header of web template
# web_include_css = "/assets/lead_intelligence/css/lead_intelligence.css"
# web_include_js = "/assets/lead_intelligence/js/lead_intelligence.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lead_intelligence/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Lead": "public/js/lead.js",
    "Lead Campaign": "public/js/lead_campaign.js",
    "Company Profile": "public/js/company_profile.js",
    "Outreach Template": "public/js/outreach_template.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "lead_intelligence.utils.jinja_methods",
#	"filters": "lead_intelligence.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lead_intelligence.install.before_install"
# after_install = "lead_intelligence.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lead_intelligence.uninstall.before_uninstall"
# after_uninstall = "lead_intelligence.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lead_intelligence.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron": {
        # Run campaign executions every 5 minutes
        "*/5 * * * *": [
            "lead_intelligence.api.campaigns.process_scheduled_campaigns"
        ],
        # Update analytics daily at 2 AM
        "0 2 * * *": [
            "lead_intelligence.api.analytics.update_daily_analytics"
        ],
        # Clean up old execution logs weekly
        "0 3 * * 0": [
            "lead_intelligence.api.maintenance.cleanup_old_logs"
        ]
    }
}

# Testing
# -------

# before_tests = "lead_intelligence.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "lead_intelligence.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "lead_intelligence.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lead_intelligence.utils.before_request"]
# after_request = ["lead_intelligence.utils.after_request"]

# Job Events
# ----------
# before_job = ["lead_intelligence.utils.before_job"]
# after_job = ["lead_intelligence.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"lead_intelligence.auth.validate"
# ]

# Website Route Rules
# -------------------

website_route_rules = [
    {"from_route": "/lead-intelligence", "to_route": "Lead Intelligence Dashboard"},
    {"from_route": "/campaign-dashboard", "to_route": "Campaign Dashboard"},
    {"from_route": "/lead-analytics", "to_route": "Lead Analytics"}
]

# Workspace
# ---------

workspaces = [
    {
        "name": "Lead Intelligence",
        "category": "Modules",
        "label": "Lead Intelligence",
        "icon": "fa fa-bullhorn",
        "color": "blue",
        "shortcuts": [
            {
                "label": "Lead Campaign",
                "type": "DocType",
                "name": "Lead Campaign"
            },
            {
                "label": "Company Profile",
                "type": "DocType",
                "name": "Company Profile"
            },
            {
                "label": "Outreach Template",
                "type": "DocType",
                "name": "Outreach Template"
            },
            {
                "label": "Campaign Execution",
                "type": "DocType",
                "name": "Campaign Execution"
            },
            {
                "label": "Lead Intelligence Dashboard",
                "type": "Page",
                "name": "lead-intelligence"
            }
        ]
    }
]

# Fixtures
# --------

fixtures = [
    "Custom Field",
    "Property Setter",
    "Workspace"
]