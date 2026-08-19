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

export function normalizeProfileDisplayName(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

export function normalizeProfileBio(value: string): string {
  return value.trim();
}

export function normalizeProfileWebsite(value: string): string {
  const website = value.trim();
  if (!website) return "";
  return /^https?:\/\//i.test(website) ? website : `https://${website}`;
}

export function normalizeProfileAvatarUrl(value?: string): string {
  return value?.trim() ?? "";
}

export function isValidWebsite(value: string): boolean {
  const website = normalizeProfileWebsite(value);
  if (!website) return true;
  try {
    const parsed = new URL(website);
    const host = parsed.hostname.toLowerCase();
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && (host.includes(".") || host === "localhost");
  } catch {
    return false;
  }
}

export function isSafeAvatarUrl(value?: string): boolean {
  const avatarUrl = normalizeProfileAvatarUrl(value);
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
    const displayName = normalizeProfileDisplayName(patch.displayName ?? "");
    if (!displayName) {
      errors.displayName = "Display name cannot be empty.";
    } else if (displayName.length > 40) {
      errors.displayName = "Display names can be up to 40 characters.";
    }
  }

  if (patch.bio !== undefined) {
    const bio = normalizeProfileBio(patch.bio ?? "");
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

export function normalizeProfilePatch(patch: Partial<{
  username: string;
  displayName: string;
  bio: string;
  location: string;
  website: string;
  avatarUrl: string;
}>) {
  return {
    ...(patch.username !== undefined ? { username: normalizeProfileUsername(patch.username ?? "") } : {}),
    ...(patch.displayName !== undefined ? { displayName: normalizeProfileDisplayName(patch.displayName ?? "") } : {}),
    ...(patch.bio !== undefined ? { bio: normalizeProfileBio(patch.bio ?? "") } : {}),
    ...(patch.location !== undefined ? { location: (patch.location ?? "").trim() } : {}),
    ...(patch.website !== undefined ? { website: normalizeProfileWebsite(patch.website ?? "") } : {}),
    ...(patch.avatarUrl !== undefined ? { avatarUrl: normalizeProfileAvatarUrl(patch.avatarUrl) } : {}),
  };
}
