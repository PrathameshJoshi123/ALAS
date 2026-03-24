"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { Check, CheckCircle2, ChevronDown, Layers, Building2, Loader2, Play, User } from "lucide-react";
import Cookies from "js-cookie";

export default function SignupPage() {
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<'firm' | 'user'>('firm');
  const [tenants, setTenants] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    firm_name: "",
    industry: "",
    address: "",
    first_name: "",
    last_name: "",
    email: "",
    password: "", 
    subscription_tier: "free",
    selected_tenant_id: "", // For user registration
  });
  
  const [loading, setLoading] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    // Read URL search params
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab");
      if (tab === "user") setActiveTab("user");
      else if (tab === "firm") setActiveTab("firm");
    }

    // Fetch tenants for the User registration dropdown
    const fetchTenants = async () => {
      try {
        const data = await apiClient.getTenants();
        setTenants(data || []);
      } catch (error) {
        console.error("Failed to fetch tenants", error);
      }
    };
    fetchTenants();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleTierSelect = (tier: string) => {
    setFormData((prev) => ({
      ...prev,
      subscription_tier: tier,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!agreed) {
      toast.error("Please agree to the Terms of Service and Privacy Policy.");
      return;
    }

    if (activeTab === 'firm' && !formData.firm_name) {
      toast.error("Firm Name is required.");
      return;
    }

    if (activeTab === 'user' && !formData.selected_tenant_id) {
       toast.error("Please select a Firm to join.");
       return;
    }

    if (!formData.first_name || !formData.last_name || !formData.email || !formData.password) {
      toast.error("Please fill in all user profile fields.");
      return;
    }

    setLoading(true);

    try {
      const name = `${formData.first_name} ${formData.last_name}`.trim();
      let response;

      if (activeTab === 'firm') {
        response = await apiClient.signup({
          name: name,
          email: formData.email,
          password: formData.password,
          company_name: formData.firm_name,
          industry: formData.industry,
          subscription_tier: formData.subscription_tier,
        });
      } else {
        response = await apiClient.registerUser({
          tenant_id: formData.selected_tenant_id,
          name: name,
          email: formData.email,
          password: formData.password,
        });
      }

      const { access_token, refresh_token, user } = response;

      Cookies.set("access_token", access_token);
      Cookies.set("refresh_token", refresh_token);
      setUser(user);

      toast.success(
        activeTab === "firm" ? `Workspace created successfully! Welcome to ALAS.` : `Joined successfully! Welcome to ALAS.`,
        { duration: 4000 }
      );
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900 flex flex-col relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-full h-[600px] bg-gradient-to-br from-indigo-50/80 via-white/50 to-transparent -z-10" />
      <div className="absolute top-0 right-0 w-[800px] h-[600px] bg-blue-50/40 rounded-full blur-[100px] -z-10" />
      
      {/* Header */}
      <header className="w-full px-8 lg:px-12 py-8 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-[#0b1437] flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4 text-white">
               <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="font-bold text-2xl tracking-tight text-slate-900">
            ALAS
          </span>
        </Link>
        <div className="text-[13px] font-medium text-slate-600">
          Already have an account? <Link href="/auth/login" className="text-slate-900 font-bold hover:underline ml-1 tracking-wide">Sign In</Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-[1400px] mx-auto px-8 lg:px-12 flex flex-col lg:flex-row gap-16 lg:gap-24 items-start pt-6 pb-20">
        
        {/* Left Column (Info) */}
        <div className="flex-1 lg:max-w-lg mt-6 lg:mt-12">
          <p className="text-[#3b5fe5] font-bold text-[10px] tracking-[0.2em] uppercase mb-6">
            {activeTab === 'firm' ? 'Tenant Onboarding' : 'User Registration'}
          </p>
          <h1 className="text-4xl lg:text-[2.8rem] font-bold tracking-tight text-slate-900 mb-6 leading-[1.1]">
            Scale your practice with <span className="text-[#102B6D] italic">architectural</span> precision.
          </h1>
          <p className="text-[15px] text-slate-600 leading-relaxed max-w-[400px] mb-12">
            Join elite law firms using our AI-driven analysis platform to reduce contract review cycles by 70%.
          </p>

          <div className="space-y-8 mb-16">
            <div className="flex gap-4">
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-blue-600 stroke-[3]" />
              </div>
              <div>
                <h4 className="font-bold text-[14px] text-slate-900 mb-1">Enterprise-Grade Security</h4>
                <p className="text-[13px] text-slate-500">SOC2 Type II compliant document handling.</p>
              </div>
            </div>
            <div className="flex gap-4">
               <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-blue-600 stroke-[3]" />
              </div>
              <div>
                <h4 className="font-bold text-[14px] text-slate-900 mb-1">Collaborative Workspaces</h4>
                <p className="text-[13px] text-slate-500">Granular permissions for partners and associates.</p>
              </div>
            </div>
          </div>

          {/* Testimonial Card directly mimicking the image */}
          <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-[#030e21] text-white p-8 group">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 to-[#030e21] opacity-70"></div>
            <div className="absolute top-1/2 left-3/4 -translate-y-1/2 -translate-x-1/2 w-64 h-64 rounded-full border border-blue-500/20 shadow-[0_0_40px_rgba(59,130,246,0.3)]"></div>
            <div className="absolute top-1/2 left-3/4 -translate-y-1/2 -translate-x-1/2 w-48 h-48 rounded-full border border-blue-400/30"></div>
            <div className="absolute top-1/2 left-3/4 -translate-y-1/2 -translate-x-1/2 w-32 h-32 rounded-full border border-blue-300/40"></div>
            
            <div className="relative z-10 pt-16 mt-4">
              <p className="text-[15px] font-medium leading-relaxed italic mb-4 font-serif text-slate-200">
                “ALAS has redefined how we process complex M&A documents.”
              </p>
              <p className="text-xs text-slate-400 font-medium">
                — Managing Partner, Lexington & Co.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column (Form) */}
        <div className="flex-1 w-full max-w-[650px] bg-white rounded-xl shadow-[0_8px_40px_rgba(0,0,0,0.03)] border border-slate-100 p-10 lg:p-14 mb-10">
          
          {/* Tabs */}
          <div className="flex items-center gap-6 mb-12 border-b border-slate-200">
            <button 
              onClick={() => setActiveTab('firm')}
              className={`pb-4 text-[13px] font-bold uppercase tracking-wider transition-colors ${activeTab === 'firm' ? 'text-[#102B6D] border-b-2 border-[#102B6D]' : 'text-slate-400 hover:text-slate-600'}`}
            >
              Register Firm
            </button>
            <button 
              onClick={() => setActiveTab('user')}
              className={`pb-4 text-[13px] font-bold uppercase tracking-wider transition-colors ${activeTab === 'user' ? 'text-[#102B6D] border-b-2 border-[#102B6D]' : 'text-slate-400 hover:text-slate-600'}`}
            >
              Join Existing Firm
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-12">
            
            {activeTab === 'firm' && (
               <section>
                 <div className="border-l-[3px] border-slate-900 pl-4 mb-8">
                   <h2 className="text-[19px] font-bold text-slate-900 mb-1">Organization Profile</h2>
                   <p className="text-[12px] text-slate-500">Tell us about your law firm or legal department.</p>
                 </div>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                   <div>
                     <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Firm Name</label>
                     <input 
                       type="text" 
                       name="firm_name"
                       required={activeTab === 'firm'}
                       value={formData.firm_name}
                       onChange={handleChange}
                       placeholder="e.g. Pearson Hardman LLP" 
                       className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                     />
                   </div>
                   <div>
                     <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Industry Focus</label>
                     <input 
                       type="text" 
                       name="industry"
                       value={formData.industry}
                       onChange={handleChange}
                       placeholder="e.g. Healthcare, Finance..." 
                       className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                     />
                   </div>
                 </div>
                 <div>
                    <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Headquarters Address</label>
                    <input 
                       type="text" 
                       name="address"
                       value={formData.address}
                       onChange={handleChange}
                       placeholder="Street, City, Country" 
                       className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                     />
                 </div>
               </section>
            )}

            {activeTab === 'user' && (
               <section>
                 <div className="border-l-[3px] border-slate-900 pl-4 mb-8">
                   <h2 className="text-[19px] font-bold text-slate-900 mb-1">Organization Details</h2>
                   <p className="text-[12px] text-slate-500">Select the firm you belong to.</p>
                 </div>
                 <div>
                    <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Select Your Firm</label>
                    <div className="relative">
                      <select 
                        name="selected_tenant_id"
                        value={formData.selected_tenant_id}
                        onChange={handleChange}
                        required={activeTab === 'user'}
                        className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none cursor-pointer bg-white"
                      >
                        <option value="" disabled>Select a Firm</option>
                        {tenants.map((t) => (
                           <option key={t.id} value={t.id}>{t.company_name}</option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                    </div>
                 </div>
               </section>
            )}

            {/* Section 2: Primary Administrator / User Profile */}
            <section>
              <div className="border-l-[3px] border-slate-900 pl-4 mb-8">
                <h2 className="text-[19px] font-bold text-slate-900 mb-1">{activeTab === 'firm' ? 'Primary Administrator' : 'Your Profile'}</h2>
                <p className="text-[12px] text-slate-500">{activeTab === 'firm' ? 'The person responsible for managing the account.' : 'Your personal account details.'}</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                 <div>
                  <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">First Name</label>
                  <input 
                    type="text" 
                    name="first_name"
                    required
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder="John" 
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Last Name</label>
                  <input 
                    type="text" 
                    name="last_name"
                    required
                    value={formData.last_name}
                    onChange={handleChange}
                    placeholder="Doe" 
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                  />
                </div>
              </div>
              <div className="mb-6">
                 <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Professional Email</label>
                 <input 
                    type="email" 
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="john.doe@firm.com" 
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                  />
              </div>
              <div>
                 <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Account Password</label>
                 <input 
                    type="password" 
                    name="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••" 
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg text-[13px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-300"
                  />
              </div>
            </section>

            {/* Section 3: Select Workspace Tier (Firm Only) */}
            {activeTab === 'firm' && (
               <section>
                 <div className="border-l-[3px] border-slate-900 pl-4 mb-8">
                   <h2 className="text-[19px] font-bold text-slate-900 mb-1">Select Workspace Tier</h2>
                   <p className="text-[12px] text-slate-500">Choose the volume that fits your firm's caseload.</p>
                 </div>
                 
                 <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                   {/* Free Tier */}
                   <div 
                     onClick={() => handleTierSelect("free")}
                     className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all flex flex-col justify-between ${formData.subscription_tier === 'free' ? 'border-[#3b5fe5] bg-[#Eef3FE]' : 'border-slate-100 bg-white hover:border-slate-200'}`}
                   >
                     <div>
                       <User className={`w-5 h-5 mb-4 ${formData.subscription_tier === 'free' ? 'text-[#102B6D]' : 'text-slate-400'}`} />
                       <h3 className="text-[14px] font-bold text-slate-900 mb-1">Free Tier</h3>
                       <p className="text-[11px] text-slate-500 mb-4">Basic analysis</p>
                     </div>
                     <div className="flex items-baseline gap-1 mt-auto">
                        <span className="text-[20px] font-bold text-slate-900">$0</span>
                        <span className="text-[11px] text-slate-500">/month</span>
                     </div>
                   </div>

                   {/* Associate Tier */}
                   <div 
                     onClick={() => handleTierSelect("associate")}
                     className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all flex flex-col justify-between ${formData.subscription_tier === 'associate' ? 'border-[#3b5fe5] bg-[#Eef3FE]' : 'border-slate-100 bg-white hover:border-slate-200'}`}
                   >
                     {formData.subscription_tier === 'associate' && (
                        <div className="absolute top-3 right-3 bg-[#102B6D] text-white text-[8px] font-bold uppercase tracking-wider px-2 py-1 rounded">
                          Popular
                        </div>
                     )}
                     <div>
                       <Layers className={`w-5 h-5 mb-4 ${formData.subscription_tier === 'associate' ? 'text-[#102B6D]' : 'text-slate-400'}`} />
                       <h3 className="text-[14px] font-bold text-slate-900 mb-1">Associate</h3>
                       <p className="text-[11px] text-slate-500 mb-4">Up to 50 docs/mo</p>
                     </div>
                     <div className="flex items-baseline gap-1 mt-auto">
                        <span className="text-[20px] font-bold text-slate-900">$299</span>
                        <span className="text-[11px] text-slate-500">/mo</span>
                     </div>
                   </div>

                   {/* Partner Tier */}
                   <div 
                     onClick={() => handleTierSelect("partner")}
                     className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all flex flex-col justify-between ${formData.subscription_tier === 'partner' ? 'border-[#3b5fe5] bg-[#Eef3FE]' : 'border-slate-100 bg-white hover:border-slate-200'}`}
                   >
                     <div>
                       <Building2 className={`w-5 h-5 mb-4 ${formData.subscription_tier === 'partner' ? 'text-[#102B6D]' : 'text-slate-400'}`} />
                       <h3 className="text-[14px] font-bold text-slate-900 mb-1">Partner</h3>
                       <p className="text-[11px] text-slate-500 mb-4">Unlimited docs</p>
                     </div>
                     <div className="flex items-baseline gap-1 mt-auto">
                        <span className="text-[20px] font-bold text-slate-900">$899</span>
                        <span className="text-[11px] text-slate-500">/mo</span>
                     </div>
                   </div>
                 </div>
               </section>
            )}

            {/* Submit & Terms */}
            <div className="pt-6 border-t border-slate-100 flex flex-col md:flex-row items-center justify-between gap-6">
               <label className="flex items-start gap-3 cursor-pointer group flex-1">
                 <div className="relative flex items-center justify-center shrink-0 w-4 h-4 mt-0.5">
                   <input 
                     type="checkbox" 
                     className="peer appearance-none w-4 h-4 border border-slate-300 rounded-sm bg-white checked:bg-blue-600 checked:border-blue-600 transition-colors"
                     checked={agreed}
                     onChange={(e) => setAgreed(e.target.checked)}
                   />
                   <Check className="w-3 h-3 text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100" strokeWidth={3} />
                 </div>
                 <span className="text-[11px] text-slate-500 leading-relaxed max-w-[200px]">
                   I agree to the <a href="#" className="font-semibold text-slate-700 hover:text-blue-600 transition-colors underline decoration-slate-300 underline-offset-2">Terms of Service</a> and <a href="#" className="font-semibold text-slate-700 hover:text-blue-600 transition-colors underline decoration-slate-300 underline-offset-2">Privacy Policy</a>.
                 </span>
               </label>
               
               <button 
                 type="submit"
                 disabled={loading}
                 className="w-full md:w-auto px-8 py-3.5 bg-[#102B6D] hover:bg-[#0a1b46] disabled:bg-blue-300 text-white rounded-lg text-[13px] font-bold shadow-[0_4px_14px_rgba(16,43,109,0.3)] transition-all flex items-center justify-center gap-2"
               >
                 {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                 {loading ? "Processing..." : (activeTab === 'firm' ? "Create Firm Workspace" : "Join Firm")}
               </button>
            </div>
          </form>

        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-200/60 bg-[#F4F7FB] py-6 px-8 lg:px-12">
         <div className="max-w-[1400px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-slate-200 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" className="w-[10px] h-[10px] text-slate-600">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span className="font-bold text-[16px] tracking-tight text-slate-900">
                ALAS
              </span>
            </div>
            
            <div className="flex gap-8 text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase">
              <Link href="#" className="hover:text-slate-900 transition-colors">Help Center</Link>
              <Link href="#" className="hover:text-slate-900 transition-colors">Security</Link>
              <Link href="#" className="hover:text-slate-900 transition-colors">API Docs</Link>
            </div>

            <div className="text-[11px] text-slate-400">
              © 2024 ALAS. Professionalism through Precision.
            </div>
         </div>
      </footer>
    </div>
  );
}
