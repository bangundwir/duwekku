# Implementation Plan

- [x] 1. Create Subscription Formatter Module




  - [ ] 1.1 Create `src/subscription/formatter.py` with SubscriptionFormatter class
    - Implement `format_countdown(days: int) -> str` method
    - Implement `format_progress_emoji(progress: float) -> str` method
    - Implement `format_amount(amount: float) -> str` method
    - Implement `format_relative_date(target_date: date) -> str` method
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ]* 1.2 Write property test for emoji progress indicator
    - **Property 7: Emoji progress indicator accuracy**
    - **Validates: Requirements 6.1**
  - [ ]* 1.3 Write property test for currency formatting
    - **Property 8: Currency formatting consistency**
    - **Validates: Requirements 6.3**
  - [ ]* 1.4 Write property test for relative date formatting
    - **Property 9: Relative date formatting accuracy**
    - **Validates: Requirements 6.4**
  - [x]* 1.5 Write property test for warning indicators




    - **Property 1: Warning indicators for expiring subscriptions**
    - **Validates: Requirements 1.2, 6.2**

- [ ] 2. Create Subscription Keyboard Builder
  - [ ] 2.1 Create `src/subscription/keyboard.py` with SubscriptionKeyboardBuilder class
    - Implement `main_menu() -> InlineKeyboardMarkup` method
    - Implement `subscription_detail(sub_id: int) -> InlineKeyboardMarkup` method
    - Implement `delete_confirmation(sub_id: int) -> InlineKeyboardMarkup` method


    - Implement `renew_options(sub_id: int) -> InlineKeyboardMarkup` method




    - Implement `filter_options() -> InlineKeyboardMarkup` method
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 2.2 Write property test for detail keyboard
    - **Property 3: Detail keyboard contains action buttons**
    - **Validates: Requirements 2.2**


- [x] 3. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Enhance HTML Exporter with Live Countdown
  - [ ] 4.1 Update `src/utils/exporter.py` to add countdown JavaScript
    - Add `_generate_countdown_js()` method for live timer

    - Update `subscriptions_to_html()` to include countdown elements

    - Add data attributes for countdown target dates
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [ ]* 4.2 Write property test for expired status display
    - **Property 2: Expired status display**
    - **Validates: Requirements 1.3**



- [ ] 5. Add CSS Animations to HTML Export
  - [ ] 5.1 Update `src/utils/exporter.py` to add animation CSS
    - Add `_generate_animation_css()` method
    - Implement card fade-in animations with stagger effect
    - Implement hover effects for subscription cards
    - Implement progress bar fill animation
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 6. Add Filter and Sort Functionality to HTML Export
  - [ ] 6.1 Update `src/utils/exporter.py` to add filter/sort JavaScript
    - Add `_generate_filter_js()` method
    - Implement status filter buttons (All, Active, Expiring Soon, Expired)
    - Implement sort options (name, amount, expiry date)
    - Implement real-time search functionality
    - _Requirements: 4.1, 4.2, 4.3, 4.4_







- [ ] 7. Add Statistics Section to HTML Export
  - [ ] 7.1 Update `src/utils/exporter.py` to add statistics section
    - Add `_generate_statistics_section()` method

    - Display total monthly and yearly cost
    - Display category breakdown with percentages
    - Display upcoming renewals (next 30 days)
    - Add timeline view for subscription periods
    - _Requirements: 5.1, 5.2, 5.3, 5.4_



  - [ ]* 7.2 Write property test for total cost calculation
    - **Property 4: Total cost calculation accuracy**
    - **Validates: Requirements 5.1**
  - [ ]* 7.3 Write property test for category breakdown
    - **Property 5: Category breakdown accuracy**
    - **Validates: Requirements 5.2**
  - [ ]* 7.4 Write property test for upcoming renewals filter
    - **Property 6: Upcoming renewals filter**
    - **Validates: Requirements 5.3**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Integrate Enhanced Components into Bot Commands
  - [ ] 9.1 Update `src/bot/commands.py` to use new formatter
    - Import and use SubscriptionFormatter for display
    - Update subscription list display with emoji progress
    - Update countdown display with warning indicators
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ] 9.2 Update `src/bot/commands.py` to use new keyboard builder
    - Import and use SubscriptionKeyboardBuilder
    - Update callback handlers for new button actions
    - Add confirmation dialogs for delete
    - Add renewal period selection
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 10. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
