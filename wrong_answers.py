from dotenv import load_dotenv
import json
import os
import openai
import logging
from pathlib import Path
from time import sleep

log = logging.getLogger(__name__)


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
data_path = Path('JEOPARDY_QUESTIONS1.json')
out_data_path = Path('OUT_JEOPARDY_QUESTIONS.json')
'''
Data is of the form of a list of objects with the following keys:
    category
    air_date
    question
    value (as a string, like '$200')
    answer
    round (i.e., Jeopardy, Double Jeopardy, Final Jeopardy)
    show_number
'''

system_prompt = '''You are an assistant coming up with plausible but incorrect answers to Jeopardy questions (just the answer, no "what is"). Here's an example:\n
Q: 'For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory'
Category: HISTORY
Correct Answer: Copernicus\n
Response: Brahe'''

def make_user_prompt(clue):
    user_prompt = f"Q: '{clue['question']}'\nCategory: {clue['category']}\nCorrect Answer: {clue['answer']}\n\nResponse: "
    return user_prompt

def get_chat_completion(system_message, user_message):
    try:
        completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ])
    except Exception as e:
        log.error(e)
        return None, 0
    return completion.choices[0].message.content, completion.usage.total_tokens


def main():
    with open(data_path, 'r') as f:
        data = json.load(f)
    if out_data_path.exists():
        with open(out_data_path, 'r') as f:
            out_data = json.load(f)
    else:
        out_data = []
    clues_done = set([clue['question'] for clue in out_data])
    total_tokens = 0
    num_clues = 0
    for i in range(100):
        clue = data[i]
        if 'href' in clue or clue in clues_done:
            continue
        user_prompt = make_user_prompt(clue)
        wrong_answer, toks = get_chat_completion(system_prompt, user_prompt)
        total_tokens += toks
        while wrong_answer is None:
            sleep(2)
            wrong_answer, toks = get_chat_completion(system_prompt, user_prompt)
            total_tokens += toks
        new_clue = clue.copy()
        new_clue['wrong_answer'] = wrong_answer
        print(new_clue)
        out_data.append(new_clue)
        clues_done.add(new_clue['question'])
        num_clues += 1
        if i % 100 == 0:
            print(f'Total tokens: {total_tokens}')
            print(f"Tokens per question: {total_tokens/num_clues}")
            with open(out_data_path, 'w') as f:
                json.dump(out_data, f)
    print(f'Total tokens: {total_tokens}')
    print(f"Tokens per question: {total_tokens/num_clues}")
    with open(out_data_path, 'w') as f:
        json.dump(out_data, f)

if __name__ == '__main__':
    main()
