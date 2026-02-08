#!/usr/bin/env python3
"""
Lekker Find - Agency Lead Report Generator (Interactive Dashboard)
==================================================================
Generates a professional, interactive HTML dashboard from the agency leads CSV.
Features:
- Client-side filtering & sorting (Alpine.js)
- JSON data injection
- Professional UI (Tailwind CSS)
- One-click copy for pitches

Usage:
    python scripts/generate_lead_report.py
"""

import pandas as pd
import os
import json
from datetime import datetime

CSV_FILE = 'data/agency_leads.csv'
OUTPUT_HTML = 'public/agency_leads_dashboard.html'

def generate_interactive_dashboard():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found. Run find_agencies.py first.")
        return

    # 1. Load Data & Prepare JSON
    df = pd.read_csv(CSV_FILE)
    
    # Clean/Fill NaNs for JSON serialization
    df = df.fillna('')
    
    # Convert to list of dicts for JSON injection
    leads_data = df.to_dict(orient='records')
    
    # Serialize to JSON string
    leads_json = json.dumps(leads_data)

    # 2. HTML Template with Alpine.js
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lekker Find - Agency Prospecting Dashboard</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        [x-cloak] {{ display: none !important; }}
    </style>
    
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#2563eb',
                        secondary: '#475569',
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800" x-data="leadDashboard()">

    <!-- Toast Notification -->
    <div x-show="toast.visible" 
         x-transition:enter="transition ease-out duration-300"
         x-transition:enter-start="opacity-0 transform translate-y-2"
         x-transition:enter-end="opacity-100 transform translate-y-0"
         x-transition:leave="transition ease-in duration-200"
         x-transition:leave-start="opacity-100 transform translate-y-0"
         x-transition:leave-end="opacity-0 transform translate-y-2"
         @click="toast.visible = false"
         class="fixed bottom-5 right-5 z-50 bg-slate-800 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 cursor-pointer"
         x-cloak>
        <span x-text="toast.message"></span>
    </div>

    <!-- Navigation -->
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-40 bg-opacity-90 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="bg-blue-600 text-white p-1.5 rounded-lg font-bold text-lg">LF</div>
                <h1 class="font-bold text-xl text-slate-900 tracking-tight">Agency Scout</h1>
            </div>
            
            <div class="flex items-center gap-4 text-sm font-medium text-slate-500">
                <span>Leads: <span x-text="leads.length" class="text-slate-900"></span></span>
                <span class="h-4 w-px bg-slate-300"></span>
                <span>Generated: {datetime.now().strftime('%d %b %H:%M')}</span>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-8">
        
        <!-- Stats Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">High Value Targets</div>
                <div class="mt-2 text-3xl font-bold text-emerald-600" x-text="stats.highValue">0</div>
                <div class="text-xs text-slate-500 mt-1">Score > 100</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Missing Websites</div>
                <div class="mt-2 text-3xl font-bold text-rose-600" x-text="stats.noWebsite">0</div>
                <div class="text-xs text-slate-500 mt-1">Immediate opportunity</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Marketing Active</div>
                <div class="mt-2 text-3xl font-bold text-blue-600" x-text="stats.hasPixel">0</div>
                <div class="text-xs text-slate-500 mt-1">Has Ads/Pixel</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Lead Score</div>
                <div class="mt-2 text-3xl font-bold text-indigo-600" x-text="stats.avgScore">0</div>
                <div class="text-xs text-slate-500 mt-1">Overall potential</div>
            </div>
        </div>

        <!-- Controls -->
        <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-6 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <!-- Search -->
            <div class="relative w-full md:w-96">
                <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">🔍</span>
                <input type="text" x-model="search" placeholder="Search venues, issues, tech..." 
                       class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm">
            </div>
            
            <!-- Filters -->
            <div class="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0">
                <button @click="filter = 'all'" :class="filter === 'all' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1.5 rounded-full text-sm font-medium transition whitespace-nowrap">All</button>
                <button @click="filter = 'high_value'" :class="filter === 'high_value' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'" class="px-3 py-1.5 rounded-full text-sm font-medium transition whitespace-nowrap">High Value 💎</button>
                <button @click="filter = 'no_website'" :class="filter === 'no_website' ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'" class="px-3 py-1.5 rounded-full text-sm font-medium transition whitespace-nowrap">No Website 🚫</button>
                <button @click="filter = 'pixel'" :class="filter === 'pixel' ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'" class="px-3 py-1.5 rounded-full text-sm font-medium transition whitespace-nowrap">Running Ads 📊</button>
            </div>
        </div>

        <!-- Leads List -->
        <div class="space-y-4">
            <template x-for="lead in filteredLeads" :key="lead.Name">
                <div class="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition duration-200 overflow-hidden group">
                    <div class="md:flex">
                        
                        <!-- Left: Score column -->
                        <div class="md:w-24 bg-slate-50 border-r border-slate-100 flex flex-col items-center justify-center p-4">
                            <div class="text-2xl font-bold" 
                                 :class="lead.Lead_Score > 100 ? 'text-emerald-600' : (lead.Lead_Score > 60 ? 'text-blue-600' : 'text-slate-500')" 
                                 x-text="Math.round(lead.Lead_Score)"></div>
                            <div class="text-[10px] uppercase font-bold text-slate-400 tracking-wider mt-1">Score</div>
                        </div>

                        <!-- Middle: Details -->
                        <div class="p-5 flex-1 md:border-r border-slate-100">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-bold text-lg text-slate-900 group-hover:text-blue-600 transition" x-text="lead.Name"></h3>
                                    <div class="text-sm text-slate-500" x-text="lead.Address"></div>
                                </div>
                                <div class="flex gap-2">
                                    <span x-show="lead.Website_Status === 'Missing'" class="px-2 py-1 bg-rose-100 text-rose-700 text-xs font-bold rounded">No Website</span>
                                    <span x-show="lead.Lead_Score > 100" class="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded">Top Tier</span>
                                    <span x-show="(lead.Tech_Stack || '').includes('Pixel')" class="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-bold rounded">Ads</span>
                                </div>
                            </div>
                            
                            <!-- Badges & Tech -->
                            <div class="mt-3 flex flex-wrap gap-2 text-xs">
                                <template x-if="lead.Tech_Stack">
                                    <template x-for="tech in lead.Tech_Stack.split(', ')">
                                        <span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded border border-slate-200" x-text="tech"></span>
                                    </template>
                                </template>
                            </div>

                            <!-- Issues -->
                            <div x-show="lead.Issues" class="mt-3 text-sm text-rose-600 flex items-start gap-1.5 bg-rose-50 p-2 rounded-lg border border-rose-100 w-fit">
                                <span class="mt-0.5">⚠️</span>
                                <span x-text="lead.Issues" class="font-medium"></span>
                            </div>
                        </div>

                        <!-- Right: Action & Pitch -->
                        <div class="md:w-1/3 p-5 bg-slate-50/50 flex flex-col justify-between">
                            <div>
                                <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Strategy & Pitch</h4>
                                <div class="text-sm text-slate-700 italic border-l-2 border-indigo-400 pl-3 leading-relaxed">
                                    <span x-html="formatAdvice(lead.Advice)"></span>
                                </div>
                            </div>

                            <div class="mt-4 flex flex-wrap gap-3 pt-4 border-t border-slate-200">
                                <template x-if="lead.Website">
                                    <a :href="lead.Website" target="_blank" class="text-xs font-medium text-blue-600 hover:underline flex items-center gap-1">
                                        🌐 Visit Site
                                    </a>
                                </template>
                                <template x-if="lead.Emails">
                                    <a :href="'mailto:' + lead.Emails" class="text-xs font-medium text-slate-600 hover:text-blue-600 flex items-center gap-1">
                                        📧 Email
                                    </a>
                                </template>
                                <template x-if="lead.Phone">
                                    <a :href="'tel:' + lead.Phone" class="text-xs font-medium text-slate-600 hover:text-blue-600 flex items-center gap-1">
                                        📞 Call
                                    </a>
                                </template>
                                
                                <button @click="copyPitch(lead)" class="ml-auto text-xs bg-white border border-slate-300 hover:border-blue-400 text-slate-700 px-3 py-1.5 rounded shadow-sm hover:shadow transition font-medium">
                                    📋 Copy Pitch
                                </button>
                            </div>
                        </div>

                    </div>
                    
                    <!-- Expandable Data Draw (Hidden logic could go here) -->
                </div>
            </template>
            
            <div x-show="filteredLeads.length === 0" class="text-center py-12 text-slate-400">
                No leads match your current filters.
            </div>
        </div>

    </main>

    <script>
        document.addEventListener('alpine:init', () => {{
            Alpine.data('leadDashboard', () => ({{
                rawLeads: {leads_json},
                search: '',
                filter: 'all',
                toast: {{ visible: false, message: '' }},

                get leads() {{
                    return this.rawLeads;
                }},

                get filteredLeads() {{
                    return this.leads.filter(lead => {{
                        // Text Search
                        const searchLower = this.search.toLowerCase();
                        const matchesSearch = 
                            (lead.Name || '').toLowerCase().includes(searchLower) ||
                            (lead.Issues || '').toLowerCase().includes(searchLower) ||
                            (lead.Tech_Stack || '').toLowerCase().includes(searchLower) ||
                            (lead.Advice || '').toLowerCase().includes(searchLower);

                        if (!matchesSearch) return false;

                        // Category Filter
                        if (this.filter === 'high_value') return lead.Lead_Score > 100;
                        if (this.filter === 'no_website') return lead.Website_Status === 'Missing';
                        if (this.filter === 'pixel') return (lead.Tech_Stack || '').includes('Pixel') || (lead.Tech_Stack || '').includes('Analytics');
                        
                        return true;
                    }}).sort((a, b) => b.Lead_Score - a.Lead_Score);
                }},

                get stats() {{
                    const l = this.leads;
                    return {{
                        highValue: l.filter(x => x.Lead_Score > 100).length,
                        noWebsite: l.filter(x => x.Website_Status === 'Missing').length,
                        hasPixel: l.filter(x => (x.Tech_Stack || '').includes('Pixel') || (x.Tech_Stack || '').includes('Analytics')).length,
                        avgScore: l.length ? Math.round(l.reduce((a, b) => a + (b.Lead_Score || 0), 0) / l.length) : 0
                    }}
                }},

                formatAdvice(advice) {{
                    if (!advice) return 'Review manually.';
                    return advice.split('|').map(chunk => chunk.trim()).join('<br/><br/>👉 ');
                }},
                
                async copyPitch(lead) {{
                    const text = lead.Advice.replace(/\\|/g, '\\n');
                    try {{
                        await navigator.clipboard.writeText(text);
                        this.showToast('Pitch copied to clipboard!');
                    }} catch (err) {{
                        this.showToast('Failed to copy');
                    }}
                }},

                showToast(msg) {{
                    this.toast.message = msg;
                    this.toast.visible = true;
                    setTimeout(() => this.toast.visible = false, 3000);
                }}
            }}))
        }});
    </script>
</body>
</html>
    """
    
    os.makedirs('public', exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive Dashboard generated: {OUTPUT_HTML}")
    
    if os.name == 'nt':
        os.startfile(os.path.abspath(OUTPUT_HTML))

if __name__ == "__main__":
    generate_interactive_dashboard()
