// Lead Intelligence - Contact DocType JavaScript

frappe.ui.form.on('Contact', {
    refresh: function(frm) {
        // Add custom buttons for Lead Intelligence features
        if (!frm.doc.__islocal) {
            add_contact_intelligence_buttons(frm);
            setup_contact_score_display(frm);
            show_social_profiles(frm);
        }
    },
    
    email_id: function(frm) {
        // Validate email and check for related leads/customers
        if (frm.doc.email_id && validate_email(frm.doc.email_id)) {
            check_related_records(frm);
        }
    },
    
    phone: function(frm) {
        // Validate and format phone number
        if (frm.doc.phone) {
            format_phone_number(frm);
        }
    },
    
    before_save: function(frm) {
        // Update contact intelligence data before saving
        update_contact_intelligence_data(frm);
    }
});

function add_contact_intelligence_buttons(frm) {
    // Enrich Contact Data button
    frm.add_custom_button(__('Enrich Data'), function() {
        enrich_contact_data(frm);
    }, __('Lead Intelligence'));
    
    // Calculate Score button
    frm.add_custom_button(__('Calculate Score'), function() {
        calculate_contact_score(frm);
    }, __('Lead Intelligence'));
    
    // Find Social Profiles button
    frm.add_custom_button(__('Find Social Profiles'), function() {
        find_social_profiles(frm);
    }, __('Lead Intelligence'));
    
    // View Related Records button
    frm.add_custom_button(__('Related Records'), function() {
        show_related_records(frm);
    }, __('Lead Intelligence'));
    
    // Export Contact button
    frm.add_custom_button(__('Export Contact'), function() {
        export_contact_data(frm);
    }, __('Lead Intelligence'));
}

function setup_contact_score_display(frm) {
    if (frm.doc.contact_score !== undefined && frm.doc.contact_score !== null) {
        const score = frm.doc.contact_score;
        const level = get_contact_level(score);
        
        // Create score display HTML
        const scoreHtml = `
            <div class="contact-score-display">
                <div class="score-circle ${level.toLowerCase()}">
                    <span class="score-value">${Math.round(score)}</span>
                </div>
                <div class="score-details">
                    <div class="score-label">Contact Score</div>
                    <div class="level-badge ${level.toLowerCase()}">${level}</div>
                </div>
            </div>
        `;
        
        // Add to form sidebar
        frm.sidebar.add_user_action(scoreHtml);
    }
}

function show_social_profiles(frm) {
    if (frm.doc.social_profiles) {
        try {
            const profiles = JSON.parse(frm.doc.social_profiles);
            
            let profilesHtml = '<div class="social-profiles">';
            profilesHtml += '<h5><i class="fa fa-share-alt"></i> Social Profiles</h5>';
            
            for (const [platform, url] of Object.entries(profiles)) {
                if (url) {
                    profilesHtml += `
                        <div class="social-profile-item">
                            <i class="fa fa-${platform.toLowerCase()}"></i>
                            <a href="${url}" target="_blank">${platform}</a>
                        </div>
                    `;
                }
            }
            
            profilesHtml += '</div>';
            
            frm.dashboard.add_section(profilesHtml, __('Social Profiles'));
        } catch (e) {
            // Invalid JSON, ignore
        }
    }
}

function check_related_records(frm) {
    if (frm.doc.email_id) {
        // Check for related leads
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Lead',
                filters: {
                    email_id: frm.doc.email_id
                },
                fields: ['name', 'lead_name', 'company_name', 'lead_score', 'status'],
                limit: 3
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    show_related_leads_indicator(frm, r.message);
                }
            }
        });
        
        // Check for related customers
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Customer',
                filters: {
                    email_id: frm.doc.email_id
                },
                fields: ['name', 'customer_name', 'customer_group'],
                limit: 3
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    show_related_customers_indicator(frm, r.message);
                }
            }
        });
    }
}

