"""Deploy the AutoPostInsta web app to Cloudflare Workers (free plan).

Run after `npx wrangler login`. It:
  1. creates the KV namespace the first time and writes its id into web/wrangler.jsonc,
  2. deploys the worker,
  3. uploads the secrets from your env file (never printed),
and prints the live URL.

Usage: python web/scripts/deploy.py [env_file]
"""
import json
import pathlib
import re
import secrets
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
CONFIG = WEB / "wrangler.jsonc"
WRANGLER = ["npx", "--yes", "wrangler@4.166.0"]
sys.path.insert(0, str(ROOT))
from post_instagram import DEFAULT_ENV, read_env, save_env_value  # noqa: E402

SECRET_KEYS = {
    "APP_PASSWORD": "AUTOPOST_APP_PASSWORD",
    "BUFFER_API_KEY": "BUFFER_API_KEY",
    "BUFFER_CHANNEL_ID": "BUFFER_CHANNEL_ID",
    "CF_ACCOUNT_ID": "CF_ACCOUNT_ID",
    "CF_API_TOKEN": "CF_API_TOKEN",
    # Free text providers, tried in this order before Cloudflare (each optional).
    "GROQ_API_KEY": "GROQ_API_KEY",
    "GEMINI_API_KEY": "GEMINI_API_KEY",
    "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    # Free image backup: Z-Image Turbo on Hugging Face (read token).
    "HF_TOKEN": "HF_TOKEN",
    # Backup Cloudflare accounts, used in order once earlier ones run out: _2, _3 … _20 (the worker reads the same range).
    **{f"CF_{part}_{n}": f"CF_{part}_{n}" for n in range(2, 21) for part in ("ACCOUNT_ID", "API_TOKEN")},
}


def wrangler(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run([*WRANGLER, *args, "--config", str(CONFIG)], input=stdin, text=True,
                            encoding="utf-8", errors="replace",  # wrangler prints emoji
                            capture_output=True, cwd=ROOT, shell=sys.platform == "win32")
    if result.returncode != 0:
        sys.exit(f"wrangler {' '.join(args)} failed:\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}")
    return result.stdout


def ensure_kv() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    if "REPLACE_WITH_KV_ID" not in text:
        print("KV namespace already set up.")
        return
    # Reuse a namespace from an earlier, interrupted run before creating a new one.
    listed = wrangler("kv", "namespace", "list")
    existing = [ns for ns in json.loads(listed[listed.index("["):]) if ns.get("title", "").endswith("STORE")]
    if existing:
        kv_id = existing[0]["id"]
        print(f"Found the existing KV namespace '{existing[0]['title']}'.")
    else:
        out = wrangler("kv", "namespace", "create", "STORE")
        match = re.search(r'"id":\s*"([0-9a-f]{32})"', out) or re.search(r"\b([0-9a-f]{32})\b", out)
        if not match:
            sys.exit(f"Couldn't find the new KV namespace id in wrangler's output:\n{out[-1500:]}")
        kv_id = match.group(1)
        print("Created the KV namespace.")
    CONFIG.write_text(text.replace("REPLACE_WITH_KV_ID", kv_id), encoding="utf-8")
    print("Saved its id in web/wrangler.jsonc.")


def main() -> None:
    env_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ENV
    env = read_env(env_path)
    missing = [src for src in ("AUTOPOST_APP_PASSWORD", "BUFFER_API_KEY", "BUFFER_CHANNEL_ID", "CF_ACCOUNT_ID", "CF_API_TOKEN") if not env.get(src)]
    if missing:
        sys.exit(f"Missing in {env_path}: {', '.join(missing)}. Run web/scripts/make_dev_vars.py first for the password.")

    ensure_kv()
    out = wrangler("deploy")
    url = re.search(r"https://[\w.-]+\.workers\.dev", out)
    print("Deployed." + (f" Live at {url.group(0)}" if url else ""))

    if not env.get("AUTOPOST_SESSION_SECRET"):  # created once and kept, so redeploys don't log you out
        save_env_value(env_path, "AUTOPOST_SESSION_SECRET", secrets.token_urlsafe(32))
        env = read_env(env_path)
    values = {name: env.get(src, "") for name, src in SECRET_KEYS.items()}
    values["SESSION_SECRET"] = env["AUTOPOST_SESSION_SECRET"]
    values = {k: v for k, v in values.items() if v}
    accounts = sum(1 for k in values if k.startswith("CF_ACCOUNT_ID"))
    wrangler("secret", "bulk", stdin=json.dumps(values))  # reads the JSON from stdin; values never printed
    print(f"Secrets uploaded: {', '.join(k for k in values if not k.startswith('CF_'))} and {accounts} Cloudflare account(s)")
    if url:
        print(f"\nOpen {url.group(0)} and log in with AUTOPOST_APP_PASSWORD from your env file.")


if __name__ == "__main__":
    main()
