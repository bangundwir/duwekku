# Requirements Document

## Introduction

Fitur untuk memilih AI provider yang digunakan oleh bot Telegram Money Tracker. Saat ini bot hanya mendukung Poe API, fitur ini akan menambahkan dukungan untuk multiple AI providers termasuk Groq, OpenAI, dan provider lainnya. Pengguna dapat memilih provider dan model melalui konfigurasi atau command Telegram.

## Glossary

- **AI Provider**: Layanan API yang menyediakan model AI untuk parsing transaksi (Poe, Groq, OpenAI, dll)
- **Model**: Versi spesifik dari AI yang digunakan (contoh: gemini-2.5-flash, llama-3.3-70b-versatile)
- **Bot**: Aplikasi Telegram bot yang menerima dan memproses pesan pengguna
- **AI Parser**: Komponen yang menggunakan AI provider untuk mengekstrak informasi transaksi dari pesan natural

## Requirements

### Requirement 1

**User Story:** As a user, I want to choose which AI provider to use, so that I can use my preferred AI service or switch when one is unavailable.

#### Acceptance Criteria

1. WHEN the Bot starts THEN the Bot SHALL load AI provider configuration from environment variables
2. WHEN a user sends "/provider" command THEN the Bot SHALL display the currently active AI provider and model
3. WHEN a user sends "/provider list" command THEN the Bot SHALL display all available AI providers with their status (configured/not configured)
4. WHEN a user sends "/provider set [provider_name]" command THEN the Bot SHALL switch to the specified provider if it is configured
5. IF a user attempts to set an unconfigured provider THEN the Bot SHALL inform the user that the provider API key is not configured

### Requirement 2

**User Story:** As a user, I want to see available AI models from my selected provider, so that I can choose the best model for my needs.

#### Acceptance Criteria

1. WHEN a user sends "/models" command THEN the Bot SHALL fetch and display available models from the current AI provider
2. WHEN displaying models THEN the Bot SHALL show model ID and display name for each model
3. WHEN a user sends "/model set [model_name]" command THEN the Bot SHALL switch to the specified model
4. IF the model list fetch fails THEN the Bot SHALL display an error message and suggest checking API key configuration

### Requirement 3

**User Story:** As a developer, I want to support multiple AI providers with a unified interface, so that adding new providers is straightforward.

#### Acceptance Criteria

1. THE Bot SHALL implement a common AIProvider interface with methods: parse_transaction(), list_models(), test_connection()
2. THE Bot SHALL support Poe API provider with existing functionality
3. THE Bot SHALL support Groq API provider using OpenAI-compatible endpoint (https://api.groq.com/openai/v1)
4. THE Bot SHALL allow configuration of each provider through separate environment variables
5. WHEN parsing a transaction THEN the AI Parser SHALL use the currently selected provider and model

### Requirement 4

**User Story:** As a user, I want the bot to remember my provider preference, so that I don't have to set it every time.

#### Acceptance Criteria

1. WHEN a user changes their AI provider preference THEN the Bot SHALL save the preference to the database
2. WHEN the Bot receives a message from a user THEN the Bot SHALL use that user's saved provider preference
3. IF a user has no saved preference THEN the Bot SHALL use the default provider from configuration

### Requirement 5

**User Story:** As a developer, I want proper error handling for AI provider operations, so that the bot remains stable when providers fail.

#### Acceptance Criteria

1. IF an AI provider API call fails THEN the Bot SHALL log the error and return a user-friendly message
2. IF the current provider is unavailable THEN the Bot SHALL suggest the user to try a different provider
3. WHEN testing provider connection THEN the Bot SHALL validate API key and endpoint accessibility
4. THE Bot SHALL implement timeout handling for AI provider API calls

