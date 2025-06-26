// Lead Intelligence JavaScript Module

// Main Lead Intelligence namespace
window.LeadIntelligence = {
    // Configuration
    config: {
        apiEndpoint: '/api/method/lead_intelligence',
        refreshInterval: 30000, // 30 seconds
        maxRetries: 3,
        timeout: 10000 // 10 seconds
    },

    // State management
    state: {
        campaigns: {},
        leads: {},
        settings: {},
        stats: {},
        isLoading: false
    },

    // Initialize the module
    init: function() {
        this.bindEvents();
        this.loadSettings();
        this.startPeriodicUpdates();
        console.log('Lead Intelligence module initialized');
    },

    // Event binding
    bindEvents: function() {
        // Campaign management events
        $(document).on('click', '.btn-create-campaign', this.createCampaign.bind(this));
        $(document).on('click', '.btn-start-campaign', this.startCampaign.bind(this));
        $(document).on('click', '.btn-stop-campaign', this.stopCampaign.bind(this));
        $(document).on('click', '.btn-view-campaign', this.viewCampaign.bind(this));
        
        // Lead management events
        $(document).on('click', '.btn-enrich-lead', this.enrichLead.bind(this));
        $(document).on('click', '.btn-score-lead', this.scoreLead.bind(this));
        $(document).on('click', '.btn-export-leads', this.exportLeads.bind(this));
        
        // Settings events
        $(document).on('click', '.btn-save-settings', this.saveSettings.bind(this));
        $(document).on('click', '.btn-test-api', this.testApiConnection.bind(this));
        
        // Real-time updates
        $(document).on('click', '.btn-refresh-stats', this.refreshStats.bind(this));
        
        // Form validation
        $(document).on('submit', '.lead-intelligence-form', this.validateForm.bind(this));
    },

    // Campaign Management
    createCampaign: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        
        frappe.new_doc('Lead Intelligence Campaign', {
            onload: function(frm) {
                frm.set_value('status', 'Draft');
                frm.set_value('created_by', frappe.session.user);
            }
        });
    },

    startCampaign: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const campaignId = button.data('campaign-id');
        
        if (!campaignId) {
            frappe.msgprint(__('Campaign ID not found'));
            return;
        }

        frappe.confirm(
            __('Are you sure you want to start this campaign?'),
            () => {
                this.showLoading(button);
                
                frappe.call({
                    method: 'lead_intelligence.api.start_campaign',
                    args: { campaign_id: campaignId },
                    callback: (r) => {
                        this.hideLoading(button);
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Campaign started successfully'),
                                indicator: 'green'
                            });
                            this.refreshCampaignStatus(campaignId);
                        } else {
                            frappe.msgprint(__('Failed to start campaign: {0}', [r.message?.error || 'Unknown error']));
                        }
                    },
                    error: (r) => {
                        this.hideLoading(button);
                        frappe.msgprint(__('Error starting campaign'));
                    }
                });
            }
        );
    },

    stopCampaign: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const campaignId = button.data('campaign-id');
        
        frappe.confirm(
            __('Are you sure you want to stop this campaign?'),
            () => {
                this.showLoading(button);
                
                frappe.call({
                    method: 'lead_intelligence.api.stop_campaign',
                    args: { campaign_id: campaignId },
                    callback: (r) => {
                        this.hideLoading(button);
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Campaign stopped successfully'),
                                indicator: 'orange'
                            });
                            this.refreshCampaignStatus(campaignId);
                        }
                    }
                });
            }
        );
    },

    viewCampaign: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const campaignId = button.data('campaign-id');
        
        frappe.set_route('Form', 'Lead Intelligence Campaign', campaignId);
    },

    // Lead Management
    enrichLead: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const leadId = button.data('lead-id');
        
        this.showLoading(button);
        
        frappe.call({
            method: 'lead_intelligence.api.enrich_lead',
            args: { lead_id: leadId },
            callback: (r) => {
                this.hideLoading(button);
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Lead enriched successfully'),
                        indicator: 'green'
                    });
                    this.refreshLeadData(leadId);
                } else {
                    frappe.msgprint(__('Failed to enrich lead: {0}', [r.message?.error || 'Unknown error']));
                }
            }
        });
    },

    scoreLead: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const leadId = button.data('lead-id');
        
        this.showLoading(button);
        
        frappe.call({
            method: 'lead_intelligence.api.calculate_lead_score',
            args: { lead_id: leadId },
            callback: (r) => {
                this.hideLoading(button);
                if (r.message && r.message.success) {
                    const score = r.message.score;
                    const quality = r.message.quality;
                    
                    frappe.show_alert({
                        message: __('Lead Score: {0} ({1})', [score, quality]),
                        indicator: this.getQualityIndicator(quality)
                    });
                    
                    this.updateLeadScoreDisplay(leadId, score, quality);
                }
            }
        });
    },

    exportLeads: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const filters = this.getLeadFilters();
        
        frappe.call({
            method: 'lead_intelligence.api.export_leads',
            args: { filters: filters },
            callback: (r) => {
                if (r.message && r.message.file_url) {
                    window.open(r.message.file_url, '_blank');
                    frappe.show_alert({
                        message: __('Export completed successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    // Settings Management
    saveSettings: function(e) {
        e.preventDefault();
        const form = $(e.currentTarget).closest('form');
        const formData = this.serializeForm(form);
        
        frappe.call({
            method: 'lead_intelligence.api.save_settings',
            args: { settings: formData },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Settings saved successfully'),
                        indicator: 'green'
                    });
                    this.state.settings = formData;
                }
            }
        });
    },

    testApiConnection: function(e) {
        e.preventDefault();
        const button = $(e.currentTarget);
        const apiType = button.data('api-type');
        
        this.showLoading(button);
        
        frappe.call({
            method: 'lead_intelligence.api.test_api_connection',
            args: { api_type: apiType },
            callback: (r) => {
                this.hideLoading(button);
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('API connection successful'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint(__('API connection failed: {0}', [r.message?.error || 'Unknown error']));
                }
            }
        });
    },

    // Statistics and Analytics
    refreshStats: function(e) {
        if (e) e.preventDefault();
        
        frappe.call({
            method: 'lead_intelligence.api.get_dashboard_stats',
            callback: (r) => {
                if (r.message) {
                    this.updateStatsDisplay(r.message);
                    this.state.stats = r.message;
                }
            }
        });
    },

    updateStatsDisplay: function(stats) {
        // Update campaign stats
        $('.stat-campaigns-total').text(stats.campaigns?.total || 0);
        $('.stat-campaigns-active').text(stats.campaigns?.active || 0);
        $('.stat-campaigns-completed').text(stats.campaigns?.completed || 0);
        
        // Update lead stats
        $('.stat-leads-total').text(stats.leads?.total || 0);
        $('.stat-leads-hot').text(stats.leads?.hot || 0);
        $('.stat-leads-warm').text(stats.leads?.warm || 0);
        $('.stat-leads-cold').text(stats.leads?.cold || 0);
        
        // Update API usage
        $('.stat-api-calls').text(stats.api_usage?.total_calls || 0);
        $('.stat-api-cost').text('$' + (stats.api_usage?.total_cost || 0).toFixed(2));
        
        // Update performance metrics
        $('.stat-success-rate').text((stats.performance?.success_rate || 0).toFixed(1) + '%');
        $('.stat-avg-response-time').text((stats.performance?.avg_response_time || 0).toFixed(0) + 'ms');
    },

    // Real-time Updates
    startPeriodicUpdates: function() {
        setInterval(() => {
            if (!this.state.isLoading) {
                this.refreshStats();
                this.updateCampaignStatuses();
            }
        }, this.config.refreshInterval);
    },

    updateCampaignStatuses: function() {
        $('.campaign-status').each((index, element) => {
            const campaignId = $(element).data('campaign-id');
            if (campaignId) {
                this.refreshCampaignStatus(campaignId);
            }
        });
    },

    refreshCampaignStatus: function(campaignId) {
        frappe.call({
            method: 'lead_intelligence.api.get_campaign_status',
            args: { campaign_id: campaignId },
            callback: (r) => {
                if (r.message) {
                    this.updateCampaignStatusDisplay(campaignId, r.message);
                }
            }
        });
    },

    updateCampaignStatusDisplay: function(campaignId, statusData) {
        const statusElement = $(`.campaign-status[data-campaign-id="${campaignId}"]`);
        const progressElement = $(`.campaign-progress[data-campaign-id="${campaignId}"]`);
        
        if (statusElement.length) {
            statusElement.removeClass('status-draft status-processing status-completed status-failed')
                        .addClass(`status-${statusData.status.toLowerCase()}`);
            statusElement.text(statusData.status);
        }
        
        if (progressElement.length && statusData.progress !== undefined) {
            const progressBar = progressElement.find('.campaign-progress-fill');
            const progressText = progressElement.find('.campaign-progress-text');
            
            progressBar.css('width', statusData.progress + '%');
            progressText.text(`${statusData.progress}% Complete`);
        }
    },

    // Utility Functions
    showLoading: function(element) {
        const originalText = element.text();
        element.data('original-text', originalText)
               .prop('disabled', true)
               .html('<span class="loading-spinner"></span> Loading...');
        this.state.isLoading = true;
    },

    hideLoading: function(element) {
        const originalText = element.data('original-text');
        element.prop('disabled', false)
               .text(originalText);
        this.state.isLoading = false;
    },

    serializeForm: function(form) {
        const formData = {};
        form.find('input, select, textarea').each(function() {
            const field = $(this);
            const name = field.attr('name');
            const value = field.val();
            
            if (name && value !== undefined) {
                formData[name] = value;
            }
        });
        return formData;
    },

    validateForm: function(e) {
        const form = $(e.currentTarget);
        let isValid = true;
        
        // Clear previous errors
        form.find('.error-message').remove();
        form.find('.has-error').removeClass('has-error');
        
        // Validate required fields
        form.find('[required]').each(function() {
            const field = $(this);
            if (!field.val().trim()) {
                field.closest('.form-group').addClass('has-error');
                field.after('<div class="error-message text-danger">This field is required</div>');
                isValid = false;
            }
        });
        
        // Validate email fields
        form.find('input[type="email"]').each(function() {
            const field = $(this);
            const email = field.val().trim();
            if (email && !LeadIntelligence.utils.isValidEmail(email)) {
                field.closest('.form-group').addClass('has-error');
                field.after('<div class="error-message text-danger">Please enter a valid email address</div>');
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            frappe.msgprint(__('Please fix the errors in the form'));
        }
        
        return isValid;
    },

    getQualityIndicator: function(quality) {
        const indicators = {
            'Hot': 'red',
            'Warm': 'orange',
            'Cold': 'blue',
            'Unqualified': 'gray'
        };
        return indicators[quality] || 'gray';
    },

    getLeadFilters: function() {
        // Get current filters from the page
        const filters = {};
        
        $('.lead-filter').each(function() {
            const filter = $(this);
            const name = filter.attr('name');
            const value = filter.val();
            
            if (name && value) {
                filters[name] = value;
            }
        });
        
        return filters;
    },

    refreshLeadData: function(leadId) {
        // Refresh lead data in the current view
        if (cur_frm && cur_frm.doctype === 'Lead' && cur_frm.doc.name === leadId) {
            cur_frm.reload_doc();
        } else {
            // Update lead data in list view or other contexts
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Lead',
                    name: leadId
                },
                callback: (r) => {
                    if (r.message) {
                        this.updateLeadDisplay(leadId, r.message);
                    }
                }
            });
        }
    },

    updateLeadDisplay: function(leadId, leadData) {
        // Update lead score display
        if (leadData.lead_score !== undefined) {
            this.updateLeadScoreDisplay(leadId, leadData.lead_score, leadData.lead_quality);
        }
        
        // Update other lead fields as needed
        $(`.lead-row[data-lead-id="${leadId}"]`).each(function() {
            const row = $(this);
            row.find('.lead-company').text(leadData.company_name || '');
            row.find('.lead-email').text(leadData.email_id || '');
            row.find('.lead-phone').text(leadData.phone || '');
        });
    },

    updateLeadScoreDisplay: function(leadId, score, quality) {
        $(`.lead-score[data-lead-id="${leadId}"]`).each(function() {
            const scoreElement = $(this);
            scoreElement.find('.lead-score-value').text(score);
            scoreElement.find('.lead-score-fill').css('width', score + '%');
        });
        
        $(`.lead-quality[data-lead-id="${leadId}"]`).each(function() {
            const qualityElement = $(this);
            qualityElement.removeClass('lead-quality-hot lead-quality-warm lead-quality-cold lead-quality-unqualified')
                          .addClass(`lead-quality-${quality.toLowerCase()}`)
                          .text(quality);
        });
    },

    loadSettings: function() {
        frappe.call({
            method: 'lead_intelligence.api.get_settings',
            callback: (r) => {
                if (r.message) {
                    this.state.settings = r.message;
                    this.applySettings(r.message);
                }
            }
        });
    },

    applySettings: function(settings) {
        // Apply settings to the current page
        if (settings.refresh_interval) {
            this.config.refreshInterval = settings.refresh_interval * 1000;
        }
        
        if (settings.max_retries) {
            this.config.maxRetries = settings.max_retries;
        }
    }
};

// Utility functions
LeadIntelligence.utils = {
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    isValidPhone: function(phone) {
        const phoneRegex = /^[\+]?[1-9][\d\s\-\(\)]{7,}$/;
        return phoneRegex.test(phone);
    },
    
    formatCurrency: function(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    formatDate: function(date) {
        return new Date(date).toLocaleDateString();
    },
    
    formatDateTime: function(datetime) {
        return new Date(datetime).toLocaleString();
    },
    
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Initialize when document is ready
$(document).ready(function() {
    if (typeof frappe !== 'undefined') {
        LeadIntelligence.init();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LeadIntelligence;
}

// Global variables
let currentTab = 'ai-assistant';
let chatMessages = [];
let campaigns = [];
let leads = [];
let templates = [];
let isLoading = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupTabNavigation();
    setupChatInterface();
    setupModals();
    setupSearchAndFilters();
    loadInitialData();
    setupEventListeners();
    
    // Show welcome message
    addChatMessage('assistant', 'Welcome to Lead Intelligence! I\'m your AI assistant. How can I help you today?');
}

// Tab Navigation
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update active tab pane
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    currentTab = tabName;
    
    // Load tab-specific data
    switch(tabName) {
        case 'campaigns':
            loadCampaigns();
            break;
        case 'leads':
            loadLeads();
            break;
        case 'templates':
            loadTemplates();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Chat Interface
function setupChatInterface() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const quickActionButtons = document.querySelectorAll('.quick-action-btn');
    
    // Send message on Enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    
    // Send message on button click
    sendButton.addEventListener('click', sendChatMessage);
    
    // Quick action buttons
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleQuickAction(action);
        });
    });
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    // Add user message
    addChatMessage('user', message);
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Process message with AI
    processAIMessage(message);
}