function show_related_leads_indicator(frm, leads) {
    const leadCount = leads.length;
    
    let leadsHtml = '<div class="related-leads">';
    leadsHtml += `<h5><i class="fa fa-user"></i> Related Leads (${leadCount})</h5>`;
    
    leads.forEach(lead => {
        leadsHtml += `
            <div class="related-item">
                <a href="/app/lead/${lead.name}">${lead.lead_name || lead.company_name}</a>
                <span class="status-badge">${lead.status}</span>
                ${lead.lead_score ? `<span class="score">${Math.round(lead.lead_score)}</span>` : ''}
            </div>
        `;
    });
    
    leadsHtml += '</div>';
    
    frm.dashboard.add_section(leadsHtml, __('Related Records'));
}

function show_related_customers_indicator(frm, customers) {
    const customerCount = customers.length;
    
    let customersHtml = '<div class="related-customers">';
    customersHtml += `<h5><i class="fa fa-building"></i> Related Customers (${customerCount})</h5>`;
    
    customers.forEach(customer => {
        customersHtml += `
            <div class="related-item">
                <a href="/app/customer/${customer.name}">${customer.customer_name}</a>
                <span class="group-badge">${customer.customer_group || ''}</span>
            </div>
        `;
    });
    
    customersHtml += '</div>';
    
    frm.dashboard.add_section(customersHtml, __('Related Records'));
}

function enrich_contact_data(frm) {
    frappe.show_alert({
        message: __('Enriching contact data...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'lead_intelligence.api.enrich_contact',
        args: {
            contact_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Contact data enriched successfully'),
                    indicator: 'green'
                });
                
                // Refresh form to show updated data
                frm.reload_doc();
                
                // Show enrichment results
                if (r.message.data) {
                    show_enrichment_results(r.message.data);
                }
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to enrich contact data'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.show_alert({
                message: __('Error enriching contact data'),
                indicator: 'red'
            });
        }
    });
}

function calculate_contact_score(frm) {
    frappe.call({
        method: 'lead_intelligence.api.calculate_contact_score_api',
        args: {
            contact_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.set_value('contact_score', r.message.score);
                
                frappe.show_alert({
                    message: __('Contact score calculated: ') + Math.round(r.message.score),
                    indicator: 'green'
                });
                
                // Update score display
                setup_contact_score_display(frm);
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to calculate contact score'),
                    indicator: 'red'
                });
            }
        }
    });
}

