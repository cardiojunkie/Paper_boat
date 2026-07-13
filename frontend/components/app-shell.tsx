"use client";

import {
  Boxes,
  CircleHelp,
  Menu,
  MessageSquareText,
  RefreshCw,
  Settings,
  Upload,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useState } from "react";

const links = [
  { href: "/products", label: "All Products", icon: Boxes },
  { href: "/matches/review", label: "Pending Review", icon: MessageSquareText },
  { href: "/matches/confirmed", label: "Marketplace Sync", icon: RefreshCw },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="shell">
      <button className="mobile-menu" aria-label="Open navigation" onClick={() => setOpen(true)}>
        <Menu size={20} />
      </button>
      {open && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <aside className={`sidebar${open ? " open" : ""}`}>
        <div className="sidebar-brand">
          <span className="brand-mark">
            <Boxes size={19} />
          </span>
          <span>
            <strong>Operations</strong>
            <small>Ecommerce Hub</small>
          </span>
          <button className="sidebar-close" aria-label="Close navigation" onClick={() => setOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <Link className="sidebar-upload" href="/products#import-products" onClick={() => setOpen(false)}>
          <Upload size={16} /> Upload Excel
        </Link>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {links.map(({ href, label, icon: Icon }) => {
            const active = href === "/products" ? pathname === "/" || pathname.startsWith("/products") : pathname.startsWith(href);
            return (
              <Link
                key={href}
                className={active ? "active" : ""}
                href={href}
                aria-current={active ? "page" : undefined}
                onClick={() => setOpen(false)}
              >
                <Icon size={18} /> {label}
              </Link>
            );
          })}
          <Link href="/products#llm-settings" onClick={() => setOpen(false)}>
            <Settings size={18} /> LLM Settings
          </Link>
        </nav>

        <div className="sidebar-footer">
          <span>
            <CircleHelp size={18} /> Internal workspace
          </span>
        </div>
      </aside>
      <div className="app-main">{children}</div>
    </div>
  );
}
