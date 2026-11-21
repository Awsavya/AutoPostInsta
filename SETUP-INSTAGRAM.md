# Instagram setup (one time, about 20 minutes)

This uses Meta's **Instagram API with Instagram Login**, so no Facebook Page is needed. Only you can do these steps, because they need your logins. Never paste the token into a chat.

## 1. Make the AWSAVYA Instagram a Professional account
In the Instagram app, open **Settings → Account type and tools → Switch to professional account**. Choose **Business**, then a category such as "Software company" or "Web designer".

## 2. Create a Meta developer app
1. Go to **developers.facebook.com**, log in, and register as a developer if asked.
2. Click **My Apps → Create app**. When asked for an app type, choose **Business**. Meta's docs say the Instagram API needs a Business-type app.
3. Name it something like `AWSAVYA Auto Post`.
4. In the app dashboard, add the **Instagram** product.

## 3. Generate the access token
1. In the left menu, open **Instagram → API setup with Instagram business login**.
2. Under "Generate access tokens", click **Add account**, then log in with the AWSAVYA Instagram.
   - If Meta asks you to add the account as a tester: go to **App roles → Roles → Instagram Testers** and add the username. Then accept the invite in the Instagram app (**Settings → Website permissions → Apps and websites → Tester invites**). Meta's pages don't say whether this is needed for your own account, so do it only if asked.
3. Click **Generate token** next to the account, approve the permissions, and copy the token. Tokens made in the dashboard last **60 days**.
4. Add it to your env file, `%USERPROFILE%\OneDrive\Documents\.env`, under the Cloudflare lines:
   ```
   IG_ACCESS_TOKEN=paste-token-here
   ```

## 4. Check it works
```
python post_instagram.py check
```
You should see `Token works for @your-username (Business)` and today's post quota. Add the `IG_USER_ID=...` line it suggests.

## 5. Image hosting (decided separately)
Instagram downloads each image from a public `https://` link, so the ads have to be online first. Once hosting is set up, add this to the env file:
```
IMAGE_BASE_URL=https://.../ads
```

## 6. First post
Check everything without posting:
```
python post_instagram.py post --ad messy --dry-run
```
Then post for real:
```
python post_instagram.py post --ad messy
```

## Keeping the token alive
The token expires after 60 days unless it's refreshed. It must be at least 24 hours old to refresh. Refresh it about once a month:
```
python post_instagram.py refresh-token
```
The daily automation will do this for you once it's built.

## Notes
- Posts get Instagram's **"AI info"** label by default, because the images are AI-generated. Turn it off with `--no-ai-label`, but keeping it is the honest choice.
- Meta allows 50 API posts per 24 hours. You'll use about one.
- Images must be JPEG, under 8 MB, with an aspect ratio between 4:5 and 1.91:1. The ads are 1080×1350, which is exactly 4:5.
