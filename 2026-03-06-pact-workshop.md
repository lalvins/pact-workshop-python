# Pact Workshop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Node.js monorepo with a provider service (Ports & Adapters, SQLite + InMemory) and a consumer service (Clean Architecture) that generates a Pact contract file via a Vitest consumer test.

**Architecture:** Provider exposes a full CRUD REST API via Express, backed by a SQLiteProductRepository for normal use and an InMemoryProductRepository when started for Pact verification. Consumer follows strict Clean Architecture (domain → port → adapter → use case → API), with the HTTP adapter being the only layer that knows about the network.

**Tech Stack:** Node.js, Express 4, axios, better-sqlite3, @pact-foundation/pact v12 (PactV3 API), Vitest, concurrently

---

## Task 1: Repository Skeleton

**Files:**
- Create: `pact-workshop/package.json`
- Create: `pact-workshop/.npmrc`
- Create: `pact-workshop/product-provider-service/.npmrc`
- Create: `pact-workshop/product-consumer-service/.npmrc`
- Create: `pact-workshop/pacts/.gitkeep`

**Step 1: Initialize git**

```bash
cd /Users/luis.alvins/Documents/Projects/backmarket/pact-workshop
git init
```

Expected: `Initialized empty Git repository in .../pact-workshop/.git/`

**Step 2: Create root `.npmrc`**

```
engine-strict=false
save-exact=false
```

**Step 3: Create root `package.json`**

```json
{
  "name": "pact-workshop",
  "version": "1.0.0",
  "private": true,
  "description": "Consumer-driven contract testing workshop using Pact",
  "scripts": {
    "start": "concurrently \"npm run start:provider\" \"npm run start:consumer\"",
    "start:provider": "npm start --prefix product-provider-service",
    "start:consumer": "npm start --prefix product-consumer-service"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
```

**Step 4: Install root dev dependencies**

```bash
npm install
```

Expected: `node_modules/` created, `package-lock.json` created.

**Step 5: Create provider `.npmrc`**

File: `product-provider-service/.npmrc`

```
save-exact=false
```

**Step 6: Create consumer `.npmrc`**

File: `product-consumer-service/.npmrc`

```
save-exact=false
```

**Step 7: Create the pacts directory placeholder**

```bash
mkdir -p pacts && touch pacts/.gitkeep
```

**Step 8: Create `.gitignore`**

```
node_modules/
products.db
*.db
```

**Step 9: Commit**

```bash
git add .
git commit -m "chore: initialize repository skeleton"
```

---

## Task 2: Provider — Domain and Port

**Files:**
- Create: `product-provider-service/src/domain/Product.js`
- Create: `product-provider-service/src/ports/ProductRepositoryPort.js`

**Step 1: Create `src/domain/Product.js`**

```js
class Product {
  constructor({ id, name, price }) {
    this.id = id;
    this.name = name;
    this.price = price;
  }
}

module.exports = Product;
```

**Step 2: Create `src/ports/ProductRepositoryPort.js`**

This is the abstract interface. Any class that extends it and does not override a method will throw, making it clear the adapter is incomplete.

```js
class ProductRepositoryPort {
  async getAll() {
    throw new Error('ProductRepositoryPort.getAll() is not implemented');
  }

  async getById(id) {
    throw new Error('ProductRepositoryPort.getById() is not implemented');
  }

  async create(data) {
    throw new Error('ProductRepositoryPort.create() is not implemented');
  }

  async update(id, data) {
    throw new Error('ProductRepositoryPort.update() is not implemented');
  }

  async delete(id) {
    throw new Error('ProductRepositoryPort.delete() is not implemented');
  }
}

module.exports = ProductRepositoryPort;
```

**Step 3: Commit**

```bash
git add product-provider-service/src/
git commit -m "feat(provider): add Product domain entity and ProductRepositoryPort"
```

---

## Task 3: Provider — InMemory Adapter

**Files:**
- Create: `product-provider-service/src/adapters/InMemoryProductRepository.js`

**Step 1: Create `src/adapters/InMemoryProductRepository.js`**