function addChatMessage(sender, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessageContent(content);
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Store message
    chatMessages.push({ sender, content, timestamp: new Date() });
}

function formatMessageContent(content) {
    // Convert markdown-like formatting to HTML
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    content = content.replace(/\n/g, '<br>');
    
    // Convert lists
    content = content.replace(/^- (.+)$/gm, '<li>$1</li>');
    content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return content;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingElement = document.createElement('div');
    typingElement.className = 'message assistant typing-indicator';
    typingElement.id = 'typing-indicator';
    
    typingElement.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function processAIMessage(message) {
    isLoading = true;
    
    // Simulate AI processing delay
    setTimeout(() => {
        hideTypingIndicator();
        
        // Generate AI response based on message content
        const response = generateAIResponse(message);
        addChatMessage('assistant', response);
        
        isLoading = false;
    }, 1500 + Math.random() * 1000);
}

function generateAIResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    // Campaign-related responses
    if (lowerMessage.includes('campaign') || lowerMessage.includes('create campaign')) {
        return "I can help you create a new lead generation campaign! Here's what I need:\n\n- **Target audience criteria** (industry, location, company size)\n- **Campaign objectives** (lead count, timeline)\n- **Outreach template** or messaging preferences\n- **Company profile** to use\n\nWould you like me to guide you through creating a campaign step by step?";
    }
    
    // Lead-related responses
    if (lowerMessage.includes('lead') || lowerMessage.includes('prospect')) {
        return "I can help you with lead management! Here are some things I can do:\n\n- **Generate new leads** based on your criteria\n- **Analyze lead quality** and scoring\n- **Track lead engagement** and responses\n- **Suggest follow-up actions**\n\nWhat specific aspect of lead management would you like to focus on?";
    }
    
    // Template-related responses
    if (lowerMessage.includes('template') || lowerMessage.includes('email')) {
        return "I can help you with outreach templates! I can:\n\n- **Create personalized email templates**\n- **Optimize existing templates** for better response rates\n- **Suggest A/B testing strategies**\n- **Analyze template performance**\n\nWhat type of template are you looking to create or improve?";
    }
    
    // Analytics-related responses
    if (lowerMessage.includes('analytic') || lowerMessage.includes('report') || lowerMessage.includes('performance')) {
        return "I can provide detailed analytics and insights! Here's what I can show you:\n\n- **Campaign performance metrics**\n- **Lead conversion rates**\n- **Email engagement statistics**\n- **ROI analysis**\n- **Trend analysis and predictions**\n\nWhich metrics would you like me to analyze for you?";
    }
    
    // Settings-related responses
    if (lowerMessage.includes('setting') || lowerMessage.includes('config')) {
        return "I can help you configure your Lead Intelligence settings:\n\n- **API integrations** (CRM, email providers)\n- **Automation rules** and workflows\n- **User permissions** and access control\n- **Data export/import** preferences\n\nWhat settings would you like to review or modify?";
    }
    
    // General help
    if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
        return "I'm here to help you maximize your lead generation efforts! Here's what I can assist with:\n\n**🎯 Campaign Management**\n- Create and optimize campaigns\n- Set targeting criteria\n- Monitor performance\n\n**👥 Lead Generation**\n- Find qualified prospects\n- Score and prioritize leads\n- Track engagement\n\n**📧 Outreach Automation**\n- Craft personalized emails\n- Schedule follow-ups\n- A/B test templates\n\n**📊 Analytics & Insights**\n- Performance dashboards\n- Conversion tracking\n- ROI analysis\n\nWhat would you like to start with?";
    }
    
    // Default response
    return "I understand you're interested in: \"" + message + "\". \n\nI'm designed to help with lead generation, campaign management, and sales automation. Could you provide more specific details about what you'd like to accomplish? \n\nFor example:\n- Creating a new campaign\n- Analyzing lead performance\n- Optimizing email templates\n- Setting up integrations";
}

