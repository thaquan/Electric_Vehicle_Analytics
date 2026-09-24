# Data dictionary

This dictionary is generated from the first profiling run. Column meanings are based on the Kaggle notebook description; types and observed values are derived from the local CSV files.

| Field | Logical type | Role |
| --- | --- | --- |
| Buyer_ID | Categorical | Original-source record key |
| Age | Numeric | Buyer demographic |
| Gender | Categorical | Buyer demographic |
| Annual_Income_USD | Numeric | Financial attribute |
| City_Type | Categorical | Location segment |
| Daily_Commute_km | Numeric | Mobility attribute |
| Number_of_Cars_Owned | Numeric | Vehicle ownership |
| Current_Car_Type | Categorical | Current vehicle |
| Charging_Stations_Near_Home | Numeric | Charging infrastructure |
| Charging_Stations_Near_Work | Numeric | Charging infrastructure |
| Home_Charging_Possible | Categorical | Charging accessibility |
| Environmental_Concern_Level | Categorical | Environmental attitude |
| Subsidy_Available | Categorical | Policy/incentive |
| Range_Anxiety_Level | Categorical | EV adoption barrier |
| Will_Buy_EV | Categorical | EV purchase-interest target |
| id | Numeric | Competition record key |

Important: this is a synthetic competition dataset. Analytical results describe this dataset only and are not causal or population-level EV-market claims.
