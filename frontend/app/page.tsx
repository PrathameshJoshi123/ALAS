"use client";

import Link from "next/link";
import { 
  Building2, 
  User, 
  BarChart3, 
  Sparkles, 
  Scale, 
  Cloud, 
  Database, 
  Network, 
  MonitorSmartphone, 
  Quote 
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900 overflow-hidden relative">
      {/* Background radial gradient */}
      <div className="absolute top-0 left-0 w-full h-[800px] bg-gradient-to-br from-indigo-50/50 via-white to-slate-50/50 -z-10" />

      {/* Navigation */}
      <nav className="flex items-center justify-between px-8 lg:px-16 py-8 max-w-[1400px] mx-auto w-full">
        <div className="flex items-center gap-2">
          <span className="font-bold text-2xl tracking-tight text-slate-900">
            ALAS
          </span>
        </div>
        
        <div className="hidden md:flex items-center gap-10 text-sm font-medium text-slate-600">
          <Link href="#" className="hover:text-slate-900 transition-colors">Solutions</Link>
          <Link href="#" className="hover:text-slate-900 transition-colors">Enterprise</Link>
          <Link href="#" className="hover:text-slate-900 transition-colors">Professionals</Link>
          <Link href="#" className="hover:text-slate-900 transition-colors">Pricing</Link>
        </div>

        <div className="flex items-center gap-6 text-sm font-medium">
          <Link href="/auth/login" className="text-slate-600 hover:text-slate-900 transition-colors">Sign In</Link>
          <Link href="/auth/signup" className="bg-[#1e2756] text-white px-6 py-2.5 rounded-md hover:bg-[#151b3b] transition-all shadow-sm">
            Get Started
          </Link>
        </div>
      </nav>

      <main className="max-w-[1400px] mx-auto px-8 lg:px-16 py-12 lg:py-24 w-full">
        {/* Hero Section */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-20 items-center">
          <div className="max-w-2xl relative">
            <p className="text-blue-500 font-bold text-[11px] tracking-[0.2em] uppercase mb-8">
              The new architecture of law
            </p>
            <h1 className="text-6xl lg:text-[5rem] font-bold tracking-tight text-slate-900 mb-2 leading-[1.05]">
              Precision analysis.
            </h1>
            <h1 className="text-6xl lg:text-[5rem] font-bold tracking-tight mb-10 leading-[1.05] text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-indigo-400">
              Total restraint.
            </h1>
            <p className="text-[17px] text-slate-600 leading-relaxed max-w-xl pr-10">
              Elevate your legal workflow with an AI-native workspace designed for structural clarity, risk mitigation, and sophisticated contract generation.
            </p>
          </div>

          <div className="flex flex-col gap-6 w-[80%] ml-auto">
            {/* Card 1 */}
            <div className="bg-white p-8 rounded-2xl shadow-[0_8px_40px_rgb(0,0,0,0.04)] border border-slate-100 relative group hover:shadow-[0_8px_40px_rgb(0,0,0,0.08)] transition-all">
              <span className="absolute top-6 right-6 bg-[#EDF2FE] text-[#3B5FE5] text-[9px] uppercase font-bold tracking-[0.1em] px-3 py-1.5 rounded-sm">
                Enterprise
              </span>
              <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mb-6 text-slate-700">
                <Building2 size={24} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">For Law Firms</h3>
              <p className="text-slate-500 text-[13px] leading-relaxed mb-8 pr-16 bg-transparent">
                Centralize your firm's intelligence. Manage multi-tenant workspaces and large-scale document reviews.
              </p>
              <Link href="/auth/signup?tab=firm" className="w-full bg-[#3B5FE5] text-white py-3.5 rounded-lg font-medium text-sm hover:bg-blue-600 transition-colors flex items-center justify-center gap-2 shadow-sm">
                Register Firm <span>→</span>
              </Link>
            </div>

            {/* Card 2 */}
            <div className="bg-white p-8 rounded-2xl shadow-[0_8px_40px_rgb(0,0,0,0.04)] border border-slate-100 relative group hover:shadow-[0_8px_40px_rgb(0,0,0,0.08)] transition-all">
              <span className="absolute top-6 right-6 bg-slate-100 text-slate-500 text-[9px] uppercase font-bold tracking-[0.1em] px-3 py-1.5 rounded-sm">
                Individual
              </span>
              <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mb-6 text-slate-700">
                <User size={24} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">For Professionals</h3>
              <p className="text-slate-500 text-[13px] leading-relaxed mb-8 pr-16">
                Professional-grade tools for solo practitioners and in-house counsel focused on single-seat efficiency.
              </p>
              <Link href="/auth/signup?tab=user" className="w-full bg-white text-slate-900 border border-slate-200 py-3.5 rounded-lg font-bold text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2">
                Join as Individual
              </Link>
            </div>
          </div>
        </div>

        {/* How it Works Section */}
        <div className="mt-48 mb-16 text-center max-w-3xl mx-auto">
          <h2 className="text-[2rem] font-bold text-slate-900 mb-4">How it Works</h2>
          <p className="text-slate-500 text-[15px] max-w-2xl mx-auto leading-relaxed">
            Our platform integrates directly into your cognitive workflow, handling the heavy lifting of structure while you focus on strategy.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Structural Contract Analysis - Span 2 */}
          <div className="lg:col-span-2 bg-white rounded-3xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.03)] border border-slate-100 flex flex-col md:flex-row h-full min-h-[380px]">
            <div className="p-10 md:p-14 flex-1 flex flex-col justify-center">
              <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-600 mb-8">
                <BarChart3 size={24} />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-4">Structural Contract Analysis</h3>
              <p className="text-slate-500 leading-relaxed text-[15px] pr-8">
                Deconstruct complex agreements into logical nodes. Our AI identifies high-risk clauses, missing protections, and structural inconsistencies in seconds.
              </p>
            </div>
            {/* Blueprint Image Placeholder using subtle styling */}
            <div className="w-full md:w-[45%] bg-[#F8FAFC] relative overflow-hidden flex items-center justify-center">
              {/* Fake blueprints aesthetic */}
              <div className="absolute inset-0 opacity-30 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
              <div className="absolute w-[200%] h-48 bg-white/40 -rotate-45 shadow-xl blur-sm top-20 right-[-50%] transform"></div>
              <div className="absolute w-[200%] h-32 bg-slate-200/50 -rotate-45 shadow-sm blur-sm bottom-10 right-[-30%] transform"></div>
              {/* Some decorative architecture lines */}
              <svg className="w-full h-full opacity-10 absolute inset-0" viewBox="0 0 100 100" preserveAspectRatio="none">
                 <line x1="0" y1="100" x2="100" y2="0" stroke="currentColor" strokeWidth="0.5" />
                 <line x1="20" y1="100" x2="100" y2="20" stroke="currentColor" strokeWidth="0.5" />
                 <line x1="40" y1="100" x2="100" y2="40" stroke="currentColor" strokeWidth="0.5" />
              </svg>
            </div>
          </div>

          {/* AI Clause Gen */}
          <div className="bg-[#0b1437] text-white rounded-3xl p-10 md:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.08)] flex flex-col h-full relative overflow-hidden min-h-[380px]">
            {/* faint glow in top right */}
            <div className="absolute -top-32 -right-32 w-64 h-64 bg-blue-500/20 blur-[80px] rounded-full pointer-events-none"></div>
            <div className="mb-16">
              <Sparkles size={28} className="text-blue-100" />
            </div>
            <div className="mt-auto">
              <h3 className="text-[22px] font-bold mb-4">AI Clause Generation</h3>
              <p className="text-slate-300 text-[14px] leading-relaxed mb-10">
                Generate precision-drafted clauses based on your firm's historical precedents and the latest jurisdictional standards.
              </p>
              <Link href="#" className="inline-flex items-center text-[13px] font-medium text-slate-300 hover:text-white transition-colors">
                Explore Generation <span className="ml-2 bg-white/10 rounded-full p-1 border border-white/20"><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg></span>
              </Link>
            </div>
          </div>

          {/* Jurisdictional Drift */}
          <div className="bg-[#E9F0FE] rounded-3xl p-10 md:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.03)] flex flex-col h-full min-h-[380px]">
             <div className="mb-16 mt-4">
                 <Scale size={32} className="text-[#1A365D]" />
             </div>
             <div className="mt-auto">
                <h3 className="text-[22px] font-bold text-[#1A365D] mb-4">Jurisdictional Drift</h3>
                <p className="text-[#3b557b] text-[15px] leading-relaxed pr-6">
                  Monitor changes in law that affect your existing document corpus automatically with real-time alerts.
                </p>
             </div>
          </div>

          {/* Zero-Boundary Integration - Span 2 */}
          <div className="lg:col-span-2 bg-white rounded-3xl p-10 md:p-14 shadow-[0_8px_30px_rgb(0,0,0,0.03)] border border-slate-100 flex flex-col md:flex-row items-center gap-16 min-h-[380px]">
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-slate-900 mb-5">Zero-Boundary Integration</h3>
              <p className="text-slate-500 text-[15px] leading-relaxed max-w-md pr-10">
                Seamlessly connect with your existing document management systems through our robust architectural API.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 w-full md:w-auto">
              <div className="w-[100px] h-[70px] bg-[#F8FAFC] flex items-center justify-center rounded-xl text-slate-400">
                <Cloud size={24} />
              </div>
              <div className="w-[100px] h-[70px] bg-[#F8FAFC] flex items-center justify-center rounded-xl text-slate-400">
                <Database size={24} />
              </div>
              <div className="w-[100px] h-[70px] bg-[#F8FAFC] flex items-center justify-center rounded-xl text-slate-400">
                <Network size={24} />
              </div>
              <div className="w-[100px] h-[70px] bg-[#F8FAFC] flex items-center justify-center rounded-xl text-slate-400">
                <MonitorSmartphone size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA section */}
        <div className="mt-40 pt-20 border-t border-slate-200 grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-24 items-center">
          <div>
            <h2 className="text-[2.5rem] font-bold text-slate-900 mb-6 leading-tight">Restraint is the ultimate sophistication.</h2>
            <p className="text-slate-500 mb-10 text-[15px] leading-relaxed pr-10">
              Join 500+ elite law firms receiving our monthly dispatch on the intersection of architectural design and legal technology.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <input 
                type="email" 
                placeholder="Your professional email" 
                className="bg-[#F1F5F9] text-slate-900 placeholder:text-slate-500 px-6 py-4 rounded-xl flex-1 outline-none target:border-transparent focus:ring-2 focus:ring-blue-500/40 transition-all text-[15px]"
              />
              <button className="bg-[#3b5fe5] hover:bg-[#3451c7] transition-colors text-white px-8 py-4 rounded-xl font-medium text-[15px] whitespace-nowrap shadow-sm">
                Subscribe
              </button>
            </div>
          </div>

          <div className="bg-[#F8FAFC] border border-slate-100/50 rounded-3xl p-10 md:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
            <div className="text-blue-100 mb-8">
              <Quote size={40} className="fill-blue-50" />
            </div>
            <p className="text-[17px] font-semibold text-slate-800 italic leading-relaxed mb-10 font-serif">
              "ALAS has redefined our drafting process. It provides the structural integrity we need without the noise of typical legal platforms."
            </p>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-slate-200 rounded-lg overflow-hidden border border-slate-300/50 shadow-sm">
                {/* dummy portrait */}
                <img src={`https://ui-avatars.com/api/?name=Julian+Thorne&background=475569&color=fff&size=100`} alt="Julian Thorne" className="w-full h-full object-cover" />
              </div>
              <div className="flex flex-col gap-0.5">
                <h4 className="font-bold text-slate-900 text-sm">Julian Thorne</h4>
                <p className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">MANAGING PARTNER, THORNE & ASSOC.</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-32 bg-white">
        <div className="max-w-[1400px] mx-auto px-8 lg:px-16 py-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="font-bold tracking-tight text-slate-900 text-lg">
            ALAS
          </div>
          
          <div className="flex flex-wrap justify-center gap-10 text-[13px] font-medium text-slate-500">
            <Link href="#" className="hover:text-slate-900 transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-slate-900 transition-colors">Terms of Service</Link>
            <Link href="#" className="hover:text-slate-900 transition-colors">AI Ethics</Link>
            <Link href="#" className="hover:text-slate-900 transition-colors">Contact Support</Link>
          </div>

          <div className="text-[13px] text-slate-400">
            © 2024 ALAS. Professionalism through Precision.
          </div>
        </div>
      </footer>
    </div>
  );
}
