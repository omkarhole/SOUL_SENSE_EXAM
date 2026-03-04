# 📱 Android / iOS Event Parity Checklist

> **Version**: 1.0  
> **Last Updated**: 2026-02-27  
> **Audit Frequency**: Weekly (Every Monday)  
> **Owner**: Mobile Platform Team

---

## 🎯 Objective

Maintain 100% event parity between Android and iOS platforms to ensure consistent analytics data across all mobile touchpoints.

---

## ✅ Weekly Audit Checklist

### 1. Event Count Verification

| Platform | Expected Events | Actual Events | Status |
|----------|-----------------|---------------|--------|
| Android  | 35              | ___           | ⬜     |
| iOS      | 35              | ___           | ⬜     |

**Validation Criteria**: Both platforms must have identical event counts.

---

### 2. Event-by-Event Parity Check

| # | Event Name | Android Status | iOS Status | Matched | Notes |
|---|------------|----------------|------------|---------|-------|
| 1 | `screen_view` | ⬜ | ⬜ | ⬜ | |
| 2 | `login_screen_view` | ⬜ | ⬜ | ⬜ | |
| 3 | `signup_screen_view` | ⬜ | ⬜ | ⬜ | |
| 4 | `profile_screen_view` | ⬜ | ⬜ | ⬜ | |
| 5 | `settings_screen_view` | ⬜ | ⬜ | ⬜ | |
| 6 | `button_click` | ⬜ | ⬜ | ⬜ | |
| 7 | `start_button_click` | ⬜ | ⬜ | ⬜ | |
| 8 | `login_button_click` | ⬜ | ⬜ | ⬜ | |
| 9 | `signup_button_click` | ⬜ | ⬜ | ⬜ | |
| 10 | `logout_button_click` | ⬜ | ⬜ | ⬜ | |
| 11 | `signup_start` | ⬜ | ⬜ | ⬜ | |
| 12 | `signup_success` | ⬜ | ⬜ | ⬜ | |
| 13 | `signup_failure` | ⬜ | ⬜ | ⬜ | |
| 14 | `login_attempt` | ⬜ | ⬜ | ⬜ | |
| 15 | `login_success` | ⬜ | ⬜ | ⬜ | |
| 16 | `login_failure` | ⬜ | ⬜ | ⬜ | |
| 17 | `payment_start` | ⬜ | ⬜ | ⬜ | |
| 18 | `payment_success` | ⬜ | ⬜ | ⬜ | |
| 19 | `payment_failure` | ⬜ | ⬜ | ⬜ | |
| 20 | `journal_entry_created` | ⬜ | ⬜ | ⬜ | |
| 21 | `assessment_started` | ⬜ | ⬜ | ⬜ | |
| 22 | `assessment_completed` | ⬜ | ⬜ | ⬜ | |
| 23 | `report_viewed` | ⬜ | ⬜ | ⬜ | |
| 24 | `app_launch` | ⬜ | ⬜ | ⬜ | |
| 25 | `app_background` | ⬜ | ⬜ | ⬜ | |
| 26 | `app_foreground` | ⬜ | ⬜ | ⬜ | |
| 27 | `app_crash` | ⬜ | ⬜ | ⬜ | |
| 28 | `device_rotation` | ⬜ | ⬜ | ⬜ | |
| 29 | `session_start` | ⬜ | ⬜ | ⬜ | |
| 30 | `session_end` | ⬜ | ⬜ | ⬜ | |
| 31 | `network_error` | ⬜ | ⬜ | ⬜ | |
| 32 | `api_error` | ⬜ | ⬜ | ⬜ | |
| 33 | `validation_error` | ⬜ | ⬜ | ⬜ | |

**Legend**:  
- ⬜ = Pending / Not Verified  
- ✅ = Verified & Matched  
- ❌ = Mismatch Found  
- ⚠️ = Deprecated / To Be Removed

---

### 3. Schema Compliance Check

| Check | Android | iOS | Status |
|-------|---------|-----|--------|
| All events in `event_schema.json` | ⬜ | ⬜ | |
| Naming convention (snake_case) | ⬜ | ⬜ | |
| No camelCase events | ⬜ | ⬜ | |
| No undocumented prefixes | ⬜ | ⬜ | |

