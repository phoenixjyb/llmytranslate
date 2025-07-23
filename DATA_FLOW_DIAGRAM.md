# Translation Service - Data Flow Diagram

```mermaid
sequenceDiagram
    participant Client as Client Application
    participant LB as Load Balancer
    participant API as Translation API
    participant Auth as Auth Service
    participant Cache as Redis Cache
    participant TE as Translation Engine
    participant Stats as Statistics Service
    participant Ollama as Ollama Client
    participant LLM as Local LLM
    participant DB as Database

    %% Authentication and Request Processing
    Client->>+LB: POST /api/trans/vip/translate
    Note over Client,LB: Request: {q: "hello", from: "en", to: "zh", appid: "xxx", sign: "xxx"}
    
    LB->>+API: Forward request
    API->>+Auth: Validate API credentials
    Auth->>+DB: Check API key & permissions
    DB-->>-Auth: Validation result
    Auth-->>-API: Authentication success/failure
    
    alt Authentication fails
        API-->>-LB: 401 Unauthorized
        LB-->>-Client: Error response
    else Authentication succeeds
        
        %% Cache Check
        API->>+Cache: Check for cached translation
        Cache-->>-API: Cache miss/hit result
        
        alt Cache hit
            API-->>-LB: Cached translation result
            LB-->>-Client: JSON response
            API->>Stats: Log cache hit metrics
        else Cache miss
            
            %% Translation Process
            API->>+TE: Process translation request
            Note over TE: Validate input, prepare prompt
            
            TE->>+Ollama: Send translation prompt
            Note over Ollama,LLM: Prompt: "Translate 'hello' from English to Chinese"
            
            Ollama->>+LLM: Execute translation
            Note over LLM: Process with local model
            LLM-->>-Ollama: Translation result
            Ollama-->>-TE: Return: "你好"
            
            %% Post-processing
            TE->>Cache: Store translation in cache
            TE->>+Stats: Log request metrics
            Note over Stats: Record: tokens used, response time, success
            Stats->>+DB: Persist statistics
            DB-->>-Stats: Confirmation
            Stats-->>-TE: Metrics logged
            
            TE-->>-API: Translation response
            API-->>-LB: JSON response
            LB-->>-Client: Final result
            Note over Client,LB: Response: {"from":"en","to":"zh","trans_result":[{"src":"hello","dst":"你好"}]}
        end
    end

    %% Health Check Flow
    rect rgb(240, 248, 255)
        Client->>+LB: GET /api/health
        LB->>+API: Forward health check
        API->>+TE: Check translation engine
        TE->>+Ollama: Ping Ollama service
        Ollama->>+LLM: Check model availability
        LLM-->>-Ollama: Model status
        Ollama-->>-TE: Service status
        TE-->>-API: Health status
        API-->>-LB: Health response
        LB-->>-Client: {"status": "healthy", "model": "available"}
    end

    %% Statistics Query Flow
    rect rgb(255, 248, 240)
        Client->>+LB: GET /api/stats
        LB->>+API: Forward stats request
        API->>+Auth: Validate admin access
        Auth-->>-API: Admin authorization
        API->>+Stats: Get statistics
        Stats->>+DB: Query metrics data
        DB-->>-Stats: Statistics data
        Stats-->>-API: Formatted stats
        API-->>-LB: Statistics response
        LB-->>-Client: {"requests": 1000, "success_rate": 0.98, "avg_tokens": 15}
    end
```
