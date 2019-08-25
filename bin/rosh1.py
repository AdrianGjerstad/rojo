#!/usr/bin/env python3

import readline
from datetime import datetime
import os
import sys

import rojo_interpreter as rojint

MODE_DEBUG = False

SHELL_VERSION = "1"
INT_VERSION = rojint.version

if len(sys.argv) > 1:
    if sys.argv[1] == "--private_restarted":
        print("\033[1m\033[34mRestart completed!\033[0m")
        sys.argv.remove("--private_restarted")
    else:
        print("Rojo Shell v%s (ROSH%s) (rojo%s, UTC:%s)" % (SHELL_VERSION, SHELL_VERSION, INT_VERSION, datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")))
        print("Running on " + os.uname().sysname + " " + os.uname().machine)
        print("Run ROSH commands by prefixing the line with '!'")
        print("Type \"!help\", \"!copyright\", \"!credits\", or \"!license\" for more information.")

    for i in range(len(sys.argv)):
        if sys.argv[i] == "--debug":
            if MODE_DEBUG:
                sys.argv.pop(i)
            else:
                MODE_DEBUG = True

else:
    print("Rojo Shell v%s (ROSH%s) (rojo%s, UTC:%s)" % (SHELL_VERSION, SHELL_VERSION, INT_VERSION, datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")))
    print("Running on " + os.uname().sysname + " " + os.uname().machine)
    print("Run ROSH commands by prefixing the line with '!'")
    print("Type \"!help\", \"!copyright\", \"!credits\", or \"!license\" for more information.")

while True:
    text = ""

    try:
        text = input("\033[1m\033[32mrosh%s \033[34m>\033[0m " % (SHELL_VERSION))
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt (Use !exit instead)")
        continue

    text = text.strip()

    if len(text) == 0:
        continue

    if text[0] == "!":
        args = []

        if text.find(" ") != -1:
            command = text[1:text.find(" ")]
            args = text[text.find(" ")+1:].split(" ")
        else:
            command = text[1:]

        if command == "exit":
            if len(args) <= 1:
                print("Exiting...")
                if len(args) == 1:
                    exit(int(args[0]))
                break
            else:
                print("Unexpected ROSH command argument: %s" % (args[1]))
                print("ArgImbalanceError (!exit has one argument max)")
        elif command == "help":
            print("ROSH%s commands (Prefixed with '!')" % (SHELL_VERSION))
            print("         !exit  Closes the shell")
            print("                code: The exit code (Default 0)")
            print("         !help  Displays this screen")
            print("")
            print("    !copyright  Displays copyright information about the shell and interpreter")
            print("      !credits  Displays credits for shell and interpreter")
            print("      !license  Displays license information about the shell and interpreter")
            print("")
            print("      !version  Displays the version of the shell and interpreter")
            print("         !read  Displays all of the data from a file with line numbers")
            print("                filename: The name of the file for reading")
            print("        !clear  Clears the screen")
            print("      !restart  Resets the current process with any code changes implemented")
            print("                ...args: New flags and arguments to give the new process.")
            print("                         (Default: current args)")
            print("")
            print("        !debug  Sets the debug mode (Shows token list and AST)")
            print("                mode: Wether to turn debug off (Optional. Shows debug mode")
            print("                      if no arguments are present)")

        elif command == "copyright":
            if len(args) == 0:
                print("Copyright (c) 2019 Adrian Gjerstad. Type \"!license\" for license details.")
            else:
                print("ArgImbalanceError (!copyright does not take arguments)")
        elif command == "credits":
            if len(args) == 0:
                print("Thanks to the creator and contributors of Rojo and its shells (ROSH).")
                print("Creator: Adrian Gjerstad")
                print("Thanks to the creators of Python for the beautiful language that Rojo is built on.\n")
                print("(Python Credits)")
                credits()
            else:
                print("ArgImbalanceError (!credits does not take arguments)")
        elif command == "license":
            if len(args) == 0:
                print("ROSH%s and rojo%s and other Rojo works are licensed under the GNU GPLv3." % (SHELL_VERSION, INT_VERSION))
                print("Rojo is OpenSource, so you can contribute to Rojo. With your help,")
                print("We can grow as a community!\n")
                print("Rojo is distributed WITHOUT WARRANTY, NOT EVEN FOR MERCHANTIBILITY OR FITNESS.")
            else:
                print("ArgImbalanceError (!license does not take arguments)")
        elif command == "version":
            if len(args) == 0:
                print("Rojo Shell v%s (ROSH%s) using Rojo v%s" % (SHELL_VERSION, SHELL_VERSION, INT_VERSION))
                print("ROSH versions are integers, because the shell doesn't get updated that often.")
            else:
                print("ArgImbalanceError (!version does not take arguments)")
        elif command == "read":
            if len(args) == 1:
                try:
                    data = open(args[0], "r").read()
                except FileNotFoundError:
                    print("\033[1m\033[31mFile at `" + os.environ["PWD"] + "/" + args[0] + "` does not exist.\033[0m")
                    continue
                print("\033[1m\033[35mShowing data from " + os.environ["PWD"] + "/" + args[0] + "\033[0m")
                data = data.split("\n")

                num_len = len(str(len(data)))
                for i in range(len(data)):
                    num_len_now = len(str(i+1))
                    print("\033[1m\033[32m\033[7m%s%s\033[0m %s" % (str(i+1), " " * (num_len - num_len_now), data[i]))
            else:
                print("ArgImbalanceError (!read takes one argument)")
        elif command == "clear":
            if len(args) == 0:
                print("\033[2J\033[1;1H\033[1m\033[35mCleared.\033[0m")
            else:
                print("ArgImbalanceError (!clear does not take arguments)")
        elif command == "restart":
            for i in range(len(sys.argv)-1):
                args.append(sys.argv[i+1])
            if len(args) == 0:
                print("\033[1m\033[35mRestarting without args...\033[0m")
            else:
              print("\033[1m\033[35mRestarting with args %s...\033[0m" % (str(args)[1:len(str(args))-1]))
            print("\033[1m\033[33m\033[7mNOTE:\033[0m\033[1m\033[33m Code history will be reset, as the process is replaced.\033[0m")

            args.insert(0, "--private_restarted")
            args.insert(0, "arg_placeholder")
            os.execvp(sys.argv[0], args)
        elif command == "debug":
            if len(args) == 1:
                if args[0].lower() == "true" or args[0].lower() == "on":
                    if not MODE_DEBUG:
                        MODE_DEBUG = True
                        sys.argv.append("--debug")
                        print("\033[1m\033[34mDEBUG MODE: \033[0mOn")
                elif args[0].lower() == "false" or args[0].lower() == "off":
                    if MODE_DEBUG:
                        MODE_DEBUG = False
                        sys.argv.remove("--debug")
                        print("\033[1m\033[34mDEBUG MODE: \033[0mOff")
                else:
                    print("UnkownArgError (!debug takes [true|on|false|off])")
            elif len(args) == 0:
                print("\033[1m\033[34mDEBUG MODE: \033[0m" + "On" if MODE_DEBUG else "Off")
            else:
                print("ArgImbalanceError (!debug takes one argument max)")
        else:
            print("Unknown ROSH%s command: %s" % (SHELL_VERSION, text))

        continue

    # Not a ROSH command, lex, parse, and interpret

    result, error = rojint.run("<stdin>", text, {"debug":MODE_DEBUG})

    if error:
        print(error)
    else:
        print("\033[1m\033[30mret\033[0m   \033[1m\033[34m<\033[0m " + str(result))
