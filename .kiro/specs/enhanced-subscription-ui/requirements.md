# Requirements Document

## Introduction

Fitur ini meningkatkan tampilan dan interaksi subscription/langganan pada Money Tracker Bot. Fokus utama adalah membuat tampilan lebih interaktif dengan countdown real-time, tombol-tombol yang responsif, export HTML yang lebih menarik dengan animasi, dan kemudahan navigasi untuk pengguna.

## Glossary

- **Subscription**: Langganan berulang seperti Netflix, Spotify, VPS, domain, dll
- **Countdown**: Penghitung mundur waktu menuju tanggal berakhir langganan
- **Progress Bar**: Visualisasi persentase waktu yang telah berlalu dari periode langganan
- **Interactive Button**: Tombol inline keyboard Telegram yang responsif
- **HTML Export**: File HTML yang dapat diunduh berisi data langganan dengan tampilan visual
- **Real-time Update**: Pembaruan tampilan secara otomatis tanpa refresh manual

## Requirements

### Requirement 1

**User Story:** As a user, I want to see my subscriptions with live countdown timers, so that I can easily track when each subscription expires.

#### Acceptance Criteria

1. WHEN the HTML export is opened THEN the system SHALL display a live countdown timer (days, hours, minutes, seconds) for each active subscription
2. WHEN a subscription has less than 7 days remaining THEN the system SHALL highlight the countdown with warning colors (orange/red)
3. WHEN a subscription expires THEN the system SHALL display "Expired" status with appropriate visual indicator
4. WHEN the countdown reaches zero THEN the system SHALL automatically update the display to show expired status

### Requirement 2

**User Story:** As a user, I want interactive buttons in Telegram to manage my subscriptions easily, so that I can perform actions without typing commands.

#### Acceptance Criteria

1. WHEN viewing subscription list THEN the system SHALL display inline buttons for common actions (Add, Delete, Renew, Export)
2. WHEN a user taps on a subscription THEN the system SHALL show detail view with action buttons (Renew, Delete, Edit)
3. WHEN a user taps Delete button THEN the system SHALL show confirmation dialog before deleting
4. WHEN a user taps Renew button THEN the system SHALL show renewal options (1 month, 3 months, 6 months, 1 year)

### Requirement 3

**User Story:** As a user, I want the subscription HTML export to have beautiful animations and modern design, so that it looks professional and easy to read.

#### Acceptance Criteria

1. WHEN the HTML export is generated THEN the system SHALL include smooth CSS animations for card appearances
2. WHEN hovering over subscription cards THEN the system SHALL display hover effects with subtle animations
3. WHEN the page loads THEN the system SHALL animate elements with staggered fade-in effects
4. WHEN displaying progress bars THEN the system SHALL animate the fill with smooth transitions

### Requirement 4

**User Story:** As a user, I want to filter and sort my subscriptions in the HTML export, so that I can find specific subscriptions quickly.

#### Acceptance Criteria

1. WHEN viewing HTML export THEN the system SHALL provide filter buttons for status (All, Active, Expiring Soon, Expired)
2. WHEN viewing HTML export THEN the system SHALL provide sort options (by name, amount, expiry date)
3. WHEN a filter is applied THEN the system SHALL update the display with smooth animation
4. WHEN searching by name THEN the system SHALL filter subscriptions in real-time as user types

### Requirement 5

**User Story:** As a user, I want to see subscription statistics and insights in the HTML export, so that I can understand my subscription spending better.

#### Acceptance Criteria

1. WHEN viewing HTML export THEN the system SHALL display total monthly and yearly cost prominently
2. WHEN viewing HTML export THEN the system SHALL show cost breakdown by category with percentage
3. WHEN viewing HTML export THEN the system SHALL display upcoming renewals in the next 30 days
4. WHEN viewing HTML export THEN the system SHALL show a timeline view of subscription periods

### Requirement 6

**User Story:** As a user, I want the subscription display in Telegram to be more visual and informative, so that I can quickly understand my subscription status.

#### Acceptance Criteria

1. WHEN viewing subscription list in Telegram THEN the system SHALL display visual progress indicators using emoji
2. WHEN a subscription is expiring soon THEN the system SHALL show warning emoji and highlight text
3. WHEN displaying subscription amount THEN the system SHALL format with proper currency and period notation
4. WHEN displaying dates THEN the system SHALL show relative time (e.g., "3 hari lagi") alongside absolute dates

