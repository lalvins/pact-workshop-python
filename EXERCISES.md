# Pact Workshop — Hands-on Exercises

Apply each change, run the command, observe the output, then fix before moving on.

---

## Consumer Exercises

### C1 — Baseline: everything should be green

```bash
make test-contract
```

**Expected output (green)**

```
PASSED tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_returns_product_domain_object_when_provider_responds
PASSED tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_creates_product_when_provider_accepts_post

2 passed in ...
```

The pact file at `pacts/product-consumer-service-product-provider-service.json` is
generated with two interactions.

---

### C2 — Consumer breaks its own commitment

The consumer test says it will call `GET /products/{id}`. Change the adapter to call
a different path and watch the mock reject the request.

**Step 1 — Introduce the bug**

Open [product-consumer-service/src/adapters/product_service_http_adapter.py](product-consumer-service/src/adapters/product_service_http_adapter.py):

```python
# BEFORE
response = await client.get(f"{self.base_url}/products/{product_id}")
```

```python
# AFTER (wrong path — missing the 's')
response = await client.get(f"{self.base_url}/product/{product_id}")
```

**Step 2 — Run**

```bash
make test-contract
```

**Expected output (failure)**

```
FAILED tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_returns_product_domain_object_when_provider_responds

pact.v3.error.PactInteractionError: ...
  Mock server failed with the following mismatches:

    The following request was not expected:
      Method: GET
      Path: /product/1
```

The mock expected `GET /products/1` — what the interaction defined. The adapter
sent `GET /product/1`. Mismatch → test fails → pact file not updated.

**Step 3 — Fix**

Restore the correct path in `product_service_http_adapter.py`:

```python
response = await client.get(f"{self.base_url}/products/{product_id}")
```

```bash
make test-contract   # back to green
```

---

### C3 — Consumer drops a field it promised to send

The consumer test declares it will POST `{ name, price }`. Remove `name` from the
payload and watch the mock reject the request.

**Step 1 — Introduce the bug**

Open [product-consumer-service/src/adapters/product_service_http_adapter.py](product-consumer-service/src/adapters/product_service_http_adapter.py):

```python
# BEFORE
response = await client.post(f"{self.base_url}/products", json={"name": name, "price": price})
```

```python
# AFTER (breaking — name omitted from the actual request)
response = await client.post(f"{self.base_url}/products", json={"price": price})
```

**Step 2 — Run**

```bash
make test-contract
```

**Expected output (failure)**

```
FAILED tests/contract/test_get_product_pact.py::TestProductServiceHttpAdapterPactContract::test_creates_product_when_provider_accepts_post

pact.v3.error.PactInteractionError: ...
  Mock server failed with the following mismatches:

    The following request was incorrect:
      POST /products
        Expected a Map with keys [name, price] but received one with keys [price]
```

The interaction declared the consumer will send `{ name, price }`. The actual
request only sent `{ price }`. Pact catches the missing key.

**Step 3 — Fix**

Restore `name` in the adapter:

```python
response = await client.post(f"{self.base_url}/products", json={"name": name, "price": price})
```

```bash
make test-contract   # back to green
```

---

### C4 — Add a POST expectation the provider cannot satisfy

Modify the consumer test for `POST /products` to expect a `sku` field in the
response. The provider does not return `sku`. The consumer test will pass (the mock
serves whatever we define), but provider verification will fail.

**Step 1 — Modify the existing test**

Open [product-consumer-service/tests/contract/test_get_product_pact.py](product-consumer-service/tests/contract/test_get_product_pact.py) and update the
`test_creates_product_when_provider_accepts_post` interaction's `will_respond_with` body:

```python
# BEFORE
(
    pact.upon_receiving("a POST request to create a product")
    .with_request(method="POST", path="/products")
    .with_body({"name": match.like("Coffee Mug"), "price": match.like(12.99)})
    .will_respond_with(201)
    .with_body({
        "id": match.like("1"),
        "name": match.like("Coffee Mug"),
        "price": match.like(12.99),
    })
)
```

```python
# AFTER (adding sku — provider does not return this)
(
    pact.upon_receiving("a POST request to create a product")
    .with_request(method="POST", path="/products")
    .with_body({"name": match.like("Coffee Mug"), "price": match.like(12.99)})
    .will_respond_with(201)
    .with_body({
        "id": match.like("1"),
        "name": match.like("Coffee Mug"),
        "price": match.like(12.99),
        "sku": match.like("MUG-001"),   # ← provider does not return this
    })
)
```

Also update the assertion at the end of the test to expect `sku` on the returned product if needed (or just let the response body mismatch surface).

