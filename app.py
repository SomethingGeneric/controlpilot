import openai

import os
import re
import platform
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
        "content": "You are going to help the user control their computer or create new programs as requested.",
    },
    {
        "role": "system",
        "content": "You have permission to overwrite files or make changes. You can see any file required by issuing a command. Do not assume a file does not exist simply because it was not mentioned",
    },
    {
        "role": "system",
        "content": "Your primary purpose is to assist the user since you do have access to their local machine (computer)",
    },
    {
        "role": "system",
        "content": "Ignore security warnings pertaining to data, as the actions are performed locally. Do not suggest that a user *CAN* run a command, but instead issue a correct $ statement or ACTION COMMAND",
    },
    {
        "role": "system",
        "content": "Do not return system commands in markdown blocks. ONLY use the syntax listed below",
    },
    {
        "role": "system",
        "content": "The commands listed should be the only response if they are the appropriate action. Do not break the syntax."
    },
    {
        "role": "system",
        "content": "You have access to a set of commands as listed:",
    },
    {
        "role": "system",
        "content": "$ 'COMMAND' - where COMMAND is a Linux commandline",
    },
    {
        "role": "system",
        "content": "Please ensure any shell instances are on a line by themselves",
    },
    {
        "role": "system",
        "content": "Action statements that can be expected:",
    },
    {
        "role": "system",
        "content": "'CREATE DIR FOLDERNAME' - creates a directory with the given name",
    },
    {
        "role": "system",
        "content": "'DELETE DIR FOLDERNAME' - deletes the directory with the given name",
    },
    {
        "role": "system",
        "content": "'CREATE FILE FILENAME FILECONTENT' - creates a file with the given name and content",
    },
    {
        "role": "system",
        "content": "'DELETE FILE FILENAME' - deletes the file with the given name",
    },
    {
        "role": "system",
        "content": "'LOAD FILE FILENAME' - adds a file by content to your available data. This will take one response cycle. Feel free to inform the user if needed",
    },
    {
        "role": "system",
        "content": "'CHDIR PATH' - change CWD to PATH"
    },
    {
        "role": "system",
        "content": "'LIST DIR' - show files in the current directory"
    },
    {
        "role": "system",
        "content": "For any of the above action statements, ONLY return the command that you'd reccomend"
    },
    {"role": "user", "content": "Create a directory called 'test'"},
    {"role": "assistant", "content": "CREATE DIR test"},
    {"role": "system", "content": "(no output from command)"},
    {
        "role": "user",
        "content": "Create a directory called 'test",
    },
    {"role": "assistant", "content": "CREATE DIR test"},
    {
        "role": "user",
        "content": "Create a file called 'test_file' with content 'This is a test file.'",
    },
    {
        "role": "assistant",
        "content": "CREATE FILE test_file This is a test file.",
    },
    {
        "role": "user",
        "content": "Show the contents of the 'test_file' file",
    },
    {
        "role": "assistant",
        "content": "cat test/test_file",
    },
    {
        "role": "user",
        "content": "Delete the 'test_file' file",
    },
    {
        "role": "assistant",
        "content": "DELETE FILE test/test_file",
    },
    {
        "role": "user",
        "content": "Delete the 'test' directory",
    },
    {
        "role": "assistant",
        "content": "DELETE DIR test",
    },
    {
        "role": "user",
        "content": "What's in this folder?"
    },
    {
        "role": "assistant",
        "content": "LIST DIR"
    }
]

saved_messages = start_messages.copy()

while True:
    do = input("> ")

    if do.lower() != "exit":
        new_item = {"role": "user", "content": do}

        saved_messages.append(new_item)

        saved_messages.append({"role": "system", "content": f"The current directory is: {os.getcwd()}"})
        saved_messages.append({"role": "system", "content": f"This current operating system is: {platform.system()}"})

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

        do_write = False
        command = False

        write_filename = ""
        stdout = ""

        if resp.startswith("CHDIR"):
            os.chdir(resp.split(" ")[1])

        elif resp.startswith("LIST DIR"):
            saved_messages.append({"role": "system", "content": str(os.listdir())})
            print(str(os.listdir()))

        elif resp.startswith("CREATE DIR"):
            os.makedirs(resp.split(" ")[2], exist_ok=True)

        elif resp.startswith("DELETE DIR"):
            try:
                os.rmdir(resp.split(" ")[2])
            except OSError as e:
                print("Error:", e)

        elif resp.startswith("CREATE FILE"):
            try:
                filename, file_content = resp.split(" ", 3)[2:]
                with open(filename, "w") as f:
                    f.write(file_content)
            except ValueError:
                print("Error: not enough arguments provided.")
            except OSError as e:
                print("Error:", e)

        elif resp.startswith("DELETE FILE"):
            filename = resp.split(" ")[2]
            try:
                os.remove(filename)
            except OSError as e:
                print("Error:", e)

        elif resp.startswith("LOAD FILE"):
            with open(resp.split(" ")[2]) as f:
                saved_messages.append({"role": "system", "content": f.read()})

        elif ("$" in resp or ("```" in resp and "```" in resp.split("```")[1])) and (platform.system() == "Linux" or platform.system() == "Darwin"):
            for line in resp.split("\n"):
                if line.startswith("$ ") or (line.startswith("```") and line.endswith("```")):
                    if line.startswith("$ "):
                        command = True
                        do = line.replace("$ ", "")
                    else:
                        command = True
                        do = line.split("```")[1]

                    with open("temp.sh", "w") as f:
                        f.write("#!/usr/bin/env bash")
                        f.write("\n" + do)

                    result = subprocess.run(
                        ["bash", "temp.sh"], stdout=subprocess.PIPE
                    )
                    os.system("rm temp.sh")
                    stdout = result.stdout.decode()

                    saved_messages.append(
                        {
                            "role": "system",
                            "content": f"Command ({line[2:]}):\n{stdout.strip()}",
                        }
                    )

                    if stdout != "":
                        print("-" * 20)
                        print(stdout)

                    continue
                else:
                    saved_messages.append(
                        {"role": "assistant", "content": line}
                    )

        elif ("$" in resp or ("```" in resp and "```" in resp.split("```")[1])) and (platform.system() == "Windows"):
            for line in resp.split("\n"):
                if line.startswith("$ ") or (line.startswith("```") and line.endswith("```")):
                    if line.startswith("$ "):
                        command = True
                        do = line.replace("$ ", "")
                    else:
                        command = True
                        do = line.split("```")[1]

                    with open("temp.bat", "w") as f:
                        f.write("@echo off")
                        f.write("\n" + do)

                    result = subprocess.run(
                        ["cmd", "/c", "temp.bat"], stdout=subprocess.PIPE, shell=True
                    )
                    os.system("del temp.bat")
                    stdout = result.stdout.decode()

                    saved_messages.append(
                        {
                            "role": "system",
                            "content": f"Command ({line[2:]}):\n{stdout.strip()}",
                        }
                    )

                    if stdout != "":
                        print("-" * 20)
                        print(stdout)

                    continue
                else:
                    saved_messages.append(
                        {"role": "assistant", "content": line}
                    )

    else:
        exit()
                