Pre-seeded with two deterministic products. Used when starting the service for Pact provider verification.

```js
const ProductRepositoryPort = require('../ports/ProductRepositoryPort');
const Product = require('../domain/Product');

class InMemoryProductRepository extends ProductRepositoryPort {
  constructor() {
    super();
    this._store = new Map([
      ['1', new Product({ id: '1', name: 'Coffee Mug', price: 12.99 })],
      ['2', new Product({ id: '2', name: 'Laptop Stand', price: 45.00 })],
    ]);
    this._nextId = 3;
  }

  async getAll() {
    return Array.from(this._store.values());
  }

  async getById(id) {
    return this._store.get(String(id)) || null;
  }

  async create({ name, price }) {
    const id = String(this._nextId++);
    const product = new Product({ id, name, price });
    this._store.set(id, product);
    return product;
  }

  async update(id, { name, price }) {
    const existing = this._store.get(String(id));
    if (!existing) return null;
    const updated = new Product({ id: String(id), name, price });
    this._store.set(String(id), updated);
    return updated;
  }

  async delete(id) {
    return this._store.delete(String(id));
  }
}

module.exports = InMemoryProductRepository;
```

**Step 2: Commit**

```bash
git add product-provider-service/src/adapters/InMemoryProductRepository.js
git commit -m "feat(provider): add InMemoryProductRepository for Pact verification"
```

---

## Task 4: Provider — SQLite Adapter

**Files:**
- Create: `product-provider-service/src/adapters/SQLiteProductRepository.js`
- Create: `product-provider-service/package.json`

**Step 1: Create `product-provider-service/package.json`**

```json
{
  "name": "product-provider-service",
  "version": "1.0.0",
  "private": true,
  "description": "Product provider service for Pact workshop",
  "main": "src/api/server.js",
  "scripts": {
    "start": "node src/api/server.js",
    "start:pact": "USE_IN_MEMORY_DB=true node src/api/server.js"
  },
  "dependencies": {
    "better-sqlite3": "^9.4.3",
    "express": "^4.18.2"
  }
}
```

**Step 2: Install provider dependencies**

```bash
cd product-provider-service && npm install && cd ..
```

Expected: `product-provider-service/node_modules/` created.

**Step 3: Create `src/adapters/SQLiteProductRepository.js`**

```js
const Database = require('better-sqlite3');
const path = require('path');
const ProductRepositoryPort = require('../ports/ProductRepositoryPort');
const Product = require('../domain/Product');

class SQLiteProductRepository extends ProductRepositoryPort {
  constructor(dbPath = path.join(__dirname, '../../products.db')) {
    super();
    this._db = new Database(dbPath);
    this._migrate();
  }

  _migrate() {
    this._db.exec(`
      CREATE TABLE IF NOT EXISTS products (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT    NOT NULL,
        price REAL   NOT NULL
      )
    `);

    const { count } = this._db.prepare('SELECT COUNT(*) AS count FROM products').get();
    if (count === 0) {
      const insert = this._db.prepare('INSERT INTO products (name, price) VALUES (?, ?)');
      insert.run('Coffee Mug', 12.99);
      insert.run('Laptop Stand', 45.00);
    }
  }

  async getAll() {
    return this._db
      .prepare('SELECT * FROM products')
      .all()
      .map(row => new Product({ id: String(row.id), name: row.name, price: row.price }));
  }

  async getById(id) {
    const row = this._db.prepare('SELECT * FROM products WHERE id = ?').get(id);
    return row ? new Product({ id: String(row.id), name: row.name, price: row.price }) : null;
  }

  async create({ name, price }) {
    const info = this._db.prepare('INSERT INTO products (name, price) VALUES (?, ?)').run(name, price);
    return new Product({ id: String(info.lastInsertRowid), name, price });
  }

  async update(id, { name, price }) {
    const info = this._db.prepare('UPDATE products SET name = ?, price = ? WHERE id = ?').run(name, price, id);
    if (info.changes === 0) return null;
    return new Product({ id: String(id), name, price });
  }

  async delete(id) {
    const info = this._db.prepare('DELETE FROM products WHERE id = ?').run(id);
    return info.changes > 0;
  }
}

module.exports = SQLiteProductRepository;
```