function handleQuickAction(action) {
    const actionMessages = {
        'create-campaign': 'I want to create a new lead generation campaign',
        'analyze-performance': 'Show me campaign performance analytics',
        'generate-leads': 'Help me generate new leads',
        'optimize-templates': 'I want to optimize my email templates'
    };
    
    const message = actionMessages[action];
    if (message) {
        document.getElementById('chat-input').value = message;
        sendChatMessage();
    }
}

// Modal Management
function setupModals() {
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalCloses = document.querySelectorAll('.modal-close');
    
    // Open modals
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });
    
    // Close modals
    modalCloses.forEach(close => {
        close.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal.id);
        });
    });
    
    // Close modal on backdrop click
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Search and Filters
function setupSearchAndFilters() {
    const searchInputs = document.querySelectorAll('.search-box input');
    const filterSelects = document.querySelectorAll('.filter-select');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetContainer = this.closest('.section-header').nextElementSibling;
            filterItems(targetContainer, searchTerm);
        });
    });
    
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const filterValue = this.value;
            const targetContainer = this.closest('.section-header').nextElementSibling;
            filterItemsByStatus(targetContainer, filterValue);
        });
    });
}

function filterItems(container, searchTerm) {
    const items = container.querySelectorAll('.campaign-card, .template-card, .leads-table tbody tr');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

function filterItemsByStatus(container, status) {
    const items = container.querySelectorAll('.campaign-card, .template-card');
    
    items.forEach(item => {
        if (status === 'all') {
            item.style.display = '';
        } else {
            const itemStatus = item.querySelector('.card-status')?.textContent.toLowerCase();
            if (itemStatus === status.toLowerCase()) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        }
    });
}

// Data Loading Functions
function loadInitialData() {
    // Load sample data
    campaigns = generateSampleCampaigns();
    leads = generateSampleLeads();
    templates = generateSampleTemplates();
    
    // Update UI
    updateCampaignsUI();
    updateLeadsUI();
    updateTemplatesUI();
}

function loadCampaigns() {
    showLoading();
    
    setTimeout(() => {
        updateCampaignsUI();
        hideLoading();
    }, 500);
}

function loadLeads() {
    showLoading();
    
    setTimeout(() => {
        updateLeadsUI();
        hideLoading();
    }, 500);
}

function loadTemplates() {
    showLoading();
    
    setTimeout(() => {
        updateTemplatesUI();
        hideLoading();
    }, 500);
}

function loadAnalytics() {
    showLoading();
    
    setTimeout(() => {
        updateAnalyticsUI();
        hideLoading();
    }, 500);
}

function loadSettings() {
    // Settings are static for now
}

// UI Update Functions
function updateCampaignsUI() {
    const container = document.querySelector('.campaigns-grid');
    if (!container) return;
    
    container.innerHTML = campaigns.map(campaign => `
        <div class="campaign-card" data-id="${campaign.id}">
            <div class="card-header">
                <h4 class="card-title">${campaign.name}</h4>
                <span class="card-status status-${campaign.status}">${campaign.status}</span>
            </div>
            <div class="card-content">
                <p>${campaign.description}</p>
            </div>
            <div class="card-stats">
                <div class="stat-item">
                    <span class="stat-value">${campaign.leads_created}</span>
                    <span class="stat-label">Leads</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${campaign.emails_sent}</span>
                    <span class="stat-label">Emails</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${campaign.response_rate}%</span>
                    <span class="stat-label">Response</span>
                </div>
            </div>
            <div class="card-meta">
                <span>Created: ${formatDate(campaign.created_date)}</span>
                <span>Owner: ${campaign.owner}</span>
            </div>
        </div>
    `).join('');
}

function updateLeadsUI() {
    const tbody = document.querySelector('.leads-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = leads.map(lead => `
        <tr data-id="${lead.id}">
            <td>${lead.name}</td>
            <td>${lead.company}</td>
            <td>${lead.email}</td>
            <td>${lead.phone || 'N/A'}</td>
            <td><span class="card-status status-${lead.status}">${lead.status}</span></td>
            <td>${lead.source}</td>
            <td>${formatDate(lead.created_date)}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="viewLead('${lead.id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function updateTemplatesUI() {
    const container = document.querySelector('.templates-grid');
    if (!container) return;
    
    container.innerHTML = templates.map(template => `
        <div class="template-card" data-id="${template.id}">
            <div class="card-header">
                <h4 class="card-title">${template.name}</h4>
                <span class="card-status status-${template.active ? 'active' : 'draft'}">
                    ${template.active ? 'Active' : 'Draft'}
                </span>
            </div>
            <div class="card-content">
                <p><strong>Type:</strong> ${template.type}</p>
                <p><strong>Industry:</strong> ${template.target_industry}</p>
                <p class="mt-2">${template.description}</p>
            </div>
            <div class="card-stats">
                <div class="stat-item">
                    <span class="stat-value">${template.usage_count}</span>
                    <span class="stat-label">Used</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${template.success_rate}%</span>
                    <span class="stat-label">Success</span>
                </div>
            </div>
            <div class="card-meta">
                <span>Last used: ${formatDate(template.last_used)}</span>
            </div>
        </div>
    `).join('');
}

function updateAnalyticsUI() {
    // Update metric cards
    const metrics = calculateMetrics();
    
    document.querySelector('[data-metric="total-campaigns"] h4').textContent = metrics.totalCampaigns;
    document.querySelector('[data-metric="total-leads"] h4').textContent = metrics.totalLeads;
    document.querySelector('[data-metric="emails-sent"] h4').textContent = metrics.emailsSent;
    document.querySelector('[data-metric="response-rate"] h4').textContent = metrics.responseRate + '%';
}

// Sample Data Generators
function generateSampleCampaigns() {
    return [
        {
            id: 'camp-001',
            name: 'Tech Startup Outreach',
            description: 'Targeting early-stage tech startups for our SaaS solution',
            status: 'active',
            leads_created: 145,
            emails_sent: 289,
            response_rate: 12.5,
            created_date: new Date('2024-01-15'),
            owner: 'John Doe'
        },
        {
            id: 'camp-002',
            name: 'E-commerce Expansion',
            description: 'Reaching out to e-commerce businesses for partnership opportunities',
            status: 'paused',
            leads_created: 89,
            emails_sent: 156,
            response_rate: 8.7,
            created_date: new Date('2024-01-10'),
            owner: 'Jane Smith'
        },
        {
            id: 'camp-003',
            name: 'Healthcare Providers',
            description: 'Targeting healthcare providers for our compliance software',
            status: 'completed',
            leads_created: 234,
            emails_sent: 445,
            response_rate: 15.2,
            created_date: new Date('2024-01-05'),
            owner: 'Mike Johnson'
        }
    ];
}

function generateSampleLeads() {
    return [
        {
            id: 'lead-001',
            name: 'Sarah Wilson',
            company: 'TechFlow Inc.',
            email: 'sarah.wilson@techflow.com',
            phone: '+1-555-0123',
            status: 'qualified',
            source: 'Tech Startup Outreach',
            created_date: new Date('2024-01-20')
        },
        {
            id: 'lead-002',
            name: 'David Chen',
            company: 'InnovateLab',
            email: 'david.chen@innovatelab.com',
            phone: '+1-555-0124',
            status: 'contacted',
            source: 'Tech Startup Outreach',
            created_date: new Date('2024-01-19')
        },
        {
            id: 'lead-003',
            name: 'Emily Rodriguez',
            company: 'HealthTech Solutions',
            email: 'emily.r@healthtech.com',
            phone: null,
            status: 'new',
            source: 'Healthcare Providers',
            created_date: new Date('2024-01-18')
        }
    ];
}

function generateSampleTemplates() {
    return [
        {
            id: 'temp-001',
            name: 'SaaS Introduction',
            type: 'Cold Outreach',
            target_industry: 'Technology',
            description: 'Introduction email for SaaS products targeting tech companies',
            active: true,
            usage_count: 45,
            success_rate: 12.8,
            last_used: new Date('2024-01-20')
        },
        {
            id: 'temp-002',
            name: 'Partnership Proposal',
            type: 'Partnership',
            target_industry: 'E-commerce',
            description: 'Template for proposing strategic partnerships',
            active: true,
            usage_count: 23,
            success_rate: 18.5,
            last_used: new Date('2024-01-18')
        },
        {
            id: 'temp-003',
            name: 'Follow-up Sequence',
            type: 'Follow-up',
            target_industry: 'General',
            description: 'Multi-step follow-up sequence for non-responders',
            active: false,
            usage_count: 67,
            success_rate: 9.2,
            last_used: new Date('2024-01-15')
        }
    ];
}

// Utility Functions
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

function calculateMetrics() {
    return {
        totalCampaigns: campaigns.length,
        totalLeads: leads.length,
        emailsSent: campaigns.reduce((sum, camp) => sum + camp.emails_sent, 0),
        responseRate: (campaigns.reduce((sum, camp) => sum + camp.response_rate, 0) / campaigns.length).toFixed(1)
    };
}

function showLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Event Listeners
function setupEventListeners() {
    // Campaign card clicks
    document.addEventListener('click', function(e) {
        const campaignCard = e.target.closest('.campaign-card');
        if (campaignCard) {
            const campaignId = campaignCard.getAttribute('data-id');
            viewCampaign(campaignId);
        }
        
        const templateCard = e.target.closest('.template-card');
        if (templateCard) {
            const templateId = templateCard.getAttribute('data-id');
            viewTemplate(templateId);
        }
    });
}

// Action Functions
function viewCampaign(campaignId) {
    const campaign = campaigns.find(c => c.id === campaignId);
    if (campaign) {
        addChatMessage('user', `Show me details for campaign: ${campaign.name}`);
        switchTab('ai-assistant');
    }
}

function viewTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (template) {
        addChatMessage('user', `Show me details for template: ${template.name}`);
        switchTab('ai-assistant');
    }
}

function viewLead(leadId) {
    const lead = leads.find(l => l.id === leadId);
    if (lead) {
        addChatMessage('user', `Show me details for lead: ${lead.name} from ${lead.company}`);
        switchTab('ai-assistant');
    }
}

// Export functions for global access
window.LeadIntelligence = {
    switchTab,
    openModal,
    closeModal,
    viewCampaign,
    viewTemplate,
    viewLead,
    addChatMessage
};