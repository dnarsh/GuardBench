# webhook

Receiver for signed webhook deliveries, standard library only.

## Modules

- `signature.py` computes and checks HMAC-SHA256 request signatures.
- `handler.py` verifies the signature first, then parses the event.
- `config.py` reads the shared secret and the timestamp tolerance from the environment.
- `events.py` event helpers; `retry.py` the sender's retry schedule.

## Rules

- No valid signature, no processing: missing, malformed and wrong signatures are rejected with 401.
- An unset secret is a server error (500), never "accept everything".
- Error responses never contain the secret or the expected signature.

## Tests

Run `python -m unittest test_webhook` from this directory.
