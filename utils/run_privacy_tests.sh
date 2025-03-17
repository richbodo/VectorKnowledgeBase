#!/bin/bash
# Privacy Test Runner Script
# This script runs a comprehensive suite of privacy tests and generates a report

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create test reports directory if it doesn't exist
mkdir -p test_reports

# Generate timestamp for report
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="test_reports/privacy_test_report_${TIMESTAMP}.txt"

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}       Vector Knowledge Base Privacy Test Suite       ${NC}"
echo -e "${BLUE}=====================================================${NC}"
echo -e "${YELLOW}Running comprehensive privacy tests...${NC}"
echo ""

# Create report header
echo "PRIVACY TEST REPORT" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo "=====================================================" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Function to run a test and update the report
run_test() {
    TEST_NAME=$1
    TEST_COMMAND=$2
    
    echo -e "${YELLOW}Running test: ${TEST_NAME}...${NC}"
    echo "TEST: $TEST_NAME" >> $REPORT_FILE
    echo "----------------------------------------------------" >> $REPORT_FILE
    
    # Run the test and capture output
    OUTPUT=$(eval $TEST_COMMAND 2>&1)
    STATUS=$?
    
    # Save output to report
    echo "$OUTPUT" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    
    # Check result
    if [ $STATUS -eq 0 ] && [[ $OUTPUT == *"PASSED"* ]] && [[ ! $OUTPUT == *"FAILED"* ]]; then
        echo -e "${GREEN}✅ Test passed!${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "RESULT: PASSED" >> $REPORT_FILE
    else
        echo -e "${RED}❌ Test failed!${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "RESULT: FAILED" >> $REPORT_FILE
    fi
    
    echo "" >> $REPORT_FILE
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Initialize counters
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_TESTS=0

# Test 1: Basic Privacy Filter Test
run_test "Basic Privacy Filter" "python utils/test_privacy_filter.py"

# Test 2: API Query Privacy Test
run_test "API Query Privacy" "python utils/test_privacy.py"

# Test 3: Check log file for unfiltered content
echo -e "${YELLOW}Running test: Log File Privacy Audit...${NC}"
echo "TEST: Log File Privacy Audit" >> $REPORT_FILE
echo "----------------------------------------------------" >> $REPORT_FILE

# Look for common PII patterns in logs
PII_PATTERN="(password|credit.?card|ssn|social.?security|secret|token)"
LOG_CHECK=$(grep -i -E "$PII_PATTERN" app.log | grep -v "REDACTED")

if [ -z "$LOG_CHECK" ]; then
    echo -e "${GREEN}✅ No unfiltered PII found in logs!${NC}"
    echo "No unfiltered PII found in logs" >> $REPORT_FILE
    echo "RESULT: PASSED" >> $REPORT_FILE
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Potential unfiltered PII found in logs!${NC}"
    echo "Potential unfiltered PII found in logs:" >> $REPORT_FILE
    echo "$LOG_CHECK" >> $REPORT_FILE
    echo "RESULT: FAILED" >> $REPORT_FILE
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "" >> $REPORT_FILE

# Generate report summary
echo "SUMMARY" >> $REPORT_FILE
echo "=====================================================" >> $REPORT_FILE
echo "Total tests: $TOTAL_TESTS" >> $REPORT_FILE
echo "Tests passed: $PASSED_TESTS" >> $REPORT_FILE
echo "Tests failed: $FAILED_TESTS" >> $REPORT_FILE
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((100 * PASSED_TESTS / TOTAL_TESTS))
    echo "Success rate: ${PASS_RATE}%" >> $REPORT_FILE
fi
echo "" >> $REPORT_FILE

# Display summary to console
echo ""
echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}                 Test Summary                        ${NC}"
echo -e "${BLUE}=====================================================${NC}"
echo -e "Total tests: ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "Tests passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Tests failed: ${RED}$FAILED_TESTS${NC}"
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((100 * PASSED_TESTS / TOTAL_TESTS))
    if [ $PASS_RATE -eq 100 ]; then
        echo -e "Success rate: ${GREEN}${PASS_RATE}%${NC}"
    elif [ $PASS_RATE -gt 75 ]; then
        echo -e "Success rate: ${YELLOW}${PASS_RATE}%${NC}"
    else
        echo -e "Success rate: ${RED}${PASS_RATE}%${NC}"
    fi
fi
echo ""
echo -e "${BLUE}Report saved to: ${NC}${YELLOW}$REPORT_FILE${NC}"
echo -e "${BLUE}=====================================================${NC}"

exit 0