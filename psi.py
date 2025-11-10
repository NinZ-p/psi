from openai import OpenAI
import re
import sys

class Evaluator:
  class Answer:
    def __init__(self,action_plan,evaluation):
      self.action_plan=action_plan
      self.evaluation=evaluation
    
    def __repr__(self):
      r=""
      r+=f'action_plan: """{self.action_plan}"""\nevaluation: """{self.evaluation}"""'
      return (r)
    def __str__(self):
      return (self.__repr__())

  def __init__(self,model_id):
    self.model_id=model_id
    self.api_key=None

    try:
      with open("key.txt","r") as file_obj:
        self.api_key=file_obj.readline()
    except:
      sys.exit("Couldn't open API key file. Create a key.txt file with a valid openrouter key.")
    if not re.match(r"^[a-zA-Z0-9_.-]{32,}$",self.api_key):
      sys.exit("Invalid API key")
  
  def __call_model_on_prompt(self,prompt):
    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=self.api_key,
    )

    completion = client.chat.completions.create(
      extra_headers={
      },
      extra_body={},
      model=self.model_id,
      messages=[
        {
          "role": "user",
          "content": prompt
        }
      ]
    )
    return(completion.choices[0].message.content)

  def __generate_policy_prompt(self,user_prompt):
    try:
      with open("prompt_policy_head.txt","r") as file_obj:
        file_content="".join(file_obj.readlines())
    except:
      sys.exit("Couldn't read the policy head prompt")
    return file_content.replace("<USER_PROMPT>",user_prompt)

  def __generate_evaluation_prompt(self,user_prompt,action_plan,corporate_values):
    try:
      with open("prompt_evaluation_head.txt","r") as file_obj:
        file_content="".join(file_obj.readlines())
    except:
      sys.exit("Couldn't read the policy head prompt")
    return file_content.replace("<USER_PROMPT>",user_prompt).replace("<ACTION_PLAN>",action_plan).replace("<CORPORATE_VALUES>",corporate_values)

  def __find_eval(self,topic,answer):
    for line in answer.split("\n"):
      if topic in line:
        if "<adequado>" in line: return ("<adequado>")
        elif "<inconclusivo>" in line: return ("<inconclusivo>")
        elif "<inadequado>" in line: return ("<inadequado>")
        else:
          sys.exit(f"Model didn't return a valid evaluation: {answer}")
    sys.exit(f"Evaluation topic not in model's answer: {answer}")

  def find_action(self,user_prompt,corporate_values):
    if self.model_id==None:
      return ()

    action_plan=...

    while True:

      answer=(self.__call_model_on_prompt(self.__generate_policy_prompt(user_prompt)))
      if not "###plano_de_acao" in answer:
        sys.exit(f"Policy head didn't output a action plan: '{answer}'")

      action_plan=answer.split("###plano_de_acao")[-1]

      eval_prompt=self.__generate_evaluation_prompt(user_prompt,action_plan,corporate_values)

      evaluation_answer=self.__call_model_on_prompt(eval_prompt)

      evaluation_dict={
        "etica":self.__find_eval("###ética",evaluation_answer),
        "moral":self.__find_eval("###moral",evaluation_answer),
        "efetividade_economica":self.__find_eval("###efetividade_econômica",evaluation_answer),
        "valores_empresariais":self.__find_eval("###valores_empresariais",evaluation_answer)
      }

      if evaluation_dict["etica"]!="<adequado>" or evaluation_dict["moral"]=="<inadequado>" or evaluation_dict["efetividade_economica"]=="<inadequado>" or evaluation_dict["valores_empresariais"]=="<inadequado>":
        continue

      return Evaluator.Answer(
        action_plan=action_plan,
        evaluation=evaluation_dict
      )