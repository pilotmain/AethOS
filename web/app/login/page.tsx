"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { fetchAuthSession } from "@/lib/onboarding/tenantSetup";

/** Public login entry — AethosGate renders TenantAuthCard when unauthenticated. */

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    void fetchAuthSession().then((session) => {
      // Next.js basePath prepends /aethos automatically — bare app path only.
      if (session?.authenticated) router.replace("/");
    });
  }, [router]);

  return null;
}
