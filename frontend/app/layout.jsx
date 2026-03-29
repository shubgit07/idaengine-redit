import "./globals.css";

export const metadata = {
  title: "RedEngine Dashboard",
  description: "Pain point intelligence feed",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
