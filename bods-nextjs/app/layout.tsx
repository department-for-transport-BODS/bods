import { headers } from "next/headers";
import type { Metadata } from "next";
import "./govuk.scss";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/session-auth";
import { HostProvider } from "@/lib/bods-host-context";
import { GDSProvider } from "@/components/gds/GDSProvider";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PhaseBanner } from "@/components/layout/PhaseBanner";
import { hostnameFromHeaders } from "@/config/hosts";

export const metadata: Metadata = {
  title: "Bus Open Data Service",
  description: "Bus Open Data Service - BODS",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const requestHeaders = await headers();
  const hostname = hostnameFromHeaders(
    requestHeaders.get("host"),
    requestHeaders.get("x-forwarded-host"),
  );

  return (
    <html lang="en" className="govuk-template govuk-template--rebranded">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="blue" />
      </head>
      <body className="govuk-template__body js-enabled govuk-frontend-supported">
        <AuthProvider>
          <HostProvider hostname={hostname}>
            <GDSProvider>
              <a href="#main-content" className="govuk-skip-link" data-module="govuk-skip-link">
                Skip to main content
              </a>
              <Header />
              <main id="main-content" role="main">
                <div className="govuk-width-container">
                  <PhaseBanner />
                </div>
                {children}
              </main>
              <Footer />
            </GDSProvider>
          </HostProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
