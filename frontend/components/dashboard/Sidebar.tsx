"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileText, Users, Copy, TrendingUp, BookOpen, HelpCircle, LogOut, Briefcase } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/services/api";
import toast from "react-hot-toast";

const navItems = [
  { href: "/dashboard", label: "My Contracts", icon: FileText },
  { href: "/dashboard/tenant-files", label: "Tenant Files", icon: Users },
  { href: "/dashboard/templates", label: "Templates", icon: Copy },
  { href: "/dashboard/risk-reports", label: "Risk Reports", icon: TrendingUp },
  { href: "/dashboard/legal-library", label: "Legal Library", icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      if (user) await apiClient.logout(user.id, user.tenant_id);
      logout();
      router.push("/auth/login");
    } catch (error) {
      toast.error("Logout failed");
    }
  };

  return (
    <aside className="w-[260px] bg-[#F4F7FB] border-r border-[#E2E8F0] flex flex-col shrink-0 h-full overflow-hidden">
      {/* Firm & User Info */}
      <div className="p-8 pb-6">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-11 h-11 rounded bg-[#0B1437] flex items-center justify-center shrink-0">
            <Briefcase className="w-5 h-5 text-white" strokeWidth={2} />
          </div>
          <div className="overflow-hidden">
            <h3 className="font-bold text-[14px] text-slate-900 truncate">Lexington & Co</h3>
            <p className="text-[12px] text-slate-500 font-medium truncate">Senior Associate</p>
          </div>
        </div>

        {/* Upload Button */}
        <Link href="/dashboard" className="w-full bg-[#0B1437] text-white rounded-xl py-3.5 px-4 flex items-center justify-center gap-2 text-[13px] font-bold hover:bg-[#152458] transition shadow-md">
          <FileText className="w-4 h-4" />
          Upload Contract
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-8 py-2 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href === "/dashboard/my-contracts" && pathname === "/dashboard");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 py-2.5 text-[13px] font-bold transition-colors ${
                isActive
                  ? "text-[#0B1437]"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <Icon className="w-[18px] h-[18px]" strokeWidth={2.5} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="p-8 mt-auto space-y-5 border-t border-slate-200/60 bg-[#F4F7FB]">
        <button className="flex items-center gap-3 w-full text-[13px] font-bold text-slate-500 hover:text-slate-900 transition">
          <HelpCircle className="w-[18px] h-[18px]" strokeWidth={2.5} />
          Help Center
        </button>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 w-full text-[13px] font-bold text-red-500 hover:text-red-700 transition"
        >
          <LogOut className="w-[18px] h-[18px]" strokeWidth={2.5} />
          Log Out
        </button>
      </div>
    </aside>
  );
}
