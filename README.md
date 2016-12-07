# Java-Grader

Java-Grader is a python program written for Computer Science teachers to help evaluate student work. It works by compiling and running individual java classes/methods and then writting each program's output to a text file.  In addition, each individual program can be run through a variety of different sinareos to see how the program performs in different situations.

## Quick Start

1. Download and install python 2.7 if you don't already have it.
2. Place all of the programs that you want to evaluate (as `txt` files) into a folder.
3. Download the python program to the same directory.
4. Place as many tests as you would like (as `java` files) in the same directory.
5. Execute the python program.

### How it Works

Java-Grader works by writing the contents of the first `java` test file to a new `java` file followed by the contents of the first `txt` file.  The new java file is then compiled and executed.  Everything written to the console is captured and written to a new txt file.  This is repeated with each test file before moving on to the next txt file.  The end result is a single txt file called `ProgramResults` that contains the output of every test with every file.
