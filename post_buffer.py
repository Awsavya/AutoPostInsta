"""Post an AWSAVYA ad to Instagram through Buffer (no Facebook account needed).

Buffer's GraphQL API (https://api.buffer.com) is on its free plan. Buffer fetches the image from a public
URL and publishes it to the Instagram channel connected in Buffer with Instagram login.

Commands
  channels                    List your Buffer channels and find the Instagram channel ID.
  queue                       Show posts waiting in the Instagram channel (the free plan holds 10).
  post --ad KEY [--at "YYYY-MM-DD HH:MM" | --queue | --now]
                              Post ads/ad-KEY.jpg with its caption from ads/captions.json.
                              --at   schedule for that time, India time (IST)
                              --queue add to the next free slot in Buffer's posting schedule
                              --now  publish right away
                              --draft save as a Buffer draft only (nothing is published)
  post --image-url URL --caption-file FILE [...]
                              Post any public JPEG with a caption from a text file.

Options for post
  --dry-run                   Check the image, caption and time, show what would be sent, call nothing at Buffer.
  --no-ai-label               Don't set Instagram's "AI info" label (on by default: these images are AI-made).

Env file (default %USERPROFILE%\\OneDrive\\Documents\\.env, or --env PATH):
  BUFFER_API_KEY=...          publish.buffer.com/settings/api > Personal Access > New Key
  BUFFER_CHANNEL_ID=...       Optional; found automatically when you have exactly one Instagram channel
  IMAGE_BASE_URL=https://...  Public folder the ad images are served from (needed for --ad)

The API key is never printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.request

from post_instagram import DEFAULT_ENV, MAX_ALT, check_caption, check_image_url, read_env, resolve_post

API = "https://api.buffer.com"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
MAX_HASHTAGS = 5          # Buffer's limit for Instagram posts
MIN_LEAD = dt.timedelta(minutes=5)  # a scheduled time must be at least this far ahead


class BufferError(RuntimeError):
    pass


class Buffer:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def gql(self, query: str, variables: dict | None = None) -> dict:
        body = json.dumps({"query": query, "variables": variables or {}}).encode()
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AutoPostInsta/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:300]
            if err.code == 401:
                raise BufferError("Buffer rejected the API key (401). Check BUFFER_API_KEY, or regenerate it.") from None
            if err.code == 429:
                raise BufferError(f"Buffer rate limit reached; retry after {err.headers.get('Retry-After', '?')}s.") from None
            raise BufferError(f"Buffer returned HTTP {err.code}: {detail}") from None
        if data.get("errors"):
            first = data["errors"][0]
            code = first.get("extensions", {}).get("code", "")
            raise BufferError(f"{code} {first.get('message', '')}".strip())
        return data["data"]

    def organizations(self) -> list[dict]:
        return self.gql("query { account { organizations { id name } } }")["account"]["organizations"]

    def channels(self, org_id: str) -> list[dict]:
        q = """query ($input: ChannelsInput!) {
                 channels(input: $input) { id name displayName service isQueuePaused isDisconnected }
               }"""
        return self.gql(q, {"input": {"organizationId": org_id}})["channels"]

    def all_channels(self) -> list[dict]:
        return [{**ch, "org_id": org["id"], "org": org["name"]}
                for org in self.organizations() for ch in self.channels(org["id"])]

    def instagram_channel(self, configured_id: str | None) -> dict:
        channels = self.all_channels()
        if configured_id:
            match = [c for c in channels if c["id"] == configured_id]
            if not match:
                raise BufferError(f"BUFFER_CHANNEL_ID {configured_id} is not one of your Buffer channels.")
            return match[0]
        insta = [c for c in channels if c["service"] == "instagram"]
        if len(insta) == 1:
            return insta[0]
        if not insta:
            raise BufferError("No Instagram channel in Buffer yet. Connect it: Buffer > Connect channel > Instagram > Professional.")
        names = ", ".join(f"{c['name']} ({c['id']})" for c in insta)
        raise BufferError(f"Several Instagram channels ({names}). Set BUFFER_CHANNEL_ID to the one to use.")

    def scheduled_posts(self, org_id: str, channel_id: str) -> list[dict]:
        q = """query ($input: PostsInput!) {
                 posts(first: 20, input: $input) { edges { node { id status dueAt text } } }
               }"""
        variables = {"input": {"organizationId": org_id,
                               "filter": {"channelIds": [channel_id], "status": ["scheduled"]}}}
        return [e["node"] for e in self.gql(q, variables)["posts"]["edges"] or []]

    def create_post(self, post_input: dict) -> dict:
        q = """mutation ($input: CreatePostInput!) {
                 createPost(input: $input) {
                   __typename
                   ... on PostActionSuccess { post { id status dueAt } }
                   ... on MutationError { message }
                 }
               }"""
        result = self.gql(q, {"input": post_input})["createPost"]
        if result.get("__typename") != "PostActionSuccess":
            raise BufferError(f"{result.get('__typename')}: {result.get('message', 'no message')}")
        return result["post"]


# ---------- building the post ----------

def parse_ist(text: str, now: dt.datetime | None = None) -> dt.datetime:
    """'2026-11-22 10:00' in India time -> aware datetime; must be at least MIN_LEAD in the future."""
    try:
        when = dt.datetime.strptime(text.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except ValueError:
        raise ValueError(f"--at must look like 2026-11-22 10:00 (India time), got '{text}'") from None
    now = now or dt.datetime.now(dt.timezone.utc)
    if when - now < MIN_LEAD:
        raise ValueError(f"--at {text} IST is in the past or less than {MIN_LEAD.seconds // 60} minutes away")
    return when


def build_input(channel_id: str, image_url: str, caption: str, alt: str | None,
                mode: str, due: dt.datetime | None, ai_label: bool, draft: bool = False) -> dict:
    image: dict = {"url": image_url}
    if alt:
        image["metadata"] = {"altText": alt}
    post = {
        "channelId": channel_id,
        "text": caption,
        "schedulingType": "automatic",
        "mode": mode,
        "assets": [{"image": image}],
        "aiAssisted": True,
        "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True, "isAiGenerated": ai_label}},
    }
    if due:
        post["dueAt"] = due.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if draft:
        post["saveToDraft"] = True  # stays in Buffer's drafts; never published until scheduled by hand
    return post


def describe_mode(mode: str, due: dt.datetime | None) -> str:
    if mode == "customScheduled" and due:
        return f"scheduled for {due.astimezone(IST):%a %d %b %Y, %H:%M} IST"
    return {"addToQueue": "next free slot in Buffer's schedule", "shareNow": "right away"}[mode]


# ---------- commands ----------

def client(env: dict[str, str]) -> Buffer:
    key = env.get("BUFFER_API_KEY")
    if not key:
        sys.exit("BUFFER_API_KEY is not set in the env file. See SETUP-BUFFER.md, step 3.")
    return Buffer(key)


def cmd_channels(env: dict[str, str]) -> None:
    channels = client(env).all_channels()
    if not channels:
        print("No channels connected in Buffer yet.")
        return
    for c in channels:
        flags = [f for f, on in (("queue paused", c["isQueuePaused"]), ("DISCONNECTED", c["isDisconnected"])) if on]
        print(f"{c['service']:<10} {c['displayName'] or c['name']:<30} id={c['id']}  org={c['org']}"
              + (f"  [{', '.join(flags)}]" if flags else ""))
    insta = [c for c in channels if c["service"] == "instagram"]
    if len(insta) == 1 and not env.get("BUFFER_CHANNEL_ID"):
        print(f"\nTip: add BUFFER_CHANNEL_ID={insta[0]['id']} to the env file to skip this lookup.")


def cmd_queue(env: dict[str, str]) -> None:
    buf = client(env)
    channel = buf.instagram_channel(env.get("BUFFER_CHANNEL_ID"))
    posts = buf.scheduled_posts(channel["org_id"], channel["id"])
    print(f"{len(posts)} post(s) waiting on {channel['displayName'] or channel['name']} (free plan holds 10)")
    for p in sorted(posts, key=lambda p: p.get("dueAt") or ""):
        due = dt.datetime.fromisoformat(p["dueAt"].replace("Z", "+00:00")).astimezone(IST) if p.get("dueAt") else None
        first_line = (p.get("text") or "").splitlines()[0][:60] if p.get("text") else ""
        print(f"  {due:%a %d %b %H:%M} IST  {first_line}" if due else f"  (no time)  {first_line}")


def cmd_post(args: argparse.Namespace, env: dict[str, str]) -> None:
    image_url, caption, alt = resolve_post(args, env)
    problems = check_caption(caption, max_hashtags=MAX_HASHTAGS) + check_image_url(image_url)
    if alt and len(alt) > MAX_ALT:
        problems.append(f"alt text is {len(alt)} characters (max {MAX_ALT})")

    due = None
    if args.at:
        mode = "customScheduled"
        try:
            due = parse_ist(args.at)
        except ValueError as err:
            problems.append(str(err))
    elif args.now:
        mode = "shareNow"
    else:
        mode = "addToQueue"

    print(f"Image:    {image_url}")
    if args.draft:
        print("When:     never: saved as a Buffer draft only, not published")
    else:
        print(f"When:     {describe_mode(mode, due) if mode != 'customScheduled' or due else args.at}")
    print(f"AI label: {'on' if not args.no_ai_label else 'off'}")
    print(f"Alt text: {alt or '(none)'}")
    print("Caption:\n" + "\n".join("  " + line for line in caption.splitlines()))
    if problems:
        sys.exit("Not sent:\n" + "\n".join(f"  - {p}" for p in problems))
    if args.dry_run:
        print("\nDry run: everything checks out. Nothing was sent to Buffer.")
        return

    buf = client(env)
    channel = buf.instagram_channel(env.get("BUFFER_CHANNEL_ID"))
    post = buf.create_post(build_input(channel["id"], image_url, caption, alt, mode, due,
                                       not args.no_ai_label, draft=args.draft))
    when = post.get("dueAt")
    when_ist = dt.datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(IST) if when else None
    print(f"\nSent to Buffer: post {post['id']} is {post['status']}"
          + (f", going out {when_ist:%a %d %b %Y at %H:%M} IST" if when_ist else ""))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Post AWSAVYA ads to Instagram through Buffer.")
    parser.add_argument("--env", type=pathlib.Path, default=DEFAULT_ENV, help="env file with the Buffer API key")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("channels", help="list Buffer channels")
    sub.add_parser("queue", help="show posts waiting on the Instagram channel")
    p = sub.add_parser("post", help="send one image post to Buffer")
    p.add_argument("--ad", help="ad key from ads/captions.json, e.g. messy")
    p.add_argument("--image-url", help="public https URL of a JPEG")
    p.add_argument("--caption-file", help="text file holding the caption")
    p.add_argument("--alt-text", help="alt text for --image-url posts")
    when = p.add_mutually_exclusive_group()
    when.add_argument("--at", help='India time, e.g. "2026-11-22 10:00"')
    when.add_argument("--queue", action="store_true", help="next free slot in Buffer's schedule (default)")
    when.add_argument("--now", action="store_true", help="publish right away")
    when.add_argument("--draft", action="store_true", help="save as a Buffer draft only; nothing is published")
    p.add_argument("--dry-run", action="store_true", help="check everything, send nothing")
    p.add_argument("--no-ai-label", action="store_true", help="don't set Instagram's AI info label")
    args = parser.parse_args(argv)

    env = read_env(args.env)
    try:
        {"channels": lambda: cmd_channels(env),
         "queue": lambda: cmd_queue(env),
         "post": lambda: cmd_post(args, env)}[args.command]()
    except BufferError as err:
        sys.exit(f"Buffer said no: {err}")


if __name__ == "__main__":
    main()
