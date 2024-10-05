const express = require('express');
const session = require('express-session');
const passport = require('passport');
const GitHubStrategy = require('passport-github2').Strategy;
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

passport.use(new GitHubStrategy({
  clientID: process.env.GITHUB_CLIENT_ID,
  clientSecret: process.env.GITHUB_CLIENT_SECRET,
  callbackURL: "http://localhost:3000/auth/callback"
},
async (accessToken, refreshToken, profile, done) => {
  try {
    const userData = await axios.get('https://api.github.com/user', {
      headers: { Authorization: `token ${accessToken}` }
    });
    
    const repoData = await axios.get('https://api.github.com/user/repos', {
      headers: { Authorization: `token ${accessToken}` }
    });

    const profileWithRepos = {
      ...profile,
      repos: repoData.data,
      stats: userData.data
    };
    return done(null, profileWithRepos);
  } catch (error) {
    return done(error, null);
  }
}));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

app.use(session({ secret: 'secret', resave: false, saveUninitialized: true }));
app.use(passport.initialize());
app.use(passport.session());

app.set('view engine', 'ejs');
app.use(express.static('public'));

// 首页
app.get('/', (req, res) => {
  res.render('index', { user: req.user });
});

// GitHub 认证
app.get('/auth/github',
  passport.authenticate('github', { scope: ['user:email'] })
);

// GitHub 认证回调
app.get('/auth/callback', 
  passport.authenticate('github', { failureRedirect: '/' }),
  (req, res) => {
    res.redirect('/dashboard');
  }
);

// 仪表盘页面
app.get('/dashboard', (req, res) => {
  if (!req.isAuthenticated()) {
    return res.redirect('/');
  }
  
  const { stats, repos } = req.user;
  const totalStars = repos.reduce((acc, repo) => acc + repo.stargazers_count, 0);
  const totalForks = repos.reduce((acc, repo) => acc + repo.forks_count, 0);
  
  res.render('dashboard', { 
    user: stats, 
    repos, 
    totalStars, 
    totalForks 
  });
});

// 注销
app.get('/logout', (req, res) => {
  req.logout(() => {});
  res.redirect('/');
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
