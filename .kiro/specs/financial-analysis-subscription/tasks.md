# Implementation Plan

- [x] 1. Create Subscription Model and Database Schema




  - [ ] 1.1 Create Subscription dataclass model
    - Create `src/models/subscription.py` with Subscription dataclass
    - Include properties: id, user_id, name, amount, category, start_date, end_date, is_active, notes, created_at, synced
    - Implement `days_remaining` and `status` computed properties
    - Implement `to_dict()` and `from_dict()` methods


    - Implement `format_display()` for Telegram output

    - _Requirements: 3.1, 3.2, 7.2_
  - [x] 1.2 Write property test for Subscription status calculation


    - **Property 7: Subscription Status Correctness**
    - **Validates: Requirements 3.3, 3.4, 7.2**
  - [x] 1.3 Write property test for days_remaining calculation




    - **Property 12: Days Remaining Calculation**
    - **Validates: Requirements 3.2**
  - [ ] 1.4 Extend database schema for subscriptions table
    - Add `create_subscriptions_table()` method to SQLite and TiDB database classes
    - Create table with columns: id, user_id, name, amount, category, start_date, end_date, is_active, notes, created_at, synced
    - Add indexes for user_id, end_date, category


    - _Requirements: 3.1_


- [x] 2. Implement Subscription Manager

  - [ ] 2.1 Create SubscriptionManager class
    - Create `src/subscription/manager.py`

    - Implement `add_subscription()` method
    - Implement `get_subscriptions()` method with include_expired filter
    - Implement `get_subscription_by_id()` method
    - Implement `delete_subscription()` method

    - Implement `renew_subscription()` method
    - _Requirements: 3.1, 3.2, 3.5, 7.3_

  - [ ] 2.2 Write property test for subscription CRUD round-trip
    - **Property 6: Subscription CRUD Round-Trip**




    - **Validates: Requirements 3.1**
  - [x] 2.3 Write property test for subscription deletion

    - **Property 8: Subscription Deletion Completeness**
    - **Validates: Requirements 3.5**
  - [x] 2.4 Write property test for subscription renewal

    - **Property 11: Subscription Renewal Update**
    - **Validates: Requirements 7.3**

  - [ ] 2.5 Implement subscription query methods
    - Implement `get_expiring_soon()` for subscriptions within N days of expiration
    - Implement `get_monthly_cost()` for total and category breakdown

    - Implement `get_by_category()` for grouping subscriptions
    - _Requirements: 3.3, 4.2, 4.3_

  - [ ] 2.6 Write property test for category aggregation
    - **Property 9: Category Aggregation Correctness**
    - **Validates: Requirements 4.2, 4.3**


