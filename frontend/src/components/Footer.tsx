export default function Footer() {
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-sm text-muted sm:flex-row sm:px-6">
        <p>&copy; {new Date().getFullYear()} OnSide.uz — havaskor futbol platformasi</p>
        <p>Futbolchilar &middot; Jamoalar &middot; Turnirlar &middot; Statistika</p>
      </div>
    </footer>
  );
}
