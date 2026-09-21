import { initials } from "@/lib/format";
import { resolveMediaUrl } from "@/lib/media";

const COLORS = ["bg-blue", "bg-navy", "bg-win", "bg-draw"];

function colorFor(name: string): string {
  const sum = name.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return COLORS[sum % COLORS.length];
}

export default function Avatar({
  src,
  name,
  size = 40,
  rounded = "full",
}: {
  src?: string | null;
  name: string;
  size?: number;
  rounded?: "full" | "md";
}) {
  const url = resolveMediaUrl(src);
  const radius = rounded === "full" ? "rounded-full" : "rounded-md";

  if (url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={url}
        alt={name}
        width={size}
        height={size}
        className={`${radius} object-cover`}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-center ${radius} ${colorFor(name)} font-semibold text-white`}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {initials(name) || "?"}
    </div>
  );
}
