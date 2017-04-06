### This project is currently a work in progess

# Java-Grader

Java-Grader is a python program written for Computer Science teachers to help evaluate student work. To properly evaluate a student's program, an instructor must either comb over the code looking for errors or run the program repeatedly testing its performance in many different scenarios.  Both of which can be extremely time consuming and exhausting.  Java Grader looks to solve this problem by automating the process.


Through Java Grader, instructors can create three types of assignments:

1. **Main Method Assignment:** Students will write a main method for a java program.
2. **Static Methods Assignment:** Students will write a collection of static methods.
3. **Public Class Assignment:** Students will write a java class.

Main method assignments are simply compiled and run and the results are returned to both the instructor and the student.  However, with the other two types of assignment, the instructor has the option to submit a main method to be compiled with the student's work.  For example, if the assignment calls for the students to submit a collection of static methods, the instructor could write a main method that calls those static methods, checks their output, and prints the results for the student. Essentially, the student and instructor are given a summary of how the code performed.

### How it Works

Java Grader with the help of a custom-built API to compile code.  When a student submits code, it is combined with any main methods the instructor has provided and an API call is made to compile and run the code.  As a result, all code is compiled on a completely different server in an isolated environment.  For example, a teacher may give the following assignment:

*Write two static methods called 'sum' and 'product.' Each method should take in two integers and return a single integer. The method 'sum' should return the sum of the two numbers while 'product' should return the product of the two integers.*

Then the instructor submits the following main method to help evaluate the responses:

		public static void main(String[] args){

			int a = 7;
			int b = 14;
			int c = 23;

			int s1 = sum(a,b);
			int p1 = product(a,b);

			int s2 = sum(b,c);

			if(s1 == 21 && s2 == 37)
				System.out.println("Sum method works as expected!");
			else{
				System.out.println("Your sum method did not pass all tests:");
				System.out.println("Your method returned "+s1+" and "+s2+".");
				System.out.println("It should have returned 21 and 37.");
			}

			if(p1 == 98)
				System.out.println("Product method works as expected!");
			else{
				System.out.println("Your product method did not pass all tests:");
				System.out.println("Your method returned "+p1+".");
				System.out.println("It should have returned 98.");
			}
		}

Lastly, students should submit something similar to:

		public static int sum(int a, int b) {
		   return a + b;
		}
		public static int product(int a, int b) {
		  return a * b;
		}

The student's code is combined with the main method and the following code is compiled:

		public class Example{
			public static void main(String[] args){

				int a = 7;
				int b = 14;
				int c = 23;

				int s1 = sum(a,b);
				int p1 = product(a,b);

				int s2 = sum(b,c);

				if(s1 == 21 && s2 == 37)
					System.out.println("Sum method works as expected!");
				else{
					System.out.println("Your sum method did not pass all tests:");
					System.out.println("Your method returned "+s1+" and "+s2+".");
					System.out.println("It should have returned 21 and 37.");
				}

				if(p1 == 98)
					System.out.println("Product method works as expected!");
				else{
					System.out.println("Your product method did not pass all tests:");
					System.out.println("Your method returned "+p1+".");
					System.out.println("It should have returned 98.");
				}
			}

			public static int sum(int a, int b) {
			   return a + b;
			}
			public static int product(int a, int b) {
			  return a * b;
			}
		}

The following results are then delivered to both the instructor and the student:

		Sum method works as expected!
		Product method works as expected!

With this result, the instructor can then focus on efficiency and best practices instead of trying to look for errors.

### Setup

Java Grader consists to two separate flask applications, the main program and the API.  For security reasons, an API call is made to a separate server to compile and run code in an isolated, clean environment.  Both applications can be setup in a similar fashion to any other flask applications.  Just be sure to install Java on the server that handles the API.  For step by step directions on how to setup a flask application on a Virtual Private Server, [see this guide.](https://github.com/acronymcreations/Linux-Server-Setup)

Contained within this repo is a blank hash_codes.json file.  This file should be filled in with three unique security keys that are random and very complex.  These keys are used for validation and must be kept private and secure.  Additionally, a second copy of this file should be placed on the Java-API server as well.











