# GitHub OAuth App

This is a simple Node.js application that allows users to log in with their GitHub account using OAuth 2.0 and view key metrics on a dashboard.

## Features
- GitHub OAuth 2.0 Authentication
- Displays user information and key metrics from GitHub API
- Dashboard with metrics like followers, following, total stars, total forks, and repository statistics

## Requirements
- Node.js (v14 or higher)
- A GitHub OAuth App with a `Client ID` and `Client Secret`

## Custom info
- change .env data as follows
```
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

## run
```
node app.js
```