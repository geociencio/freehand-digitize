---
name: testing-standards
description: Standards for automated testing, CI/CD, and the use of Mocks. Use when writing or executing tests, designing testing strategies, or managing testing infrastructure.
---

# Testing and Automation Standards

Ensures code stability through a controlled execution environment, simulation
strategies (Mocks), and CI/CD practices.

## When to use this skill
- When creating new unit or integration test cases.
- When debugging failures in the CI/CD pipeline.
- When configuring or modifying the testing environment.

## Degree of Freedom
- **Guided**: Follow the testing strategies defined for the project, aiming for high
  coverage and isolation.

## Workflow
1. **Design**: Apply "Test-Driven Development (TDD)" or "Behaviour-Driven Development
   (BDD)" strategies as appropriate for the project.
2. **Implementation**: Create tests using the project's primary framework
   (e.g. `pytest`, `unittest`, `jest`, ...). Isolate external dependencies using Mocks.
3. **Execution**: Validate locally with the project's test runner, then run the
   containerized/CI command (for example `make docker-test`) when the project
   provides one.
4. **Coverage**: Verify that the minimum required coverage is achieved (> 80%).

## Instructions and Rules

### Testing Strategy
- **Isolation**: Unit tests must run quickly and without external dependencies
  (databases, network, UI).
- **Mocks**: Simulate (mock) external services and complex third-party libraries.
  Rigorously clean up mocks after each test.
- **Arithmetic mocks**: when mocking geometry or UI value objects used in layout
  math, return numeric values for dimensional methods (width, height, x, y) to
  avoid `TypeError`s during layout calculations or comparisons.
- **Integration**: Integration tests must validate the complete flow in an environment
  as close as possible to production (e.g. Docker containers).

### Testing Environment
- **Consistency**: The main test command must be the definitive health check. If it
  passes locally, it must pass in CI/CD.
- **Containers**: when the project provides a containerized test command, treat it
  as the definitive health check and keep the base image aligned with the runtime.
- **Mock switches**: use flags such as `FORCE_MOCKS=0` only for real integration
  runs; unit tests should stay mock-first.
- **Cleanup**: Avoid leaving residual state in the environment from tests.

## Quality Checklist
- [ ] Is the coverage of new services satisfactory (> 80%)?
- [ ] Are patches/Mocks cleaned up after each test?
- [ ] Can unit tests be executed in isolation without starting heavy services?
- [ ] Does the testing environment report zero failures?
- [ ] Is the containerized/CI test command green?
