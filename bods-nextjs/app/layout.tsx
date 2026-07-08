import type { Metadata } from "next";
import "./govuk.scss";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/jwt-auth";
import { GDSProvider } from "@/components/gds/GDSProvider";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PhaseBanner } from "@/components/layout/PhaseBanner";

export const metadata: Metadata = {
  title: "Bus Open Data Service",
  description: "Bus Open Data Service - BODS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="govuk-template govuk-template--rebranded">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="blue" />
      </head>
      <body className="govuk-template__body js-enabled govuk-frontend-supported">
        <AuthProvider>
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
        </AuthProvider>
      </body>
    </html>
  );
}
