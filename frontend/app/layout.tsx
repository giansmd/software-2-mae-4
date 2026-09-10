import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { ThemeProvider } from "@/lib/theme";
import { I18nProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "Gemelo Digital de Humedales Costeros",
  description:
    "Prototipo de gemelo digital para modelar la retención de carbono y la restauración de humedales costeros.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          <I18nProvider>
            <Navbar />
            {children}
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}