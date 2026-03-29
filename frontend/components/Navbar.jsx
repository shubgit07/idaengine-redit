import Badge from "@/components/Badge";

export default function Navbar() {
  return (
    <header className="sticky top-4 z-20 mb-7">
      <nav className="mx-auto flex w-full max-w-[1180px] items-center justify-between rounded-[1.6rem] border border-white/10 bg-slate-900/60 px-4 py-3 shadow-glow backdrop-blur-xl sm:px-5">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 text-sm font-extrabold text-slate-950">
            RE
          </div>
          <div>
            <p className="text-sm font-semibold tracking-wide text-slate-100">RedEngine</p>
            <p className="text-xs text-slate-400">Opportunity Intelligence</p>
          </div>
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <Badge tone="accent">Live Feed</Badge>
          <Badge>Dashboard</Badge>
        </div>
      </nav>
    </header>
  );
}
