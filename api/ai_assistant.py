# AI Assistant API

import frappe
from frappe import _
from frappe.utils import nowdate, now, cint, flt
import json
import openai
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


@frappe.whitelist()
def chat_with_assistant(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a chat message with the AI assistant
    
    Args:
        message: User's message
        context: Optional context information
    
    Returns:
        Dictionary containing AI response
    """
    try:
        # Get AI settings
        ai_settings = frappe.get_single('Lead Intelligence Settings')
        if not ai_settings.openai_api_key:
            return {
                'success': False,
                'error': _("OpenAI API key not configured")
            }
        
        # Set up OpenAI client
        openai.api_key = ai_settings.openai_api_key
        
        # Build conversation context
        system_prompt = build_system_prompt(context)
        
        # Get conversation history
        conversation_history = get_conversation_history(frappe.session.user)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": message}
        ]
        
        # Make OpenAI API call
        response = openai.ChatCompletion.create(
            model=ai_settings.openai_model or "gpt-3.5-turbo",
            messages=messages,
            max_tokens=ai_settings.max_tokens or 1000,
            temperature=ai_settings.temperature or 0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Save conversation
        save_conversation_message(frappe.session.user, "user", message)
        save_conversation_message(frappe.session.user, "assistant", ai_response)
        
        # Update usage statistics
        update_ai_usage_stats(response.usage)
        
        # Process any actions mentioned in the response
        actions = extract_actions_from_response(ai_response)
        
        return {
            'success': True,
            'response': ai_response,
            'actions': actions,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        frappe.log_error(f"AI chat failed: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to process your message. Please try again.")
        }


@frappe.whitelist()
def generate_email_content(template_data: Dict[str, Any], lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized email content using AI
    
    Args:
        template_data: Email template information
        lead_data: Lead/prospect information
    
    Returns:
        Dictionary containing generated email content
    """
    try:
        # Get AI settings
        ai_settings = frappe.get_single('Lead Intelligence Settings')
        if not ai_settings.openai_api_key:
            return {
                'success': False,
                'error': _("OpenAI API key not configured")
            }
        
        openai.api_key = ai_settings.openai_api_key
        
        # Build personalization prompt
        prompt = build_email_personalization_prompt(template_data, lead_data)
        
        # Generate content
        response = openai.ChatCompletion.create(
            model=ai_settings.openai_model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert email copywriter specializing in B2B outreach. Generate personalized, professional emails that are engaging and likely to get responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        generated_content = response.choices[0].message.content
        
        # Parse the generated content
        email_parts = parse_generated_email(generated_content)
        
        # Update usage statistics
        update_ai_usage_stats(response.usage)
        
        return {
            'success': True,
            'subject': email_parts.get('subject', template_data.get('subject', '')),
            'body': email_parts.get('body', generated_content),
            'personalization_score': calculate_personalization_score(email_parts.get('body', ''), lead_data),
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Email generation failed: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to generate email content")
        }


@frappe.whitelist()
def analyze_lead_quality(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze lead quality using AI
    
    Args:
        lead_data: Lead information to analyze
    
    Returns:
        Dictionary containing lead quality analysis
    """
    try:
        # Get AI settings
        ai_settings = frappe.get_single('Lead Intelligence Settings')
        if not ai_settings.openai_api_key:
            return {
                'success': False,
                'error': _("OpenAI API key not configured")
            }
        
        openai.api_key = ai_settings.openai_api_key
        
        # Build analysis prompt
        prompt = build_lead_analysis_prompt(lead_data)
        
        # Analyze lead
        response = openai.ChatCompletion.create(
            model=ai_settings.openai_model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a lead qualification expert. Analyze leads and provide quality scores, insights, and recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )
        
        analysis_result = response.choices[0].message.content
        
        # Parse the analysis
        analysis = parse_lead_analysis(analysis_result)
        
        # Update usage statistics
        update_ai_usage_stats(response.usage)
        
        return {
            'success': True,
            'analysis': analysis,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Lead analysis failed: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to analyze lead quality")
        }


@frappe.whitelist()
def suggest_follow_up_actions(lead_id: str) -> Dict[str, Any]:
    """
    Suggest follow-up actions for a lead using AI
    
    Args:
        lead_id: ID of the lead
    
    Returns:
        Dictionary containing follow-up suggestions
    """
    try:
        # Get lead data
        lead = frappe.get_doc('Lead', lead_id)
        
        # Get interaction history
        interactions = get_lead_interactions(lead_id)
        
        # Get AI settings
        ai_settings = frappe.get_single('Lead Intelligence Settings')
        if not ai_settings.openai_api_key:
            return {
                'success': False,
                'error': _("OpenAI API key not configured")
            }
        
        openai.api_key = ai_settings.openai_api_key
        
        # Build suggestion prompt
        prompt = build_follow_up_prompt(lead.as_dict(), interactions)
        
        # Generate suggestions
        response = openai.ChatCompletion.create(
            model=ai_settings.openai_model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sales strategy expert. Analyze lead data and interaction history to suggest the best follow-up actions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        
        suggestions_text = response.choices[0].message.content
        
        # Parse suggestions
        suggestions = parse_follow_up_suggestions(suggestions_text)
        
        # Update usage statistics
        update_ai_usage_stats(response.usage)
        
        return {
            'success': True,
            'suggestions': suggestions,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Follow-up suggestions failed: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to generate follow-up suggestions")
        }


@frappe.whitelist()
def optimize_campaign_strategy(campaign_id: str) -> Dict[str, Any]:
    """
    Analyze campaign performance and suggest optimizations
    
    Args:
        campaign_id: ID of the campaign to optimize
    
    Returns:
        Dictionary containing optimization suggestions
    """
    try:
        # Get campaign data
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        
        # Get campaign analytics
        from lead_intelligence.api.campaign_management import calculate_campaign_analytics
        analytics = calculate_campaign_analytics(campaign_id)
        
        # Get AI settings
        ai_settings = frappe.get_single('Lead Intelligence Settings')
        if not ai_settings.openai_api_key:
            return {
                'success': False,
                'error': _("OpenAI API key not configured")
            }
        
        openai.api_key = ai_settings.openai_api_key
        
        # Build optimization prompt
        prompt = build_campaign_optimization_prompt(campaign.as_dict(), analytics)
        
        # Generate optimization suggestions
        response = openai.ChatCompletion.create(
            model=ai_settings.openai_model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a marketing optimization expert. Analyze campaign data and suggest specific improvements to increase performance."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.4
        )
        
        optimization_text = response.choices[0].message.content
        
        # Parse optimization suggestions
        optimizations = parse_optimization_suggestions(optimization_text)
        
        # Update usage statistics
        update_ai_usage_stats(response.usage)
        
        return {
            'success': True,
            'optimizations': optimizations,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign optimization failed: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to generate optimization suggestions")
        }


# Helper Functions

def build_system_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    """
    Build system prompt for AI assistant
    """
    base_prompt = """
You are an AI assistant for Lead Intelligence, a lead generation and sales automation platform. 
You help users with:

1. Creating and managing lead generation campaigns
2. Analyzing lead quality and conversion potential
3. Optimizing email outreach strategies
4. Providing insights on campaign performance
5. Suggesting follow-up actions for leads

You have access to the user's campaign data, lead information, and performance metrics.
Provide helpful, actionable advice while being concise and professional.

When suggesting actions, use specific function calls like:
- CREATE_CAMPAIGN: To create a new campaign
- ANALYZE_LEAD: To analyze a specific lead
- GENERATE_EMAIL: To create email content
- VIEW_ANALYTICS: To show performance data
"""
    
    if context:
        if context.get('current_tab'):
            base_prompt += f"\n\nThe user is currently viewing: {context['current_tab']}"
        
        if context.get('recent_activity'):
            base_prompt += f"\n\nRecent activity: {context['recent_activity']}"
    
    return base_prompt


def build_email_personalization_prompt(template_data: Dict[str, Any], lead_data: Dict[str, Any]) -> str:
    """
    Build prompt for email personalization
    """
    prompt = f"""
Personalize this email template for the following prospect:

PROSPECT INFORMATION:
- Company: {lead_data.get('company_name', 'N/A')}
- Contact: {lead_data.get('lead_name', 'N/A')}
- Industry: {lead_data.get('industry', 'N/A')}
- Location: {lead_data.get('address_line1', 'N/A')}
- Website: {lead_data.get('website', 'N/A')}
- Business Type: {lead_data.get('business_types', 'N/A')}

EMAIL TEMPLATE:
Subject: {template_data.get('subject_line', '')}
Body: {template_data.get('email_body', '')}

PERSONALIZATION INSTRUCTIONS:
{template_data.get('ai_personalization_instructions', 'Make the email more personal and relevant to the prospect.')}

Generate a personalized version that:
1. Uses specific details about the prospect's business
2. Shows genuine interest and research
3. Maintains a professional but friendly tone
4. Includes a clear call to action
5. Keeps the email concise (under 150 words)

Format the response as:
SUBJECT: [personalized subject]
BODY: [personalized email body]
"""
    
    return prompt


def build_lead_analysis_prompt(lead_data: Dict[str, Any]) -> str:
    """
    Build prompt for lead quality analysis
    """
    prompt = f"""
Analyze the quality of this lead and provide a comprehensive assessment:

LEAD INFORMATION:
- Company: {lead_data.get('company_name', 'N/A')}
- Contact: {lead_data.get('lead_name', 'N/A')}
- Industry: {lead_data.get('industry', 'N/A')}
- Location: {lead_data.get('address_line1', 'N/A')}
- Website: {lead_data.get('website', 'N/A')}
- Phone: {lead_data.get('phone', 'N/A')}
- Email: {lead_data.get('email_id', 'N/A')}
- Business Rating: {lead_data.get('custom_business_rating', 'N/A')}
- Total Reviews: {lead_data.get('custom_total_reviews', 'N/A')}
- Business Types: {lead_data.get('custom_business_types', 'N/A')}
- Source: {lead_data.get('source', 'N/A')}
- Status: {lead_data.get('status', 'N/A')}

Provide analysis in this format:
SCORE: [1-100]
QUALITY: [High/Medium/Low]
REASONS: [Key factors affecting quality]
OPPORTUNITIES: [Potential business opportunities]
RISKS: [Potential challenges or red flags]
RECOMMENDATIONS: [Specific next steps]
PRIORITY: [High/Medium/Low]
"""
    
    return prompt


def build_follow_up_prompt(lead_data: Dict[str, Any], interactions: List[Dict]) -> str:
    """
    Build prompt for follow-up suggestions
    """
    interactions_text = "\n".join([
        f"- {interaction.get('date', '')}: {interaction.get('type', '')} - {interaction.get('summary', '')}"
        for interaction in interactions
    ])
    
    prompt = f"""
Suggest the best follow-up actions for this lead based on their profile and interaction history:

LEAD PROFILE:
- Company: {lead_data.get('company_name', 'N/A')}
- Contact: {lead_data.get('lead_name', 'N/A')}
- Status: {lead_data.get('status', 'N/A')}
- Industry: {lead_data.get('industry', 'N/A')}
- Last Contact: {lead_data.get('last_contact_date', 'N/A')}

INTERACTION HISTORY:
{interactions_text or 'No previous interactions'}

Provide 3-5 specific follow-up suggestions with:
1. Action type (email, call, social media, etc.)
2. Timing (when to execute)
3. Message/approach
4. Expected outcome
5. Priority level

Format as numbered list with clear action items.
"""
    
    return prompt


def build_campaign_optimization_prompt(campaign_data: Dict[str, Any], analytics: Dict[str, Any]) -> str:
    """
    Build prompt for campaign optimization
    """
    prompt = f"""
Analyze this campaign's performance and suggest specific optimizations:

CAMPAIGN DATA:
- Name: {campaign_data.get('campaign_name', 'N/A')}
- Status: {campaign_data.get('status', 'N/A')}
- Target: {campaign_data.get('target_lead_count', 'N/A')} leads
- Created: {campaign_data.get('leads_created', 0)} leads
- Industry: {campaign_data.get('target_business_type', 'N/A')}
- Location: {campaign_data.get('target_location', 'N/A')}

PERFORMANCE METRICS:
- Emails Sent: {analytics.get('emails_sent', 0)}
- Delivery Rate: {analytics.get('delivery_rate', 0):.1f}%
- Open Rate: {analytics.get('open_rate', 0):.1f}%
- Click Rate: {analytics.get('click_rate', 0):.1f}%
- Response Rate: {analytics.get('response_rate', 0):.1f}%
- Cost per Lead: ${analytics.get('cost_per_lead', 0):.2f}

Provide optimization suggestions in these categories:
1. TARGETING: Improvements to audience selection
2. MESSAGING: Email content and subject line optimizations
3. TIMING: Best times to send emails
4. FOLLOW-UP: Sequence and cadence improvements
5. BUDGET: Cost optimization strategies

For each suggestion, include:
- Specific action to take
- Expected impact
- Implementation difficulty (Easy/Medium/Hard)
- Priority (High/Medium/Low)
"""
    
    return prompt


def parse_generated_email(content: str) -> Dict[str, str]:
    """
    Parse generated email content into subject and body
    """
    lines = content.strip().split('\n')
    subject = ''
    body = ''
    
    for i, line in enumerate(lines):
        if line.upper().startswith('SUBJECT:'):
            subject = line[8:].strip()
        elif line.upper().startswith('BODY:'):
            body = '\n'.join(lines[i+1:]).strip()
            break
    
    if not subject and not body:
        # If no clear format, treat entire content as body
        body = content
    
    return {'subject': subject, 'body': body}


def parse_lead_analysis(content: str) -> Dict[str, Any]:
    """
    Parse lead analysis response
    """
    analysis = {}
    
    patterns = {
        'score': r'SCORE:\s*(\d+)',
        'quality': r'QUALITY:\s*([^\n]+)',
        'reasons': r'REASONS:\s*([^\n]+(?:\n[^A-Z:][^\n]*)*)',
        'opportunities': r'OPPORTUNITIES:\s*([^\n]+(?:\n[^A-Z:][^\n]*)*)',
        'risks': r'RISKS:\s*([^\n]+(?:\n[^A-Z:][^\n]*)*)',
        'recommendations': r'RECOMMENDATIONS:\s*([^\n]+(?:\n[^A-Z:][^\n]*)*)',
        'priority': r'PRIORITY:\s*([^\n]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            analysis[key] = match.group(1).strip()
    
    return analysis


def parse_follow_up_suggestions(content: str) -> List[Dict[str, str]]:
    """
    Parse follow-up suggestions from AI response
    """
    suggestions = []
    
    # Split by numbered items
    items = re.split(r'\n\d+\.\s*', content)
    
    for item in items[1:]:  # Skip first empty item
        if item.strip():
            suggestions.append({
                'action': item.strip(),
                'type': 'follow_up',
                'priority': 'medium'  # Default priority
            })
    
    return suggestions


def parse_optimization_suggestions(content: str) -> Dict[str, List[Dict]]:
    """
    Parse campaign optimization suggestions
    """
    optimizations = {
        'targeting': [],
        'messaging': [],
        'timing': [],
        'follow_up': [],
        'budget': []
    }
    
    current_category = None
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Check for category headers
        for category in optimizations.keys():
            if category.upper() in line.upper() and ':' in line:
                current_category = category
                break
        
        # Add suggestions to current category
        if current_category and line.startswith('-'):
            optimizations[current_category].append({
                'suggestion': line[1:].strip(),
                'category': current_category
            })
    
    return optimizations


def calculate_personalization_score(email_body: str, lead_data: Dict[str, Any]) -> int:
    """
    Calculate how personalized an email is
    """
    score = 0
    
    # Check for company name
    if lead_data.get('company_name') and lead_data['company_name'].lower() in email_body.lower():
        score += 20
    
    # Check for contact name
    if lead_data.get('lead_name') and lead_data['lead_name'].lower() in email_body.lower():
        score += 20
    
    # Check for industry mention
    if lead_data.get('industry') and lead_data['industry'].lower() in email_body.lower():
        score += 15
    
    # Check for location mention
    if lead_data.get('address_line1'):
        location_parts = lead_data['address_line1'].split(',')
        for part in location_parts:
            if part.strip().lower() in email_body.lower():
                score += 10
                break
    
    # Check for website mention
    if lead_data.get('website') and lead_data['website'] in email_body:
        score += 10
    
    # Check for specific business details
    business_keywords = ['rating', 'reviews', 'business', 'service', 'product']
    for keyword in business_keywords:
        if keyword in email_body.lower():
            score += 5
    
    return min(score, 100)


def get_conversation_history(user: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get recent conversation history for a user
    """
    try:
        # This would typically fetch from a conversation log table
        # For now, return empty list
        return []
    except Exception:
        return []


def save_conversation_message(user: str, role: str, content: str):
    """
    Save a conversation message
    """
    try:
        # This would typically save to a conversation log table
        pass
    except Exception as e:
        frappe.log_error(f"Failed to save conversation: {str(e)}", "AI Assistant Error")


def get_lead_interactions(lead_id: str) -> List[Dict[str, Any]]:
    """
    Get interaction history for a lead
    """
    try:
        # Get communications
        communications = frappe.get_all('Communication',
            filters={
                'reference_doctype': 'Lead',
                'reference_name': lead_id
            },
            fields=['communication_type', 'subject', 'content', 'creation'],
            order_by='creation desc',
            limit=10
        )
        
        interactions = []
        for comm in communications:
            interactions.append({
                'type': comm.communication_type,
                'summary': comm.subject or comm.content[:100],
                'date': comm.creation
            })
        
        return interactions
        
    except Exception:
        return []


def update_ai_usage_stats(usage: Any):
    """
    Update AI usage statistics
    """
    try:
        # This would typically update usage tracking
        pass
    except Exception as e:
        frappe.log_error(f"Failed to update AI usage stats: {str(e)}", "AI Assistant Error")


def extract_actions_from_response(response: str) -> List[Dict[str, str]]:
    """
    Extract actionable items from AI response
    """
    actions = []
    
    # Look for action patterns
    action_patterns = {
        'CREATE_CAMPAIGN': r'CREATE_CAMPAIGN(?:\s*:\s*(.+))?',
        'ANALYZE_LEAD': r'ANALYZE_LEAD(?:\s*:\s*(.+))?',
        'GENERATE_EMAIL': r'GENERATE_EMAIL(?:\s*:\s*(.+))?',
        'VIEW_ANALYTICS': r'VIEW_ANALYTICS(?:\s*:\s*(.+))?'
    }
    
    for action_type, pattern in action_patterns.items():
        matches = re.findall(pattern, response, re.IGNORECASE)
        for match in matches:
            actions.append({
                'type': action_type.lower(),
                'description': match or action_type.replace('_', ' ').title()
            })
    
    return actions


@frappe.whitelist()
def get_ai_usage_statistics() -> Dict[str, Any]:
    """
    Get AI usage statistics
    
    Returns:
        Dictionary containing usage statistics
    """
    try:
        # This would typically fetch from usage tracking tables
        return {
            'success': True,
            'statistics': {
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'requests_today': 0,
                'average_response_time': 0.0
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get AI usage statistics: {str(e)}", "AI Assistant Error")
        return {
            'success': False,
            'error': _("Failed to retrieve AI usage statistics")
        }