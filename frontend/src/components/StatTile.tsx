export default function StatTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card p-4 text-center transition hover:border-blue/30">
      <p className="text-2xl font-extrabold tracking-tight text-navy">{value}</p>
      <p className="mt-0.5 text-xs font-medium text-muted">{label}</p>
    </div>
  );
}