**Step 4: Commit**

```bash
git add product-provider-service/
git commit -m "feat(provider): add SQLiteProductRepository and package.json"
```

---

## Task 5: Provider — API Server

**Files:**
- Create: `product-provider-service/src/api/server.js`

**Step 1: Create `src/api/server.js`**

The server factory receives the repository as a parameter (dependency injection). The startup block at the bottom reads `USE_IN_MEMORY_DB` from the environment to decide which adapter to use.

```js
const express = require('express');
const InMemoryProductRepository = require('../adapters/InMemoryProductRepository');
const SQLiteProductRepository = require('../adapters/SQLiteProductRepository');

function createApp(repository) {
  const app = express();
  app.use(express.json());

  app.get('/products', async (req, res) => {
    const products = await repository.getAll();
    res.json(products);
  });

  app.get('/products/:id', async (req, res) => {
    const product = await repository.getById(req.params.id);
    if (!product) return res.status(404).json({ error: 'Product not found' });
    res.json(product);
  });

  app.post('/products', async (req, res) => {
    const { name, price } = req.body;
    const product = await repository.create({ name, price });
    res.status(201).json(product);
  });

  app.put('/products/:id', async (req, res) => {
    const { name, price } = req.body;
    const product = await repository.update(req.params.id, { name, price });
    if (!product) return res.status(404).json({ error: 'Product not found' });
    res.json(product);
  });

  app.delete('/products/:id', async (req, res) => {
    const deleted = await repository.delete(req.params.id);
    if (!deleted) return res.status(404).json({ error: 'Product not found' });
    res.status(204).send();
  });

  return app;
}

const PORT = 3001;
const useInMemory = process.env.USE_IN_MEMORY_DB === 'true';
const repository = useInMemory
  ? new InMemoryProductRepository()
  : new SQLiteProductRepository();

const app = createApp(repository);
app.listen(PORT, () => {
  const mode = useInMemory ? 'InMemory (Pact mode)' : 'SQLite';
  console.log(`Product Provider running on http://localhost:${PORT} [${mode}]`);
});
```

**Step 2: Smoke-test the provider manually**

```bash
npm start --prefix product-provider-service
# In another terminal:
curl http://localhost:3001/products
curl http://localhost:3001/products/1
curl http://localhost:3001/products/999
```

Expected:
- `/products` → JSON array with two products
- `/products/1` → `{ "id": "1", "name": "Coffee Mug", "price": 12.99 }`
- `/products/999` → `{ "error": "Product not found" }` with 404

**Step 3: Smoke-test InMemory mode**

```bash
npm run start:pact --prefix product-provider-service
curl http://localhost:3001/products
```

Expected: same two products, log says `[InMemory (Pact mode)]`

**Step 4: Commit**

```bash
git add product-provider-service/src/api/
git commit -m "feat(provider): add Express API server with CRUD routes"
```

---

## Task 6: Consumer — Domain, Port, and package.json

**Files:**
- Create: `product-consumer-service/package.json`
- Create: `product-consumer-service/src/domain/Product.js`
- Create: `product-consumer-service/src/domain/ProductNotFoundError.js`
- Create: `product-consumer-service/src/ports/ProductServicePort.js`

**Step 1: Create `product-consumer-service/package.json`**

```json
{
  "name": "product-consumer-service",
  "version": "1.0.0",
  "private": true,
  "description": "Product consumer service for Pact workshop",
  "main": "src/api/server.js",
  "scripts": {
    "start": "node src/api/server.js",
    "test:contract": "vitest run tests/contract"
  },
  "dependencies": {
    "axios": "^1.6.7",
    "express": "^4.18.2"
  },
  "devDependencies": {
    "@pact-foundation/pact": "^12.1.0",
    "vitest": "^1.3.1"
  }
}
```

**Step 2: Install consumer dependencies**

```bash
cd product-consumer-service && npm install && cd ..
```

**Step 3: Create `src/domain/Product.js`**

```js
class Product {
  constructor({ id, name, price }) {
    this.id = id;
    this.name = name;
    this.price = price;
  }
}

