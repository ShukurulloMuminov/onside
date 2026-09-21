"use client";

import Script from "next/script";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

interface GoogleCredentialResponse {
  credential: string;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export default function GoogleSignInButton() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  if (!CLIENT_ID) {
    // Sign-in with Google isn't configured yet — hide the button rather
    // than show a broken control. See README for the one-time Google
    // Cloud Console setup step.
    return null;
  }

  async function handleCredential(response: GoogleCredentialResponse) {
    setError(null);
    const res = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: response.credential }),
    });
    if (!res.ok) {
      setError("Google orqali kirishda xatolik yuz berdi.");
      return;
    }
    router.push("/dashboard");
    router.refresh();
  }

  function handleScriptLoad() {
    if (!window.google || !containerRef.current) return;
    window.google.accounts.id.initialize({
      client_id: CLIENT_ID!,
      callback: handleCredential,
    });
    window.google.accounts.id.renderButton(containerRef.current, {
      theme: "outline",
      size: "large",
      width: 320,
      text: "continue_with",
    });
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex w-full items-center gap-3 text-xs text-muted">
        <span className="h-px flex-1 bg-border" />
        yoki
        <span className="h-px flex-1 bg-border" />
      </div>
      <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" onLoad={handleScriptLoad} />
      <div ref={containerRef} />
      {error ? <p className="text-sm text-loss">{error}</p> : null}
    </div>
  );
}