function find_social_profiles(frm) {
    if (!frm.doc.email_id) {
        frappe.msgprint(__('Email ID is required to find social profiles'));
        return;
    }
    
    frappe.show_alert({
        message: __('Searching for social profiles...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'lead_intelligence.api.find_social_profiles',
        args: {
            email: frm.doc.email_id,
            name: frm.doc.first_name + ' ' + (frm.doc.last_name || '')
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                if (r.message.profiles && Object.keys(r.message.profiles).length > 0) {
                    frm.set_value('social_profiles', JSON.stringify(r.message.profiles));
                    
                    frappe.show_alert({
                        message: __('Social profiles found and updated'),
                        indicator: 'green'
                    });
                    
                    // Refresh social profiles display
                    show_social_profiles(frm);
                } else {
                    frappe.show_alert({
                        message: __('No social profiles found'),
                        indicator: 'orange'
                    });
                }
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to find social profiles'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_related_records(frm) {
    if (!frm.doc.email_id) {
        frappe.msgprint(__('Email ID is required to find related records'));
        return;
    }
    
    frappe.call({
        method: 'lead_intelligence.api.get_contact_related_records',
        args: {
            contact_id: frm.doc.name,
            email: frm.doc.email_id
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_related_records_dialog(r.message.records);
            } else {
                frappe.msgprint(__('Failed to load related records'));
            }
        }
    });
}

function show_related_records_dialog(records) {
    const dialog = new frappe.ui.Dialog({
        title: __('Related Records'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'records_html'
            }
        ]
    });
    
    let html = '<div class="related-records-dialog">';
    
    // Leads section
    if (records.leads && records.leads.length > 0) {
        html += '<h4>Related Leads</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><th>Name</th><th>Company</th><th>Score</th><th>Quality</th><th>Status</th></tr></thead><tbody>';
        
        records.leads.forEach(lead => {
            html += '<tr>';
            html += `<td><a href="/app/lead/${lead.name}">${lead.lead_name || '-'}</a></td>`;
            html += `<td>${lead.company_name || '-'}</td>`;
            html += `<td>${lead.lead_score ? Math.round(lead.lead_score) : '-'}</td>`;
            html += `<td><span class="quality-badge ${(lead.lead_quality || '').toLowerCase()}">${lead.lead_quality || '-'}</span></td>`;
            html += `<td>${lead.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
    }
    
    // Customers section
    if (records.customers && records.customers.length > 0) {
        html += '<h4>Related Customers</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><th>Name</th><th>Group</th><th>Territory</th><th>Status</th></tr></thead><tbody>';
        
        records.customers.forEach(customer => {
            html += '<tr>';
            html += `<td><a href="/app/customer/${customer.name}">${customer.customer_name || '-'}</a></td>`;
            html += `<td>${customer.customer_group || '-'}</td>`;
            html += `<td>${customer.territory || '-'}</td>`;
            html += `<td>${customer.disabled ? 'Disabled' : 'Active'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
    }
    
    // Opportunities section
    if (records.opportunities && records.opportunities.length > 0) {
        html += '<h4>Related Opportunities</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><th>Title</th><th>Customer</th><th>Value</th><th>Stage</th><th>Status</th></tr></thead><tbody>';
        
        records.opportunities.forEach(opp => {
            html += '<tr>';
            html += `<td><a href="/app/opportunity/${opp.name}">${opp.title || '-'}</a></td>`;
            html += `<td>${opp.customer || '-'}</td>`;
            html += `<td>${opp.opportunity_amount || '-'}</td>`;
            html += `<td>${opp.sales_stage || '-'}</td>`;
            html += `<td>${opp.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
    }
    
    if (!records.leads?.length && !records.customers?.length && !records.opportunities?.length) {
        html += '<p class="text-muted">No related records found.</p>';
    }
    
    html += '</div>';
    
    dialog.fields_dict.records_html.$wrapper.html(html);
    dialog.show();
}

function export_contact_data(frm) {
    const filters = {
        contact_id: frm.doc.name
    };
    
    frappe.call({
        method: 'lead_intelligence.api.export_contact_data',
        args: {
            filters: JSON.stringify(filters)
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Contact data exported successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to export contact data'),
                    indicator: 'red'
                });
            }
        }
    });
}

function update_contact_intelligence_data(frm) {
    // Update any intelligence-related fields before saving
    if (frm.doc.email_id && !frm.doc.contact_score) {
        // Calculate initial contact score
        calculate_contact_score(frm);
    }
}

function get_contact_level(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    if (score >= 20) return 'Poor';
    return 'Very Poor';
}

function format_phone_number(frm) {
    const phone = frm.doc.phone;
    if (phone && phone.length > 0) {
        // Basic phone number formatting (can be enhanced)
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            const formatted = `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
            frm.set_value('phone', formatted);
        }
    }
}

function validate_email(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function show_enrichment_results(data) {
    let message = 'Enrichment completed:';
    
    if (data.social_profiles) {
        message += `<br>• Social profiles found`;
    }
    
    if (data.company_info) {
        message += `<br>• Company information updated`;
    }
    
    if (data.additional_emails) {
        message += `<br>• Additional emails found`;
    }
    
    frappe.msgprint({
        title: __('Enrichment Results'),
        message: message,
        indicator: 'green'
    });
}

// Export functions for use in other modules
window.LeadIntelligence = window.LeadIntelligence || {};
window.LeadIntelligence.Contact = {
    enrichData: enrich_contact_data,
    calculateScore: calculate_contact_score,
    findSocialProfiles: find_social_profiles,
    showRelatedRecords: show_related_records
};