import Link from "next/link";
import type { ReactNode } from "react";

import { Providers } from "../components/providers";
import "./globals.css";

export const metadata = {
  title: "PickPilot Products",
  description: "Internal product ingestion dashboard",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="shell">
            <header className="topbar">
              <Link href="/products" className="brand">
                PickPilot
              </Link>
              <nav className="nav">
                <Link href="/products">Products</Link>
              </nav>
            </header>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
