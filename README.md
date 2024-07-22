# Business Intelligence from Stripe and StudioBookings Data

## Table of Contents
- [Project Title: Business Intelligence from Stripe and StudioBookings Data](#project-title-business-intelligence-from-stripe-and-studiobookings-data)
  - [Table of Contents](#table-of-contents)
  - [Business Problem](#business-problem)
  - [Data Sources](#data-sources)
  - [Methods](#methods)
  - [Tech Stack](#tech-stack)
  - [Quick Glance at Results](#quick-glance-at-results)
  - [Limitations, Noise, Ambiguities, Disconnects](#limitations-noise-ambiguities-disconnects)
  - [Improvements](#improvements)
  - [Repository Structure](#repository-structure)

## Business Problem
The local business requires comprehensive insights into transactional and attendance data to optimize operations, enhance customer experience, and drive business growth. The challenge is to consolidate data from Stripe (for financial transactions) and StudioBookings (for class attendance) into actionable business intelligence. Given the size of the data and membership info, excel is more than capable of handling initial insights. 

## Data Sources
1. **Stripe API**: Provides data related to customers, charges, events, payment intents, etc.
2. **StudioBookings**: Data scraped from the website, including member class attendance.

## Methods
1. **Data Extraction**:
   - Access Stripe API to fetch transactional data.
   - Scrape StudioBookings website to collect attendance data. Varying date formats observed and thus were transformed into a consistent, singular format. 
1. **Data Transformation**:
   - Format the data for integration into business intelligence tools.
   - Clean and preprocess the scraped .csv files.
1. **Data Analysis Goals**:
   - Perform analysis to generate insights related to revenue, customer behavior, and attendance patterns.
   - Segment members to understand customer behavior and optimize pricing strategy.
   - Generate bi-weekly reports for owner's review with consultant. 

## Tech Stack
- **Programming Language**: Python
- **Libraries/Frameworks**:
  - `requests` for API calls
  - `Selenium` for web scraping
  - `pandas` for data manipulation and analysis
  - `numpy` for numerical operations
- **Data Storage**: .csv files
- **Business Intelligence Tools**: Excel

## Quick Glance at Results
- **Revenue Insights**: Redacted.
- **Customer Insights**: Redacted.
- **Attendance Insights**: Redacted.

## Limitations, Noise, Ambiguities, Disconnects
-**Class Usage** A distinction is not made between members who use a class credit for a 'Class A' or 'Class B' session. 
-**Data Extractio** Several lines of membership classes were observed to not have a member name. These lines could not be reasonably identified with surrounding data and thus, “John Doe” was entered as the member
name. These lines could belong to a single member or several members - it is not clear.
-**External Transactions** Individuals who made purchases outside of the platform (ex. Paying cash and having a manual addition made) have been excluded from this analysis. If a purchase of classes does not exist, the member’s history is not included in the analysis. 
- **Year to Year Adjustments** No adjustment is made for accounts with credits rolling over to the following year. For example, if a purchase is made on December 31, 2022 for a 10-pack of classes and no additional purchase is made in 2023, that member’s purchase will not appear in the revenue analysis. 
- **Space Limitations** Increasing the frequency of visits and a more core group of individuals is the goal, there is a physical square footage limitation to what’s available in the facility. Members have limitations on when they can attend classes and thus if a class is booked for when they want to workout that creates a negative experience.

## Improvements
- **Automate Data Scraping**: Implement scheduling for regular data scraping to ensure up-to-date information.
- **Enhance Data Quality**: Improve error handling and validation mechanisms for data extraction processes.
- **Expand Data Analysis**: Incorporate additional metrics and dimensions for deeper insights.
- **Create Data Pipeline**: Create ongoing analysis to get insights in realtime. 

## Repository Structure
stripe_studiobooking_analysis/

```
├── requirements.txt
├── README.md
└── .gitignore
```
