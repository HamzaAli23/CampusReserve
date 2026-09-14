# Test report

CampusReserve 0.2.1 was tested on 14 September 2026 using Python 3.12.14, FastAPI 0.141.1, SQLModel 0.0.42 and Uvicorn 0.52.4.

## Passed

- `pytest -q`: **5 passed**.
- JavaScript syntax validation with Node.js: **passed**.
- Python bytecode compilation: **passed**.
- Source distribution and wheel build: **passed**.
- Local server startup and `/api/health`: **passed**.
- AYBU concept disclosure, API-documentation link and cancellation control in the browser interface: **passed**.
- Resource creation and booking creation through live HTTP requests: **passed**.
- Overlapping booking returned the expected **HTTP 409 Conflict**: **passed**.
- Cancellation through the live API changed the booking status to `cancelled`: **passed**.
- UTC-qualified API timestamp regression check for correct local display: **passed**.
- Automated coverage includes adjacent bookings, cancellation/rebooking, invalid intervals, missing resources, resource ordering and persisted booking lists.

## Warnings and limits

The test run emitted two non-failing third-party deprecation warnings from the FastAPI/Starlette test-client stack. Version 0.2 has no authentication and does not provide database-enforced protection against cross-process concurrent booking races. These limitations are documented in the README.

## Packaging

The repository ZIP excludes the virtual environment, caches, local SQLite databases, raw logs and build output.
