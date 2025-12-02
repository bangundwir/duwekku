# Requirements Document

## Introduction

Fitur Admin Dashboard menyediakan antarmuka web untuk administrator bot Telegram Money Tracker. Dashboard ini memungkinkan admin untuk melihat dan mengelola semua user yang menggunakan bot, mengatur sistem langganan user, membatasi penggunaan query, dan melakukan manajemen user secara keseluruhan. Website admin dirancang dengan UI yang modern, rapi, dan responsif.

## Glossary

- **Admin Dashboard**: Antarmuka web untuk administrator mengelola bot dan user
- **User**: Pengguna bot Telegram yang terdaftar dalam sistem
- **Query Limit**: Batasan jumlah permintaan yang dapat dilakukan user per periode waktu
- **Subscription Plan**: Paket langganan yang menentukan fitur dan batasan untuk user
- **Admin**: Pengguna dengan hak akses khusus untuk mengelola sistem melalui dashboard

## Requirements

### Requirement 1

**User Story:** As an admin, I want to view all registered users in a dashboard, so that I can monitor who is using the bot.

#### Acceptance Criteria

1. WHEN an admin accesses the dashboard THEN the Admin Dashboard SHALL display a paginated list of all registered users with username, user ID, registration date, and status
2. WHEN the user list is displayed THEN the Admin Dashboard SHALL show total user count and active user statistics
3. WHEN an admin searches for a user THEN the Admin Dashboard SHALL filter users by username or user ID within 500ms
4. WHEN displaying user data THEN the Admin Dashboard SHALL sort users by registration date in descending order by default

### Requirement 2

**User Story:** As an admin, I want to manage user subscriptions, so that I can control access to premium features.

#### Acceptance Criteria

1. WHEN an admin views a user profile THEN the Admin Dashboard SHALL display current subscription status, plan type, and expiration date
2. WHEN an admin assigns a subscription plan to a user THEN the Admin Dashboard SHALL update the user's access level and record the change timestamp
3. WHEN an admin creates a new subscription plan THEN the Admin Dashboard SHALL allow setting plan name, duration, query limits, and price
4. WHEN a subscription expires THEN the Admin Dashboard SHALL mark the user as free-tier and restrict premium features

### Requirement 3

**User Story:** As an admin, I want to set query limits for users, so that I can prevent abuse and manage server resources.

#### Acceptance Criteria

1. WHEN an admin sets a daily query limit for a user THEN the Admin Dashboard SHALL enforce the limit and block requests exceeding the threshold
2. WHEN an admin sets a monthly query limit for a user THEN the Admin Dashboard SHALL track cumulative usage and enforce the monthly cap
3. WHEN a user reaches their query limit THEN the Bot SHALL notify the user and reject further requests until the limit resets
4. WHEN viewing user details THEN the Admin Dashboard SHALL display current query usage statistics (daily and monthly)

### Requirement 4

**User Story:** As an admin, I want to block or delete users, so that I can handle policy violations and manage the user base.

#### Acceptance Criteria

1. WHEN an admin blocks a user THEN the Admin Dashboard SHALL prevent the user from accessing bot features and display blocked status
2. WHEN an admin unblocks a user THEN the Admin Dashboard SHALL restore the user's access according to their subscription level
3. WHEN an admin deletes a user THEN the Admin Dashboard SHALL remove user data and require confirmation before deletion
4. WHEN a blocked user attempts to use the bot THEN the Bot SHALL display a blocked message and reject all commands

### Requirement 5

**User Story:** As an admin, I want a clean and modern web interface, so that I can efficiently manage users and subscriptions.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the Admin Dashboard SHALL display a responsive layout that works on desktop and mobile devices
2. WHEN navigating the dashboard THEN the Admin Dashboard SHALL provide a sidebar menu with clear navigation to Users, Subscriptions, and Settings sections
3. WHEN displaying data tables THEN the Admin Dashboard SHALL use consistent styling with alternating row colors and hover effects
4. WHEN performing actions THEN the Admin Dashboard SHALL show loading indicators and success/error notifications

### Requirement 6

**User Story:** As an admin, I want secure authentication, so that only authorized personnel can access the dashboard.

#### Acceptance Criteria

1. WHEN accessing the dashboard THEN the Admin Dashboard SHALL require username and password authentication
2. WHEN authentication fails THEN the Admin Dashboard SHALL display an error message and log the failed attempt
3. WHEN an admin session is inactive for 30 minutes THEN the Admin Dashboard SHALL automatically log out the admin
4. WHEN an admin logs out THEN the Admin Dashboard SHALL invalidate the session and redirect to the login page

### Requirement 7

**User Story:** As an admin, I want to view usage analytics, so that I can understand bot usage patterns.

#### Acceptance Criteria

1. WHEN viewing the dashboard home THEN the Admin Dashboard SHALL display summary statistics including total users, active subscriptions, and daily queries
2. WHEN viewing analytics THEN the Admin Dashboard SHALL show a chart of daily query volume for the past 30 days
3. WHEN viewing user activity THEN the Admin Dashboard SHALL display last active timestamp and total queries made by each user
