# Implementation Plan

- [x] 1. Set up project structure and configuration



  - [x] 1.1 Initialize UV project with pyproject.toml

    - Create pyproject.toml with all dependencies (python-telegram-bot, openai, pymysql, pydantic-settings, pytest, hypothesis)
    - Set up project metadata and Python version requirement
    - _Requirements: 4.1, 4.2_


  - [ ] 1.2 Create directory structure and base files
    - Create src/, config/, tests/, data/ directories


    - Create __init__.py files for all packages
    - _Requirements: 4.1_




  - [ ] 1.3 Implement settings module
    - Create config/settings.py with Pydantic Settings
    - Create .env.example template
    - _Requirements: 4.2_

- [x] 2. Implement data models


  - [ ] 2.1 Create Transaction model
    - Implement Transaction dataclass with all fields (id, user_id, type, amount, category, description, created_at, synced)
    - Implement to_dict() and from_dict() methods
    - Implement format_display() for Telegram output
    - _Requirements: 2.4, 1.3_




  - [ ]* 2.2 Write property test for Transaction display completeness
    - **Property 2: Transaction Display Completeness**
    - **Validates: Requirements 1.3, 2.4**
  - [x] 2.3 Create ParsedTransaction model


    - Implement ParsedTransaction dataclass for AI parser output
    - Include type, amount, category, description, confidence fields
    - _Requirements: 6.4_


  - [ ]* 2.4 Write property test for parser output structure
    - **Property 8: Parser Output Structure**
    - **Validates: Requirements 6.4**

- [ ] 3. Implement database layer
  - [ ] 3.1 Implement SQLite database module
    - Create src/database/sqlite_db.py with SQLiteDB class
    - Implement init_tables() to create schema
    - Implement insert_transaction(), get_transactions(), delete_transaction()
    - Implement mark_synced() and get_pending_sync()
    - _Requirements: 3.1, 3.3_
  - [ ] 3.2 Implement TiDB Cloud database module
    - Create src/database/tidb_db.py with TiDBCloud class

    - Implement connection with SSL certificate
    - Implement insert_transaction(), delete_transaction(), test_connection()
    - _Requirements: 3.2_



  - [ ] 3.3 Implement Database Manager
    - Create src/database/manager.py with DatabaseManager class
    - Implement save_transaction() with dual-write logic
    - Implement get_transactions(), get_summary(), delete_transaction()
    - Implement sync_pending() for background sync
    - _Requirements: 1.2, 3.1, 3.2, 3.3_

  - [ ]* 3.4 Write property test for transaction persistence round trip
    - **Property 1: Transaction Persistence Round Trip**
    - **Validates: Requirements 1.2, 3.1**
  - [ ]* 3.5 Write property test for pending sync marking
    - **Property 5: Pending Sync Marking**




    - **Validates: Requirements 3.3**
  - [ ]* 3.6 Write property test for delete removes from database
    - **Property 6: Delete Removes from Database**
    - **Validates: Requirements 5.1**

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement AI parser
  - [ ] 5.1 Create amount normalization utility
    - Implement function to convert Indonesian amount strings (rb, jt, k) to numeric


    - Handle various formats: "50rb", "5jt", "100k", "1.5jt"
    - _Requirements: 6.3_
  - [ ]* 5.2 Write property test for amount normalization
    - **Property 7: Amount Normalization**
    - **Validates: Requirements 6.3**
  - [ ] 5.3 Implement AI Parser class
    - Create src/ai/parser.py with AIParser class




    - Implement _build_prompt() with Indonesian language support
    - Implement parse_transaction() using Poe API (OpenAI client)
    - Implement _parse_response() to extract JSON from AI response


    - _Requirements: 1.1, 6.1, 6.2, 6.4, 6.5_

- [ ] 6. Implement bot handlers
  - [ ] 6.1 Implement command handlers
    - Create src/bot/commands.py with CommandHandler class
    - Implement cmd_start() with welcome message
    - Implement cmd_history() to show last 10 transactions
    - Implement cmd_summary() with optional month/year params
    - Implement cmd_delete() to remove transaction by ID
    - _Requirements: 1.5, 2.1, 2.2, 2.3, 5.1, 5.2, 5.3_
  - [ ]* 6.2 Write property test for history limit and order
    - **Property 3: History Limit and Order**
    - **Validates: Requirements 2.1**
  - [ ]* 6.3 Write property test for summary calculation correctness
    - **Property 4: Summary Calculation Correctness**
    - **Validates: Requirements 2.2, 2.3**
  - [ ] 6.4 Implement bot handler
    - Create src/bot/handler.py with BotHandler class
    - Implement handle_message() for transaction parsing
    - Wire up command handlers to Telegram bot
    - Implement error handling and user feedback
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.4_
  - [ ]* 6.5 Write property test for error handling resilience
    - **Property 9: Error Handling Resilience**
    - **Validates: Requirements 4.4**

- [ ] 7. Implement main entry point
  - [ ] 7.1 Create main.py
    - Create src/main.py as entry point
    - Initialize all components (settings, database, AI parser, bot)
    - Implement startup sync for pending transactions
    - Start bot polling
    - _Requirements: 3.4, 4.3_

- [ ] 8. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
