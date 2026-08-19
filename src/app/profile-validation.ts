export type ProfileValidationErrors = Partial<{
  username: string;
  displayName: string;
  bio: string;
  location: string;
  website: string;
  avatarUrl: string;
}>;

const USERNAME_RE = /^[a-z0-9._]{3,24}$/;

export function normalizeProfileUsername(value: string): string {
  return value.trim().replace(/^@/, "").toLowerCase();
}

export function isValidWebsite(value: string): boolean {
  const website = value.trim();
  if (!website) return true;
  try {
    const candidate = /^https?:\/\//i.test(website) ? website : `https://${website}`;
    const parsed = new URL(candidate);
    const host = parsed.hostname.toLowerCase();
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && (host.includes(".") || host === "localhost");
  } catch {
    return false;
  }
}

export function isSafeAvatarUrl(value?: string): boolean {
  const avatarUrl = value?.trim() ?? "";
  if (!avatarUrl) return true;
  if (avatarUrl.startsWith("data:")) return true;
  try {
    const parsed = new URL(avatarUrl);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && !!parsed.hostname;
  } catch {
    return false;
  }
}

export function validateProfilePatch(patch: Partial<{
  username: string;
  displayName: string;
  bio: string;
  location: string;
  website: string;
  avatarUrl: string;
}>): ProfileValidationErrors {
  const errors: ProfileValidationErrors = {};

  if (patch.username !== undefined) {
    const username = normalizeProfileUsername(patch.username ?? "");
    if (!username) {
      errors.username = "Pick a username.";
    } else if (!USERNAME_RE.test(username)) {
      errors.username = "Usernames are 3–24 characters: letters, numbers, dots and underscores.";
    }
  }

  if (patch.displayName !== undefined) {
    const displayName = (patch.displayName ?? "").trim();
    if (displayName.length > 40) {
      errors.displayName = "Display names can be up to 40 characters.";
    }
  }

  if (patch.bio !== undefined) {
    const bio = patch.bio ?? "";
    if (bio.length > 160) {
      errors.bio = "Bios can be up to 160 characters.";
    }
  }

  if (patch.location !== undefined) {
    const location = (patch.location ?? "").trim();
    if (location.length > 80) {
      errors.location = "Locations can be up to 80 characters.";
    }
  }

  if (patch.website !== undefined && !isValidWebsite(patch.website ?? "")) {
    errors.website = "Enter a valid website URL, like https://example.com.";
  }

  if (patch.avatarUrl !== undefined && !isSafeAvatarUrl(patch.avatarUrl)) {
    errors.avatarUrl = "Profile photos can only be uploaded from your device or kept as-is.";
  }

  return errors;
}

export function getProfileValidationError(patch: Partial<{ username: string; displayName: string; bio: string; location: string; website: string; avatarUrl: string; }>) {
  return Object.values(validateProfilePatch(patch))[0];
}
