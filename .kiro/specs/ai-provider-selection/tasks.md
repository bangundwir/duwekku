# Implementation Plan

- [x] 1. Update configuration and settings
  - [x] 1.1 Add Groq API settings to config/settings.py
    - Add groq_api_key, groq_base_url, groq_model fields
    - Add default_ai_provider field
    - _Requirements: 1.1, 3.4_
  
  - [x] 1.2 Update .env.example with new environment variables
    - Add GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL
    - Add DEFAULT_AI_PROVIDER
    - _Requirements: 1.1, 3.4_

- [x] 2. Create AI Provider interface and base classes
  - [x] 2.1 Create AIProvider abstract base class
    - Create src/ai/providers/__init__.py
    - Create src/ai/providers/base.py with AIProvider ABC
    - Define AIModel and ProviderInfo dataclasses
    - Define abstract methods: parse_transaction(), list_models(), test_connection(), set_model()
    - _Requirements: 3.1_
  
  - [ ]* 2.2 Write property test for provider display completeness
    - **Property 2: Provider Display Completeness**
    - **Validates: Requirements 1.2, 2.2**

- [x] 3. Implement Poe Provider
  - [x] 3.1 Refactor existing parser to PoeProvider class
    - Create src/ai/providers/poe.py
    - Move existing AIParser logic to PoeProvider
    - Implement AIProvider interface methods
    - Implement list_models() with predefined Poe models
    - _Requirements: 3.2_

- [x] 4. Implement Groq Provider
  - [x] 4.1 Create GroqProvider class
    - Create src/ai/providers/groq.py
    - Implement parse_transaction() using OpenAI-compatible API
    - Implement list_models() fetching from Groq API endpoint
    - Implement test_connection() and set_model()
    - _Requirements: 3.3_
  
  - [ ]* 4.2 Write property test for graceful error handling
    - **Property 9: Graceful Error Handling**
    - **Validates: Requirements 5.1, 5.4**

- [x] 5. Implement User Preference storage
  - [x] 5.1 Create UserPreference model
    - Add UserPreference dataclass to src/models/
    - Include user_id, provider, model, updated_at fields
    - _Requirements: 4.1_
  
  - [x] 5.2 Add user_preferences table to database
    - Update SQLite schema in sqlite_db.py
    - Update TiDB schema in tidb_db.py
    - Add methods: save_user_preference(), get_user_preference()
    - _Requirements: 4.1_
  
  - [ ]* 5.3 Write property test for user preference persistence round trip
    - **Property 7: User Preference Persistence Round Trip**
    - **Validates: Requirements 4.1**

- [x] 6. Implement Provider Manager
  - [x] 6.1 Create ProviderManager class
    - Create src/ai/provider_manager.py
    - Implement _init_providers() to initialize configured providers
    - Implement get_provider() with user preference lookup
    - Implement set_user_provider() and set_user_model()
    - Implement list_providers() and list_models()
    - _Requirements: 1.1, 3.5, 4.2, 4.3_
  
  - [ ]* 6.2 Write property test for provider configuration loading
    - **Property 1: Provider Configuration Loading**
    - **Validates: Requirements 1.1, 3.4**
  
  - [ ]* 6.3 Write property test for provider list completeness
    - **Property 3: Provider List Completeness**
    - **Validates: Requirements 1.3**
  
  - [ ]* 6.4 Write property test for provider switch consistency
    - **Property 4: Provider Switch Consistency**
    - **Validates: Requirements 1.4, 4.1, 4.2**
  
  - [ ]* 6.5 Write property test for unconfigured provider rejection
    - **Property 5: Unconfigured Provider Rejection**
    - **Validates: Requirements 1.5**
  
  - [ ]* 6.6 Write property test for model switch consistency
    - **Property 6: Model Switch Consistency**
    - **Validates: Requirements 2.3**
  
  - [ ]* 6.7 Write property test for default provider fallback
    - **Property 8: Default Provider Fallback**
    - **Validates: Requirements 4.3**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement provider commands
  - [x] 8.1 Add /provider command to CommandHandler
    - Implement cmd_provider() for showing current provider
    - Implement /provider list subcommand
    - Implement /provider set [name] subcommand
    - _Requirements: 1.2, 1.3, 1.4, 1.5_
  
  - [x] 8.2 Add /models and /model commands to CommandHandler
    - Implement cmd_models() to list available models
    - Implement cmd_model() with set subcommand
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 9. Update bot handler and main entry point
  - [x] 9.1 Update BotHandler to use ProviderManager
    - Inject ProviderManager into BotHandler
    - Update handle_message() to get provider per user
    - Register new command handlers
    - _Requirements: 3.5, 4.2_
  
  - [x] 9.2 Update main.py initialization
    - Initialize ProviderManager with settings
    - Pass ProviderManager to BotHandler and CommandHandler
    - _Requirements: 1.1_

- [x] 10. Update existing AI parser module
  - [x] 10.1 Update src/ai/__init__.py exports
    - Export ProviderManager, AIProvider, providers
    - Maintain backward compatibility with existing imports
    - _Requirements: 3.1_

- [x] 11. Final Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.
