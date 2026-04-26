"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Settings } from "lucide-react";

export default function Header() {
  const pathname = usePathname();

  const tabs = [
    { name: "Dashboard", href: "/dashboard" },
    { name: "Documents", href: "/dashboard/tenant-files" },
    { name: "Analysis", href: "/dashboard/analysis" },
    { name: "Archive", href: "/dashboard/archive" },
  ];

  return (
    <header className="h-[70px] bg-white border-b border-slate-100 px-6 lg:px-10 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-12 h-full">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="font-bold text-[18px] tracking-tight text-slate-900">
            ALAS
          </span>
        </Link>

        {/* Top Tabs */}
        <nav className="hidden md:flex h-full items-end gap-8">
          {tabs.map((tab) => {
            const isActive = pathname === tab.href || (tab.href !== "/dashboard" && pathname.startsWith(tab.href));
            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={`text-[13px] font-bold tracking-wide pb-4 border-b-[3px] transition-colors ${
                  isActive
                    ? "text-[#3b5fe5] border-[#3b5fe5]"
                    : "text-slate-500 border-transparent hover:text-slate-800 hover:border-slate-200"
                }`}
              >
                {tab.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Right icons */}
      <div className="flex items-center gap-5">
        <button className="text-slate-400 hover:text-slate-600 transition relative">
          <Bell className="w-[18px] h-[18px]" strokeWidth={2.5} />
        </button>
        <button className="text-slate-400 hover:text-slate-600 transition">
          <Settings className="w-[18px] h-[18px]" strokeWidth={2.5} />
        </button>
        <button className="w-8 h-8 rounded-full overflow-hidden border border-slate-300 ml-2">
          {/* Avatar placeholder */}
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=Eef3FE" alt="Avatar" className="w-full h-full object-cover" />
        </button>
      </div>
    </header>
  );
}