- [x] 3. Checkpoint - Ensure subscription tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Financial Analyzer
  - [ ] 4.1 Create FinancialHealth dataclass
    - Create `src/analysis/analyzer.py`

    - Define FinancialHealth dataclass with: score, income_total, expense_total, balance, expense_ratio, savings_rate, top_categories, trend, month_comparison, warnings, suggestions
    - _Requirements: 1.1, 1.2_

  - [ ] 4.2 Implement health score calculation
    - Implement `calculate_health_score()` with expense ratio (40%), savings rate (40%), category diversity (20%) components

    - Score must be bounded 0-100
    - _Requirements: 1.1_
  - [x] 4.3 Write property test for health score bounds

    - **Property 1: Health Score Bounds**
    - **Validates: Requirements 1.1**



  - [ ] 4.4 Implement expense breakdown analysis
    - Implement `get_expense_breakdown()` to calculate category amounts and percentages
    - Percentages must sum to 100%
    - _Requirements: 1.2_

  - [ ] 4.5 Write property test for expense breakdown consistency
    - **Property 2: Expense Breakdown Consistency**
    - **Validates: Requirements 1.2**
  - [x] 4.6 Implement month comparison

    - Implement `compare_months()` to compare current vs previous month
    - Calculate trend: improving, stable, declining
    - _Requirements: 1.4_
  - [x] 4.7 Write property test for month comparison trend

    - **Property 4: Month Comparison Trend Accuracy**
    - **Validates: Requirements 1.4**
  - [x] 4.8 Implement suggestions generator

    - Implement `generate_suggestions()` based on financial health
    - Identify top 3 expense categories



    - Flag categories exceeding 30% of expenses
    - Generate warnings for expense ratio > 80%
    - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4_
  - [x] 4.9 Write property test for financial warnings

    - **Property 3: Financial Warning Correctness**
    - **Validates: Requirements 1.3, 2.3, 2.4**
  - [ ] 4.10 Write property test for top categories ordering
    - **Property 5: Top Categories Ordering**

    - **Validates: Requirements 2.1**
  - [ ] 4.11 Implement main analyze() method
    - Combine all analysis components
    - Handle insufficient data case (< 5 transactions)

    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Checkpoint - Ensure analyzer tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 6. Enhance HTML Exporter
  - [ ] 6.1 Add subscription section to HTML export
    - Extend `src/utils/exporter.py`

    - Implement `_generate_subscription_section()` with status indicators
    - Group subscriptions by category with subtotals
    - _Requirements: 5.4_

  - [ ] 6.2 Add financial analysis section to HTML export
    - Implement `_generate_analysis_section()` with health score display
    - Include expense breakdown chart data
    - Include warnings and suggestions



    - _Requirements: 5.5_
  - [ ] 6.3 Implement interactive HTML features
    - Add Chart.js for visualizations

    - Add client-side JavaScript filters for date, category, type
    - Implement responsive dark theme CSS
    - _Requirements: 5.2, 5.3, 6.1, 6.2, 6.3, 6.4_
  - [x] 6.4 Implement to_html_full() method


    - Combine transactions, subscriptions, and analysis into single HTML
    - Ensure all data is included
    - _Requirements: 5.1_
  - [ ] 6.5 Write property test for HTML export completeness
    - **Property 10: HTML Export Data Completeness**
    - **Validates: Requirements 5.1, 5.4, 5.5**

- [ ] 7. Implement Bot Commands
  - [ ] 7.1 Implement /analysis command
    - Add `cmd_analysis()` to CommandHandler
    - Display health score, breakdown, trend, warnings, suggestions
    - Handle insufficient data case
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4_
  - [ ] 7.2 Implement /addsub command
    - Add `cmd_addsub()` to CommandHandler
    - Parse: /addsub [name] [amount] [start_date] [end_date] [category]
    - Validate inputs and create subscription
    - _Requirements: 3.1, 4.1_
  - [ ] 7.3 Implement /subs command
    - Add `cmd_subs()` to CommandHandler
    - Display all subscriptions grouped by category
    - Show status indicators (active, expiring_soon, expired)
    - _Requirements: 3.2, 3.3, 3.4, 4.2_
  - [ ] 7.4 Implement /delsub command
    - Add `cmd_delsub()` to CommandHandler
    - Parse: /delsub [id]
    - Delete subscription and confirm
    - _Requirements: 3.5_
  - [ ] 7.5 Implement /renewsub command
    - Add `cmd_renewsub()` to CommandHandler
    - Parse: /renewsub [id] [new_end_date]
    - Update subscription end date
    - _Requirements: 7.3_
  - [ ] 7.6 Implement /subcost command
    - Add `cmd_subcost()` to CommandHandler
    - Display total monthly cost and category breakdown
    - _Requirements: 4.3_
  - [ ] 7.7 Implement /export command
    - Add `cmd_export()` to CommandHandler
    - Generate full HTML report
    - Send as document attachment
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4_

- [ ] 8. Register Commands and Integration
  - [ ] 8.1 Register new commands in bot handler
    - Add command handlers to Application
    - Update help text with new commands
    - _Requirements: All_
  - [ ] 8.2 Initialize new components in main.py
    - Create SubscriptionManager instance
    - Create FinancialAnalyzer instance
    - Wire dependencies
    - _Requirements: All_

- [ ] 9. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
