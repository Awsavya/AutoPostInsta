"""Post an AWSAVYA ad to Instagram (Instagram API with Instagram Login, graph.instagram.com).

Commands
  check                       Verify the token: prints the account's username, type and today's post quota.
  post --ad KEY               Post ads/ad-KEY.jpg with its caption from ads/captions.json.
                              The image must be online: IMAGE_BASE_URL + "ad-KEY.jpg".
  post --image-url URL --caption-file FILE
                              Post any public JPEG with a caption from a text file.
  refresh-token               Extend the token by another 60 days and save it back to the env file.

Options for post
  --dry-run                   Check the image and caption, show what would be sent, call nothing at Meta.
  --no-ai-label               Don't set Instagram's "AI info" label (on by default: these images are AI-made).

Env file (default %USERPROFILE%\\OneDrive\\Documents\\.env, or --env PATH):
  IG_ACCESS_TOKEN=...         From Meta App Dashboard > Instagram > API setup with Instagram business login
  IG_USER_ID=...              Optional; looked up from the token when missing
  IG_API_VERSION=v27.0        Optional
  IMAGE_BASE_URL=https://...  Public folder the ad images are served from (needed for --ad)

The token is never printed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
DEFAULT_ENV = pathlib.Path.home() / "OneDrive" / "Documents" / ".env"
HOST = "https://graph.instagram.com"
DEFAULT_VERSION = "v27.0"

MAX_CAPTION = 2200
MAX_HASHTAGS = 30
MAX_MENTIONS = 20
MAX_ALT = 1000
MAX_IMAGE_BYTES = 8 * 1024 * 1024
STATUS_POLL_SECONDS = 15
STATUS_TIMEOUT_SECONDS = 5 * 60


class MetaError(RuntimeError):
    pass


# ---------- env ----------

def read_env(path: pathlib.Path) -> dict[str, str]:
    if not path.exists():
        sys.exit(f"Env file not found: {path}")
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def save_env_value(path: pathlib.Path, key: str, value: str) -> None:
    """Replace one KEY=... line (or append it), leaving every other line as it was."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- Meta API ----------

