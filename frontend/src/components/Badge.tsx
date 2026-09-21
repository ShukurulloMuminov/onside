const TONE_CLASSES = {
  neutral: "bg-blue-light text-blue-dark ring-1 ring-inset ring-blue/10",
  win: "bg-green-50 text-win ring-1 ring-inset ring-win/15",
  draw: "bg-amber-50 text-draw ring-1 ring-inset ring-draw/15",
  loss: "bg-red-50 text-loss ring-1 ring-inset ring-loss/15",
  navy: "bg-navy text-white",
};

export default function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: keyof typeof TONE_CLASSES;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
