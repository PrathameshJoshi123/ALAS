"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { Check, ChevronDown, Loader2 } from "lucide-react";
import Cookies from "js-cookie";

export default function LoginPage() {
  const router = useRouter();
  
  const [tenants, setTenants] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    tenant_id: "",
    email: "",
    password: "", 
  });
  
  const [loading, setLoading] = useState(false);
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    // Fetch tenants for the login dropdown
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

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.tenant_id) {
       toast.error("Please select a Firm to sign in.");
       return;
    }

    if (!formData.email || !formData.password) {
      toast.error("Please fill in email and password.");
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.login(formData.email, formData.password, formData.tenant_id);
      const { access_token, refresh_token, user } = response;

      Cookies.set("access_token", access_token);
      Cookies.set("refresh_token", refresh_token);
      setUser(user);

      toast.success("Login successful!", { duration: 4000 });
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Login failed. Please check your credentials."
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
          Don't have an account? <Link href="/auth/signup" className="text-slate-900 font-bold hover:underline ml-1 tracking-wide">Sign Up</Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-[1400px] mx-auto px-8 lg:px-12 flex flex-col lg:flex-row gap-16 lg:gap-24 items-center justify-center pt-6 pb-20">
        
        {/* Left Column (Info) */}
        <div className="flex-1 w-full max-w-lg hidden lg:block">
          <p className="text-[#3b5fe5] font-bold text-[10px] tracking-[0.2em] uppercase mb-6">
            Secure Authentication
          </p>
          <h1 className="text-4xl lg:text-[2.8rem] font-bold tracking-tight text-slate-900 mb-6 leading-[1.1]">
            Access your <span className="text-[#102B6D] italic">intelligent</span> workspaces.
          </h1>
          <p className="text-[15px] text-slate-600 leading-relaxed max-w-[400px] mb-12">
            Log in to manage your legal documentation, collaborate with your firm, and review AI insights safely.
          </p>

          <div className="space-y-8 mb-16">
            <div className="flex gap-4">
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-blue-600 stroke-[3]" />
              </div>
              <div>
                <h4 className="font-bold text-[14px] text-slate-900 mb-1">SOC2 Type II Protected</h4>
                <p className="text-[13px] text-slate-500">Industry-leading data encryption.</p>
              </div>
            </div>
            <div className="flex gap-4">
               <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-blue-600 stroke-[3]" />
              </div>
              <div>
                <h4 className="font-bold text-[14px] text-slate-900 mb-1">Synchronized Continuity</h4>
                <p className="text-[13px] text-slate-500">Pick up right where you left off.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (Form) */}
        <div className="flex-1 w-full max-w-[500px] bg-white rounded-xl shadow-[0_8px_40px_rgba(0,0,0,0.03)] border border-slate-100 p-10 lg:p-12 mb-10 shrink-0">
          
          <div className="mb-10 text-center lg:text-left">
            <h2 className="text-[24px] font-bold text-slate-900 mb-2">Welcome Back</h2>
            <p className="text-[13px] text-slate-500">Sign in to your ALAS account.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            
            <section>
                <div className="mb-6">
                  <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase mb-2">Select Your Firm</label>
                  <div className="relative">
                    <select 
                      name="tenant_id"
                      value={formData.tenant_id}
                      onChange={handleChange}
                      required
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
              
              <div className="mb-6">
                 <div className="flex items-center justify-between mb-2">
                    <label className="block text-[10px] font-bold tracking-[0.1em] text-slate-500 uppercase">Account Password</label>
                    <Link href="/auth/forgot-password" className="text-[11px] font-bold text-blue-600 hover:text-blue-800 transition-colors">Forgot?</Link>
                 </div>
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

               <label className="flex items-center gap-3 cursor-pointer group mb-2">
                 <div className="relative flex items-center justify-center shrink-0 w-4 h-4">
                   <input 
                     type="checkbox" 
                     className="peer appearance-none w-4 h-4 border border-slate-300 rounded-sm bg-white checked:bg-blue-600 checked:border-blue-600 transition-colors"
                   />
                   <Check className="w-3 h-3 text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100" strokeWidth={3} />
                 </div>
                 <span className="text-[12px] font-medium text-slate-600">
                   Remember me
                 </span>
               </label>
            </section>

            {/* Submit */}
            <div className="pt-2">
               <button 
                 type="submit"
                 disabled={loading}
                 className="w-full px-8 py-3.5 bg-[#102B6D] hover:bg-[#0a1b46] disabled:bg-blue-300 text-white rounded-lg text-[13px] font-bold shadow-[0_4px_14px_rgba(16,43,109,0.3)] transition-all flex items-center justify-center gap-2"
               >
                 {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                 {loading ? "Authenticating..." : "Sign In to Workspace"}
               </button>
            </div>
          </form>

        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-200/60 bg-[#F4F7FB] py-6 px-8 lg:px-12 mt-auto">
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