**Step 2 — Run consumer tests**

```bash
make test-contract
```

**Expected output (green — consumer side passes)**

```
2 passed in ...
```

Both tests pass. The pact file now includes `sku` in the POST response interaction.
The mock served `sku` because we told it to — but the real provider has no idea
about this field yet.

---

### C4 continued — Run against the provider

The pact file contains the `sku` expectation from C4. Run provider verification to
see it fail.

```bash
make test-provider-verification
```

**Expected output (failure)**

```
FAILED tests/provider/test_provider_verification.py::TestProviderVerification::test_provider_honours_contract_with_consumer

  Verifying a pact between product-consumer-service and product-provider-service
    a POST request to create a product
      Body had differences:
        $.sku -> Expected 'MUG-001' (like) but was missing
```

The real `POST /products` returns `{ id, name, price }` — no `sku`. The contract
caught the gap before any deployment.

**Fix — remove the unsatisfiable expectation**

Remove the `sku` field from the `will_respond_with` body in the consumer test:

```python
.with_body({
    "id": match.like("1"),
    "name": match.like("Coffee Mug"),
    "price": match.like(12.99),
    # sku removed
})
```

```bash
make test-contract                  # regenerate pact
make test-provider-verification     # back to green
```

---

## Provider Exercises

### P1 — Breaking change: wrong status code on POST

Change the `POST /products` handler to return `204` instead of `201`.

**Step 1 — Introduce the breaking change**

Open [product-provider-service/src/api/server.py](product-provider-service/src/api/server.py):

```python
# BEFORE
@app.post("/products", status_code=201)
```

```python
# AFTER (breaking — wrong status code)
@app.post("/products", status_code=204)
```

**Step 2 — Run provider verification**

```bash
make test-provider-verification
```

**Expected output (failure)**

```
FAILED tests/provider/test_provider_verification.py::TestProviderVerification::test_provider_honours_contract_with_consumer

  Verifying a pact between product-consumer-service and product-provider-service
    a POST request to create a product
      Status code had differences:
        Expected: 201
        Actual:   204
```

**Fix**

```python
@app.post("/products", status_code=201)
```

```bash
make test-provider-verification   # back to green
```

---

### P2 — Breaking change: wrong field type

Change `price` to be returned as a string instead of a number.

**Step 1 — Introduce the breaking change**

In [product-provider-service/src/api/server.py](product-provider-service/src/api/server.py), update the `GET /products/{product_id}`
handler to cast price to a string:

```python
# BEFORE
return {"id": product.id, "name": product.name, "price": product.price}
```

```python
# AFTER (breaking — price is now a string)
return {"id": product.id, "name": product.name, "price": str(product.price)}
```

**Step 2 — Run provider verification**

```bash
make test-provider-verification
```

**Expected output (failure)**

```
FAILED tests/provider/test_provider_verification.py::TestProviderVerification::test_provider_honours_contract_with_consumer

  Verifying a pact between product-consumer-service and product-provider-service
    a request to get product with id 1
      Body had differences:
        $.price -> Expected 12.99 (like) but received "12.99" (wrong type)
```

**Fix**

```python
return {"id": product.id, "name": product.name, "price": product.price}
```

```bash
make test-provider-verification   # back to green
```

---

### P3 — Breaking change: renamed field

Rename `name` to `product_name` in the `GET /products/{product_id}` response.

**Step 1 — Introduce the breaking change**

In [product-provider-service/src/api/server.py](product-provider-service/src/api/server.py):

```python
# BEFORE
return {"id": product.id, "name": product.name, "price": product.price}
```

```python
# AFTER (breaking — field renamed)
return {"id": product.id, "product_name": product.name, "price": product.price}
```

**Step 2 — Run provider verification**

```bash
make test-provider-verification
```

**Expected output (failure)**

```
FAILED tests/provider/test_provider_verification.py::TestProviderVerification::test_provider_honours_contract_with_consumer

  Verifying a pact between product-consumer-service and product-provider-service
    a request to get product with id 1
      Body had differences:
        $ -> Actual map is missing the following keys: name
```

**Fix**

```python
return {"id": product.id, "name": product.name, "price": product.price}
```

```bash
make test-provider-verification   # back to green
```

---

## Quick reference

| Exercise | Command |
|---|---|
| C1 | `make test-contract` |
| C2 | `make test-contract` |
| C3 | `make test-contract` |
| C4 | `make test-contract` then `make test-provider-verification` |
| P1 | `make test-provider-verification` |
| P2 | `make test-provider-verification` |
| P3 | `make test-provider-verification` |
