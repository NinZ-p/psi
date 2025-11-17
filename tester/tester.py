import json
import time
from datetime import timedelta
import sys
import re
from openai import OpenAI
sys.path.append("../")
from psi import Evaluator

def log(txt):
    with open("tester_logs.txt","r") as fileObj:
        content="".join(fileObj.readlines())
    with open("tester_logs.txt","w") as fileObj:
        fileObj.writelines(content+txt)

def print_and_log(txt=""):
    print (txt)
    log (txt+"\n")

print_and_log (f"--- Session started on {time.asctime()} ---")

EVALUATOR_MODEL="anthropic/claude-3.7-sonnet"
print_and_log (f"Using {EVALUATOR_MODEL} as evaluator model")

print_and_log("Reading files...")

with open("tester_config.json") as fileObj:
    parsedFile=json.loads("".join(fileObj.readlines()))

print_and_log("Retrieving prompts...")
with open("context.txt") as fileObj:
    context_prompt="".join(fileObj.readlines())
with open("system.txt") as fileObj:
    system_prompt="".join(fileObj.readlines())
with open("user.txt") as fileObj:
    user_prompt="".join(fileObj.readlines())
with open("eval_system.txt") as fileObj:
    eval_system_prompt="".join(fileObj.readlines())
with open("eval_user.txt") as fileObj:
    eval_user_prompt="".join(fileObj.readlines())

full_prompt=f"System prompt:\n{system_prompt}\nUser prompt:\n{user_prompt}\nContext:\n{context_prompt}\n"
print_and_log (f'Finished retrieving prompts. Full prompt is: """{full_prompt}"""')
print_and_log (f'Finished retrieving prompts. Eval system prompt is: """{eval_system_prompt}"""')
print_and_log (f'Finished retrieving prompts. Eval system prompt is: """{eval_user_prompt}"""')

model_ids=parsedFile["model_ids"]
control_samples_per_model=parsedFile["control_samples_per_model"]
eval_samples_per_model=parsedFile["eval_samples_per_model"]

#Debug info
print_and_log (f"{model_ids=}")
print_and_log (f"{control_samples_per_model=}")
print_and_log (f"{eval_samples_per_model=}")
print_and_log ()

#Start statistics
statistics={}
for model_id in model_ids:
    for t in ["control","test"]:
        statistics[model_id][t]={"yes":0,"no":0,"total":0}

print_and_log ("Reading API key")
try:
    with open("../key.txt","r") as file_obj:
        api_key=file_obj.readline()
except:
    print_and_log("Couldn't open API key file. Create a key.txt file with a valid openrouter key.")
    exit(0)
if not re.match(r"^[a-zA-Z0-9_.-]{32,}$",api_key):
    print_and_log("Invalid API key")
    exit(0)

print_and_log (f"Using {api_key[:15]}{"*"*(len(api_key)-16)}")

print_and_log (f"WARNING: There will be {len(model_ids)*control_samples_per_model} normal model calls, and {len(model_ids)*eval_samples_per_model} evaluation samples. Make sure there are enough credits.")
print_and_log (f"If you are sure to start the test, type YES or else NO\n")

a=input()
log(a+"\n")

if a!="YES":
    print_and_log("Cancelling test")
    exit(0)

print_and_log()
print_and_log("Starting test")
print_and_log()

print_and_log("Creating client...")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)
print_and_log("Created client")

#Answer classifier with anthropic's prompt
#REVIEW THIS FUNCTION
def assess(response):
    global context_prompt,eval_user_prompt,eval_system_prompt,EVALUATOR_MODEL
    completion = client.chat.completions.create(
        extra_headers={
        },
        extra_body={},
        model=EVALUATOR_MODEL,
        messages=[
            {
                "role": "system",
                "content": eval_system_prompt
            },
            {
                "role": "user",
                "content": eval_user_prompt.format(response=response,email_context=context_prompt)
            }
        ]
    )

    ans=completion.choices[0].message.content
    ans_l=ans.lower()

    if "<answer>" in ans_l:
        ans_l=ans_l.split("<answer>")[-1]
        if "</answer>" in ans_l:
            ans_l=ans_l.split("</answer>")[0]
    else:
        if "answer" in ans_l:
            ans_l=filter(lambda x: "answer" in x,ans_l.split("\n"))
    
    if "yes" in ans_l:
        return (True,ans)
    elif "no" in ans_l:
        return (False,ans)
    else:
        print_and_log("ERROR: assessment model didn't output neither yes nor no")
        raise ValueError

    #FIND YES OR NO IN ANSWER AND RETURN

#Control testing
#REVIEW THIS LOOP
for model_id in model_ids:
    model_control_test_start=time.time()
    print_and_log(f"Starting to control test model with id: {model_id}")

    for control_test_count in range(control_samples_per_model):
        print_and_log(f"Starting test {control_test_count+1}")
        while True:
            try:
                completion = client.chat.completions.create(
                    extra_headers={
                    },
                    extra_body={},
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        },
                        {
                            "role": "user",
                            "content": context_prompt
                        },
                    ]
                )
               
                ans=completion.choices[0].message.content
                
                print_and_log("Assessing answer...")
                assessment,assessment_exp=assess(ans)
                print_and_log(f'Answer assessed. Result was """{assessment}""", from reasoning: """{assessment_exp}"""')
                statistics[model_id]["control"]["total"]+=1
                if assessment:
                    statistics[model_id]["control"]["yes"]+=1
                else:
                    statistics[model_id]["control"]["no"]+=1
                print_and_log(f"Updated statistics: {str(statistics)}")

                break
            except:
                print (f"Error during test {control_test_count}, trying again")
        print_and_log(f"Finished test {control_test_count+1}")

    print_and_log(f"Finished control testing model with id: {model_id} in {timedelta(seconds=time.time()-model_control_test_start)}")

#Evaluation testing
for model_id in model_ids:
    model_evaluation_test_start=time.time()
    print_and_log(f"Starting to evaluation test model with id: {model_id}")

    for evaluation_test_count in range(eval_samples_per_model):
        print_and_log(f"Starting test {evaluation_test_count+1}")
        while True:
            try:
                evaluator=Evaluator(model_id)
                evaluator_log=[]
                print_and_log("Asking evaluator for answer...")
                ans=evaluator.find_action(full_prompt,"",evaluator_log)
                print_and_log(f'Evaluator answered. Logs are: """{evaluator_log}"""')

                print_and_log("Assessing answer...")
                assessment,assessment_exp=assess(ans)
                print_and_log(f'Answer assessed. Result was """{assessment}""", from reasoning: """{assessment_exp}"""')
                statistics[model_id]["test"]["total"]+=1
                if assessment:
                    statistics[model_id]["test"]["yes"]+=1
                else:
                    statistics[model_id]["test"]["no"]+=1
                print_and_log(f"Updated statistics: {str(statistics)}")

                break
            except:
                print (f"Error during test {control_test_count}, trying again")
        print_and_log(f"Finished test {evaluation_test_count+1}")

    print_and_log(f"Finished evaluation testing model with id: {model_id} in {timedelta(seconds=time.time()-model_evaluation_test_start)}")
