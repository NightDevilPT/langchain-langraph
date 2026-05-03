CLASSIFIER_PROMPT = """Classify as 'hardware' or 'software'.

Examples:
"CPU usage?" → hardware
"RAM info?" → hardware
"Disk space?" → hardware
"What OS?" → software
"Python packages?" → software
"Is Chrome running?" → software

Return ONLY: hardware or software"""