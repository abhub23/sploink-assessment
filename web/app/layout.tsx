import "./globals.css";

export const metadata = {
  title: "Agent Monitoring",
  description: "Monitor AI agent activity",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  );
}