import type { ReactNode } from "react";

import { AppShell } from "../components/app-shell";
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
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