module.exports = Product;
```

**Step 4: Create `src/domain/ProductNotFoundError.js`**

```js
class ProductNotFoundError extends Error {
  constructor(productId) {
    super(`Product with id "${productId}" not found`);
    this.name = 'ProductNotFoundError';
  }
}

module.exports = ProductNotFoundError;
```

**Step 5: Create `src/ports/ProductServicePort.js`**

```js
class ProductServicePort {
  async getProduct(productId) {
    throw new Error('ProductServicePort.getProduct() is not implemented');
  }
}

module.exports = ProductServicePort;
```

**Step 6: Commit**

```bash
git add product-consumer-service/
git commit -m "feat(consumer): add domain entities, ProductNotFoundError, and ProductServicePort"
```

---

## Task 7: Consumer — Write the Pact Test First (TDD)

> Write the test before implementing the adapter. The test will fail because the adapter does not exist yet.

**Files:**
- Create: `product-consumer-service/tests/contract/getProduct.pact.test.js`

**Step 1: Create `tests/contract/getProduct.pact.test.js`**

```js
const { describe, it, expect } = require('vitest');
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const path = require('path');

const ProductServiceHttpAdapter = require('../../src/adapters/ProductServiceHttpAdapter');
const GetProductUseCase = require('../../src/application/GetProductUseCase');
const Product = require('../../src/domain/Product');

const { like } = MatchersV3;

const provider = new PactV3({
  consumer: 'product-consumer-service',
  provider: 'product-provider-service',
  dir: path.resolve(__dirname, '../../../pacts'),
  logLevel: 'warn',
});

describe('ProductServiceHttpAdapter — Pact consumer contract', () => {
  it('returns a Product domain object when the provider responds with a product', async () => {
    await provider
      .given('product with id 1 exists')
      .uponReceiving('a GET request for product with id 1')
      .withRequest({
        method: 'GET',
        path: '/products/1',
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: like('1'),
          name: like('Coffee Mug'),
          price: like(12.99),
        },
      })
      .executeTest(async (mockServer) => {
        const adapter = new ProductServiceHttpAdapter(mockServer.url);
        const useCase = new GetProductUseCase(adapter);

        const product = await useCase.execute('1');

        expect(product).toBeInstanceOf(Product);
        expect(typeof product.id).toBe('string');
        expect(typeof product.name).toBe('string');
        expect(typeof product.price).toBe('number');
      });
  });
});
```

**Step 2: Run the test — verify it fails**

```bash
npm run test:contract --prefix product-consumer-service
```

Expected: FAIL — `Cannot find module '../../src/adapters/ProductServiceHttpAdapter'`

This is correct. The test is red because the adapter does not exist yet.

**Step 3: Commit the failing test**

```bash
git add product-consumer-service/tests/
git commit -m "test(consumer): add Pact consumer contract test (red)"
```

---

## Task 8: Consumer — HTTP Adapter (make the test green)

**Files:**
- Create: `product-consumer-service/src/adapters/ProductServiceHttpAdapter.js`

**Step 1: Create `src/adapters/ProductServiceHttpAdapter.js`**

```js
const axios = require('axios');
const ProductServicePort = require('../ports/ProductServicePort');
const Product = require('../domain/Product');
const ProductNotFoundError = require('../domain/ProductNotFoundError');

class ProductServiceHttpAdapter extends ProductServicePort {
  constructor(baseUrl = 'http://localhost:3001') {
    super();
    this._baseUrl = baseUrl;
  }

  async getProduct(productId) {
    try {
      const { data } = await axios.get(`${this._baseUrl}/products/${productId}`);
      return new Product({ id: data.id, name: data.name, price: data.price });
    } catch (error) {
      if (error.response?.status === 404) {
        throw new ProductNotFoundError(productId);
      }
      throw error;
    }
  }
}

