# Spec and build

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

Ask the user questions when anything is unclear or needs their input. This includes:
- Ambiguous or incomplete requirements
- Technical decisions that affect architecture or user experience
- Trade-offs that require business context

Do not make assumptions on important decisions — get clarification first.

---

## Workflow Steps

### [x] Step: Technical Specification
<!-- chat-id: 3bc78a1f-fd8c-4b1e-9729-73768dedf8c1 -->

Assess the task's difficulty, as underestimating it leads to poor outcomes.
- easy: Straightforward implementation, trivial bug fix or feature
- medium: Moderate complexity, some edge cases or caveats to consider
- hard: Complex logic, many caveats, architectural considerations, or high-risk changes

Create a technical specification for the task that is appropriate for the complexity level:
- Review the existing codebase architecture and identify reusable components.
- Define the implementation approach based on established patterns in the project.
- Identify all source code files that will be created or modified.
- Define any necessary data model, API, or interface changes.
- Describe verification steps using the project's test and lint commands.

Save the output to `{@artifacts_path}/spec.md` with:
- Technical context (language, dependencies)
- Implementation approach
- Source code structure changes
- Data model / API / interface changes
- Verification approach

If the task is complex enough, create a detailed implementation plan based on `{@artifacts_path}/spec.md`:
- Break down the work into concrete tasks (incrementable, testable milestones)
- Each task should reference relevant contracts and include verification steps
- Replace the Implementation step below with the planned tasks

Rule of thumb for step size: each step should represent a coherent unit of work (e.g., implement a component, add an API endpoint, write tests for a module). Avoid steps that are too granular (single function).

Important: unit tests must be part of each implementation task, not separate tasks. Each task should implement the code and its tests together, if relevant.

Save to `{@artifacts_path}/plan.md`. If the feature is trivial and doesn't warrant this breakdown, keep the Implementation step below as is.

---

### [x] Step: Update weather.py to use Open-Meteo API
<!-- chat-id: f1f9fab6-1421-464c-a2b8-744ea684fe1d -->

Implement the core weather API replacement:
- Remove `python_weather` import and use existing `aiohttp` HTTP client
- Add `WMO_WEATHER_SYMBOL` dictionary mapping WMO weather codes to emojis
- Implement `get_coordinates()` helper function using Open-Meteo Geocoding API
- Implement Open-Meteo Weather API integration in `get_weather()` function
- Map API response data to existing Notion block format
- Add comprehensive error handling (network failures, city not found, malformed responses)
- Add logging for debugging
- Update all 22 tests in `tests/test_weather.py` to mock `aiohttp.ClientSession`
- Add new tests for `get_coordinates()` function
- Add new tests for error scenarios (network timeout, city not found, malformed JSON)
- Run tests: `poetry run pytest tests/test_weather.py -v`

**Verification**:
- All weather tests pass
- Code handles error cases gracefully
- Weather data mapping is correct

---

### [x] Step: Update dependencies and documentation
<!-- chat-id: 37ce20f7-3d53-4827-aa4e-ecd2125b99ab -->

Clean up dependencies and update documentation:
- Remove `python-weather` dependency from `pyproject.toml`
- Update `README.md` to remove `OPENWEATHER_API_KEY` and mention Open-Meteo as the weather data source
- Add note about Open-Meteo being free and requiring no API key
- Run full test suite: `poetry run pytest`
- Run linting: `poetry run flake8 src tests`
- Run formatting check: `poetry run black src tests --check && poetry run isort src tests --check --profile black`

**Verification**:
- All 82+ tests pass
- Linting passes with no warnings
- Formatting is compliant
- Documentation is accurate

---

### [ ] Step: Integration testing and final verification
<!-- chat-id: 0fe81d6a-b3f4-4aad-9b35-ff73eab52e05 -->

Perform manual integration testing:
- Test with real Open-Meteo API calls locally: `poetry run python -m startpage.startpage`
- Verify weather data displays correctly in Notion page
- Test multiple cities to ensure geocoding and data accuracy
- Test error scenarios (invalid city name, network failures)
- Verify Lambda deployment works (optional, if changes affect deployment)
- Write implementation report to `{@artifacts_path}/report.md`

**Verification**:
- Weather data fetches successfully from Open-Meteo
- Correct emoji, temperature range, humidity, wind data displayed
- Notion page updates correctly
- Error handling works as expected
