### This project is currently in the process of going from a stand-alone program to a full web application.

# Java-Grader

Java-Grader is a python program written for Computer Science teachers to help evaluate student work. It works by taking students' classes/methods and adding custom main methods (test files) to them to create a complete java programs.  The programs are then compiled and executed where all output is captured and written to a text file.  It can add multiple main methods to each method/class as well.

## Quick Start

1. Download and install python 2.7 if you don't already have it.
2. Place all the programs that you want to evaluate (as `.txt` files) into a folder.
3. Download `AutomaticGrader.py` to the same directory.
4. Place as many tests as you would like (as `.java` files) in the same directory.
5. Execute the python program.

### How it Works

Each student's static methods/class should be in the form of a `.txt` file, while each test file should be in the form of a `.java` file.

Java-Grader works by writing the contents of the first `.java` test file to a new `.java` file followed by the contents of the first `.txt` file.  The new java file is then compiled and executed.  Everything written to the console is captured and written to a new `.txt` file.  This is repeated with each test file before moving on to the next `.txt` file.  The result is a single `.txt` file called `ProgramResults.txt` that contains the output of every test with every file.

### Test Files

All test files must start with `public class ActiveFile {` for them to compile correctly!  In addition, the file should include a complete main method that utilizes the static methods/classes from the students' `.txt` files.  Additional static methods can also be added to the bottom of the test files if needed.  Multiple test files can be included if you would like to run a variety of tests.  The output from each test file will be written to the `ProgramResults.txt` file in alphabetical order.  If student files contain static methods, do not include the final closing bracket for the package.  Instead, you will need to change the variable `contains_static_methods` to `True` at the top of the python program.  Otherwise, close the package bracket per usual.

### Student Files

Student files should not include any package information or a main method.  Results are written to `ProgramResults.txt` per the file name so it is recommended for students to name the file after themselves.  If an error is thrown, (and not caught) the error is recorded in `ProgramResults.txt` as well.  If student files contain classes, the classes cannot be public.  For example, if the student file contains the class `Matrix`, then the file should start with `class Matrix {` not `public class Matrix {`.
