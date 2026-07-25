# Feature verification

Choose the cheapest layer that can falsify the implementation:

1. Type checking, lint or static contract.
2. Pure unit test for state, codec or transformation logic.
3. Module or service integration test.
4. Hvigor debug build.
5. Bound-target Instrument/Hypium test.
6. Physical-device or external-system end-to-end validation.

Move to a more expensive layer only when the previous layer passes or cannot observe the behavior. A mocked external result never proves remote availability.