class Instagram:
    def __init__(self, token: str, version: str = DEFAULT_VERSION, user_id: str | None = None) -> None:
        self.token = token
        self.base = f"{HOST}/{version}"
        self._user_id = user_id

    def _call(self, method: str, url: str, params: dict[str, str]) -> dict:
        params = {**params, "access_token": self.token}
        data = urllib.parse.urlencode(params)
        if method == "GET":
            req = urllib.request.Request(f"{url}?{data}")
        else:
            req = urllib.request.Request(url, data=data.encode(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            body = err.read().decode(errors="replace")
            try:
                e = json.loads(body).get("error", {})
                detail = f"{e.get('message', body)} (code {e.get('code')}, subcode {e.get('error_subcode')})"
            except json.JSONDecodeError:
                detail = body[:300]
            path = urllib.parse.urlsplit(url).path  # never echo the query string: it holds the token
            raise MetaError(f"{method} {path} failed with HTTP {err.code}: {detail}") from None

    def me(self) -> dict:
        data = self._call("GET", f"{self.base}/me", {"fields": "user_id,username,account_type"})
        return data["data"][0] if "data" in data else data

    @property
    def user_id(self) -> str:
        if not self._user_id:
            self._user_id = str(self.me()["user_id"])
        return self._user_id

    def publishing_limit(self) -> dict:
        data = self._call("GET", f"{self.base}/{self.user_id}/content_publishing_limit",
                          {"fields": "quota_usage,config"})
        return data["data"][0] if data.get("data") else {}

    def create_container(self, image_url: str, caption: str, alt_text: str | None, ai_label: bool) -> str:
        params = {"image_url": image_url, "caption": caption, "is_ai_generated": "true" if ai_label else "false"}
        if alt_text:
            params["alt_text"] = alt_text
        return self._call("POST", f"{self.base}/{self.user_id}/media", params)["id"]

    def wait_until_ready(self, container_id: str) -> None:
        deadline = time.monotonic() + STATUS_TIMEOUT_SECONDS
        while True:
            info = self._call("GET", f"{self.base}/{container_id}", {"fields": "status_code,status"})
            code = info.get("status_code")
            if code == "FINISHED":
                return
            if code in ("ERROR", "EXPIRED"):
                raise MetaError(f"Instagram could not process the image: {code} {info.get('status', '')}")
            if time.monotonic() > deadline:
                raise MetaError(f"Image still processing after {STATUS_TIMEOUT_SECONDS // 60} minutes (last status {code})")
            print(f"  processing ({code}), checking again in {STATUS_POLL_SECONDS}s")
            time.sleep(STATUS_POLL_SECONDS)

    def publish(self, container_id: str) -> str:
        return self._call("POST", f"{self.base}/{self.user_id}/media_publish", {"creation_id": container_id})["id"]

    def permalink(self, media_id: str) -> str:
        return self._call("GET", f"{self.base}/{media_id}", {"fields": "permalink"}).get("permalink", "")

    def refresh(self) -> tuple[str, int]:
        data = self._call("GET", f"{HOST}/refresh_access_token", {"grant_type": "ig_refresh_token"})
        return data["access_token"], int(data.get("expires_in", 0))


# ---------- checks ----------

def check_caption(caption: str, max_hashtags: int = MAX_HASHTAGS) -> list[str]:
    problems = []
    if not caption.strip():
        problems.append("caption is empty")
    if len(caption) > MAX_CAPTION:
        problems.append(f"caption is {len(caption)} characters (max {MAX_CAPTION})")
    hashtags = len(re.findall(r"(?<!\w)#\w+", caption))
    if hashtags > max_hashtags:
        problems.append(f"{hashtags} hashtags (max {max_hashtags})")
    if len(re.findall(r"(?<!\w)@\w+", caption)) > MAX_MENTIONS:
        problems.append(f"more than {MAX_MENTIONS} @mentions")
    return problems


def check_image_url(url: str) -> list[str]:
    """Instagram fetches the image itself, so it must be a public JPEG under 8 MB."""
    if not url.startswith("https://"):
        return ["image URL must start with https://"]
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "AutoPostInsta/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "")
            size = int(resp.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as err:
        return [f"image URL returned HTTP {err.code}: is it public yet?"]
    except urllib.error.URLError as err:
        return [f"image URL is not reachable: {err.reason}"]
    problems = []
    if "jpeg" not in ctype and "jpg" not in ctype:
        problems.append(f"image must be served as JPEG, got Content-Type '{ctype}'")
    if size > MAX_IMAGE_BYTES:
        problems.append(f"image is {size / 1024 / 1024:.1f} MB (max 8 MB)")
    return problems


def resolve_post(args: argparse.Namespace, env: dict[str, str]) -> tuple[str, str, str | None]:
    if args.ad:
        captions = json.loads((HERE / "ads" / "captions.json").read_text(encoding="utf-8"))
        if args.ad not in captions:
            sys.exit(f"No caption for '{args.ad}' in ads/captions.json. Known: {', '.join(captions)}")
        base = env.get("IMAGE_BASE_URL", "").rstrip("/")
        if not base:
            sys.exit("IMAGE_BASE_URL is not set in the env file, so --ad can't build the image URL.")
        entry = captions[args.ad]
        return f"{base}/ad-{args.ad}.jpg", entry["caption"], entry.get("alt")
    if not (args.image_url and args.caption_file):
        sys.exit("Use --ad KEY, or both --image-url and --caption-file.")
    return args.image_url, pathlib.Path(args.caption_file).read_text(encoding="utf-8").strip(), args.alt_text


# ---------- commands ----------

def client(env: dict[str, str]) -> Instagram:
    token = env.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set in the env file. See SETUP-INSTAGRAM.md, step 3.")
    return Instagram(token, env.get("IG_API_VERSION", DEFAULT_VERSION), env.get("IG_USER_ID") or None)


def cmd_check(env: dict[str, str]) -> None:
    ig = client(env)
    me = ig.me()
    ig._user_id = str(me["user_id"])
    print(f"Token works for @{me.get('username')} ({me.get('account_type')}), Instagram user ID {me['user_id']}")
    if not env.get("IG_USER_ID"):
        print(f"Tip: add IG_USER_ID={me['user_id']} to the env file to skip this lookup.")
    limit = ig.publishing_limit()
    if limit:
        total = limit.get("config", {}).get("quota_total", "?")
        print(f"API posts in the last 24 hours: {limit.get('quota_usage', 0)} of {total}")


def cmd_post(args: argparse.Namespace, env: dict[str, str]) -> None:
    image_url, caption, alt = resolve_post(args, env)
    problems = check_caption(caption) + check_image_url(image_url)
    if alt and len(alt) > MAX_ALT:
        problems.append(f"alt text is {len(alt)} characters (max {MAX_ALT})")
    print(f"Image:    {image_url}")
    print(f"AI label: {'on' if not args.no_ai_label else 'off'}")
    print(f"Alt text: {alt or '(none)'}")
    print("Caption:\n" + "\n".join("  " + line for line in caption.splitlines()))
    if problems:
        sys.exit("Not posted:\n" + "\n".join(f"  - {p}" for p in problems))
    if args.dry_run:
        print("\nDry run: everything checks out. Nothing was sent to Instagram.")
        return

    ig = client(env)
    print("\nUploading to Instagram...")
    container = ig.create_container(image_url, caption, alt, ai_label=not args.no_ai_label)
    ig.wait_until_ready(container)
    media_id = ig.publish(container)
    print(f"Posted. Media ID {media_id}")
    link = ig.permalink(media_id)
    if link:
        print(f"Live at {link}")


def cmd_refresh(env_path: pathlib.Path, env: dict[str, str]) -> None:
    token, expires_in = client(env).refresh()
    save_env_value(env_path, "IG_ACCESS_TOKEN", token)
    print(f"Token refreshed and saved to {env_path}. Valid for about {expires_in // 86400} more days.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Post AWSAVYA ads to Instagram.")
    parser.add_argument("--env", type=pathlib.Path, default=DEFAULT_ENV, help="env file with the Instagram token")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="verify the token and show today's quota")
    p = sub.add_parser("post", help="post one image")
    p.add_argument("--ad", help="ad key from ads/captions.json, e.g. messy")
    p.add_argument("--image-url", help="public https URL of a JPEG")
    p.add_argument("--caption-file", help="text file holding the caption")
    p.add_argument("--alt-text", help="alt text for --image-url posts")
    p.add_argument("--dry-run", action="store_true", help="check everything, send nothing")
    p.add_argument("--no-ai-label", action="store_true", help="don't set Instagram's AI info label")
    sub.add_parser("refresh-token", help="extend the token by 60 days")
    args = parser.parse_args(argv)

    env = read_env(args.env)
    try:
        if args.command == "check":
            cmd_check(env)
        elif args.command == "post":
            cmd_post(args, env)
        else:
            cmd_refresh(args.env, env)
    except MetaError as err:
        sys.exit(f"Instagram said no: {err}")


if __name__ == "__main__":
    main()
