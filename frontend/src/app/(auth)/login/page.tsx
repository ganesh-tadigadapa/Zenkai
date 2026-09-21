import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { AuthForm } from "@/components/auth/AuthForm";
import { DemoCredentials } from "@/components/auth/DemoCredentials";
import { getCurrentUser } from "@/lib/require-user";

export const metadata: Metadata = { title: "Sign in" };
export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string }>;
}) {
  // Resolve the session rather than checking the cookie exists. A cookie that
  // outlived its session would otherwise bounce between here and the route it
  // came from, forever.
  if (await getCurrentUser()) redirect("/dashboard");

  const { next, expired } = await searchParams;
  return (
    <>
      <AuthForm mode="login" next={next} expired={expired === "1"} />
      <DemoCredentials />
    </>
  );
}
