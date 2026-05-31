HUBSPOT_CONTACT_COUNT: int = 1000
HUBSPOT_ACTIVITY_COUNT: int = 5000
MARKETING_SOURCE_COUNT: int = 10

D365_STUDENT_COUNT: int = 300
ENROLMENT_COUNT: int = 1000
COURSE_COUNT: int = 20
INTAKE_COUNT: int = 6

PARADIGM_STUDENT_COUNT: int = 250
UNITS_PER_COURSE: int = 5
RESULT_COUNT: int = 1500

RANDOM_SEED: int = 42
OUTPUT_BASE_PATH: str = "output/"

# Cross-system linkage rates
D365_CONTACT_LINK_RATE: float = 0.90   # 90% of D365 students have a HubSpot contact_id
EMAIL_CASING_MESS_RATE: float = 0.30   # 30% of emails get uppercase or mixed-case casing
PARADIGM_D365_COVERAGE_RATE: float = 0.833  # ~250 of 300 D365 students appear in Paradigm
