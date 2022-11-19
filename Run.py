import sys
import subprocess

CATEGORY = [
    'category_Development',
    'category_Business',
    'category_Finance_Accounting',
    'category_IT_Software',
    'category_Office_Productivity',
    'category_Personal_Development',
    'category_Design',
    'category_Marketing',
    'category_Lifestyle',
    'category_Photography_Video',
    'category_Health_Fitness',
    'category_Music',
    'category_Teaching_Academics'
]

print("Starting Script", end="\n\n")

for C in CATEGORY:
    print(f"Fetching {C}")
    subprocess.run(f"python Spider.py {C}")
    print(f"Finished {C}", end="\n\n")

print("Script Ended", end="\n\n")
