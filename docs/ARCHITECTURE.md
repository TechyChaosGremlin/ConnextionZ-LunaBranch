# ConnextionZ Platform Architecture

## System Design Overview

The ConnextionZ platform is engineered as a **Modular Monolith** that can evolve into microservices when scale demands. The architecture prioritizes:
- **Scale**: Horizontal scaling capabilities
- **Modularity**: Clean separation of concerns
- **Simplicity**: Easy local development
- **User Experience**: Responsive and accessible interfaces

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Web App    │  │ Mobile App   │  │   Admin UI   │   │
│  │   (React)    │  │ (React Native│  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │ GraphQL / REST
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            FastAPI (Python)                          │  │
│  │  - Authentication & Authorization                    │  │
│  │  - Request Validation                                │  │
│  │  - Rate Limiting                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Features  │  │  Services   │  │   AI/ML     │     │
│  │  - Auth     │  │  - RabbitMQ │  │  - Two-Tower│     │
│  │  - Feed     │  │  - Redis    │  │  - Agentic  │     │
│  │  - Collab   │  │  - LLM API  │  │    Router   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Repositories (Python)                         │  │
│  │  - PostgreSQL (Primary DB)                           │  │
│  │  - pgvector (Vector Storage)                         │  │
│  │  - Redis (Cache & Sessions)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │     AWS      │  │ LocalStack   │  │   Docker     │   │
│  │  - EKS       │  │ (Local Dev)  │  │  Compose     │   │
│  │  - RDS       │  │              │  │              │   │
│  │  - ElastiCache│ │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer
- **Web Application**: React with TypeScript
  - Responsive design with mobile-first approach
  - GraphQL client (Apollo Client or Relay)
  - Real-time updates via WebSocket

- **Mobile Application**: React Native with TypeScript
  - Shared business logic with web via `/hooks` and `/utils`
  - Native performance for critical paths
  - Offline-first architecture

### 2. API Gateway Layer (FastAPI)
- **Authentication**: JWT-based with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Validation**: Pydantic models for request/response validation
- **Documentation**: OpenAPI (Swagger) auto-generated
- **Rate Limiting**: Per-user and per-endpoint limits
- **CORS**: Configured for web and mobile origins

### 3. Business Logic Layer

#### Features Module
Domain-driven design with feature modules:
- **Auth**: Registration, login, password reset, 2FA
- **Feed**: Personalized content ranking using Two-Tower model
- **Collaboration**: Request management, matching algorithm
- **Messaging**: Real-time chat with WebSocket support
- **Streaming**: Live stream management and playback
- **Analytics**: Metrics aggregation and reporting

#### Services Module
External integrations:
- **RabbitMQ**: Asynchronous task processing
  - Email notifications
  - Content moderation
  - Analytics event processing
  
- **Redis**: Caching and session management
  - User sessions
  - API response cache
  - Real-time presence tracking
  
- **LLM API**: Agentic router for complex queries
  - Intent parsing
  - Natural language search
  - Content summarization

#### AI/ML Module
- **Two-Tower Model**: User and Item embedding generation
  - User Tower: User preferences, behavior, demographics
  - Item Tower: Content features, metadata
  - Cosine similarity for matching
  
- **Agentic Router**: LLM-powered query understanding
  - Parses natural language searches
  - Routes to appropriate retrieval mechanism
  - Falls back to Two-Tower for simple queries

- **Candidate Generation**: Approximate Nearest Neighbor (ANN)
  - Indexes user and item embeddings
  - Fast retrieval of top-K candidates
  - Supports pgvector or dedicated vector DB

### 4. Data Access Layer (Repositories)
Clean abstraction over database operations:
- **UserRepository**: User profiles, authentication, reputation
- **ContentRepository**: Posts, comments, media metadata
- **CollaborationRepository**: Collaboration requests, agreements
- **FeedRepository**: Feed items, interactions, embeddings
- **AnalyticsRepository**: Event logs, aggregated metrics

### 5. Infrastructure Layer

#### AWS Production Environment
- **EKS**: Kubernetes for container orchestration
- **RDS**: PostgreSQL with pgvector extension
- **ElastiCache**: Redis for caching
- **MQ**: RabbitMQ for message queuing
- **S3**: Media storage
- **CloudFront**: CDN for static assets

#### Local Development Environment
- **LocalStack**: AWS service emulation
- **Docker Compose**: Full stack orchestration
- **Infracost**: Cost estimation for Terraform plans
- **Checkov**: Security scanning for IaC

## Data Flow Examples

### 1. User Feed Generation
```
User Request → API Gateway → Feed Service → Two-Tower Model
                                            ↓
                                    Generate User Embedding
                                            ↓
                                    ANN Search (pgvector)
                                            ↓
                                    Retrieve Candidate Items
                                            ↓
                                    Re-ranking (ML Model)
                                            ↓
                                    Apply Business Rules
                                            ↓
                                    Return Personalized Feed
```

### 2. Collaboration Request
```
Creator A sends request → API Gateway → Collaboration Service
                                            ↓
                                    Validate Request
                                            ↓
                                    Publish to RabbitMQ
                                            ↓
                                    Notification Service (Consumer)
                                            ↓
                                    Push Notification to Creator B
                                            ↓
                                    Real-time Update via WebSocket
```

### 3. Natural Language Search
```
User Query → API Gateway → Agentic Router (LLM)
                            ↓
                    Parse Intent & Entities
                            ↓
                    Route to Search Strategy
                            ↓
                    [Simple] → Two-Tower Retrieval
                    [Complex] → Hybrid Search (Vector + Keyword)
                            ↓
                    Merge & Rank Results
                            ↓
                    Return Relevant Creators/Content
```

## Security Architecture

### Authentication Flow
1. User login with email/password
2. Server validates credentials
3. Returns access token (short-lived) and refresh token (long-lived)
4. Client stores tokens securely
5. Access token used for API requests
6. Automatic token refresh via refresh token

### Data Protection
- **Encryption at Rest**: PostgreSQL, Redis, S3
- **Encryption in Transit**: TLS 1.3 for all communications
- **Sensitive Data**: Hashed passwords (bcrypt), encrypted PII
- **Secrets Management**: AWS Secrets Manager or HashiCorp Vault

### API Security
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS protection (Content Security Policy)
- CSRF protection for web clients
- Rate limiting to prevent abuse

## Scalability Considerations

### Horizontal Scaling
- **Stateless API Servers**: Multiple FastAPI instances behind load balancer
- **Database Read Replicas**: Offload read queries
- **Redis Cluster**: Distributed caching
- **RabbitMQ Clustering**: High availability for message queue

### Performance Optimization
- **Database Indexing**: Optimized queries for common access patterns
- **CDN**: Static asset delivery via CloudFront
- **Lazy Loading**: Images and non-critical content
- **Pagination**: Limit data transfer for large collections
- **Background Jobs**: Offload heavy computations to workers

## Monitoring & Observability

### Metrics
- **Application Metrics**: Request latency, error rates, throughput
- **Business Metrics**: User engagement, collaboration success rate
- **Infrastructure Metrics**: CPU, memory, disk usage

### Logging
- Structured logging (JSON format)
- Centralized log aggregation (ELK stack or AWS CloudWatch)
- Correlation IDs for request tracing

### Alerting
- PagerDuty integration for critical issues
- Slack notifications for warnings
- Automated rollback on deployment failures

## Disaster Recovery

### Backup Strategy
- **PostgreSQL**: Daily automated backups to S3
- **Redis**: AOF persistence with periodic snapshots
- **Media Assets**: S3 cross-region replication

### Recovery Procedures
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 15 minutes
- Documented runbooks for common failure scenarios
- Regular disaster recovery drills

## Future Evolution: Microservices Transition

The Modular Monolith design enables gradual extraction of microservices:
1. **Phase 1**: Extract Collaboration Service (high isolation, clear boundaries)
2. **Phase 2**: Extract Feed Service (ML-heavy, different scaling needs)
3. **Phase 3**: Extract Messaging Service (real-time requirements)
4. **Phase 4**: Extract Analytics Service (write-heavy, eventual consistency)

Each transition will be guided by:
- Team autonomy requirements
- Independent scaling needs
- Data ownership clarity
- Deployment frequency

## References
- SRS Section 4: Full Stack Backend & Data Tier
- SRS Section 5: AI & Recommendation Engine
- SRS Section 6: Frontend & Mobile Requirements
- SRS Section 7: Non-Functional Requirements
