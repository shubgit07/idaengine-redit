export default function SkeletonCard() {
  return (
    <article className="animate-pulse overflow-hidden rounded-[1.35rem] border border-[#2e2417] bg-[#13100e] shadow-[0_0_0_1px_rgba(255,176,76,0.06),0_22px_42px_rgba(0,0,0,0.42)]">
      <div className="px-5 pb-4 pt-4 sm:px-7">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex gap-2">
            <div className="h-7 w-28 rounded-full bg-[#2a231d]" />
            <div className="h-7 w-20 rounded-full bg-[#3a4d6e]" />
          </div>
          <div className="h-7 w-20 rounded-full bg-[#2f1a1a]" />
        </div>

        <div className="mb-3 h-7 w-3/4 rounded bg-[#2a241d]" />

        <div className="mb-2 flex items-center gap-3">
          <div className="h-[6px] flex-1 rounded-full bg-[#272727]">
            <div className="h-full w-3/4 rounded-full bg-[#4c1f25]" />
          </div>
          <div className="h-5 w-14 rounded bg-[#2a241d]" />
        </div>
      </div>

      <div className="h-px bg-[#2a231c]" />

      <div className="grid md:grid-cols-2">
        <div className="px-5 py-4 sm:px-7">
          <div className="mb-3 h-4 w-44 rounded bg-[#2a241d]" />

          <div className="rounded-2xl border border-[#25211d] bg-[#181513] p-4">
            <div className="mb-2 h-4 w-full rounded bg-[#2a241d]" />
            <div className="mb-2 h-4 w-11/12 rounded bg-[#2a241d]" />
            <div className="mb-3 h-4 w-10/12 rounded bg-[#2a241d]" />

            <div className="flex items-center justify-between gap-2">
              <div className="h-4 w-28 rounded bg-[#2a241d]" />
              <div className="h-4 w-24 rounded bg-[#2a241d]" />
            </div>
          </div>
        </div>

        <div className="border-t border-[#2a231c] px-5 py-4 md:border-l md:border-t-0 sm:px-7">
          <div className="mb-3 h-4 w-28 rounded bg-[#2a241d]" />

          <div className="rounded-2xl border border-[#65481d] bg-[#2a1f12] p-4">
            <div className="mb-2 h-6 w-1/2 rounded bg-[#3a2d1d]" />
            <div className="h-4 w-full rounded bg-[#3a2d1d]" />
            <div className="mt-2 h-4 w-11/12 rounded bg-[#3a2d1d]" />
            <div className="mt-2 h-4 w-10/12 rounded bg-[#3a2d1d]" />

            <div className="mt-3 border-t border-[#4b3923] pt-3">
              <div className="h-3 w-10/12 rounded bg-[#3a2d1d]" />
              <div className="mt-2 h-3 w-full rounded bg-[#3a2d1d]" />
              <div className="mt-2 h-3 w-6/12 rounded bg-[#3a2d1d]" />
            </div>
          </div>
        </div>
      </div>

    </article>
  );
}
