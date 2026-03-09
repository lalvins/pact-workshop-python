# Pact Workshop — Design Document

**Date:** 2026-03-06
**Goal:** Node.js monorepo for a workshop demonstrating consumer-driven contract testing with Pact, using Clean Architecture and Ports & Adapters on both services.

---

## Overview

Two Express.js services in the same repository communicate over HTTP. The consumer generates a Pact contract file. The provider is architected to support Pact provider verification via an InMemory database adapter, making it runnable in full isolation from any real database.

---

## Repository Structure

```
pact-workshop/
├── package.json                              ← root: start, start:provider, start:consumer scripts
├── .npmrc
├── docs/plans/
│   └── 2026-03-06-pact-workshop-design.md
│
├── product-provider-service/
│   ├── .npmrc
│   ├── package.json
│   └── src/
│       ├── domain/Product.js
│       ├── ports/ProductRepositoryPort.js
│       ├── adapters/
│       │   ├── SQLiteProductRepository.js
│       │   └── InMemoryProductRepository.js
│       └── api/server.js
│
├── product-consumer-service/
│   ├── .npmrc
│   ├── package.json
│   └── src/
│       ├── domain/Product.js
│       ├── ports/ProductServicePort.js
│       ├── adapters/ProductServiceHttpAdapter.js
│       ├── application/GetProductUseCase.js
│       └── api/server.js
│   └── tests/
│       └── contract/
│           └── getProduct.pact.test.js
│
└── pacts/                                    ← generated pact JSON files
```

---

## Product Provider Service

### Architecture: Ports & Adapters

**Domain**
- `Product.js` — entity `{ id, name, price }`

**Port**
- `ProductRepositoryPort.js` — abstract interface with CRUD methods:
  - `getAll()`
  - `getById(id)`
  - `create(product)`
  - `update(id, product)`
  - `delete(id)`

**Adapters**
- `SQLiteProductRepository.js` — default runtime adapter using `better-sqlite3`; creates a `products.db` file on first run; pre-seeds two products if empty
- `InMemoryProductRepository.js` — pre-seeded, deterministic in-memory store; used when starting the service for Pact provider verification

**API**
- `api/server.js` — Express server, receives the repository adapter as a dependency
- Endpoints:
  - `GET /products` — list all products
  - `GET /products/:id` — get product by id (404 if not found)
  - `POST /products` — create a product
  - `PUT /products/:id` — update a product (404 if not found)
  - `DELETE /products/:id` — delete a product (404 if not found)
- Port: `3001`

**Start scripts (provider `package.json`)**
- `npm start` — boots with `SQLiteProductRepository`
- `npm run start:pact` — boots with `InMemoryProductRepository` (isolated, deterministic)

---

## Product Consumer Service

### Architecture: Clean Architecture

**Data flow:** `API route → GetProductUseCase → ProductServicePort → ProductServiceHttpAdapter → HTTP → Provider`

**Domain**
- `Product.js` — entity `{ id, name, price }`

**Port**
- `ProductServicePort.js` — abstract interface: `getProduct(productId)`

**Adapter**
- `ProductServiceHttpAdapter.js`
  - Implements `ProductServicePort`
  - Uses `axios` to call `GET /products/:id` on the provider
  - Provider base URL is configurable via constructor argument (defaults to `http://localhost:3001`)
  - Maps HTTP response body into a `Product` domain object
  - Throws a domain-level `ProductNotFoundError` on 404

**Application**
- `GetProductUseCase.js`
  - Constructor accepts a `ProductServicePort` instance (dependency injection)
  - `execute(productId)` — calls the port and returns the product

**API**
- `api/server.js` — Express server, wires adapter and use case, port `3000`
- Endpoint: `GET /product/:id`
  - Calls `GetProductUseCase`
  - Returns product as JSON
  - Returns 404 on `ProductNotFoundError`

---

## Contract Tests (Consumer Side)

**File:** `tests/contract/getProduct.pact.test.js`
**Runner:** Vitest
**Library:** `@pact-foundation/pact` v12, using `PactV3` + `MatchersV3`

**Flow:**
1. `beforeAll` — instantiate `PactV3`, configure mock provider, `await pact.addInteraction(...)` for happy path
2. Test — instantiate `ProductServiceHttpAdapter` pointing at mock server URL; call `GetProductUseCase.execute("1")`; assert returned `Product` matches expected shape
3. `afterAll` — `await pact.finalize()` → writes pact JSON to `../../pacts/`

**Interaction defined:**
```
Given: product with id "1" exists
Upon receiving: GET /products/1
Will respond with: 200 { id: like("1"), name: like("Coffee Mug"), price: decimal(12.99) }
```

**Output:** `pacts/product-consumer-service-product-provider-service.json`

---

## Scripts

### Root `package.json`
```json
{
  "scripts": {
    "start": "concurrently \"npm run start:provider\" \"npm run start:consumer\"",
    "start:provider": "npm start --prefix product-provider-service",
    "start:consumer": "npm start --prefix product-consumer-service"
  }
}
```

### Provider `package.json`
```json
{
  "scripts": {
    "start": "node src/api/server.js",
    "start:pact": "USE_IN_MEMORY_DB=true node src/api/server.js"
  }
}
```

### Consumer `package.json`
```json
{
  "scripts": {
    "start": "node src/api/server.js",
    "test:contract": "vitest run tests/contract"
  }
}
```

---

## Dependencies

### Provider
- `express` — HTTP server
- `better-sqlite3` — SQLite adapter

### Consumer
- `express` — HTTP server
- `axios` — HTTP client for provider calls

### Consumer dev
- `vitest` — test runner
- `@pact-foundation/pact` — Pact V3 consumer DSL

### Root dev
- `concurrently` — run both services in one terminal

---

## Key Design Decisions

1. **Symmetry** — both services follow Ports & Adapters; workshops can explore the pattern on both sides
2. **Isolation** — `start:pact` boots the provider with InMemory DB, making provider verification runnable without SQLite state
3. **Dependency injection** — adapters are injected at server startup; no global singletons, easy to swap
4. **Consumer test points at the mock** — `ProductServiceHttpAdapter` receives the base URL as a constructor argument; the Pact test passes the mock server URL, the real server passes `http://localhost:3001`
5. **Pact output path** — set to `../../pacts/` (repo root) so it is visible at the monorepo level
