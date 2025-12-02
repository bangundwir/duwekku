# Implementation Plan

- [x] 1. Setup database schema and models for admin dashboard




  - [x] 1.1 Create BotUser model with all required fields

    - Add user_id, username, first_name, registered_at, last_active, is_blocked


    - Add subscription_id, daily/monthly query limits and usage counters


    - _Requirements: 1.1, 3.4_


  - [x] 1.2 Create SubscriptionPlan model


    - Add id, name, daily_query_limit, monthly_query_limit, price, duration_days, features
    - _Requirements: 2.3_

  - [ ] 1.3 Create UserSubscription model
    - Add id, user_id, plan_id, start_date, end_date, status, assigned_by, assigned_at
    - _Requirements: 2.1, 2.2_





  - [ ] 1.4 Create AdminSession model for authentication
    - Add token, admin_username, created_at, expires_at, is_valid

    - _Requirements: 6.1_
  - [x] 1.5 Create database migration to add new tables

    - Add bot_users, subscription_plans, user_subscriptions, admin_sessions tables
    - _Requirements: 1.1, 2.1, 6.1_

  - [ ]* 1.6 Write property test for model field completeness
    - **Property 1: User list contains required fields**


    - **Property 6: Subscription plan completeness**

    - **Validates: Requirements 1.1, 2.3**


- [ ] 2. Implement User Service
  - [ ] 2.1 Implement get_users with pagination and search
    - Support page, per_page, and search parameters
    - Return PaginatedResult with users and total_count



    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 2.2 Implement user sorting by registration date

    - Default sort by registered_at descending
    - _Requirements: 1.4_
  - [x] 2.3 Implement block_user and unblock_user methods


    - Update is_blocked status in database
    - _Requirements: 4.1, 4.2_
  - [ ] 2.4 Implement delete_user method
    - Remove user and related data from database

    - _Requirements: 4.3_



  - [ ] 2.5 Implement user registration tracking in bot handler
    - Record new users when they first interact with bot

    - Update last_active on each interaction
    - _Requirements: 1.1, 7.3_
  - [x]* 2.6 Write property tests for User Service


    - **Property 2: User count consistency**

    - **Property 3: Search filter correctness**

    - **Property 4: User list sorting**
    - **Validates: Requirements 1.2, 1.3, 1.4**

- [ ] 3. Implement Subscription Service
  - [ ] 3.1 Implement get_plans and create_plan methods
    - CRUD operations for subscription plans

    - _Requirements: 2.3_
  - [x] 3.2 Implement assign_subscription method


    - Assign plan to user with start/end dates


    - Record assignment timestamp and admin

    - _Requirements: 2.2_
  - [ ] 3.3 Implement subscription expiration check
    - Mark expired subscriptions and update user status



    - _Requirements: 2.4_

  - [ ]* 3.4 Write property tests for Subscription Service
    - **Property 5: Subscription assignment persistence**
    - **Validates: Requirements 2.2**


