import subprocess
import os
import sys

# Change this to true if the student files contain static methods.
# Leave it as False if the student files contain a class
contains_static_methods = False

folder_directory = os.path.dirname(os.path.realpath(__file__))


def writeJavaFile(file, testfile):
    txtFile = open(file, 'r')
    txtContents = txtFile.read()
    txtContents = txtContents.replace(
        'public class Fraction', 'class Fraction')
    txtFile.close()

    mainTxt = open(testfile, 'r')
    main_method = mainTxt.read()
    mainTxt.close()

    javaFile = open('ActiveFile.java', 'w')
    javaFile.write(main_method)
    javaFile.write(txtContents)
    if contains_static_methods:
        javaFile.write('}')
    javaFile.close()


def compileJava():
    output = ''
    try:
        subprocess.check_output(['javac', 'ActiveFile.java'], stderr=subprocess.STDOUT).communicate()[0]
        
    except subprocess.CalledProcessError as e:
        err_message = e.output
        output += "Error with file:\n%s\n" % err_message
    except Exception, e:
        subprocess.check_output(['javac', 'ActiveFile.java'])
        output += subprocess.check_output(['java', 'ActiveFile'])

    delete_files()
    return output


def delete_files():
    try:
        if os.path.isfile('ActiveFile.class'):
            os.remove('ActiveFile.class')
        if os.path.isfile('ActiveFile.java'):
            os.remove('ActiveFile.java')
        for file in os.listdir(folder_directory):
            if file.endswith('.class'):
                os.remove(file)
    except:
        print("Could not delete files")
    

def get_test_files():
    testfiles = []
    for file in os.listdir(folder_directory):
        if file.endswith('.java'):
            fileList.append(file)
    return testfiles


fileList = []
testfiles = get_test_files()
delete_files()
if os.path.isfile('ProgramResults.txt'):
    os.remove('ProgramResults.txt')

for file in os.listdir(folder_directory):
    if file.endswith('.txt'):
        fileList.append(file)

outputFile = ''

for file in fileList:
    outputFile += file + '\n'
    for test in testfiles:
        writeJavaFile(file, test)
        outputFile += compileJava()
        outputFile += '\n'
    print '%s Complete'%file

finalSolutions = open('ProgramResults.txt', 'w')
finalSolutions.write(outputFile)
finalSolutions.close()

subprocess.call(['open', '-a', 'TextEdit', 'ProgramResults.txt'])