module.exports = ProductServiceHttpAdapter;
```

**Step 2: Run the test — verify it is still red (GetProductUseCase is missing)**

```bash
npm run test:contract --prefix product-consumer-service
```

Expected: FAIL — `Cannot find module '../../src/application/GetProductUseCase'`

Good — the test is guiding us to the next missing piece.

---

## Task 9: Consumer — Use Case (make the test green)

**Files:**
- Create: `product-consumer-service/src/application/GetProductUseCase.js`

**Step 1: Create `src/application/GetProductUseCase.js`**

```js
class GetProductUseCase {
  constructor(productServicePort) {
    this._port = productServicePort;
  }

  async execute(productId) {
    return this._port.getProduct(productId);
  }
}

module.exports = GetProductUseCase;
```

**Step 2: Run the Pact test — verify it passes**

```bash
npm run test:contract --prefix product-consumer-service
```

Expected:
```
✓ ProductServiceHttpAdapter — Pact consumer contract
  ✓ returns a Product domain object when the provider responds with a product

Test Files  1 passed (1)
Tests       1 passed (1)
```

Also verify the pact file was generated:

```bash
ls pacts/
```

Expected: `product-consumer-service-product-provider-service.json`

**Step 3: Commit**

```bash
git add product-consumer-service/src/
git commit -m "feat(consumer): add ProductServiceHttpAdapter and GetProductUseCase — contract test green"
```

---

## Task 10: Consumer — API Server

**Files:**
- Create: `product-consumer-service/src/api/server.js`

**Step 1: Create `src/api/server.js`**

```js
const express = require('express');
const ProductServiceHttpAdapter = require('../adapters/ProductServiceHttpAdapter');
const GetProductUseCase = require('../application/GetProductUseCase');
const ProductNotFoundError = require('../domain/ProductNotFoundError');

const app = express();
app.use(express.json());

const providerUrl = process.env.PROVIDER_URL || 'http://localhost:3001';
const adapter = new ProductServiceHttpAdapter(providerUrl);
const getProductUseCase = new GetProductUseCase(adapter);

app.get('/product/:id', async (req, res) => {
  try {
    const product = await getProductUseCase.execute(req.params.id);
    res.json(product);
  } catch (error) {
    if (error instanceof ProductNotFoundError) {
      return res.status(404).json({ error: error.message });
    }
    res.status(500).json({ error: 'Internal server error' });
  }
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Product Consumer running on http://localhost:${PORT}`);
  console.log(`  → Calling provider at ${providerUrl}`);
});
```

**Step 2: Smoke-test end-to-end (both services running)**

```bash
# Terminal 1
npm run start:provider

# Terminal 2
npm run start:consumer

# Terminal 3 — call the consumer
curl http://localhost:3000/product/1
curl http://localhost:3000/product/999
```

Expected:
- `/product/1` → `{ "id": "1", "name": "Coffee Mug", "price": 12.99 }`
- `/product/999` → `{ "error": "Product with id \"999\" not found" }` with 404

Or start both at once from the repo root:

```bash
npm start
```

**Step 3: Commit**

```bash
git add product-consumer-service/src/api/
git commit -m "feat(consumer): add Express API server — end-to-end integration complete"
```

---

## Task 11: Final Verification

**Step 1: Run the full contract test from the repo root**

```bash
npm run test:contract --prefix product-consumer-service
```

Expected: 1 test passing, pact file present at `pacts/product-consumer-service-product-provider-service.json`.

**Step 2: Verify `start` and `start:pact` scripts work**

```bash
# Default mode (SQLite)
npm run start:provider

# Pact mode (InMemory)
npm run start:pact --prefix product-provider-service
```

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: verify all scripts and contract test — workshop ready"
```

---

## Cheat Sheet for Workshop Attendees

```bash
# Install all dependencies
npm install
(cd product-provider-service && npm install)
(cd product-consumer-service && npm install)

# Start both services
npm start

# Start services independently
npm run start:provider
npm run start:consumer

# Start provider in Pact mode (InMemory DB, isolated)
npm run start:pact --prefix product-provider-service

# Run consumer contract tests (generates pact file)
npm run test:contract --prefix product-consumer-service

# Inspect the generated pact file
cat pacts/product-consumer-service-product-provider-service.json
```
