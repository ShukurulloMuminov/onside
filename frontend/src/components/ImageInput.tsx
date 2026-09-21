"use client";

import { ChangeEvent, useState } from "react";

import Avatar from "./Avatar";

export default function ImageInput({
  label,
  name,
  currentUrl,
  fallbackName,
  rounded = "full",
  onChange,
}: {
  label: string;
  name: string;
  currentUrl?: string | null;
  fallbackName: string;
  rounded?: "full" | "md";
  onChange: (file: File | null) => void;
}) {
  const [preview, setPreview] = useState<string | null>(null);

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    onChange(file);
    if (file) {
      setPreview(URL.createObjectURL(file));
    } else {
      setPreview(null);
    }
  }

  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <div className="flex items-center gap-3">
        <Avatar src={preview ?? currentUrl} name={fallbackName} size={56} rounded={rounded} />
        <input
          type="file"
          name={name}
          accept="image/*"
          onChange={handleChange}
          className="block flex-1 text-sm text-muted file:mr-3 file:rounded-full file:border-0 file:bg-blue-light file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-dark hover:file:opacity-90"
        />
      </div>
    </label>
  );
}
