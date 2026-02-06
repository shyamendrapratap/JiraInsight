#!/bin/bash
# Test script to monitor filter changes in real-time

echo "==============================================="
echo "Dashboard Filter Test Monitor"
echo "==============================================="
echo ""
echo "Dashboard URL: http://127.0.0.1:8050"
echo ""
echo "Instructions:"
echo "1. Open http://127.0.0.1:8050 in your browser"
echo "2. Go to the Overview tab"
echo "3. Change the 'Select Projects' dropdown"
echo "4. Watch this terminal for log output"
echo ""
echo "Expected behavior:"
echo "- Selecting CCT only → Sprint Predictability ~71%"
echo "- Selecting SCPX only → Sprint Predictability ~0%"
echo "- Selecting both → Combined average"
echo ""
echo "Monitoring dashboard.log for filter activity..."
echo "Press Ctrl+C to stop"
echo ""
echo "==============================================="
echo ""

# Follow the log and filter for relevant lines
tail -f dashboard.log | grep --line-buffered -E "_apply_filters|Filter applied|Sprint Predictability|Work Mix|Cycle Time"
