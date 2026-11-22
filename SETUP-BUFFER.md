# Buffer setup (one time, about 10 minutes, no Facebook needed)

Buffer posts to Instagram for us. Its free plan includes API access, and a Professional Instagram account connects with your Instagram login. Never paste the API key into a chat.

## 1. Make the AWSAVYA Instagram a Professional account
In the Instagram app, open **Settings → Account type and tools → Switch to professional account → Business**. Personal accounts only get a phone reminder from Buffer instead of automatic posting.

## 2. Connect Instagram to a free Buffer account
1. Sign up at **buffer.com** (free plan) and verify your email.
2. Click **Connect channel → Instagram → Professional → Connect to Instagram**, then log in with the AWSAVYA Instagram.
   - Don't use "Setup a Personal account", which only sends reminders.
   - If you see "Invalid session error 400", that's a known Meta-side issue Buffer lists. Wait a while and try again.

## 3. Create the API key
1. Go to **publish.buffer.com/settings/api → Personal Access → + New Key**.
2. Name it `AutoPostInsta`, leave the permissions ticked, and set **Expiration: 1 year**.
3. Click **Generate API Key** and copy it. The free plan allows 1 key, and generating a new key cancels the old one.
4. Add it to your env file, `%USERPROFILE%\OneDrive\Documents\.env`:
   ```
   BUFFER_API_KEY=paste-key-here
   ```

## 4. Check it works
```
python post_buffer.py channels
```
You should see your Instagram channel. Add the `BUFFER_CHANNEL_ID=...` line it suggests.

## 5. First post
Check everything without sending:
```
python post_buffer.py post --ad messy --at "2026-11-23 10:00" --dry-run
```
Send it to Buffer for real (times are India time):
```
python post_buffer.py post --ad messy --at "2026-11-23 10:00"
```
See what's waiting:
```
python post_buffer.py queue
```
You can also see, edit or delete queued posts in the Buffer app before they go out.

## Free plan limits
- 3 channels (you need 1), and **10 posts queued per channel**. The queue refills as posts go out.
- **5 hashtags per Instagram post.** The script blocks captions with more.
- 600 API calls a day. One post uses about 3.
- No "first comment" on the free plan.
- The API key expires after a year at most. Buffer emails you before it does.

## Notes
- Posts get Instagram's **"AI info"** label by default, because the images are AI-generated. Turn it off with `--no-ai-label`.
- Images must be public `https://` JPEGs between 3:4 and 1.91:1 and under 8 MB. Our 1080×1350 ads fit. Buffer fetches the image when the post goes out, so don't delete images from the repo while their posts are queued.
