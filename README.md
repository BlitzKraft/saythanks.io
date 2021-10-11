# ☼ The 'Say Thanks' Project

[![saythanks](https://img.shields.io/badge/say-thanks-modal.svg)](https://saythanks.io/to/kennethreitz)

**If you're interested in financially supporting Kenneth Reitz open source, consider [visiting this link](https://cash.me/$KennethReitz). Your support helps tremendously with sustainability of motivation, as Open Source is no longer part of my day job.**

## Spreading Thankfulness in Open Source™

[**saythanks.io**](https://saythanks.io/) will provide a button/link for use by open source projects, to encourage users to send a simple _thank you_ note to the creator (or creators) of that project.

This simple button/link can be added to READMEs and project documentation.

The author can then enjoy a nice inbox (ideally) filled with very small, thoughtful messages from the happy users of the software they enjoy to toil over.

## Implementation Concepts

### ☤ The Basics

- Email when a new message of thankfulness is submitted (csrf enabled).
- Inbox page for each user/project with simple aggregation of messages (private).

### ☤ The Architecture

- Flask for API and Frontend, single application
- Auth0 for credential storage (in progress)
- Heroku for Hosting (done!)
- CloudFlare for SSL termination (done!)
- GitHub account creation, as well as passwordless email accounts

## Intended Collaborators

- Erin "The X" O'Connell (Python)
- Tom "The Pythonist" Baker (Javascript)
- Tom "Sea of Clouds" Matthews (Logo and Graphic Design)
- Kenneth "Your Name Here Instead, Idan?" Reitz (Frontend Design)

## Random Inspirational Links

- [Say Thanks for Package Control](https://packagecontrol.io/say_thanks)
- [Random 'Thanks' Issue on GH](https://github.com/foxmask/wallabag_api/issues/1)

## Initial Setup for Development

- Refer to [docs](/docs/README.md)
