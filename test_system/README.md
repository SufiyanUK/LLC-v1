# Employee Tracker Test System

This test system allows you to verify the departure detection and alert classification logic without using any PDL credits.

## Quick Start

### Windows
Double-click `run_test.bat` or run:
```bash
run_test.bat
```

### Mac/Linux or Python
```bash
python run_test.py
```

Or directly:
```bash
python test_departure_system.py
```

## What Gets Tested

The test system simulates 5 different scenarios:

### 1. **Level 1 Alert - Standard Departure**
- Employee: John Smith
- Scenario: OpenAI → Microsoft (big tech to big tech)
- Expected: Yellow alert (Level 1)

### 2. **Level 2 Alert - Building Signals**
- Employee: Sarah Johnson  
- Scenario: Anthropic → "Working on something new"
- Expected: Orange alert (Level 2)
- Signals: "building", "something new", "stealth mode"

### 3. **Level 3 Alert - Joined Startup**
- Employee: Michael Chen
- Scenario: Meta → NeuralTech AI (CTO & Co-Founder)
- Expected: Red alert (Level 3)
- Company size: 11-50 employees

### 4. **Level 3 Alert - Stealth Mode**
- Employee: Emily Rodriguez
- Scenario: Google → CEO (no company name)
- Expected: Red alert (Level 3)
- Signals: "Building in stealth"

### 5. **No Alert - Still Employed**
- Employee: David Kim
- Scenario: Stays at DeepMind
- Expected: No departure detected

## Test Flow

1. **Initial Tracking**: Simulates tracking 5 employees
2. **Departure Check**: Checks for departures after 1 month
3. **Alert Classification**: Classifies departures using production logic
4. **Email Simulation**: Shows what emails would be sent
5. **Validation**: Verifies results match expected outcomes

## Files

- `test_departure_system.py` - Main test script
- `mock_pdl_data.py` - Mock PDL API responses
- `run_test.bat` - Windows batch file runner
- `run_test.py` - Cross-platform Python runner

## Understanding Results

The test will show:
- ✅ **PASSED**: Classification matches expected level
- ❌ **FAILED**: Classification doesn't match expected level

Example output:
```
🔴 LEVEL 3 - STARTUP/FOUNDER (2 alerts)
  • Michael Chen
    From: Meta → To: NeuralTech AI
    Signals: startup_size, recent_founding, cto_cofounder

🟠 LEVEL 2 - BUILDING SIGNALS (1 alert)
  • Sarah Johnson
    From: Anthropic → To: Stealth Startup
    Signals: building_something, stealth_mode

🟡 LEVEL 1 - STANDARD DEPARTURE (1 alert)
  • John Smith
    From: OpenAI → To: Microsoft
```

## Credits Usage

This test system uses **0 PDL credits**. It shows what would be used in production:
- Initial tracking: 5 credits
- Monthly check: 5 credits
- Total per month: 10 credits