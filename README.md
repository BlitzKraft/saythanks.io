# ☼ The 'Say Thanks' Project

[![saythanks](https://img.shields.io/badge/say-thanks-modal.svg)](https://saythanks.io/to/lifebalance)

## Spreading Thankfulness in Open Source™

[**saythanks.io**](https://saythanks.io/) will provide a button/link for use by open source projects, to encourage users to send a simple _thank you_ note to the creator (or creators) of that project.

This simple button/link can be added to READMEs and project documentation.

The author can then enjoy a nice inbox (ideally) filled with very small, thoughtful messages from the happy users of the software they enjoy to toil over.

## Recent Improvements

- **Versatile Markdown Editor:** Added a powerful and user-friendly markdown editor (Toast UI Editor) for thank you note writing, featuring live preview and enhanced formatting options for users.
- Codebase has been prettified and refactored for maintainability.
- Improved CSRF protection and message inbox aggregation for users/projects.
- Hosting migrated to [KGiSL](https://www.kgisl.com) (was Heroku); CloudFlare continues for SSL termination.
- Unnecessary files and legacy configs cleaned up.
- UI and UX improvements, including updated button colors.
- Enhanced documentation and developer setup instructions.
- Ongoing improvements to authentication (Auth0, OAuth2).

## Implementation Concepts

### ☤ The Basics

- Email when a new message of thankfulness is submitted ([csrf](https://en.wikipedia.org/wiki/Cross-site_request_forgery) enabled).
- Inbox page for each user/project with simple aggregation of messages (private).

### ☤ The Architecture

- Flask for API and Frontend, single application
- Auth0 for credential storage (done, Auth2 in progress)
- Heroku for Hosting (done!)
  - now hosted at [KGiSL](https://www.kgisl.com)
- CloudFlare for SSL termination (done!)
- GitHub account creation, as well as password-less email accounts

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
