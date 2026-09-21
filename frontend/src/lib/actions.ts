"use server";

/**
 * Server actions.
 *
 * All mutations go through here so the admin token and the API base URL stay on
 * the server. Each action revalidates the paths whose data it invalidates.
 */
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { api, ApiError } from "./api";
import { clearSessionCookie, setSessionCookie } from "./session";

export interface ActionResult {
  ok: boolean;
  message?: string;
}

function fail(error: unknown): ActionResult {
  if (error instanceof ApiError) {
    return { ok: false, message: error.message };
  }
  return { ok: false, message: "Could not reach the Zenkai API." };
}

const FEED_PATHS = ["/dashboard", "/opportunities", "/saved", "/deadlines"];

function revalidateFeeds() {
  for (const path of FEED_PATHS) revalidatePath(path);
}

/* --- Authentication ------------------------------------------------------ */

export async function signupAction(formData: FormData): Promise<ActionResult> {
  const email = String(formData.get("email") ?? "").trim();
  const name = String(formData.get("name") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !name || !password) {
    return { ok: false, message: "Fill in every field." };
  }

  try {
    const session = await api.auth.signup({ email, name, password });
    await setSessionCookie(session.token);
  } catch (error) {
    return fail(error);
  }
  // Outside the try: redirect() signals by throwing, and catching it here would
  // turn a successful sign-up into an error message.
  redirect("/profile?welcome=1");
}

export async function loginAction(formData: FormData): Promise<ActionResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const next = String(formData.get("next") ?? "/dashboard");

  if (!email || !password) {
    return { ok: false, message: "Enter your email and password." };
  }

  try {
    const session = await api.auth.login({ email, password });
    await setSessionCookie(session.token);
  } catch (error) {
    return fail(error);
  }
  // Only ever redirect within this app, so a crafted ?next= cannot bounce
  // someone to another origin straight after signing in.
  redirect(next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard");
}

export async function logoutAction(): Promise<void> {
  try {
    await api.auth.logout();
  } catch {
    // The session may already be gone server-side; clearing the cookie is what
    // matters, and it must happen either way.
  }
  await clearSessionCookie();
  revalidateFeeds();
  redirect("/");
}

export async function changePasswordAction(formData: FormData): Promise<ActionResult> {
  const current_password = String(formData.get("current_password") ?? "");
  const new_password = String(formData.get("new_password") ?? "");
  const confirm = String(formData.get("confirm_password") ?? "");

  if (new_password !== confirm) {
    return { ok: false, message: "The new passwords do not match." };
  }

  try {
    const session = await api.auth.changePassword({ current_password, new_password });
    // The server revoked every session, including this one, and issued a fresh
    // token — store it or the user is signed out of the device they just used.
    await setSessionCookie(session.token);
    revalidatePath("/profile");
    return { ok: true, message: "Password changed. Other devices were signed out." };
  } catch (error) {
    return fail(error);
  }
}

export async function toggleSaveAction(
  opportunityId: string,
  currentlySaved: boolean,
): Promise<ActionResult> {
  try {
    if (currentlySaved) {
      await api.unsave(opportunityId);
    } else {
      await api.save(opportunityId);
    }
    revalidateFeeds();
    return { ok: true };
  } catch (error) {
    return fail(error);
  }
}

export async function updateProfileAction(formData: FormData): Promise<ActionResult> {
  const list = (value: FormDataEntryValue | null) =>
    String(value ?? "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  try {
    await api.updateProfile({
      name: String(formData.get("name") ?? "").trim() || undefined,
      preferences: {
        degree: String(formData.get("degree") ?? "").trim() || null,
        field_of_study: String(formData.get("field_of_study") ?? "").trim() || null,
        year: String(formData.get("year") ?? "").trim() || null,
        country: String(formData.get("country") ?? "").trim() || null,
        location: String(formData.get("location") ?? "").trim() || null,
        remote_preference: String(formData.get("remote_preference") ?? "any"),
        skills: list(formData.get("skills")),
        interests: list(formData.get("interests")),
        preferred_categories: formData.getAll("preferred_categories").map(String),
      },
    });
    revalidatePath("/profile");
    revalidateFeeds();
    return { ok: true, message: "Preferences saved." };
  } catch (error) {
    return fail(error);
  }
}

export async function reviewAction(
  opportunityId: string,
  action: "approve" | "reject",
  reviewer: string,
  notes?: string,
): Promise<ActionResult> {
  try {
    if (action === "approve") {
      await api.admin.approve(opportunityId, reviewer, notes);
    } else {
      await api.admin.reject(opportunityId, reviewer, notes);
    }
    revalidatePath("/admin");
    revalidateFeeds();
    return { ok: true, message: `Opportunity ${action === "approve" ? "approved" : "rejected"}.` };
  } catch (error) {
    return fail(error);
  }
}

export async function editOpportunityAction(
  opportunityId: string,
  changes: Record<string, unknown>,
  reviewer: string,
): Promise<ActionResult> {
  try {
    await api.admin.edit(opportunityId, reviewer, changes);
    revalidatePath("/admin");
    revalidateFeeds();
    return { ok: true, message: "Changes saved." };
  } catch (error) {
    return fail(error);
  }
}