---

### 4. Property Parity Check

| Event | Android Properties | iOS Properties | Matched |
|-------|-------------------|----------------|---------|
| `session_end` | `session_duration_ms`, `session_duration_seconds` | `session_duration_ms`, `session_duration_seconds` | ⬜ |
| `button_click` | `button_name`, `element_type` | `button_name`, `element_type` | ⬜ |
| `screen_view` | `screen_name` | `screen_name` | ⬜ |

---

### 5. New Events Since Last Audit

| Event Name | Platform | Date Added | Schema Updated | Status |
|------------|----------|------------|----------------|--------|
| | | | | |

---

### 6. Deprecated Events

| Event Name | Platform | Deprecation Date | Removal Target | Status |
|------------|----------|------------------|----------------|--------|
| | | | | |

---

## 🏃‍♂️ How to Run Weekly Audit

### Automated Audit (Recommended)

```bash
# Run the automated parity audit
python scripts/audit_event_parity.py

# Generate detailed report
python scripts/audit_event_parity.py --format markdown --output docs/parity_reports/

# Compare specific files
python scripts/audit_event_parity.py --android mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java \
                                     --ios mobile-app/ios/SoulSense/AnalyticsEvents.swift
```

### Manual Verification Steps

1. **Open both files side-by-side**:
   - Android: `mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java`
   - iOS: `mobile-app/ios/SoulSense/AnalyticsEvents.swift`

2. **Cross-reference with schema**:
   - Master: `shared/analytics/event_schema.json`

3. **Verify each event**:
   - Check event name spelling
   - Check event value matches exactly
   - Verify property names are consistent

4. **Document findings** in this checklist

---

## 📊 Parity Score Calculation

```
Parity Score = (Matched Events / Total Expected Events) × 100
```

| Score | Status | Action Required |
|-------|--------|-----------------|
| 100% | ✅ Perfect | None |
| 95-99% | ⚠️ Good | Document discrepancies |
| 90-94% | 🔶 Warning | Schedule fix within 1 week |
| <90% | 🚨 Critical | Immediate action required |

**Current Parity Score**: ___%

---

## 🔧 Remediation Process

### When Mismatch Detected

1. **Immediate Actions** (Day 1):
   - [ ] Create JIRA ticket with label `analytics-parity`
   - [ ] Document the mismatch in this checklist
   - [ ] Notify mobile platform team

2. **Investigation** (Day 1-2):
   - [ ] Identify source of mismatch
   - [ ] Determine which platform has the correct implementation
   - [ ] Check if schema needs updating

3. **Fix Implementation** (Day 2-3):
   - [ ] Update the out-of-sync platform
   - [ ] Update schema if new event added
   - [ ] Add test cases for the event

4. **Verification** (Day 4):
   - [ ] Re-run audit script
   - [ ] Verify 100% parity restored
   - [ ] Update this checklist

---

## 📈 Historical Trends

| Week | Parity Score | Android Events | iOS Events | Mismatches | Notes |
|------|--------------|----------------|------------|------------|-------|
| 2026-W09 | ___% | ___ | ___ | ___ | |
| 2026-W08 | ___% | ___ | ___ | ___ | |
| 2026-W07 | ___% | ___ | ___ | ___ | |

---

## 🔗 Related Documents

- [Analytics Architecture](../shared/analytics/README.md)
- [Event Schema](../shared/analytics/event_schema.json)
- [Android Analytics](../mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java)
- [iOS Analytics](../mobile-app/ios/SoulSense/AnalyticsEvents.swift)

---

## 📝 Audit Log

| Date | Auditor | Parity Score | Issues Found | Actions Taken |
|------|---------|--------------|--------------|---------------|
| 2026-02-27 | | | | |

---

## 🚨 Escalation

If parity falls below 90%, escalate to:
1. Mobile Platform Lead
2. Data Analytics Team Lead
3. Engineering Manager

---

*This checklist is automatically generated and updated by the weekly audit process.*
