import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CaseHunter AI",
  description: "AI-assisted story production studio",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
