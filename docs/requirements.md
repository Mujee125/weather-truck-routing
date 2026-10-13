# Weather-Aware Truck Routing — Requirements

**Project:** Spotter.ai Full Stack Developer Assessment  
**Stack:** React + Django  
**Time limit:** No more than 4 days and 16 work hours

## 1. Objective

Build a web application that helps a truck driver choose a route by considering weather conditions, load weight, and travel time.

## 2. User Inputs

The user enters:

- Origin and destination
- Departure date and time
- Load weight

## 3. Functional Requirements

The application must:

1. Generate **three route options** using a routing API.
2. Sample weather along each route every **10, 25, or 50 miles**, using the truck's estimated arrival time at each checkpoint.
3. Calculate checkpoint weather risk using the weather thresholds and load rules in Section 4.
4. Recommend the best route using the preference order in Section 5.
5. Show all available routes, checkpoints, risk levels, ETAs, and route summaries on a map.
6. Show a weather heatmap along the trip corridor with a **0–48-hour forecast slider**.

Third-party routing, geocoding, and weather APIs may be used. Building a routing engine is not required.

## 4. Risk Rules

### 4.1 Weather thresholds

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind | < 25 mph | 25–34 mph | 35–44 mph | 45–54 mph | ≥ 55 mph |
| Rain | < 0.10 in/hr | 0.10–0.25 in/hr | 0.25–0.50 in/hr | 0.50–1.00 in/hr | > 1.00 in/hr |
| Snow | < 0.5 in/hr | 0.5–1.0 in/hr | 1.0–2.0 in/hr | 2.0–3.0 in/hr | > 3.0 in/hr |

### 4.2 Load rules

- Wind **≥ 55 mph** means **No Travel** for any load.
- Wind **45–54 mph** with load **> 30,000 lb** means **No Travel**.
- Wind **35–44 mph** with load **> 40,000 lb** means **Severe**.

## 5. Route Recommendation

Prefer routes in this order:

1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel time

## 6. Deliverables

- GitHub repository
- Hosted application
- 5–10 minute Loom walkthrough

## 7. Evaluation Criteria

| Area | Weight |
|---|---:|
| Routes, weather, risk, and recommendation logic | 40% |
| UI, map, heatmap smoothness, and performance | 35% |
| Code quality | 10% |
| Documentation and walkthrough | 5% |

## 8. Clarifications to Resolve During Implementation

The assessment does not specify:

- How to resolve overlapping boundary values in the rain and snow ranges.
- How to combine wind, rain, and snow risks at a checkpoint.
- How checkpoint risk is converted into Severe miles, High miles, and average risk.
- How a route containing a No Travel checkpoint affects the final recommendation.
- What to display when the routing API returns fewer than three routes or weather data is unavailable.
- The reference time for the 0–48-hour forecast slider.
