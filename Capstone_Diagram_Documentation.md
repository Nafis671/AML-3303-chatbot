# AI-Powered Customer Support Assistant — Diagram Documentation

---

## 1. User Flow Diagrams

The user flow diagram defines two separate flows within the system.

![Alt text](user_flow.drawio.svg)

### 1.1 Admin/Support User Flow

This flow represents the journey of an internal admin or support staff member:

1. **Sign up** — The user registers for an account on the platform.
2. **Create Org** — After signing up, the user creates an organization.
3. **Dashboard** — The user is taken to the main dashboard, which serves as the central hub.
4. **Upload Documents** — From the dashboard, the user can upload support documents into the system.
5. **View Conversation** — The dashboard also allows the user to view customer conversations.
6. **Review Chats** — From the conversation view, the user can review individual chat histories.

The flow is linear from Sign up through to Dashboard, which then branches into two paths: one toward Upload Documents and another downward toward View Conversation → Review Chats.

### 1.2 Customer Chat Flow

This flow represents how an end customer interacts with the chatbot:

1. **Open Widget** — The customer opens the chat widget.
2. **Ask Question** — The customer types and submits a question.
3. **RAG search** — The system performs a retrieval-augmented generation search against the knowledge base.
4. **Generate Answer** — The system generates an answer based on the retrieved context.

Two alternate paths branch from Generate Answer:

- **Follow-up question** — A dotted loop path returns from Generate Answer back to Ask Question, allowing the customer to continue the conversation.
- **No answer → Handover to Human** — If the system cannot generate an answer, the conversation is escalated to a human support agent.

---

## 2. System Architecture

The architecture diagram shows a three-tier system connected via Server actions / REST API.

![Alt text](Architecture.drawio.svg)

### 2.1 Frontend (Top Layer)

The frontend layer contains three components:

- **Auth Pages** — Handles user authentication screens.
- **Dashboard** — The management interface for admins/support staff.
- **Chatbot Widget** — The customer-facing chat interface (visually distinct, highlighted in orange).

The frontend communicates with the backend through **Server actions / REST API**.

### 2.2 Backend (Middle Layer)

The backend layer contains four modules:

- **Auth** — Handles authentication logic. Connects downward to PostgreSQL for storing user/session data.
- **Doc Processor** — Handles document processing. Connects to File Storage (for storing uploaded files) and feeds parsed and embedded data to the RAG engine via a **Parse + Embed** connection.
- **RAG engine** — The retrieval-augmented generation engine. Connects to the Vector Store with a **Store/Retrieve** relationship for reading and writing embeddings.
- **Chat API** — Manages chat interactions. Connects to PostgreSQL for **Chat history** storage and to the LLM API via a **Feed LLM** connection.

### 2.3 Data & Infrastructure (Bottom Layer)

The data layer contains four external services/stores:

- **PostgreSQL** — Relational database receiving connections from Auth (user data) and Chat API (chat history), and from Doc Processor.
- **File Storage** — Stores uploaded document files, connected to Doc Processor.
- **Vector Store** — Stores and retrieves embedding vectors, connected to the RAG engine.
- **LLM API** — External language model service, connected to the Chat API for response generation.

---

## 3. RAG Workflow Design

The RAG workflow diagram is divided into two pipelines separated by a dashed boundary, with a connection between them.

![Alt text](RAG_workflow.drawio.svg)

### 3.1 Document Ingestion Pipeline (Left Side)

This pipeline processes documents when they are uploaded:

1. **Upload file** — A document file is uploaded into the system.
2. **Parse Text** — Raw text is extracted from the uploaded file.
3. **Chunk** — The extracted text is split into smaller segments.
4. **Generate embedding** — Each chunk is converted into a vector embedding.
5. **Store vectors** — The generated embeddings are saved to the vector store.

The flow is sequential from top to bottom: Upload file → Parse Text → Chunk → Generate embedding → Store vectors.

### 3.2 Query Pipeline (Right Side)

This pipeline executes when a user asks a question:

1. **User question** — The customer submits a question through the chat interface.
2. **Embed Query** — The user's question is converted into a vector embedding.
3. **Similarity Search** — The query embedding is compared against stored document vectors to find the most relevant chunks.
4. **Build Prompt** — A prompt is constructed using the retrieved context chunks and the original question.
5. **LLM generate response** — The assembled prompt is sent to the LLM to produce an answer.
6. **Return response** — The generated response is returned to the user.

### 3.3 Cross-Pipeline Connection

A connector line runs from **Store vectors** (end of the ingestion pipeline) to **Similarity Search** (in the query pipeline), indicating that the vectors stored during ingestion are the same vectors searched during query time.

---

## 4. Database Schema Design (ERD)

The entity relationship diagram defines seven entities with their fields, types, keys, and relationships.
![Alt text](ERD.drawio.svg)

### 4.1 Organization

| Key | Field     | Type      |
| --- | --------- | --------- |
| PK  | id        | uuid      |
|     | name      | string    |
|     | slug      | string    |
|     | createdAt | timestamp |

### 4.2 User

| Key | Field     | Type      |
| --- | --------- | --------- |
| PK  | id        | uuid      |
| FK  | orgId     | uuid      |
|     | name      | string    |
|     | email     | string    |
|     | password  | string    |
|     | role      | enum      |
|     | createdAt | timestamp |

### 4.3 KnowledgeBase

| Key | Field       | Type   |
| --- | ----------- | ------ |
| PK  | id          | uuid   |
| FK  | orgId       | uuid   |
|     | name        | string |
|     | description | string |

### 4.4 Document

| Key | Field           | Type      |
| --- | --------------- | --------- |
| PK  | id              | uuid      |
| FK  | orgId           | uuid      |
| FK  | knowledgebaseID | uuid      |
|     | fileName        | string    |
|     | fileType        | string    |
|     | fileSize        | int       |
|     | status          | enum      |
|     | createdAt       | timestamp |

### 4.5 DocumentChunk

| Key | Field       | Type      |
| --- | ----------- | --------- |
| PK  | id          | uuid      |
| FK  | documentId  | uuid      |
|     | chunkIndex  | int       |
|     | content     | string    |
|     | embeddingId | string    |
|     | createdAt   | timestamp |

### 4.6 Conversation

| Key | Field     | Type      |
| --- | --------- | --------- |
| PK  | id        | uuid      |
| FK  | orgId     | uuid      |
| FK  | userId    | uuid      |
|     | title     | string    |
|     | status    | enum      |
|     | createdAt | timestamp |
|     | updatedAt | timestamp |

### 4.7 Message

| Key | Field          | Type      |
| --- | -------------- | --------- |
| PK  | id             | uuid      |
| FK  | conversationId | uuid      |
|     | role           | string    |
|     | content        | string    |
|     | sources        | string    |
|     | createdAt      | timestamp |

### 4.8 Relationships

The ERD shows the following relationships with their cardinality labels:

| Parent Entity | Relationship | Child Entity  | Cardinality |
| ------------- | ------------ | ------------- | ----------- |
| Organization  | **owns**     | User          | One-to-Many |
| Organization  | **has**      | KnowledgeBase | One-to-Many |
| Organization  | **owns**     | Conversation  | One-to-Many |
| KnowledgeBase | **owns**     | Document      | One-to-Many |
| Document      | **contains** | DocumentChunk | One-to-Many |
| User          | **Creates**  | Conversation  | One-to-Many |
| Conversation  | **has**      | Message       | One-to-Many |

All primary keys use UUIDs. Foreign keys link child entities back to their parent through orgId, userId, knowledgebaseID, documentId, and conversationId respectively.
