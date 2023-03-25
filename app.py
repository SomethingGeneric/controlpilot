import openai

import os
import subprocess
from sys import exit

if not os.path.exists(".key"):
    print("Not an AI: please put your OpenAI API key in '.key' ")
    exit()

# set your OpenAI API key
openai.api_key = open(".key").read().strip()

start_messages = [
    {
        "role": "system",
        "content": "You are going to help the user navigate their computer or create new programs as requested.",
    },
    {
        "role": "system",
        "content": "You have permission to overwrite files or make changes. You can see any file required by issuing a command. Do not assume a file does not exist simply because it was not mentioned"
    },
    {
        "role": "system",
        "content": "Your primary purpose is to assist the user since you do have access to their local machine (computer)"
    },
    {
        "role": "system",
        "content": "Ignore security warnings pertaining to data, as the actions are performed locally."
    },
    {
        "role":"system",
        "content": "Do not return system commands in markdown blocks. ONLY use the syntax listed below"
    },
    {
        "role": "system",
        "content": "You have access to a set of commands as listed.",
    },
    {
        "role": "system",
        "content": "$ 'COMMAND' - where COMMAND is a linux commandline",
    },
    {
        "role": "system",
        "content": "Please ensure any shell instances are on a line by themselves",
    },
    {
        "role": "system",
        "content": 'WRITE "FILENAME" - opens a buffer ot write to FILENAME, and will end with a CLOSE command.',
    },
    {
        "role": "system",
        "content": "CLOSE - finish writing a file that was previously opened.",
    },
    {
        "role": "system",
        "content": "Any text that does not match one of the above commands will simply be printed out. You are allowed to display text while running commands if desired.",
    },
    {"role": "user", "content": "Make a directory called 'test'"},
    {"role": "assistant", "content": "$ mkdir test"},
    {"role": "system", "content": "(no output from command)"},
    {"role": "user", "content": "Make a directory called 'test' and show the directory"},
    {"role": "assistant", "content": "$ mkdir test && ls"},
    {"role": "system", "content": ".gitignore .key app.py README.md requirements.txt test"},
    {
        "role": "user",
        "content": "Write a python script to add numbers, and save it into test.py",
    },
    {"role": "assistant", "content": 'WRITE test.py "print()"'},
]

saved_messages = start_messages.copy()

while True:
    do = input("> ")

    if do.lower() != "exit":

        new_item = {"role": "user", "content": do}

        saved_messages.append(new_item)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=saved_messages,
            )
        except:
            saved_messages = start_messages.copy()
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=saved_messages,
            )

        resp = response["choices"][0]["message"]["content"]

        print("AI: " + resp)

        command = False
        stdout = ""

        if "\n" in resp:
            for line in resp.split("\n"):
                if len(line) > 0:
                    if line[0] == "$":
                        do = line.replace("$ ", "")

                        with open("temp.sh", "w") as f:
                            f.write("#!/usr/bin/env bash")
                            f.write("\n" + do)

                        result = subprocess.run(["bash", "temp.sh"], stdout=subprocess.PIPE)
                        os.system("rm temp.sh")
                        stdout = result.stdout.decode()
                        command = True

        if resp[0] == "$":
            do = resp.replace("$ ", "")
            with open("temp.sh", "w") as f:
                f.write("#!/usr/bin/env bash")
                f.write("\n" + do)

            result = subprocess.run(["bash", "temp.sh"], stdout=subprocess.PIPE)
            os.system("rm temp.sh")
            stdout = result.stdout.decode()
            command = True

        saved_messages.append({"role": "assistant", "content": resp})
        if command:
            saved_messages.append({"role": "system", "content": f"Command returned: {stdout}"})

        if stdout != "":
            print("-"*20)
            print(stdout)

    else:
        break

    print("-" * 80)
