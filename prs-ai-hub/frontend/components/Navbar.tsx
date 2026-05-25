import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/submit", label: "Submit PRS" },
  { href: "/enterprise", label: "Enterprise" },
  { href: "/pilot/intake", label: "Intake pilot" },
  { href: "/supplier", label: "Supplier" },
  { href: "/pilot/approvals", label: "Approvals" },
  { href: "/ccr", label: "CCR" },
  { href: "/history", label: "History" },
];

export function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-lg font-bold text-brand-700">
        Viziant AI Hub
        </Link>
        <nav className="flex gap-6 text-sm font-medium text-slate-600">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="transition-colors hover:text-brand-700"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
