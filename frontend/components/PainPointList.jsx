import { memo } from "react";

import PainPointCard from "@/components/PainPointCard";

function getItemKey(item) {
  return item.id || `${item.reddit_id}-${item.created_at}`;
}

function PainPointList({ items }) {
  return (
    <section className="grid gap-4">
      {items.map((item) => (
        <PainPointCard key={getItemKey(item)} item={item} />
      ))}
    </section>
  );
}

export default memo(PainPointList);