- [x] 4. Implement Query Limiter Service


  - [ ] 4.1 Implement set_limits method
    - Set daily and monthly query limits for user
    - _Requirements: 3.1, 3.2_

  - [ ] 4.2 Implement check_limit and increment_usage methods
    - Check if user has exceeded limits
    - Increment usage counter on each query

    - _Requirements: 3.1, 3.2, 3.3_
  - [ ] 4.3 Implement get_usage method
    - Return current daily and monthly usage stats



    - _Requirements: 3.4_
  - [x] 4.4 Integrate query limiter with bot handler

    - Check limits before processing commands
    - Send notification when limit reached
    - _Requirements: 3.3_

  - [ ]* 4.5 Write property tests for Query Limiter
    - **Property 7: Query limit enforcement**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Auth Service
  - [x] 6.1 Implement login method with password hashing

    - Validate credentials and create session token

    - _Requirements: 6.1, 6.2_
  - [ ] 6.2 Implement logout and session validation
    - Invalidate session on logout
    - Check session expiration (30 min timeout)
    - _Requirements: 6.3, 6.4_
  - [x] 6.3 Create auth middleware for API protection

    - Validate session token on protected routes
    - Return 401 for invalid/expired sessions

    - _Requirements: 6.1_
  - [ ]* 6.4 Write property tests for Auth Service
    - **Property 11: Authentication enforcement**

    - **Property 12: Session invalidation**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [ ] 7. Implement Block/Delete functionality
  - [ ] 7.1 Integrate block check in bot handler
    - Reject commands from blocked users

    - Display blocked message
    - _Requirements: 4.4_
  - [ ]* 7.2 Write property tests for block enforcement
    - **Property 8: Block enforcement**

    - **Property 9: Block-unblock round trip**
    - **Property 10: User deletion completeness**


    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 8. Implement Admin API endpoints
  - [x] 8.1 Create FastAPI router with auth middleware

    - Setup FastAPI app with CORS
    - Apply auth middleware to protected routes
    - _Requirements: 6.1_
  - [x] 8.2 Implement user management endpoints



    - GET /api/admin/users (list with pagination/search)
    - GET /api/admin/users/{user_id} (detail)
    - PUT /api/admin/users/{user_id}/block

    - PUT /api/admin/users/{user_id}/unblock
    - DELETE /api/admin/users/{user_id}
    - _Requirements: 1.1, 1.3, 4.1, 4.2, 4.3_

  - [ ] 8.3 Implement subscription endpoints
    - GET /api/admin/plans
    - POST /api/admin/plans

    - PUT /api/admin/users/{user_id}/subscription
    - _Requirements: 2.2, 2.3_
  - [ ] 8.4 Implement query limit endpoints
    - PUT /api/admin/users/{user_id}/limits

    - GET /api/admin/users/{user_id}/usage
    - _Requirements: 3.1, 3.2, 3.4_
  - [ ] 8.5 Implement analytics endpoints
    - GET /api/admin/stats (dashboard summary)

    - GET /api/admin/analytics/queries (query volume chart data)
    - _Requirements: 7.1, 7.2_
  - [ ]* 8.6 Write property test for statistics accuracy
    - **Property 13: Statistics accuracy**

    - **Validates: Requirements 7.1**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.




- [ ] 10. Create Admin Dashboard Frontend
  - [x] 10.1 Setup HTML base template with Tailwind CSS

    - Create responsive layout with sidebar navigation
    - Setup Alpine.js for interactivity
    - _Requirements: 5.1, 5.2_

  - [x] 10.2 Create login page


    - Login form with username/password
    - Error message display
    - _Requirements: 6.1, 6.2_
  - [ ] 10.3 Create dashboard home page
    - Display summary statistics cards
    - Show query volume chart
    - _Requirements: 7.1, 7.2_
  - [ ] 10.4 Create user management page
    - Paginated user table with search
    - Block/unblock/delete actions
    - User detail modal
    - _Requirements: 1.1, 1.3, 4.1, 4.2, 4.3_
  - [ ] 10.5 Create subscription management page
    - List subscription plans
    - Create new plan form
    - Assign subscription to user
    - _Requirements: 2.2, 2.3_
  - [ ] 10.6 Create user detail page with query limits
    - Display user info and subscription status
    - Set query limits form
    - Show usage statistics
    - _Requirements: 2.1, 3.1, 3.2, 3.4, 7.3_
  - [ ] 10.7 Apply consistent styling and UX
    - Alternating row colors in tables
    - Hover effects and loading indicators
    - Success/error notifications
    - _Requirements: 5.3, 5.4_

- [ ] 11. Integration and configuration
  - [ ] 11.1 Add admin credentials to settings
    - Add ADMIN_USERNAME and ADMIN_PASSWORD to .env
    - Update Settings class
    - _Requirements: 6.1_
  - [ ] 11.2 Create startup script for admin dashboard
    - Run FastAPI server alongside bot
    - Configure port and host
    - _Requirements: 5.1_
  - [ ] 11.3 Update README with admin dashboard documentation
    - Document setup and configuration
    - Document API endpoints
    - _Requirements: 5.2_

- [ ] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
