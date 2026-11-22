"""Create web/.dev.vars (local secrets for `wrangler dev`) from the env file, without printing any value.

Also makes sure the env file has an AUTOPOST_APP_PASSWORD (generated once) so the owner can find the
site password there. Usage: python web/scripts/make_dev_vars.py [env_file]
"""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from post_instagram import DEFAULT_ENV, read_env, save_env_value  # noqa: E402

env_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ENV
env = read_env(env_path)
if not env.get("AUTOPOST_APP_PASSWORD"):
    save_env_value(env_path, "AUTOPOST_APP_PASSWORD", secrets.token_urlsafe(12))
    env = read_env(env_path)
    print(f"Generated a site password and saved it in {env_path} as AUTOPOST_APP_PASSWORD")

values = {
    "APP_PASSWORD": env["AUTOPOST_APP_PASSWORD"],
    "SESSION_SECRET": secrets.token_urlsafe(32),
    "BUFFER_API_KEY": env.get("BUFFER_API_KEY", ""),
    "BUFFER_CHANNEL_ID": env.get("BUFFER_CHANNEL_ID", ""),
    "CF_ACCOUNT_ID": env.get("CF_ACCOUNT_ID", ""),
    "CF_API_TOKEN": env.get("CF_API_TOKEN", ""),
    **{f"CF_{part}_{n}": env.get(f"CF_{part}_{n}", "") for n in range(2, 21) for part in ("ACCOUNT_ID", "API_TOKEN")},
}
out = pathlib.Path(__file__).resolve().parents[1] / ".dev.vars"
out.write_text("".join(f'{k}="{v}"\n' for k, v in values.items() if v), encoding="utf-8")
print(f"Wrote {out} with: {', '.join(k for k, v in values.items() if v)}")
